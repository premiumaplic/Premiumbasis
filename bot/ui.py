"""Кнопки и данные кнопок."""

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class A(CallbackData, prefix="a"):
    """Кнопки меню владельца. act — что сделать, id и arg — номера объектов."""
    act: str
    id: int = 0
    arg: int = 0


class T(CallbackData, prefix="t"):
    """Кнопки учителя."""
    act: str
    id: int = 0


def kb(*rows) -> InlineKeyboardMarkup:
    """kb([("Текст", callback), ...], [...]) — строки кнопок. Пустые строки пропускаются."""
    keyboard = []
    for row in rows:
        buttons = [InlineKeyboardButton(text=text, callback_data=cb.pack() if hasattr(cb, "pack") else cb)
                   for text, cb in row]
        if buttons:
            keyboard.append(buttons)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def column(items, per_row: int = 1) -> list[list]:
    """Список кнопок -> строки по per_row штук."""
    items = list(items)
    return [items[i:i + per_row] for i in range(0, len(items), per_row)]


def yes_no(value) -> str:
    return "да" if value else "нет"


LANG_NAMES = {"ru": "русский", "uz": "узбекский"}
