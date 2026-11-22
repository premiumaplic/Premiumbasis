"""Учитель меняет станции: всей группе (например, сразу из Roundup 3 в A1) или одному ученику.

Всё проверяется заново на каждом нажатии: группа должна быть этого учителя, ученик — в этой группе.
Перевод группы виден владельцу (сообщение) и записывается в журнал.
"""

import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery, Message

from bot import repo, schedule
from bot.access import TeacherOnly
from bot.db import tx
from bot.handlers.common import show
from bot.texts import all_variants, t
from bot.ui import TS, column, kb

log = logging.getLogger("teacher")
router = Router(name="stations")
router.message.filter(TeacherOnly())
router.callback_query.filter(TeacherOnly())


def _group(con, teacher):
    gid = teacher["current_group_id"]
    g = repo.group(con, gid) if gid else None
    if not repo.can_teach(teacher, g):
        return None
    return g


def _name(row, lang: str) -> str:
    return row["name_uz" if lang == "uz" else "name_ru"] if row else "—"


def _overview(con, g, lang: str):
    students = repo.group_students(con, g["id"])
    rows = [[(t("stations_whole", lang), TS(act="group"))]]
    for s in students:
        cur = repo.current_stage(con, s["id"], g["subject"])
        rows.append([(f"{repo.short_name(s['full_name'])} · {_name(cur, lang)}", TS(act="student", sid=s["id"]))])
    rows.append([(t("btn_close", lang), TS(act="close"))])
    text = t("stations_head", lang, group=g["name"], stage=g["stage_uz" if lang == "uz" else "stage_ru"] or "—")
    return text, kb(*rows)


@router.message(F.text.in_(all_variants("btn_stations")))
async def stations(message: Message, con, teacher) -> None:
    lang = teacher["lang"]
    g = _group(con, teacher)
    if not g:
        return await message.answer(t("choose_group_first", lang))
    if not g["has_map"]:
        return await message.answer(t("stations_none", lang))
    text, markup = _overview(con, g, lang)
    await message.answer(text, reply_markup=markup)


@router.callback_query(TS.filter())
async def stations_button(cb: CallbackQuery, callback_data: TS, bot: Bot, con, conf, teacher) -> None:
    lang = teacher["lang"]
    g = _group(con, teacher)
    if not g or not g["has_map"]:
        return await cb.answer(t("not_your_group", lang), show_alert=True)
    act, sid, stage_id = callback_data.act, callback_data.sid, callback_data.stage
    back_to_overview = [(t("btn_back", lang), TS(act="overview"))]

    if act == "close":
        await cb.message.delete()
        return await cb.answer()
    if act == "overview":
        text, markup = _overview(con, g, lang)
        return await show(cb, text, markup)

    # ученик должен быть в этой группе
    student = None
    if sid:
        student = repo.student(con, sid)
        if not student or not repo.is_enrolled(con, sid, g["id"]):
            return await cb.answer(t("not_your_group", lang), show_alert=True)
    stages = repo.list_stages(con, g["subject"])
    target = repo.stage(con, stage_id) if stage_id else None
    if target is not None and target["subject"] != g["subject"]:
        return await cb.answer(t("not_your_group", lang), show_alert=True)

    if act in ("group", "student"):
        if student:
            cur = repo.current_stage(con, sid, g["subject"])
            current_id = cur["stage_id"] if cur else None
        else:
            current_id = g["stage_id"]
        buttons = [(_name(s, lang), TS(act="confirm", sid=sid, stage=s["id"])) for s in stages if s["id"] != current_id]
        if student:
            text = t("stations_pick_student", lang, name=student["full_name"],
                     stage=_name(repo.stage(con, current_id) if current_id else None, lang))
        else:
            text = t("stations_pick_group", lang, group=g["name"])
        return await show(cb, text, kb(*column(buttons, 3), back_to_overview))

    if act == "confirm" and target is not None:
        back = [(t("btn_back", lang), TS(act="student" if sid else "group", sid=sid))]
        yes = [(t("btn_yes_move", lang), TS(act="apply", sid=sid, stage=target["id"]))]
        if student:
            cur = repo.current_stage(con, sid, g["subject"])
            text = t("stations_confirm_student", lang, name=student["full_name"],
                     old=_name(repo.stage(con, cur["stage_id"]) if cur else None, lang), new=_name(target, lang))
        else:
            old = repo.stage(con, g["stage_id"])
            count = sum(1 for s in repo.group_students(con, g["id"])
                        if (c := repo.current_stage(con, s["id"], g["subject"])) is None
                        or c["stage_id"] == g["stage_id"])
            exam = t("stations_exam_note", lang, new=_name(target, lang)) if target["exam_transition"] else ""
            text = t("stations_confirm_group", lang, group=g["name"], old=_name(old, lang), new=_name(target, lang),
                     n=count, exam=exam)
        return await show(cb, text, kb(yes, back))

    if act == "apply" and target is not None:
        today = schedule.today()
        if student:
            with tx(con):
                repo.move_station(con, cb.from_user.id, sid, target["id"], today)
            text = t("stations_done_student", lang, name=student["full_name"], new=_name(target, lang))
        else:
            old = repo.stage(con, g["stage_id"])
            with tx(con):
                moved = repo.move_group_station(con, cb.from_user.id, g["id"], target["id"], today)
            text = t("stations_done_group", lang, group=g["name"], new=_name(target, lang), n=len(moved))
            log.info("Учитель %s перевёл группу %s на станцию %s", cb.from_user.id, g["id"], target["id"])
            if conf.owner_id and conf.owner_id != cb.from_user.id:
                try:
                    await bot.send_message(conf.owner_id, f"ℹ️ Учитель {teacher['name']} перевёл группу {g['name']} "
                                                          f"со станции {_name(old, 'ru')} на {target['name_ru']} "
                                                          f"(учеников: {len(moved)}).")
                except TelegramAPIError:
                    pass
        from bot import forms
        await cb.answer()
        await cb.message.edit_text(text)
        # кнопки форм несут данные группы — обновляем их
        g = repo.group(con, g["id"])
        await cb.message.answer(schedule.group_header(g, lang), reply_markup=forms.group_keyboard(con, conf, g, lang))
        return
    await cb.answer()
