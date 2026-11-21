"""Подсказки учителю — простые правила по посещаемости и недельным отчётам.

Пороги — в settings (стартовые предположения, владелец подстроит через месяц):
  • 2 пропуска подряд или 3 за месяц                    → «Свяжитесь с родителем»
  • 3 опоздания за 2 недели                             → «Обсудите опоздания»
  • домашка «не сделано»/«частично» 2 недели подряд     → «Домашка проседает»
  • показатель упал на 2 ступени от среднего за 4 недели → «Резкий спад: …»
  • за 3 недели до экзамена уровень ниже проходного     → «Риск не сдать экзамен»
  • рост 3 недели подряд                                → «Похвалите»

Одна подсказка по одному правилу и ученику не повторяется, пока её не закрыли
или пока условие не исчезло. Под каждой подсказкой — почему она появилась.
"""

import json
from datetime import date, datetime, timedelta

from bot import repo, reports, rules, schedule

TITLES = {
    "absent": {"ru": "Свяжитесь с родителем", "uz": "Ota-ona bilan bogʻlaning"},
    "late": {"ru": "Обсудите опоздания", "uz": "Kechikishlarni muhokama qiling"},
    "homework": {"ru": "Домашка проседает", "uz": "Uy vazifasi pasaymoqda"},
    "drop": {"ru": "Резкий спад: {q}", "uz": "Keskin pasayish: {q}"},
    "exam_risk": {"ru": "Риск не сдать экзамен", "uz": "Imtihondan oʻta olmaslik xavfi"},
    "growth": {"ru": "Похвалите", "uz": "Maqtang"},
}
WHY = {
    "absent": {"ru": "пропуски: {dates}", "uz": "kelmagan kunlar: {dates}"},
    "late": {"ru": "опоздания: {dates}", "uz": "kechikishlar: {dates}"},
    "homework": {"ru": "недели: {weeks}", "uz": "haftalar: {weeks}"},
    "drop": {"ru": "в среднем было {was}, стало {now} (из 3)", "uz": "oʻrtacha {was} edi, endi {now} (3 dan)"},
    "exam_risk": {"ru": "экзамен {date}, уровень {level}% при проходном {need}%",
                  "uz": "imtihon {date}, daraja {level}%, oʻtish uchun {need}%"},
    "growth": {"ru": "средний балл растёт {n} недели подряд", "uz": "oʻrtacha ball {n} hafta ketma-ket oʻsmoqda"},
}


def _dates(days: list[str], lang: str) -> str:
    items = [schedule.human_date(date.fromisoformat(d), lang) for d in sorted(days)]
    joiner = " и " if lang == "ru" else " va "
    return joiner.join([", ".join(items[:-1]), items[-1]]) if len(items) > 1 else items[0]


def _report_values(con, student_id: int, group_id: int, limit: int) -> list[tuple[date, dict[str, int]]]:
    """Последние отчёты ученика: [(неделя, {код вопроса: значение})], от новых к старым."""
    rows = con.execute(
        "SELECT r.week_start, q.code, a.value FROM weekly_reports r "
        "JOIN weekly_answers a ON a.report_id = r.id JOIN questions q ON q.id = a.question_id "
        "WHERE r.student_id = ? AND r.group_id = ? AND r.week_start IN ("
        "  SELECT week_start FROM weekly_reports WHERE student_id = ? AND group_id = ? "
        "  ORDER BY week_start DESC LIMIT ?)", (student_id, group_id, student_id, group_id, limit)).fetchall()
    out: dict[str, dict[str, int]] = {}
    for r in rows:
        out.setdefault(r["week_start"], {})[r["code"]] = r["value"]
    return [(date.fromisoformat(w), out[w]) for w in sorted(out, reverse=True)]


def check_student(con, student_id: int, g, on: date) -> dict[str, dict]:
    """Какие правила сработали: {ключ правила: детали}."""
    fired: dict[str, dict] = {}
    gid = g["id"]

    # ---- посещаемость (только если владелец её включил)
    att = []
    if repo.attendance_on(con):
        att = con.execute("SELECT lesson_date, status FROM attendance WHERE student_id = ? AND group_id = ? "
                          "AND lesson_date <= ? ORDER BY lesson_date DESC LIMIT 60",
                          (student_id, gid, on.isoformat())).fetchall()
    counted = [r for r in att if r["status"] != "excused"]  # уважительная причина не считается
    streak = []
    for r in counted:
        if r["status"] != "absent":
            break
        streak.append(r["lesson_date"])
    month_ago = (on - timedelta(days=30)).isoformat()
    month = [r["lesson_date"] for r in counted if r["status"] == "absent" and r["lesson_date"] > month_ago]
    if len(streak) >= repo.get_int(con, "hint_absent_streak", 2):
        fired["absent"] = {"dates": streak}
    elif len(month) >= repo.get_int(con, "hint_absent_month", 3):
        fired["absent"] = {"dates": month}

    two_weeks = (on - timedelta(days=14)).isoformat()
    lates = [r["lesson_date"] for r in att if r["status"] == "late" and r["lesson_date"] > two_weeks]
    if len(lates) >= repo.get_int(con, "hint_late_2weeks", 3):
        fired["late"] = {"dates": lates}

    # ---- недельные отчёты (только свежие: последняя неделя — текущая или прошлая)
    history = _report_values(con, student_id, gid, 5)
    current_week = reports.week_start(on)
    if history and history[0][0] >= current_week - timedelta(weeks=1):
        latest_week, latest = history[0]
        n = repo.get_int(con, "hint_homework_weeks", 2)
        recent = history[:n]
        consecutive = all(a[0] - b[0] == timedelta(weeks=1) for a, b in zip(recent, recent[1:]))
        if len(recent) == n and consecutive and all(v.get("homework", 3) <= 1 for _, v in recent):
            fired["homework"] = {"weeks": [w.isoformat() for w, _ in recent]}

        steps = repo.get_int(con, "hint_drop_steps", 2)
        older = history[1:5]
        for code, value in latest.items():
            old = [v[code] for _, v in older if code in v]
            if old and sum(old) / len(old) - value >= steps:
                fired[f"drop:{code}"] = {"code": code, "was": round(sum(old) / len(old), 1), "now": value}

        exam = rules.next_exam_for(g, on)
        if rules.exam_risk(con, student_id, g, latest_week, exam, on):
            stage = repo.stage(con, g["stage_id"])
            levels = rules.week_averages(con, student_id, gid, latest_week, 2)
            level = sum(v for _, v in levels) / len(levels) / 3
            fired["exam_risk"] = {"date": exam.isoformat(), "level": round(level * 100),
                                  "need": round(stage["pass_score"] / stage["max_score"] * 100)}

        if rules.growth_streak(con, student_id, gid, latest_week):
            fired["growth"] = {"n": repo.get_int(con, "hint_growth_weeks", 3)}
    return fired


