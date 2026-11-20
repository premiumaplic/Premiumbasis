"""Чат учителя: выбор группы, кнопки форм под полем ввода, приём данных форм.

Учитель видит только свои группы: это проверяется на каждом нажатии и каждой отправке формы.
Экзамен, карточки и подсказки появятся на этапах 3–4.
"""

import logging
from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot import forms, repo, reports, schedule
from bot.access import TeacherOnly
from bot.handlers.common import show
from bot.texts import all_variants, t
from bot.ui import T, column, kb

log = logging.getLogger("teacher")
router = Router(name="teacher")
router.message.filter(TeacherOnly())
router.callback_query.filter(TeacherOnly())


def groups_markup(con, teacher) -> object:
    groups = repo.list_groups(con, teacher_id=teacher["id"])
    lang = teacher["lang"]
    buttons = [(f"{g['name']} · {g['subject_uz' if lang == 'uz' else 'subject_ru']}", T(act="group", id=g["id"]))
               for g in groups]
    return kb(*column(buttons, 2)) if buttons else None


async def send_groups(target, con, teacher) -> None:
    markup = groups_markup(con, teacher)
    key = "hello_teacher" if markup else "no_groups"
    await show(target, t(key, teacher["lang"], name=teacher["name"]), markup)


@router.message(CommandStart())
async def start(message: Message, state: FSMContext, con, teacher) -> None:
    await state.clear()
    await send_groups(message, con, teacher)


@router.message(F.text.in_(all_variants("btn_other_group")))
async def other_group(message: Message, con, teacher) -> None:
    await send_groups(message, con, teacher)


@router.callback_query(T.filter(F.act == "groups"))
async def groups_button(cb: CallbackQuery, con, teacher) -> None:
    await send_groups(cb, con, teacher)


@router.callback_query(T.filter(F.act == "group"))
async def choose_group(cb: CallbackQuery, callback_data: T, con, conf, teacher) -> None:
    g = repo.group(con, callback_data.id)
    lang = teacher["lang"]
    # Не доверяем кнопке: группа должна быть активной и принадлежать этому учителю
    if not g or not g["active"] or g["teacher_id"] != teacher["id"]:
        return await cb.answer(t("not_your_group", lang), show_alert=True)
    reports.set_current_group(con, teacher["id"], g["id"])
    await cb.answer()
    await cb.message.answer(t("group_chosen", lang, header=schedule.group_header(g, lang)),
                            reply_markup=forms.group_keyboard(con, conf, g, lang))


@router.message(F.web_app_data)
async def form_data(message: Message, con, conf, teacher) -> None:
    now = datetime.now(timezone.utc)
    result = forms.process(con, teacher, message.from_user.id, message.web_app_data.data, message.date, now)
    log.info("Форма от %s: %s", message.from_user.id, "сохранено" if result.group_id else "отклонено")
    markup = None
    group_id = result.group_id or teacher["current_group_id"]
    g = repo.group(con, group_id) if group_id else None
    if g and g["active"] and g["teacher_id"] == teacher["id"]:
        # Ссылки в кнопках несут данные группы — после каждого сохранения обновляем клавиатуру
        markup = forms.group_keyboard(con, conf, g, teacher["lang"])
    await message.answer(result.text, reply_markup=markup)


@router.message()
async def fallback(message: Message, teacher) -> None:
    await message.answer(t("press_button", teacher["lang"]))
