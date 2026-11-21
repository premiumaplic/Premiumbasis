"""Формы Mini App: что бот кладёт в ссылку кнопки и как проверяет присланные данные.

Главное правило: форме ничего не доверяем. Всё, что пришло, проверяется заново по базе:
схема и размер, допустимые значения, принадлежность группы учителю, запись каждого
ученика в группу, даты, UUID отправки (повтор не создаёт дублей).
"""

import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

from bot import exams, hints, progress, repo, reports, schedule
from bot.payload import SEND_DATA_LIMIT, byte_size, encode_param
from bot.texts import t
from bot.timefmt import human_time

ATTENDANCE_DAYS_BACK = 7
WEEKLY_WEEKS_BACK = 1          # можно заполнить текущую и прошлую неделю
COMMENT_MAX = 80
TOPIC_MAX = 100
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
LATE_DELIVERY_SECONDS = 60


# ================================================================ данные для ссылок

def _students(con, group_id: int) -> list:
    return repo.group_students(con, group_id)


def attendance_payload(con, g, lang: str, today: date, students=None) -> dict:
    students = students if students is not None else _students(con, g["id"])
    days = [today - timedelta(days=i) for i in range(ATTENDANCE_DAYS_BACK + 1)]
    saved = reports.attendance_by_date(con, g["id"], days)
    hist = {}
    for back, day in enumerate(days):
        marks = saved.get(day.isoformat())
        if marks:
            hist[str(back)] = "".join(str(reports.ATT_INDEX[marks[s["id"]]]) if s["id"] in marks else "-"
                                      for s in students)
    return {"v": 1, "f": "att", "gid": g["id"], "g": g["name"], "lang": lang, "today": today.isoformat(),
            "days": g["weekdays"], "st": [[s["id"], repo.short_name(s["full_name"])] for s in students],
            "h": hist}


def weekly_payload(con, g, lang: str, today: date, students=None) -> dict:
    students = students if students is not None else _students(con, g["id"])
    questions = reports.questions_for(con, g["subject"])
    current = reports.week_start(today)
    weeks = [current - timedelta(weeks=i) for i in range(WEEKLY_WEEKS_BACK + 1)]
    saved = reports.reports_for_weeks(con, g["id"], weeks)
    before = reports.last_answers_before(con, g["id"], weeks[-1])

    def code(answers: dict) -> str:
        return "".join(str(answers[q["id"]]) if q["id"] in answers else "x" for q in questions)

    answers, comments, stars, goals = {}, {}, {}, {}
    for s in students:
        per_week = {}
        for back, week in enumerate(weeks):
            item = saved.get(s["id"], {}).get(week.isoformat())
            if item:
                per_week[str(back)] = code(item["answers"])
                if item["comment"]:
                    comments.setdefault(str(back), []).append(s["id"])
                if item.get("star"):
                    stars.setdefault(str(back), []).append(s["id"])
                if item.get("goal"):
                    goals.setdefault(str(back), []).append([s["id"], item["goal"]])
        if s["id"] in before:
            per_week["p"] = code(before[s["id"]])  # последний отчёт до самой ранней недели
        if per_week:
            answers[str(s["id"])] = per_week
    suffix = "uz" if lang == "uz" else "ru"
    return {
        "v": 1, "f": "wk", "gid": g["id"], "g": g["name"], "lang": lang, "wk": current.isoformat(),
        "st": [[s["id"], repo.short_name(s["full_name"]), s["card_lang"]] for s in students],
        # 7-й элемент вопроса: 1 — вопрос можно пропустить («не оценивал»)
        "q": [[q["id"], q[f"text_{suffix}"], *[q[f"opt{i}_{suffix}"] for i in range(4)], q["optional"]]
              for q in questions],
        "ph": [[p["text_ru"], p["text_uz"]] for p in reports.phrases(con)],
        "a": answers, "c": comments, "sr": stars,
        # цели на неделю: список на языке учителя и выбранные цели по неделям [[ученик, цель]]
        "gl": [[x["id"], x[f"text_{suffix}"]] for x in reports.goals_for(con, g["subject"])],
        "go": goals,
    }


