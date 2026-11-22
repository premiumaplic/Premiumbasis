"""Приложение группы — главный интерфейс учителя (docs/app/).

Под полем ввода у учителя по кнопке на каждую группу: «📱 10-А · Английский».
Кнопка открывает приложение группы; все данные группы — в ссылке кнопки (сжатый JSON).
Сохранение — Telegram.WebApp.sendData (работает только у кнопок под полем ввода).

В ссылке об учениках — только имя, первая буква фамилии и внутренние номера.
"""

from datetime import date, timedelta

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

from bot import forms, hints, profiles, progress, repo, reports, rules, schedule
from bot.payload import encode_param
from bot.texts import t

HUB_LIMIT = 6000   # символов ссылки; сервер Telegram принимает до 8000 (проверено на этапе 0)
HISTORY_WEEKS = 8  # сколько недель истории уровня ученика в ссылке
BRANCH_CODE = {"kids": "k", "main": "m", "cefr": "c", "ielts": "i"}


def history(con, group_id: int, students, today: date) -> dict[int, str]:
    """Уровень каждого ученика по неделям, от старой к текущей: строка из 8 знаков 0…9 или «-»."""
    current = reports.week_start(today)
    weeks = [current - timedelta(weeks=i) for i in range(HISTORY_WEEKS - 1, -1, -1)]
    levels = reports.week_levels(con, group_id, weeks)
    return {s["id"]: "".join(reports.level_char(levels.get(s["id"], {}).get(w.isoformat())) for w in weeks)
            for s in students}


def timing(g, today: date) -> dict:
    """Неделя внутри станции, всего недель (8 — если переход по экзамену) и дата экзамена."""
    start = schedule.anchor(g)
    by_exam = bool(g["stage_id"] and g["exam_transition"])
    if today < start:
        return {"wkn": 0, "wkt": 0, "exd": "", "sst": start.isoformat()}
    exam = rules.next_exam_for(g, today)
    return {"wkn": schedule.stage_week(start, today, by_exam),
            "wkt": schedule.WEEKS_PER_STAGE if by_exam else 0,
            "exd": exam.isoformat() if exam else "", "sst": start.isoformat()}


def stations(con, subject: str, lang: str) -> list:
    """Станции карты по порядку: [номер, название, раздел, что проходят, ветка, экзамен 0/1, месяцев]."""
    suffix = "uz" if lang == "uz" else "ru"
    return [[s["id"], s[f"name_{suffix}"], s[f"section_{suffix}"], s[f"about_{suffix}"],
             BRANCH_CODE[s["branch"]], s["exam_transition"], s["months"] or 0]
            for s in progress.ordered(con, subject)]


def skills(con, g, students, lang: str) -> tuple[list, dict]:
    """Критерии и профили учеников: (cr, pf).

    cr — [[номер, название]]; pf — {ученик: [оценки, прошлые оценки, дата, кто оценил,
    выучил, не понял, [всего выучено, всего непонятно]]}. Оценки — по критериям cr (0 — нет).
    """
    suffix = "uz" if lang == "uz" else "ru"
    crit = profiles.criteria_for(con, g["subject"])
    ids = [s["id"] for s in students]
    ratings = profiles.latest_ratings(con, ids, g["subject"])
    topics = profiles.topics_of(con, ids, g["subject"])
    names = profiles.rater_names(con, {a["by"] for items in ratings.values() for a in items})
    pf = {}
    for sid in ids:
        items, tp = ratings.get(sid, []), topics.get(sid, {"learned": [], "unclear": []})
        if not items and not tp["learned"] and not tp["unclear"]:
            continue
        vals = [[a["v"].get(c["id"], 0) for c in crit] for a in items]
        pf[str(sid)] = [vals[0] if vals else None, vals[1] if len(vals) > 1 else None,
                        items[0]["on"] if items else "", names.get(items[0]["by"], "") if items else "",
                        tp["learned"], tp["unclear"], [len(tp["learned"]), len(tp["unclear"])]]
    return [[c["id"], c[f"name_{suffix}"]] for c in crit], pf


