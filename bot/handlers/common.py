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


@router.my_chat_member()
async def leave_groups(event: ChatMemberUpdated, bot: Bot) -> None:
    # Бот работает только в личных чатах: из групп выходит сразу (канал бэкапов — исключение)
    if event.chat.type in ("group", "supergroup"):
        log.info("Бота добавили в группу %s — выхожу", event.chat.id)
        try:
            await bot.leave_chat(event.chat.id)
        except TelegramBadRequest:
            pass


@router.message(Command("myid"))
async def my_id(message: Message, lang: str = "ru") -> None:
    await message.answer(t("my_id", lang, id=message.from_user.id))