def topic_payload(con, g, lang: str) -> dict:
    units = reports.topics_for_stage(con, g["stage_id"])
    return {"v": 1, "f": "tp", "gid": g["id"], "g": g["name"], "lang": lang, "cur": g["current_topic"],
            "u": [[u["id"], u["unit_no"], u["title"]] for u in units]}


def exam_payload(con, g, lang: str, today: date) -> dict | None:
    """Форма экзамена (или решения учителя на станциях без экзамена). None — у группы нет карты."""
    stage = repo.stage(con, g["stage_id"])
    if not g["has_map"] or stage is None:
        return None
    suffix = "uz" if lang == "uz" else "ru"
    nxt = progress.next_stage(con, stage)
    students = _students(con, g["id"])
    exam = con.execute("SELECT id FROM exams WHERE group_id = ? AND stage_id = ? AND exam_date = ?",
                       (g["id"], stage["id"], today.isoformat())).fetchone()
    prev = {}
    if exam:
        for r in con.execute("SELECT student_id, score, decision, reason FROM exam_results WHERE exam_id = ?",
                             (exam["id"],)):
            prev[str(r["student_id"])] = [r["score"], 1 if r["decision"] == "pass" else 0]
    st = []
    for s in students:
        cur = repo.current_stage(con, s["id"], g["subject"])
        st.append([s["id"], repo.short_name(s["full_name"]), 1 if cur and cur["stage_id"] == stage["id"] else 0])
    return {
        "v": 1, "f": "ex", "gid": g["id"], "g": g["name"], "lang": lang, "s": stage["id"],
        "sn": stage[f"name_{suffix}"], "nx": nxt[f"name_{suffix}"] if nxt else None,
        "fork": progress.is_fork(con, stage), "mode": "score" if stage["exam_transition"] else "teacher",
        "pass": stage["pass_score"], "max": stage["max_score"], "st": st, "prev": prev,
    }


def form_url(base: str, page: str, payload: dict) -> str:
    return f"{base}forms/{page}.html#d={encode_param(payload)}"