def evaluate_group(con, group_id: int, on: date | None = None) -> int:
    """Пересчитывает подсказки группы. Возвращает число новых подсказок."""
    on = on or schedule.today()
    g = repo.group(con, group_id)
    if not g or not g["active"]:
        return 0
    now = datetime.now().isoformat(timespec="seconds")
    created = 0
    for s in repo.group_students(con, group_id):
        fired = check_student(con, s["id"], g, on)
        latest = {}
        for row in con.execute("SELECT * FROM hints WHERE student_id = ? AND group_id = ? ORDER BY id",
                               (s["id"], group_id)):
            latest[row["rule"]] = row  # последняя подсказка по каждому правилу
        for rule, details in fired.items():
            text = json.dumps(details, ensure_ascii=False)
            last = latest.get(rule)
            if last is None or last["cleared"]:
                con.execute("INSERT INTO hints (student_id, group_id, rule, details) VALUES (?, ?, ?, ?)",
                            (s["id"], group_id, rule, text))
                created += 1
            elif last["closed_at"] is None:
                con.execute("UPDATE hints SET details = ? WHERE id = ?", (text, last["id"]))
            # закрыта учителем, а условие всё ещё есть — не повторяем
        for rule, last in latest.items():
            if rule not in fired and not last["cleared"]:
                # условие исчезло: подсказка закрывается сама и в будущем может появиться снова
                con.execute("UPDATE hints SET cleared = 1, closed_at = coalesce(closed_at, ?) WHERE id = ?",
                            (now, last["id"]))
    return created


def open_hints(con, group_id: int) -> list:
    return con.execute(
        "SELECT h.*, s.full_name FROM hints h JOIN students s ON s.id = h.student_id "
        "JOIN enrollments e ON e.student_id = h.student_id AND e.group_id = h.group_id AND e.date_to IS NULL "
        "WHERE h.group_id = ? AND h.closed_at IS NULL ORDER BY s.full_name, h.id", (group_id,)).fetchall()


def close(con, hint_id: int, teacher_id: int) -> bool:
    """Закрывает подсказку, если она из группы этого учителя."""
    row = con.execute("SELECT h.id FROM hints h JOIN groups g ON g.id = h.group_id "
                      "WHERE h.id = ? AND g.teacher_id = ? AND h.closed_at IS NULL", (hint_id, teacher_id)).fetchone()
    if not row:
        return False
    con.execute("UPDATE hints SET closed_at = ? WHERE id = ?", (datetime.now().isoformat(timespec="seconds"), hint_id))
    return True


def parts(con, hint, lang: str) -> tuple[str, str]:
    """(заголовок, почему) — для приложения учителя."""
    text = describe(con, hint, lang)
    head, why = text.split("\n", 1)
    title = head.split(" — ", 1)[1] if " — " in head else head
    return title, why.split(": ", 1)[1] if ": " in why else why


def describe(con, hint, lang: str) -> str:
    """«⚠️ Азиз Каримов — Свяжитесь с родителем\nПочему: пропуски 12 и 14 ноября»."""
    rule = hint["rule"].split(":")[0]
    d = json.loads(hint["details"] or "{}")
    suffix = "uz" if lang == "uz" else "ru"
    if rule == "drop":
        q = con.execute("SELECT * FROM questions WHERE code = ?", (d["code"],)).fetchone()
        title = TITLES[rule][lang].format(q=(q[f"text_{suffix}"] if q else d["code"]).lower())
        why = WHY[rule][lang].format(was=str(d["was"]).replace(".", ","), now=d["now"])
    else:
        title = TITLES[rule][lang]
        if rule in ("absent", "late"):
            why = WHY[rule][lang].format(dates=_dates(d["dates"], lang))
        elif rule == "homework":
            weeks = [date.fromisoformat(w) for w in sorted(d["weeks"])]
            why = WHY[rule][lang].format(weeks=", ".join(
                f"{w.strftime('%d.%m')}–{(w + timedelta(days=5)).strftime('%d.%m')}" for w in weeks))
        elif rule == "exam_risk":
            why = WHY[rule][lang].format(date=schedule.human_date(date.fromisoformat(d["date"]), lang),
                                         level=d["level"], need=d["need"])
        else:
            why = WHY[rule][lang].format(n=d.get("n", 3))
    icon = "🌟" if rule == "growth" else "⚠️"
    label = "Почему" if lang == "ru" else "Sababi"
    return f"{icon} {hint['full_name']} — {title}\n{label}: {why}"
