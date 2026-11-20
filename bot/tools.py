"""Служебные команды для батников:
    python -m bot.tools backup <пометка>   — бэкап (шифрованный, + в канал); update.bat перед обновлением
    python -m bot.tools migrate            — применить миграции базы
    python -m bot.tools restore            — восстановить базу из бэкапа (restore.bat)
"""

import asyncio
import getpass
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from bot import backup, config as cfg, db, single


def _backup(reason: str) -> int:
    path = cfg.data_dir() / "school.db"
    if not path.exists():
        print("Базы ещё нет — копировать нечего.")
        return 0
    con = db.connect(path)
    try:
        conf = cfg.load()
    except cfg.ConfigError as e:
        print(f"Настройки: {e}")
        conf = None
    if conf is None or not conf.backup_password:
        # без пароля шифрованный бэкап невозможен — хотя бы простая копия на ПК
        copy = db.local_copy(con, cfg.data_dir() / "backups", reason)
        print(f"Пароль бэкапа не задан — сделана простая копия базы на ПК: {copy.name}")
        return 0
    archive = backup.create(con, cfg.data_dir(), conf.backup_password, reason)
    print(f"Шифрованный бэкап: {archive.name}")
    if conf.backup_channel_id:
        async def send() -> str:
            from aiogram import Bot
            bot = Bot(conf.token)
            try:
                count = await backup.send(bot, conf.backup_channel_id, archive)
                return f"Отправлен в канал (частей: {count})."
            finally:
                await bot.session.close()
        try:
            print(asyncio.run(send()))
        except Exception as e:  # нет интернета и т.п. — копия на ПК всё равно есть
            print(f"В канал не отправлен ({type(e).__name__}), копия есть на ПК.")
    return 0


def _ask(prompt: str) -> str:
    return input(prompt).strip().strip('"').strip("'")


def _restore() -> int:
    data = cfg.data_dir()
    if not single.acquire(data / "bot.lock"):
        print("Бот сейчас работает. Закройте окно бота и запустите restore.bat снова.")
        return 1
    print("Восстановление базы из бэкапа.\n")
    path = Path(_ask("Перетащите файл бэкапа (.zip или часть .001) в это окно и нажмите Enter:\n> "))
    if not path.exists():
        print("Файл не найден.")
        return 1
    password = getpass.getpass("Пароль бэкапа (буквы не видны при вводе): ")
    try:
        raw = backup.read_archive(path, password)
    except backup.BackupError as e:
        print(e)
        return 1
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    candidate = data / "tmp" / f"restore-{stamp}.db"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_bytes(raw)
    try:
        info = backup.inspect(candidate)
    except backup.BackupError as e:
        candidate.unlink(missing_ok=True)
        print(e)
        return 1
    print(f"\nВ бэкапе: групп {info['groups']}, учеников {info['students']}, "
          f"последний недельный отчёт: {info['last_report']}.")
    if _ask("Заменить текущую базу этим бэкапом? Напишите да и нажмите Enter: ").lower() not in ("да", "ha", "yes"):
        candidate.unlink(missing_ok=True)
        print("Отменено. Ничего не изменено.")
        return 0

    current = data / "school.db"
    if current.exists():
        # сначала сохраняем текущую базу рядом, с пометкой даты
        saved = data / "backups" / f"school-before-restore-{stamp}.db"
        saved.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(str(current))
        dest = sqlite3.connect(str(saved))
        con.backup(dest)
        dest.close()
        con.close()
        print(f"Текущая база сохранена: {saved}")
        for suffix in ("", "-wal", "-shm"):
            Path(str(current) + suffix).unlink(missing_ok=True)
    candidate.replace(current)
    con = db.connect(current)
    db.migrate(con)  # бэкап мог быть от старой версии программы
    con.close()
    print("Готово: база восстановлена. Запустите start.bat.")
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    if argv[0] == "backup":
        return _backup(argv[1] if len(argv) > 1 else "manual")
    if argv[0] == "migrate":
        con = db.connect(cfg.data_dir() / "school.db")
        applied = db.migrate(con)
        print(f"База: версия {db.schema_version(con)}" + (f" (применено: {applied})" if applied else ""))
        con.close()
        return 0
    if argv[0] == "restore":
        return _restore()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
