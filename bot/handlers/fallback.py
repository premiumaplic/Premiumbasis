"""Последний обработчик: всё, что не подошло другим."""

from aiogram import Router
from aiogram.types import CallbackQuery, Message

from bot.texts import t

router = Router(name="fallback")


@router.message()
async def any_message(message: Message, lang: str = "ru") -> None:
    await message.answer(t("press_button", lang))


@router.callback_query()
async def any_button(cb: CallbackQuery) -> None:
    # Старая кнопка (например, после перезапуска бота) — просто убираем «часики»
    await cb.answer("Нажмите /start", show_alert=False)