def payload(con, g, lang: str, today: date, teacher=None) -> dict:
    suffix = "uz" if lang == "uz" else "ru"
    students = repo.group_students(con, g["id"])
    att = forms.attendance_payload(con, g, lang, today, students) if repo.attendance_on(con) else None
    wk = forms.weekly_payload(con, g, lang, today, students)
    ex = forms.exam_payload(con, g, lang, today)
    tp = forms.topic_payload(con, g, lang)
    hist = history(con, g["id"], students, today)
    st = []
    for s in students:
        cur = repo.current_stage(con, s["id"], g["subject"]) if g["has_map"] else None
        st.append([s["id"], repo.short_name(s["full_name"]), s["card_lang"], cur["stage_id"] if cur else 0,
                   1 if s["consent"] else 0, hist[s["id"]]])
    header = schedule.group_header(g, lang, today).split(" · ", 1)
    data = {
        "v": 2, "f": "hub", "gid": g["id"], "g": g["name"], "sj": g[f"subject_{suffix}"], "sc": g["subject"],
        "lang": lang, "today": today.isoformat(),
        "hdr": header[1] if len(header) > 1 else "",
        **timing(g, today),
        "st": st,
        "att": {k: att[k] for k in ("today", "days", "h")} if att else None,
        "wk": {k: wk[k] for k in ("wk", "q", "ph", "a", "c", "sr", "gl", "go")},
        "ex": {k: ex[k] for k in ("s", "sn", "nx", "fork", "mode", "pass", "max", "prev")} if ex else None,
        "tp": {k: tp[k] for k in ("cur", "u")},
        "hn": [[h["id"], h["student_id"], *hints.parts(con, h, lang), h["rule"].split(":")[0]]
               for h in hints.open_hints(con, g["id"])],
        "stg": stations(con, g["subject"], lang) if g["has_map"] else [],
        "gs": g["stage_id"] or 0,
        "tl": profiles.topic_log(con, g["id"]),
        # саппорт-учитель в чужой группе: показать, чья это группа
        "rl": 1 if teacher is not None and g["teacher_id"] != teacher["id"] else 0,
        "tn": repo.short_name(g["teacher_name"]) if g["teacher_name"] else "",
    }
    data["cr"], data["pf"] = skills(con, g, students, lang)
    return data


# Что убирать из ссылки по очереди, если она не помещается (от наименее важного)
def _trim_steps():
    def no_about(d):
        for s in d["stg"]:
            s[3] = ""

    def no_why(d):
        d["hn"] = [[h[0], h[1], h[2], "", h[4]] for h in d["hn"]]

    def no_units(d):
        d["tp"]["u"] = []

    def short_history(d):
        for s in d["st"]:
            s[5] = s[5][-4:]

    def no_last_week(d):
        for rec in d["wk"]["a"].values():
            rec.pop("1", None)

    def short_topics(d):      # всего тем видно по счётчикам в конце записи
        d["tl"] = d["tl"][:4]
        for rec in d["pf"].values():
            rec[1], rec[4], rec[5] = None, rec[4][:5], rec[5][:5]

    def no_topics(d):
        d["tl"] = []
        for rec in d["pf"].values():
            rec[4], rec[5] = [], []

    return [no_about, no_why, no_units, short_topics, short_history, no_last_week, no_topics]


def url(con, conf, g, lang: str, today: date, teacher=None) -> str | None:
    """Ссылка приложения группы. Если не помещается — без второстепенного, иначе None."""
    data = payload(con, g, lang, today, teacher)
    link = f"{conf.forms_url}app/#d={encode_param(data)}"
    for step in _trim_steps():
        if len(link) <= HUB_LIMIT:
            return link
        step(data)
        link = f"{conf.forms_url}app/#d={encode_param(data)}"
    return link if len(link) <= HUB_LIMIT else None


def group_button(con, conf, teacher, g, today: date) -> KeyboardButton:
    lang = teacher["lang"]
    suffix = "uz" if lang == "uz" else "ru"
    link = url(con, conf, g, lang, today, teacher)
    if link:
        return KeyboardButton(text=f"📱 {g['name']} · {g[f'subject_{suffix}']}", web_app=WebAppInfo(url=link))
    # слишком большая группа для одной ссылки — старый способ: формы отдельными кнопками
    return KeyboardButton(text=f"📂 {g['name']}")


def support_group(con, teacher):
    """Чужая группа, которую саппорт-учитель выбрал последней (или None)."""
    if not repo.is_support(teacher) or not teacher["current_group_id"]:
        return None
    g = repo.group(con, teacher["current_group_id"])
    return g if g and g["active"] and g["teacher_id"] != teacher["id"] else None


def group_buttons(con, conf, teacher, today: date) -> list[KeyboardButton]:
    """Свои группы, а у саппорт-учителя — ещё и выбранная чужая группа."""
    groups = list(repo.list_groups(con, teacher_id=teacher["id"]))
    extra = support_group(con, teacher)
    if extra is not None:
        groups.insert(0, extra)
    return [group_button(con, conf, teacher, g, today) for g in groups]


def teacher_keyboard(con, conf, teacher, today: date | None = None, extra: list | None = None
                     ) -> ReplyKeyboardMarkup | None:
    """Кнопки под полем ввода: по одной на каждую группу учителя + «Обновить».

    extra — кнопки владельца (если владелец ещё и учитель): ставятся первой строкой.
    Саппорт-учителю — ещё «🛟 Все группы»: выбрать любую группу центра.
    """
    today = today or schedule.today()
    lang = teacher["lang"]
    buttons = group_buttons(con, conf, teacher, today)
    support = repo.is_support(teacher)
    if not buttons and not extra and not support:
        return None
    rows = [extra] if extra else []
    rows += [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    last = [KeyboardButton(text=t("btn_refresh", lang))]
    if support:
        last.insert(0, KeyboardButton(text=t("btn_all_groups", lang)))
    rows.append(last)
    return ReplyKeyboardMarkup(resize_keyboard=True, is_persistent=True, keyboard=rows,
                               input_field_placeholder=t("hub_placeholder", lang))
