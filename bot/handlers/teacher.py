"""Чат учителя: выбор группы, кнопки форм под полем ввода, приём данных форм.

Учитель видит только свои группы: это проверяется на каждом нажатии и каждой отправке формы.
Экзамен, карточки и подсказки появятся на этапах 3–4.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from bot import card, forms, hints, hub, panel, repo, reports, schedule
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


def keyboard(con, conf, teacher, is_owner: bool = False):
    """Кнопки под полем ввода: группы учителя (а владельцу-учителю — ещё и панель центра)."""
    return panel.keyboard(con, conf, teacher) if is_owner else hub.teacher_keyboard(con, conf, teacher)


async def send_groups(target, con, conf, teacher, is_owner: bool = False) -> None:
    """Приветствие и кнопки под полем ввода: по кнопке-приложению на каждую группу."""
    lang = teacher["lang"]
    markup = keyboard(con, conf, teacher, is_owner)
    message = target.message if isinstance(target, CallbackQuery) else target
    if isinstance(target, CallbackQuery):
        await target.answer()
    own = repo.list_groups(con, teacher_id=teacher["id"])
    if repo.is_support(teacher):
        await message.answer(t("hub_hello", lang, name=teacher["name"]), reply_markup=markup)
        return await send_support_groups(message, con, teacher)
    if markup is None or (is_owner and not own):
        return await message.answer(t("no_groups", lang, name=teacher["name"]), reply_markup=markup)
    await message.answer(t("hub_hello", lang, name=teacher["name"]), reply_markup=markup)


SUPPORT_PAGE = 40


def support_markup(con, teacher, page: int = 0):
    """Все группы центра кнопками (по 40 на странице) — для саппорт-учителя."""
    lang = teacher["lang"]
    groups = repo.list_groups(con)
    chunk = groups[page * SUPPORT_PAGE:(page + 1) * SUPPORT_PAGE]
    buttons = [(f"{g['name']} · {g['subject_uz' if lang == 'uz' else 'subject_ru']}", T(act="sgroup", id=g["id"]))
               for g in chunk]
    rows = column(buttons, 2)
    pager = []
    if page > 0:
        pager.append(("◀️", T(act="sgroups", id=page - 1)))
    if (page + 1) * SUPPORT_PAGE < len(groups):
        pager.append(("▶️", T(act="sgroups", id=page + 1)))
    if pager:
        rows.append(pager)
    return kb(*rows) if rows else None, len(groups)


async def send_support_groups(message: Message, con, teacher, page: int = 0) -> None:
    markup, total = support_markup(con, teacher, page)
    lang = teacher["lang"]
    if not total:
        return await message.answer(t("support_no_groups", lang))
    await message.answer(t("support_pick", lang), reply_markup=markup)


@router.message(F.text.in_(all_variants("btn_all_groups")))
async def all_groups(message: Message, con, teacher) -> None:
    if not repo.is_support(teacher):
        return await message.answer(t("press_button", teacher["lang"]))
    await send_support_groups(message, con, teacher)


@router.callback_query(T.filter(F.act == "sgroups"))
async def all_groups_page(cb: CallbackQuery, callback_data: T, con, teacher) -> None:
    if not repo.is_support(teacher):
        return await cb.answer(t("not_your_group", teacher["lang"]), show_alert=True)
    markup, _ = support_markup(con, teacher, max(0, callback_data.id))
    await show(cb, t("support_pick", teacher["lang"]), markup)


@router.callback_query(T.filter(F.act == "sgroup"))
async def support_choose(cb: CallbackQuery, callback_data: T, con, conf, teacher, is_owner: bool = False) -> None:
    """Саппорт-учитель выбрал группу: под полем ввода появляется кнопка её журнала."""
    lang = teacher["lang"]
    g = repo.group(con, callback_data.id)
    # не доверяем кнопке: роль и группа проверяются заново
    if not repo.is_support(teacher) or not repo.can_teach(teacher, g):
        return await cb.answer(t("not_your_group", lang), show_alert=True)
    reports.set_current_group(con, teacher["id"], g["id"])
    log.info("Саппорт-учитель %s выбрал группу %s", cb.from_user.id, g["id"])
    fresh = repo.teacher(con, teacher["id"])
    await cb.answer()
    await cb.message.answer(t("support_chosen", lang, group=g["name"], teacher=g["teacher_name"] or "—"),
                            reply_markup=keyboard(con, conf, fresh, is_owner))


@router.message(CommandStart())
async def start(message: Message, state: FSMContext, con, conf, teacher, is_owner: bool = False) -> None:
    await state.clear()
    await send_groups(message, con, conf, teacher, is_owner)


@router.message(F.text.in_(all_variants("btn_other_group") | all_variants("btn_refresh")))
async def refresh(message: Message, con, conf, teacher, is_owner: bool = False) -> None:
    await send_groups(message, con, conf, teacher, is_owner)


@router.callback_query(T.filter(F.act == "groups"))
async def groups_button(cb: CallbackQuery, con, conf, teacher, is_owner: bool = False) -> None:
    await send_groups(cb, con, conf, teacher, is_owner)


@router.message(F.text.startswith("📂 "))
async def legacy_group(message: Message, con, conf, teacher) -> None:
    """Группа слишком большая для приложения в одной ссылке — формы отдельными кнопками."""
    name = message.text[2:].strip()
    g = next((x for x in repo.teacher_groups(con, teacher) if x["name"] == name), None)
    if not g:
        return await message.answer(t("not_your_group", teacher["lang"]))
    reports.set_current_group(con, teacher["id"], g["id"])
    await message.answer(t("group_chosen", teacher["lang"], header=schedule.group_header(g, teacher["lang"])),
                         reply_markup=forms.group_keyboard(con, conf, g, teacher["lang"]))


@router.callback_query(T.filter(F.act == "group"))
async def choose_group(cb: CallbackQuery, callback_data: T, con, conf, teacher) -> None:
    g = repo.group(con, callback_data.id)
    lang = teacher["lang"]
    # Не доверяем кнопке: группа должна быть активной и принадлежать этому учителю
    if not repo.can_teach(teacher, g):
        return await cb.answer(t("not_your_group", lang), show_alert=True)
    reports.set_current_group(con, teacher["id"], g["id"])
    await cb.answer()
    await cb.message.answer(t("group_chosen", lang, header=schedule.group_header(g, lang)),
                            reply_markup=hub.teacher_keyboard(con, conf, teacher))  # старые кнопки чата


@router.message(F.web_app_data)
async def form_data(message: Message, bot: Bot, con, conf, teacher, is_owner: bool = False) -> None:
    now = datetime.now(timezone.utc)
    result = forms.process(con, teacher, message.from_user.id, message.web_app_data.data, message.date, now)
    log.info("Форма от %s: %s", message.from_user.id, "сохранено" if result.group_id else "отклонено")
    if result.text:
        # данные групп в кнопках-приложениях обновляются после каждого сохранения
        await message.answer(result.text, reply_markup=keyboard(con, conf, teacher, is_owner))
    if result.notify_owner and conf.owner_id and conf.owner_id != message.from_user.id:
        try:
            await bot.send_message(conf.owner_id, result.notify_owner)
        except TelegramAPIError:
            pass
    if result.action == "export" and result.group_id:
        await send_export(message, con, teacher, repo.group(con, result.group_id))
    if result.action == "cards" and result.group_id:
        await send_cards_for(message, con, teacher, repo.group(con, result.group_id), result.ids)
        await message.answer("✅", reply_markup=keyboard(con, conf, teacher, is_owner))


async def send_export(message: Message, con, teacher, g) -> None:
    """Excel с отчётами группы за эту и прошлую неделю — в личный чат учителя."""
    from bot import export
    week = reports.week_start(schedule.today())
    data = export.weekly_xlsx(con, [g], [week, week - timedelta(weeks=1)])   # база — в этом же потоке
    log.info("Выгрузка Excel: группа %s, учитель %s", g["id"], message.from_user.id)
    await message.answer_document(BufferedInputFile(data, filename=export.filename(g["name"], week)),
                                  caption=t("export_caption", teacher["lang"], group=g["name"]))


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
    g = repo.group(con, teacher["current_group_id"]) if teacher["current_group_id"] else None
    if not repo.can_teach(teacher, g):
        return await message.answer(t("choose_group_first", teacher["lang"]))
    await send_cards_for(message, con, teacher, g)


async def send_cards_for(message: Message, con, teacher, g, only: list[int] | None = None) -> None:
    """Рисует и присылает карточки группы: только ученики с отчётом за неделю и согласием родителя.

    only — номера учеников, которых учитель выбрал в приложении (None — все готовые).
    """
    lang = teacher["lang"]
    today = schedule.today()
    week = cards_week(con, g["id"], today)
    done = reports.reports_for_weeks(con, g["id"], [week])
    students = repo.group_students(con, g["id"])
    if only is not None:
        students = [s for s in students if s["id"] in set(only)]
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


@router.message(F.text.in_(all_variants("btn_hints")))
async def show_hints(message: Message, con, teacher) -> None:
    lang = teacher["lang"]
    g = repo.group(con, teacher["current_group_id"]) if teacher["current_group_id"] else None
    if not repo.can_teach(teacher, g):
        return await message.answer(t("choose_group_first", lang))
    hints.evaluate_group(con, g["id"])
    rows = hints.open_hints(con, g["id"])
    if not rows:
        return await message.answer(t("hints_none", lang, group=g["name"]))
    await message.answer(t("hints_header", lang, group=g["name"], n=len(rows)))
    for h in rows[:30]:
        await message.answer(hints.describe(con, h, lang),
                             reply_markup=kb([(t("btn_close_hint", lang), T(act="hint_close", id=h["id"]))]))


@router.callback_query(T.filter(F.act == "hint_close"))
async def close_hint(cb: CallbackQuery, callback_data: T, con, teacher) -> None:
    lang = teacher["lang"]
    if hints.close(con, callback_data.id, teacher["id"]):
        await cb.message.edit_text((cb.message.text or "") + "\n" + t("hint_closed", lang))
    await cb.answer(t("hint_closed", lang))


@router.message()
async def fallback(message: Message, teacher) -> None:
    await message.answer(t("press_button", teacher["lang"]))
