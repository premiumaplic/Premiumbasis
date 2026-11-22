"""Панель центра — приложение владельца (docs/owner/).

Кнопка «📊 Панель центра» под полем ввода у владельца. Все данные — в ссылке кнопки (сжатый JSON):
итоги недели по центру, учителя, группы, ученики по станциям, кому нужна помощь, кого похвалить.
Из панели владелец может отправить боту команду (sendData): напомнить учителям, сводка, бэкап.

В ссылке об учениках и учителях — только имя и первая буква фамилии, остальное — номера.
"""

import json
from datetime import date, timedelta

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

from bot import hints, hub, profiles, progress, repo, reports, rules, schedule
from bot.payload import SEND_DATA_LIMIT, byte_size, encode_param
from bot.texts import t

PANEL_LIMIT = 6000
WEEKS = 8
TOP = 12
OWNER_ACTIONS = ("o_remind", "o_summary", "o_backup", "o_export")
BTN_PANEL = "📊 Панель центра"
BTN_MENU = "☰ Меню владельца"
NEED_HELP = ("exam_risk", "drop", "homework", "absent", "late", "unclear")


def _level(con, group_id: int, week: date) -> int:
    row = con.execute("SELECT avg(a.value) FROM weekly_answers a JOIN weekly_reports r ON r.id = a.report_id "
                      "WHERE r.group_id = ? AND r.week_start = ?", (group_id, week.isoformat())).fetchone()
    return -1 if row[0] is None else min(9, round(row[0] * 3))


def _skills(con, g) -> int:
    """Средний общий рейтинг учеников группы по последним оценкам ×10 (74 = 7.4), -1 — нет оценок."""
    ids = [s["id"] for s in repo.group_students(con, g["id"])]
    vals = [profiles.overall(items[0]["v"]) for items in profiles.latest_ratings(con, ids, g["subject"]).values()]
    vals = [v for v in vals if v is not None]
    return round(sum(vals) / len(vals) * 10) if vals else -1


def payload(con, today: date) -> dict:
    week = reports.week_start(today)
    weeks = [week - timedelta(weeks=i) for i in range(WEEKS - 1, -1, -1)]
    teachers = repo.list_teachers(con, only_active=True)
    t_index = {t["id"]: i for i, t in enumerate(teachers)}
    groups = repo.list_groups(con)

    g_rows, risk, good = [], [], []
    for g in groups:
        n = g["student_count"]
        done = n - len(reports.students_without_report(con, g["id"], week))
        stars = con.execute("SELECT count(*) FROM weekly_reports WHERE group_id = ? AND week_start = ? AND star = 1",
                            (g["id"], week.isoformat())).fetchone()[0]
        open_hints = hints.open_hints(con, g["id"])
        timing = hub.timing(g, today)
        g_rows.append([g["id"], g["name"], t_index.get(g["teacher_id"], -1), g["subject"],
                       g["subject_ru"], g["stage_ru"] or "", n, done, _level(con, g["id"], week),
                       _level(con, g["id"], week - timedelta(weeks=1)), len(open_hints),
                       timing["exd"], timing["wkn"], timing["wkt"], stars, _skills(con, g)])
        for h in open_hints:
            title, why = hints.parts(con, h, "ru")
            rule = h["rule"].split(":")[0]
            item = [repo.short_name(h["full_name"]), g["name"], title, why]
            if rule in NEED_HELP:
                risk.append(item)
            elif rule == "growth":
                good.append(item)
        for r in con.execute("SELECT s.full_name FROM weekly_reports r JOIN students s ON s.id = r.student_id "
                             "WHERE r.group_id = ? AND r.week_start = ? AND r.star = 1", (g["id"], week.isoformat())):
            good.append([repo.short_name(r["full_name"]), g["name"], "⭐ Звезда недели", ""])

    # отчёты по неделям: сколько заполнено из скольких (ученики — по записям в группы на ту неделю)
    hist = []
    for w in weeks:
        done = con.execute("SELECT count(*) FROM weekly_reports r JOIN groups g ON g.id = r.group_id "
                           "WHERE g.active = 1 AND r.week_start = ?", (w.isoformat(),)).fetchone()[0]
        total = con.execute(
            "SELECT count(*) FROM enrollments e JOIN groups g ON g.id = e.group_id JOIN students s ON s.id = e.student_id "
            "WHERE g.active = 1 AND s.active = 1 AND e.date_from <= ? AND (e.date_to IS NULL OR e.date_to > ?)",
            ((w + timedelta(days=6)).isoformat(), w.isoformat())).fetchone()[0]
        hist.append([w.isoformat(), done, total])

    grades = [0, 0, 0, 0]
    for r in con.execute("SELECT a.value, count(*) AS k FROM weekly_answers a JOIN weekly_reports r ON r.id = a.report_id "
                         "WHERE r.week_start = ? GROUP BY a.value", (week.isoformat(),)):
        grades[r["value"]] = r["k"]

    dist = []
    for subj in repo.list_subjects(con):
        if not subj["has_map"]:
            continue
        counts = {r["stage_id"]: r["k"] for r in con.execute(
            "SELECT ss.stage_id, count(DISTINCT ss.student_id) AS k FROM student_stage ss "
            "JOIN students s ON s.id = ss.student_id WHERE ss.subject = ? AND ss.status = 'current' AND s.active = 1 "
            "GROUP BY ss.stage_id", (subj["code"],))}
        stages = [[s["name_ru"], counts.get(s["id"], 0), s["section_ru"]] for s in progress.ordered(con, subj["code"])]
        if any(c for _, c, _ in stages):
            dist.append([subj["name_ru"], stages])

    students = con.execute("SELECT count(*) AS n, sum(consent) AS c FROM students s WHERE s.active = 1 AND EXISTS ("
                           "SELECT 1 FROM enrollments e WHERE e.student_id = s.id AND e.date_to IS NULL)").fetchone()
    return {
        "v": 2, "f": "owner", "lang": "ru", "today": today.isoformat(), "wk": week.isoformat(),
        "center": repo.get_setting(con, "center_name"), "att": repo.attendance_on(con),
        "k": [students["n"] or 0, students["c"] or 0, len(groups), len(teachers)],
        "t": [[t["id"], repo.short_name(t["name"]), 1 if repo.is_support(t) else 0] for t in teachers],
        "g": g_rows, "hist": hist, "grades": grades, "dist": dist,
        "risk": risk[:TOP], "good": good[:TOP],
    }


