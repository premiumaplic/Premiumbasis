"""Бэкапы базы: согласованная копия SQLite → zip с шифрованием AES-256 → закрытый канал.

• Каждый день в 21:30 (настраивается), по команде /backup и перед каждым обновлением.
• На диске хранятся 7 последних копий каждого вида (data\\backups).
• Лимит Telegram для файла от бота — 50 МБ: большой архив отправляется частями.
• Пароль берётся из config.ini и никогда не пишется в журнал и сообщения.
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path

import pyzipper
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import BufferedInputFile

log = logging.getLogger("backup")

KEEP = 7
PART_SIZE = 49 * 1024 * 1024   # с запасом до лимита Telegram в 50 МБ
DB_NAME_IN_ZIP = "school.db"


class BackupError(Exception):
    """Понятное владельцу сообщение."""


def create(con: sqlite3.Connection, data_dir: Path, password: str, reason: str = "daily") -> Path:
    if not password:
        raise BackupError("В config.ini не задан пароль бэкапа (раздел [backup], строка password). "
                          "Бэкап не сделан.")
    folder = data_dir / "backups"
    tmp = data_dir / "tmp"
    folder.mkdir(parents=True, exist_ok=True)
    tmp.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    copy = tmp / f"backup-{stamp}.db"
    dest = sqlite3.connect(str(copy))
    try:
        con.backup(dest)  # встроенный механизм: согласованная копия даже при работающем боте
    finally:
        dest.close()
    target = folder / f"schoolbot-{stamp}-{reason}.zip"
    try:
        with pyzipper.AESZipFile(target, "w", compression=pyzipper.ZIP_DEFLATED,
                                 encryption=pyzipper.WZ_AES) as z:
            z.setpassword(password.encode("utf-8"))
            z.setencryption(pyzipper.WZ_AES, nbits=256)
            z.write(copy, arcname=DB_NAME_IN_ZIP)
    finally:
        copy.unlink(missing_ok=True)
    for old in sorted(folder.glob(f"schoolbot-*-{reason}.zip"))[:-KEEP]:
        old.unlink(missing_ok=True)
    log.info("Бэкап создан: %s (%s КБ)", target.name, target.stat().st_size // 1024)
    return target


def parts(path: Path, size: int = PART_SIZE) -> list[tuple[str, bytes]]:
    """Архив целиком или частями .001, .002… (если больше лимита Telegram)."""
    data = path.read_bytes()
    if len(data) <= size:
        return [(path.name, data)]
    chunks = [data[i:i + size] for i in range(0, len(data), size)]
    return [(f"{path.name}.{i + 1:03d}", chunk) for i, chunk in enumerate(chunks)]


async def send(bot: Bot, channel_id: int, path: Path) -> int:
    """Отправляет архив в канал. Возвращает число отправленных частей."""
    pieces = parts(path)
    when = datetime.now().strftime("%d.%m.%Y %H:%M")
    for i, (name, chunk) in enumerate(pieces, start=1):
        caption = f"Бэкап базы SchoolBot, {when}"
        if len(pieces) > 1:
            caption += f" (часть {i} из {len(pieces)})"
        await bot.send_document(channel_id, BufferedInputFile(chunk, filename=name), caption=caption,
                                request_timeout=600)
    return len(pieces)


async def check_channel(bot: Bot, channel_id: int | None) -> str | None:
    """Проблема с каналом бэкапов (текст для владельца) или None, если всё в порядке."""
    if not channel_id:
        return ("Канал для бэкапов не указан: впишите его ID в config.ini (backup_channel_id). "
                "Пока бэкапы сохраняются только на этом ПК.")
    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(channel_id, me.id)
    except TelegramAPIError:
        return ("Бот не видит канал для бэкапов. Добавьте бота в закрытый канал администратором "
                "с правом публиковать сообщения и проверьте backup_channel_id в config.ini.")
    if member.status != "administrator" or not getattr(member, "can_post_messages", True):
        return "Бот есть в канале бэкапов, но не может публиковать. Сделайте его администратором с правом публикации."
    return None


async def run(bot: Bot, con, data_dir: Path, password: str, channel_id: int | None, reason: str) -> str:
    """Сделать бэкап и отправить в канал. Возвращает отчёт для владельца (без пароля)."""
    path = create(con, data_dir, password, reason)
    size_mb = path.stat().st_size / 1024 / 1024
    if not channel_id:
        return f"Бэкап сохранён на ПК ({size_mb:.1f} МБ). Канал не указан — в Telegram не отправлен."
    try:
        count = await send(bot, channel_id, path)
    except TelegramAPIError as e:
        log.warning("Бэкап не отправлен в канал: %s", type(e).__name__)
        return f"Бэкап сохранён на ПК ({size_mb:.1f} МБ), но в канал не отправлен. Проверьте права бота в канале."
    if count > 1:
        return (f"⚠️ Бэкап большой ({size_mb:.1f} МБ) — отправлен в канал частями: {count}. "
                "Для восстановления скачайте все части в одну папку.")
    return f"Бэкап отправлен в канал ({size_mb:.1f} МБ)."


# ---------------------------------------------------------------- восстановление

def read_archive(path: Path, password: str) -> bytes:
    """Достаёт базу из архива (или из частей .001, .002…). Ошибки — понятным текстом."""
    if path.suffix == ".001":
        base = path.with_suffix("")
        chunks, i = [], 1
        while (part := base.with_name(f"{base.name}.{i:03d}")).exists():
            chunks.append(part.read_bytes())
            i += 1
        data = b"".join(chunks)
        import io
        source = io.BytesIO(data)
    else:
        source = path
    try:
        with pyzipper.AESZipFile(source) as z:
            z.setpassword(password.encode("utf-8"))
            return z.read(DB_NAME_IN_ZIP)
    except RuntimeError:
        raise BackupError("Неверный пароль бэкапа.") from None
    except (pyzipper.BadZipFile, KeyError, OSError):
        raise BackupError("Файл повреждён или это не бэкап SchoolBot (если бэкап из частей — "
                          "положите все части в одну папку и выберите часть .001).") from None


def inspect(db_path: Path) -> dict:
    """Проверяет, что в файле целая база SchoolBot, и возвращает краткую сводку."""
    con = sqlite3.connect(str(db_path))
    try:
        if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise BackupError("База в бэкапе повреждена.")
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        if not {"teachers", "groups", "students"} <= tables:
            raise BackupError("В архиве не база SchoolBot.")
        return {
            "version": con.execute("PRAGMA user_version").fetchone()[0],
            "students": con.execute("SELECT count(*) FROM students WHERE active = 1").fetchone()[0],
            "groups": con.execute("SELECT count(*) FROM groups WHERE active = 1").fetchone()[0],
            "last_report": con.execute("SELECT max(week_start) FROM weekly_reports").fetchone()[0] or "—",
        }
    except sqlite3.DatabaseError:
        raise BackupError("В архиве не база SQLite.") from None
    finally:
        con.close()
