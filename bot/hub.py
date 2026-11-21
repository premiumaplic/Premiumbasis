"""Приложение группы — главный интерфейс учителя (docs/app/).

Под полем ввода у учителя по кнопке на каждую группу: «📱 10-А · Английский».
Кнопка открывает приложение группы; все данные группы — в ссылке кнопки (сжатый JSON).
Сохранение — Telegram.WebApp.sendData (работает только у кнопок под полем ввода).
"""

from datetime import date

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

from bot import forms, hints, repo, schedule
from bot.payload import encode_param
from bot.texts import t

HUB_LIMIT = 6000   # символов ссылки; сервер Telegram принимает до 8000 (проверено на этапе 0)


def payload(con, g, lang: str, today: date) -> dict:
    suffix = "uz" if lang == "uz" else "ru"
    students = repo.group_students(con, g["id"])
    att = forms.attendance_payload(con, g, lang, today, students)
    wk = forms.weekly_payload(con, g, lang, today, students)
    ex = forms.exam_payload(con, g, lang, today)
    tp = forms.topic_payload(con, g, lang)
    st = []
    for s in students:
        cur = repo.current_stage(con, s["id"], g["subject"]) if g["has_map"] else None
        st.append([s["id"], repo.short_name(s["full_name"]), s["card_lang"], cur["stage_id"] if cur else 0,
                   1 if s["consent"] else 0])
    header = schedule.group_header(g, lang, today).split(" · ", 1)
    data = {
        "v": 1, "f": "hub", "gid": g["id"], "g": g["name"], "sj": g[f"subject_{suffix}"], "lang": lang,
        "hdr": header[1] if len(header) > 1 else "",
        "st": st,
        "att": {k: att[k] for k in ("today", "days", "h")},
        "wk": {k: wk[k] for k in ("wk", "q", "ph", "a", "c")},
        "ex": {k: ex[k] for k in ("s", "sn", "nx", "fork", "mode", "pass", "max", "prev")} if ex else None,
        "tp": {k: tp[k] for k in ("cur", "u")},
        "hn": [[h["id"], h["student_id"], *hints.parts(con, h, lang)] for h in hints.open_hints(con, g["id"])],
        "stg": [[s["id"], s[f"name_{suffix}"]] for s in repo.list_stages(con, g["subject"])] if g["has_map"] else [],
        "gs": g["stage_id"] or 0,
    }
    return data


def url(con, conf, g, lang: str, today: date) -> str | None:
    """Ссылка приложения группы. Если не помещается — сначала без лишнего, иначе None."""
    data = payload(con, g, lang, today)
    link = f"{conf.forms_url}app/#d={encode_param(data)}"
    if len(link) <= HUB_LIMIT:
        return link
    data["hn"] = [[h[0], h[1], h[2], ""] for h in data["hn"]]   # без пояснений к подсказкам
    data["tp"]["u"] = []                                         # без списка юнитов
    link = f"{conf.forms_url}app/#d={encode_param(data)}"
    return link if len(link) <= HUB_LIMIT else None


def teacher_keyboard(con, conf, teacher, today: date | None = None) -> ReplyKeyboardMarkup | None:
    """Кнопки под полем ввода: по одной на каждую группу учителя + «Обновить»."""
    today = today or schedule.today()
    lang = teacher["lang"]
    suffix = "uz" if lang == "uz" else "ru"
    buttons = []
    for g in repo.list_groups(con, teacher_id=teacher["id"]):
        text = f"📱 {g['name']} · {g[f'subject_{suffix}']}"
        link = url(con, conf, g, lang, today)
        if link:
            buttons.append(KeyboardButton(text=text, web_app=WebAppInfo(url=link)))
        else:
            # слишком большая группа для одной ссылки — старый способ: формы отдельными кнопками
            buttons.append(KeyboardButton(text=f"📂 {g['name']}"))
    if not buttons:
        return None
    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    rows.append([KeyboardButton(text=t("btn_refresh", lang))])
    return ReplyKeyboardMarkup(resize_keyboard=True, is_persistent=True, keyboard=rows,
                               input_field_placeholder=t("hub_placeholder", lang))
