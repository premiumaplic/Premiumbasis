"""Общее для всех: /myid, выход из групповых чатов, вывод сообщений."""

import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, ChatMemberUpdated, Message

from bot.texts import t

log = logging.getLogger("bot")
router = Router(name="common")


async def show(target, text: str, markup=None) -> None:
    """Показать экран: при нажатии кнопки — заменить сообщение, иначе — отправить новое."""
    if isinstance(target, CallbackQuery):
        try:
            await target.message.edit_text(text, reply_markup=markup)
        except TelegramBadRequest as e:
            if "not modified" not in str(e):
                await target.message.answer(text, reply_markup=markup)
        await target.answer()
    else:
        await target.answer(text, reply_markup=markup)


def channel_text(title: str, chat_id: int, can_post: bool, already: bool) -> str:
    lines = [f"ID канала «{title}»: {chat_id}"]
    if already:
        lines.append("Этот канал уже указан в config.ini — всё в порядке.")
    else:
        lines += ["Откройте config.ini и впишите строку:", f"backup_channel_id = {chat_id}",
                  "Сохраните файл и перезапустите бота (закройте окно и снова start.bat)."]
    if not can_post:
        lines.append("⚠️ У бота нет права публиковать сообщения в канале — включите его в правах администратора.")
    return "\n".join(lines)


@router.my_chat_member()
async def membership(event: ChatMemberUpdated, bot: Bot, conf=None) -> None:
    owner = conf.owner_id if conf else None
    added_by_owner = owner is not None and event.from_user and event.from_user.id == owner
    # Бот работает только в личных чатах: из групп выходит сразу (канал бэкапов — исключение)
    if event.chat.type in ("group", "supergroup"):
        if event.new_chat_member.status in ("left", "kicked"):
            return
        log.info("Бота добавили в группу %s — выхожу", event.chat.id)
        try:
            await bot.leave_chat(event.chat.id)
        except TelegramBadRequest:
            pass
        if added_by_owner:
            await bot.send_message(owner, f"Меня добавили в группу «{event.chat.title}», я из неё вышел: "
                                          "в группах бот не работает. Для бэкапов нужен закрытый КАНАЛ "
                                          "(в Telegram: «Создать канал», тип «Частный»). Добавьте меня туда "
                                          "администратором — я сам пришлю ID канала.")
        return
    if event.chat.type == "channel" and added_by_owner and event.new_chat_member.status == "administrator":
        # Бота сделали администратором канала — сразу сообщаем владельцу ID для config.ini
        can_post = bool(getattr(event.new_chat_member, "can_post_messages", False))
        await bot.send_message(owner, channel_text(event.chat.title or "", event.chat.id, can_post,
                                                   conf.backup_channel_id == event.chat.id))


@router.message(F.forward_origin)
async def forwarded(message: Message, is_owner: bool = False, lang: str = "ru") -> None:
    """Владелец пересылает сообщение из канала — бот подсказывает ID для config.ini."""
    if not is_owner:
        return await message.answer(t("press_button", lang))
    origin = message.forward_origin
    if origin.type == "channel":
        return await message.answer(channel_text(origin.chat.title or "", origin.chat.id, True, False))
    if origin.type == "chat":
        return await message.answer("Это сообщение из группы, а для бэкапов нужен закрытый КАНАЛ. "
                                    "Создайте канал, добавьте меня туда администратором — я сам пришлю ID.")
    await message.answer("Это пересланное сообщение не из канала (или переслано со скрытым отправителем). "
                         "Проще так: добавьте меня в закрытый канал администратором — я сам пришлю ID канала.")


@router.message(Command("myid"))
async def my_id(message: Message, lang: str = "ru") -> None:
    await message.answer(t("my_id", lang, id=message.from_user.id))