def url(con, conf, today: date | None = None) -> str | None:
    data = payload(con, today or schedule.today())
    link = f"{conf.forms_url}owner/#d={encode_param(data)}"
    # не помещается — сначала без списков учеников, потом без станций, потом только первые группы
    for step in ("lists", "dist", "groups"):
        if len(link) <= PANEL_LIMIT:
            return link
        if step == "lists":
            data["risk"], data["good"] = data["risk"][:4], data["good"][:4]
        elif step == "dist":
            data["dist"] = []
        else:
            data["g"] = sorted(data["g"], key=lambda g: g[7] - g[6])[:40]   # сначала отстающие
        link = f"{conf.forms_url}owner/#d={encode_param(data)}"
    return link if len(link) <= PANEL_LIMIT else None


def owner_row(con, conf) -> list[KeyboardButton]:
    link = url(con, conf)
    row = [KeyboardButton(text=BTN_PANEL, web_app=WebAppInfo(url=link))] if link else []
    return row + [KeyboardButton(text=BTN_MENU)]


def keyboard(con, conf, teacher=None) -> ReplyKeyboardMarkup:
    """Кнопки владельца под полем ввода (если владелец ещё и учитель — плюс его группы)."""
    row = owner_row(con, conf)
    if teacher is not None:
        markup = hub.teacher_keyboard(con, conf, teacher, extra=row)
        if markup is not None:
            return markup
    return ReplyKeyboardMarkup(resize_keyboard=True, is_persistent=True,
                               keyboard=[row, [KeyboardButton(text=t("btn_refresh", "ru"))]],
                               input_field_placeholder="Панель центра или меню")


def parse_action(raw: str) -> str | None:
    """Команда из панели владельца или None (это не команда панели)."""
    if byte_size(raw) > SEND_DATA_LIMIT:
        return None
    try:
        data = json.loads(raw)
    except ValueError:
        return None
    if not isinstance(data, dict) or data.get("v") != 1 or data.get("t") not in OWNER_ACTIONS:
        return None
    if not isinstance(data.get("u"), str) or not _uuid_ok(data["u"]):
        return None
    return data["t"] + ":" + data["u"]


def _uuid_ok(value: str) -> bool:
    from bot.forms import UUID_RE
    return bool(UUID_RE.match(value))


def exams_soon(con, today: date, days: int = 21) -> list[tuple[date, object]]:
    out = []
    for g in repo.list_groups(con):
        exam = rules.next_exam_for(g, today)
        if exam and (exam - today).days <= days:
            out.append((exam, g))
    return sorted(out, key=lambda x: x[0])
