"""Упаковка данных для ссылок форм и проверка размера ответа форм.

Ссылка формы несёт данные группы в одном параметре `d`:
    "1" + base64url(deflate(JSON))   — сжатый вариант (основной)
    "0" + base64url(JSON)            — без сжатия (запасной)

Форма возвращает боту обычный JSON через Telegram.WebApp.sendData,
не больше 4096 байт.
"""

import base64
import json
import zlib

SEND_DATA_LIMIT = 4096  # байт, ограничение Telegram для sendData


def to_json(obj) -> str:
    """Компактный JSON: без пробелов, кириллица как есть (не \\uXXXX)."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _unb64url(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def encode_param(obj, compress: bool = True) -> str:
    """Данные -> строка для параметра ссылки."""
    raw = to_json(obj).encode("utf-8")
    if compress:
        packer = zlib.compressobj(9, zlib.DEFLATED, -15)  # "сырой" deflate
        return "1" + _b64url(packer.compress(raw) + packer.flush())
    return "0" + _b64url(raw)


def decode_param(text: str):
    """Обратное действие (нужно для тестов и проверок)."""
    kind, body = text[:1], text[1:]
    raw = _unb64url(body)
    if kind == "1":
        raw = zlib.decompress(raw, -15)
    elif kind != "0":
        raise ValueError("неизвестный формат параметра")
    return json.loads(raw.decode("utf-8"))


def byte_size(text: str) -> int:
    """Сколько байт займёт строка в UTF-8 (так считает Telegram)."""
    return len(text.encode("utf-8"))
