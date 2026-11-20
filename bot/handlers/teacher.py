"""Чат учителя: выбор группы, кнопки форм под полем ввода, приём данных форм.

Учитель видит только свои группы: это проверяется на каждом нажатии и каждой отправке формы.
Экзамен, карточки и подсказки появятся на этапах 3–4.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from bot import card, forms, repo, reports, schedule
from bot.config import data_dir
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


def cards_week(con, group_id: int, today) -> object:
    """Неделя для карточек: текущая, а если по ней ещё нет отчётов — прошлая."""
    current = reports.week_start(today)
    for week in (current, current - timedelta(weeks=1)):
        if con.execute("SELECT 1 FROM weekly_reports WHERE group_id = ? AND week_start = ? LIMIT 1",
                       (group_id, week.isoformat())).fetchone():
            return week
    return current


@router.message(F.text.in_(all_variants("btn_cards")))
async def send_cards(message: Message, con, teacher) -> None:
    lang = teacher["lang"]
    g = repo.group(con, teacher["current_group_id"]) if teacher["current_group_id"] else None
    if not g or not g["active"] or g["teacher_id"] != teacher["id"]:
        return await message.answer(t("choose_group_first", lang))
    today = schedule.today()
    week = cards_week(con, g["id"], today)
    done = reports.reports_for_weeks(con, g["id"], [week])
    students = repo.group_students(con, g["id"])
    ready = [s for s in students if s["consent"] and s["id"] in done]
    skipped = [(s, "cards_no_consent" if not s["consent"] else "cards_no_report")
               for s in students if s not in ready]
    if not ready:
        return await message.answer(t("cards_none", lang, week=card.week_text(week, lang)) if not done
                                    else _skipped_text(skipped, lang))
    await message.answer(t("cards_wait", lang, n=len(ready)))
    folder = data_dir() / "cards"
    sent = 0
    for s in ready:
        data = card.collect(con, s["id"], g["id"], week, today)
        png = await asyncio.to_thread(card.render, data)
        card.save(png, folder, week, s["id"], g["id"])
        caption = t("cards_caption", s["card_lang"], name=s["full_name"], week=card.week_text(week, s["card_lang"]))
        try:
            await message.answer_photo(BufferedInputFile(png, filename=f"{s['id']}.png"), caption=caption)
            sent += 1
        except TelegramAPIError as e:
            log.warning("Карточка %s не отправлена: %s", s["id"], type(e).__name__)
        await asyncio.sleep(0.4)  # не упираться в ограничения Telegram на частоту
    text = t("cards_done", lang, n=sent)
    if skipped:
        text += "\n\n" + _skipped_text(skipped, lang)
    await message.answer(text)


def _skipped_text(skipped, lang: str) -> str:
    lines = [t("cards_skipped", lang)]
    lines += [f"• {s['full_name']} — {t(reason, lang)}" for s, reason in skipped]
    return "\n".join(lines)


@router.message()
async def fallback(message: Message, teacher) -> None:
    await message.answer(t("press_button", teacher["lang"]))
