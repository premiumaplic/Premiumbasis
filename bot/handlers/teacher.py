"""Чат учителя: список своих групп и выбор группы.

Формы (посещаемость, отчёт, экзамен, тема) и карточки появятся на этапах 2–3.
Учитель видит только свои группы: это проверяется на каждом нажатии.
"""

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, KeyboardButton, Message, ReplyKeyboardMarkup

from bot import repo, schedule
from bot.access import TeacherOnly
from bot.handlers.common import show
from bot.texts import all_variants, t
from bot.ui import T, column, kb

router = Router(name="teacher")
router.message.filter(TeacherOnly())
router.callback_query.filter(TeacherOnly())


def groups_markup(con, teacher) -> object:
    groups = repo.list_groups(con, teacher_id=teacher["id"])
    lang = teacher["lang"]
    buttons = [(f"{g['name']} · {g['subject_uz' if lang == 'uz' else 'subject_ru']}", T(act="group", id=g["id"]))
               for g in groups]
    return kb(*column(buttons, 2)) if buttons else None


def group_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(resize_keyboard=True, is_persistent=True,
                               keyboard=[[KeyboardButton(text=t("btn_other_group", lang))]])


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
async def choose_group(cb: CallbackQuery, callback_data: T, state: FSMContext, con, teacher) -> None:
    g = repo.group(con, callback_data.id)
    lang = teacher["lang"]
    # Не доверяем кнопке: группа должна быть активной и принадлежать этому учителю
    if not g or not g["active"] or g["teacher_id"] != teacher["id"]:
        return await cb.answer(t("not_your_group", lang), show_alert=True)
    await state.update_data(group_id=g["id"])
    await cb.answer()
    await cb.message.answer(t("group_chosen", lang, header=schedule.group_header(g, lang)),
                            reply_markup=group_keyboard(lang))


@router.message()
async def fallback(message: Message, teacher) -> None:
    await message.answer(t("press_button", teacher["lang"]))