def split_urls(base: str, page: str, builder, students: list, limit: int) -> list[str]:
    """Ссылки формы: одна, а если не помещается — несколько частей по ученикам."""
    parts = 1
    while True:
        size = -(-len(students) // parts) if students else 0
        chunks = [students[i:i + size] for i in range(0, len(students), size)] if students else [[]]
        urls = []
        for i, chunk in enumerate(chunks):
            payload = builder(chunk)
            if len(chunks) > 1:
                payload["part"] = [i + 1, len(chunks)]
            urls.append(form_url(base, page, payload))
        if max(len(u) for u in urls) <= limit or size <= 1:
            return urls
        parts += 1


def group_keyboard(con, conf, g, lang: str, today: date | None = None) -> ReplyKeyboardMarkup:
    today = today or schedule.today()
    limit = repo.get_int(con, "url_safe_length", 1800)
    students = _students(con, g["id"])
    att = split_urls(conf.forms_url, "attendance",
                     lambda chunk: attendance_payload(con, g, lang, today, chunk), students, limit)
    wk = split_urls(conf.forms_url, "weekly",
                    lambda chunk: weekly_payload(con, g, lang, today, chunk), students, limit)
    rows = []
    if repo.attendance_on(con):
        for i, url in enumerate(att):
            text = t("btn_attendance", lang) + (f" {i + 1}/{len(att)}" if len(att) > 1 else "")
            rows.append([KeyboardButton(text=text, web_app=WebAppInfo(url=url))])
    wk_buttons = [KeyboardButton(text=t("btn_weekly", lang) if len(wk) == 1 else
                                 t("btn_weekly_part", lang, i=i + 1, n=len(wk)), web_app=WebAppInfo(url=url))
                  for i, url in enumerate(wk)]
    if rows:
        rows[0] += wk_buttons[:1]
    else:
        rows.append(wk_buttons[:1])
    if len(wk_buttons) > 1:
        rows.append(wk_buttons[1:])
    third = []
    exam = exam_payload(con, g, lang, today)
    if exam:
        third.append(KeyboardButton(text=t("btn_exam", lang),
                                    web_app=WebAppInfo(url=form_url(conf.forms_url, "exam", exam))))
    third.append(KeyboardButton(text=t("btn_topic", lang),
                                web_app=WebAppInfo(url=form_url(conf.forms_url, "topic", topic_payload(con, g, lang)))))
    rows.append(third)
    rows.append([KeyboardButton(text=t("btn_cards", lang)), KeyboardButton(text=t("btn_hints", lang))])
    last = [KeyboardButton(text=t("btn_other_group", lang))]
    if g["has_map"]:
        last.insert(0, KeyboardButton(text=t("btn_stations", lang)))
    rows.append(last)
    return ReplyKeyboardMarkup(resize_keyboard=True, is_persistent=True, keyboard=rows)


# ================================================================ приём данных формы

class FormError(Exception):
    """Форма отклонена целиком. key — ключ текста причины (texts.py)."""

    def __init__(self, key: str):
        super().__init__(key)
        self.key = key


@dataclass
class Result:
    text: str
    group_id: int | None = None
    lines: list[str] = field(default_factory=list)
    action: str = ""            # "cards" — после ответа прислать карточки группы
    notify_owner: str = ""      # сообщение владельцу (например, учитель перевёл группу)
    ids: list[int] | None = None  # для "cards": каким ученикам (None — всем готовым)


def _ints(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _parse(raw: str) -> dict:
    if byte_size(raw) > SEND_DATA_LIMIT:
        raise FormError("err_bad_data")
    try:
        data = json.loads(raw)
    except ValueError:
        raise FormError("err_bad_data") from None
    if (not isinstance(data, dict) or data.get("v") != 1 or data.get("t") not in SAVERS
            or not isinstance(data.get("u"), str) or not UUID_RE.match(data["u"])
            or not _ints(data.get("g"))):
        raise FormError("err_bad_data")
    return data


def _own_group(con, teacher, group_id: int):
    g = repo.group(con, group_id)
    if not g or not g["active"] or teacher is None or g["teacher_id"] != teacher["id"]:
        raise FormError("err_not_your_group")
    return g


def _split_students(con, group_id: int, ids: list[int]) -> tuple[list[int], int]:
    """Оставляет только учеников, которые сейчас записаны в группу."""
    good = [sid for sid in ids if repo.is_enrolled(con, sid, group_id)]
    return good, len(ids) - len(good)


def _save_attendance(con, teacher, g, data, tg_id: int, today: date, lang: str) -> list[str]:
    if not repo.attendance_on(con):
        raise FormError("err_att_off")
    try:
        day = date.fromisoformat(data.get("d", ""))
    except (TypeError, ValueError):
        raise FormError("err_bad_data") from None
    if not today - timedelta(days=ATTENDANCE_DAYS_BACK) <= day <= today:
        raise FormError("err_date")
    marks = data.get("m")
    if not isinstance(marks, list) or not marks or len(marks) > 200:
        raise FormError("err_bad_data")
    parsed = {}
    for item in marks:
        if (not isinstance(item, list) or len(item) != 2 or not _ints(item[0]) or not _ints(item[1])
                or not 0 <= item[1] < len(reports.ATT_CODES) or item[0] in parsed):
            raise FormError("err_bad_data")
        parsed[item[0]] = reports.ATT_CODES[item[1]]
    good, foreign = _split_students(con, g["id"], list(parsed))
    if not good:
        raise FormError("err_no_students")
    reports.save_attendance(con, tg_id, g["id"], day, [(sid, parsed[sid]) for sid in good])
    statuses = [parsed[sid] for sid in good]
    lines = [t("saved_att", lang, group=g["name"], date=day.strftime("%d.%m"), n=len(good),
               late=statuses.count("late"), absent=statuses.count("absent"))]
    if foreign:
        lines.append(t("skipped_foreign", lang, k=foreign))
    return lines


def _save_weekly(con, teacher, g, data, tg_id: int, today: date, lang: str) -> list[str]:
    try:
        week = date.fromisoformat(data.get("w", ""))
    except (TypeError, ValueError):
        raise FormError("err_bad_data") from None
    current = reports.week_start(today)
    if week.weekday() != 0 or not current - timedelta(weeks=WEEKLY_WEEKS_BACK) <= week <= current:
        raise FormError("err_week")
    qids = data.get("q")
    allowed = [q["id"] for q in reports.questions_for(con, g["subject"])]
    if not isinstance(qids, list) or qids != allowed:
        raise FormError("err_questions")
    optional = [bool(q["optional"]) for q in reports.questions_for(con, g["subject"])]
    goal_ids = {x["id"] for x in reports.goals_for(con, g["subject"], only_active=False)}
    rows = data.get("r")
    if not isinstance(rows, list) or not rows or len(rows) > 200:
        raise FormError("err_bad_data")
    parsed = {}
    for item in rows:
        # [ученик, ответы, комментарий] (+ звезда 0/1) (+ цель на неделю: номер, 0 — нет)
        if (not isinstance(item, list) or len(item) not in (3, 4, 5) or not _ints(item[0]) or item[0] in parsed
                or not isinstance(item[1], str) or len(item[1]) != len(qids)
                or any(ch not in ("0123-" if opt else "0123") for ch, opt in zip(item[1], optional))
                or all(ch == "-" for ch in item[1])
                or not isinstance(item[2], str) or len(item[2]) > COMMENT_MAX
                or (len(item) >= 4 and (not _ints(item[3]) or item[3] not in (0, 1)))
                or (len(item) == 5 and (not _ints(item[4]) or (item[4] != 0 and item[4] not in goal_ids)))):
            raise FormError("err_bad_data")
        answers = {qid: int(ch) for qid, ch in zip(qids, item[1]) if ch != "-"}
        parsed[item[0]] = (answers, " ".join(item[2].split()), len(item) >= 4 and item[3] == 1,
                           item[4] if len(item) == 5 else 0)
    good, foreign = _split_students(con, g["id"], list(parsed))
    if not good:
        raise FormError("err_no_students")
    for sid in good:
        answers, comment, star, goal_id = parsed[sid]
        reports.save_weekly(con, tg_id, g["id"], week, sid, answers, comment, star, goal_id)
    week_text = f"{week.strftime('%d.%m')}–{(week + timedelta(days=5)).strftime('%d.%m')}"
    lines = [t("saved_wk", lang, group=g["name"], week=week_text, n=len(good))]
    left = reports.students_without_report(con, g["id"], week)
    if left:
        names = ", ".join(repo.short_name(s["full_name"]) for s in left[:15]) + ("…" if len(left) > 15 else "")
        lines.append(t("wk_left", lang, k=len(left), names=names))
    else:
        lines.append(t("wk_all_done", lang))
    if foreign:
        lines.append(t("skipped_foreign", lang, k=foreign))
    return lines


def _save_topic(con, teacher, g, data, tg_id: int, today: date, lang: str) -> list[str]:
    unit = data.get("unit")
    text = data.get("text")
    if _ints(unit):
        row = next((u for u in reports.topics_for_stage(con, g["stage_id"]) if u["id"] == unit), None)
        if not row:
            raise FormError("err_bad_data")
        topic = f"Unit {row['unit_no']}. {row['title']}"[:TOPIC_MAX]
    elif isinstance(text, str) and 0 < len(" ".join(text.split())) <= TOPIC_MAX:
        topic = " ".join(text.split())
    else:
        raise FormError("err_bad_data")
    reports.set_topic(con, g["id"], topic)
    return [t("saved_topic", lang, group=g["name"], topic=topic)]


def _num(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _save_exam(con, teacher, g, data, tg_id: int, today: date, lang: str) -> list[str]:
    stage = repo.stage(con, data.get("s")) if _ints(data.get("s")) else None
    if stage is None or not g["has_map"] or stage["subject"] != g["subject"]:
        raise FormError("err_bad_data")
    # Исправление сегодняшнего экзамена, после которого группа уже перешла на следующую станцию
    advanced_today = g["stage_id"] != stage["id"] and con.execute(
        "SELECT 1 FROM student_stage n JOIN enrollments e ON e.student_id = n.student_id "
        "AND e.group_id = ? AND e.date_to IS NULL "
        "WHERE n.stage_id = ? AND n.status = 'current' AND n.date_from = ? AND EXISTS ("
        "  SELECT 1 FROM student_stage p WHERE p.student_id = n.student_id AND p.stage_id = ? AND p.status = 'done')",
        (g["id"], g["stage_id"], today.isoformat(), stage["id"])).fetchone() is not None
    if stage["id"] != g["stage_id"] and not advanced_today:
        raise FormError("err_stage")
    by_score = bool(stage["exam_transition"])
    if by_score and (stage["pass_score"] is None or stage["max_score"] is None):
        raise FormError("err_scores_unset")
    rows = data.get("r")
    if not isinstance(rows, list) or not rows or len(rows) > 200:
        raise FormError("err_bad_data")
    parsed = {}
    for item in rows:
        if (not isinstance(item, list) or len(item) != 5 or not _ints(item[0]) or item[0] in parsed
                or item[2] not in (0, 1) or not isinstance(item[3], str) or len(item[3]) > 100
                or item[4] not in ("", "cefr", "ielts")):
            raise FormError("err_bad_data")
        score, passed, reason = item[1], bool(item[2]), " ".join(item[3].split())
        if by_score:
            if not _num(score) or not 0 <= score <= stage["max_score"]:
                raise FormError("err_bad_data")
            if exams.auto_decision(score, stage["pass_score"]) != ("pass" if passed else "repeat") and len(reason) < 3:
                raise FormError("err_reason")
        elif score is not None:
            raise FormError("err_bad_data")
        parsed[item[0]] = (score, passed, reason, item[4] or None)
    good, foreign = _split_students(con, g["id"], list(parsed))
    if not good:
        raise FormError("err_no_students")

    exam_id = exams.save_exam(con, g["id"], stage, today, tg_id) if by_score else None
    passed_names, repeat_names, fork_names, other_names = [], [], [], []
    for sid in good:
        score, passed, reason, path = parsed[sid]
        name = repo.short_name(repo.student(con, sid)["full_name"])
        cur = repo.current_stage(con, sid, g["subject"])
        moved_today = cur is not None and cur["date_from"] == today.isoformat() and \
            progress.next_stage(con, stage, cur["path"]) is not None and \
            cur["stage_id"] == progress.next_stage(con, stage, cur["path"])["id"]
        if cur is None or (cur["stage_id"] != stage["id"] and not moved_today):
            other_names.append(name)
            continue
        if by_score:
            decision = "pass" if passed else "repeat"
            exams.save_result(con, exam_id, sid, float(score), decision, reason, tg_id)
        outcome = exams.apply_decision(con, sid, stage, passed, path, today)
        if outcome == "fork_wait":
            fork_names.append(name)
        (passed_names if passed else repeat_names).append(name)
    suffix = "uz" if lang == "uz" else "ru"
    key = "saved_exam" if by_score else "saved_decision"
    lines = [t(key, lang, group=g["name"], stage=stage[f"name_{suffix}"],
               passed=len(passed_names), repeat=len(repeat_names))]
    # группа переходит, если сдала хотя бы половина ВСЕХ учеников группы (а не только тех, чьи баллы уже введены)
    nxt = exams.maybe_advance_group(con, g, stage, exams.passed_today(con, g["id"], stage["id"], today),
                                    len(repo.group_students(con, g["id"])), today)
    if nxt:
        lines.append(t("group_advanced", lang, stage=nxt[f"name_{suffix}"]))
    if repeat_names and by_score:
        lines.append(t("repeat_names", lang, names=", ".join(repeat_names)))
    if fork_names:
        lines.append(t("fork_wait", lang, names=", ".join(fork_names)))
    if other_names:
        lines.append(t("other_stage", lang, names=", ".join(other_names)))
    if foreign:
        lines.append(t("skipped_foreign", lang, k=foreign))
    return lines


def _save_hints(con, teacher, g, data, tg_id: int, today: date, lang: str) -> list[str]:
    ids = data.get("close")
    if not isinstance(ids, list) or not ids or len(ids) > 100 or not all(_ints(i) for i in ids):
        raise FormError("err_bad_data")
    closed = 0
    for hint_id in ids:
        row = con.execute("SELECT group_id FROM hints WHERE id = ?", (hint_id,)).fetchone()
        if row and row["group_id"] == g["id"] and hints.close(con, hint_id, teacher["id"]):
            closed += 1
    return [t("hints_closed_n", lang, n=closed)]


def _save_move(con, teacher, g, data, tg_id: int, today: date, lang: str, out: Result) -> list[str]:
    sid, stage_id = data.get("sid"), data.get("s")
    if not _ints(sid) or not _ints(stage_id) or not g["has_map"]:
        raise FormError("err_bad_data")
    target = repo.stage(con, stage_id)
    if target is None or target["subject"] != g["subject"]:
        raise FormError("err_bad_data")
    suffix = "uz" if lang == "uz" else "ru"
    new = target[f"name_{suffix}"]
    if sid == 0:
        old = repo.stage(con, g["stage_id"])
        moved = repo.move_group_station(con, tg_id, g["id"], stage_id, today)
        out.notify_owner = (f"ℹ️ Учитель {teacher['name']} перевёл группу {g['name']} со станции "
                             f"{old['name_ru'] if old else '—'} на {target['name_ru']} (учеников: {len(moved)}).")
        return [t("stations_done_group", lang, group=g["name"], new=new, n=len(moved))]
    if not repo.is_enrolled(con, sid, g["id"]):
        raise FormError("err_no_students")
    repo.move_station(con, tg_id, sid, stage_id, today)
    return [t("stations_done_student", lang, name=repo.student(con, sid)["full_name"], new=new)]


def _save_cards(con, teacher, g, data, tg_id: int, today: date, lang: str, out: Result) -> list[str]:
    """Сами карточки рисует и присылает обработчик чата (Result.action = "cards").

    ids — каким ученикам прислать (необязательно). Чужие номера отбрасываются.
    """
    ids = data.get("ids")
    if ids is not None:
        if not isinstance(ids, list) or not ids or len(ids) > 200 or not all(_ints(i) for i in ids):
            raise FormError("err_bad_data")
        out.ids = [i for i in dict.fromkeys(ids) if repo.is_enrolled(con, i, g["id"])]
        if not out.ids:
            raise FormError("err_no_students")
    out.action = "cards"
    return []


def _save_export(con, teacher, g, data, tg_id: int, today: date, lang: str, out: Result) -> list[str]:
    """Excel с отчётами группы присылает обработчик чата (Result.action = "export")."""
    out.action = "export"
    return []


SAVERS = {"att": _save_attendance, "wk": _save_weekly, "tp": _save_topic, "ex": _save_exam,
          "hints": _save_hints, "move": _save_move, "cards": _save_cards, "export": _save_export}
NEEDS_RESULT = {"move", "cards", "export"}   # этим обработчикам нужен сам ответ (уведомление владельцу, список)


def process(con, teacher, tg_id: int, raw: str, sent_at: datetime, now: datetime) -> Result:
    """Проверяет и сохраняет данные формы. Возвращает ответ учителю (на его языке)."""
    from bot.db import tx

    lang = teacher["lang"] if teacher else "ru"
    try:
        data = _parse(raw)
        if reports.submission_seen(con, data["u"]):
            return Result(t("duplicate", lang), data["g"])
        g = _own_group(con, teacher, data["g"])
        today = now.astimezone(schedule.TZ).date()
        out = Result("")
        args = (con, teacher, g, data, tg_id, today, lang) + ((out,) if data["t"] in NEEDS_RESULT else ())
        with tx(con):
            lines = SAVERS[data["t"]](*args)
            reports.record_submission(con, data["u"], tg_id, data["t"], "saved")
            new_hints = hints.evaluate_group(con, g["id"], today) if data["t"] in ("att", "wk", "ex", "move") else 0
        if new_hints:
            lines.append(t("new_hints", lang, n=new_hints))
    except FormError as e:
        return Result(t("form_rejected", lang, reason=t(e.key, lang)), None)
    if (now - sent_at).total_seconds() > LATE_DELIVERY_SECONDS:
        lines.insert(0, t("late_delivery", lang, when=_when(sent_at, now, lang)))
    out.text, out.group_id, out.lines = "\n".join(lines), g["id"], lines
    return out


def _when(sent_at: datetime, now: datetime, lang: str) -> str:
    text = human_time(sent_at, now)
    if lang == "uz":
        text = text.replace("сегодня в", "bugun soat").replace("вчера в", "kecha soat").replace(" в ", " soat ")
    return text
