"""Основной бот. Запуск: start.bat (python -m bot)."""

import asyncio
import logging
import sys

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramUnauthorizedError
from aiogram.types import BotCommand

from bot import config as cfg
from bot import db, keepawake, logsetup, single
from bot.app import build_dispatcher

log = logging.getLogger("bot")


def open_database():
    """Открывает базу и применяет миграции (перед миграциями — локальная копия)."""
    data = cfg.data_dir()
    path = data / "school.db"
    existed = path.exists()
    con = db.connect(path)
    pending = [n for n, _ in db.migrations() if n > db.schema_version(con)]
    if existed and pending and db.schema_version(con) > 0:
        copy = db.local_copy(con, data / "backups", "before-migration")
        log.info("Перед обновлением базы сделана копия: %s", copy.name)
    applied = db.migrate(con)
    if applied:
        log.info("База обновлена до версии %s", db.schema_version(con))
    return con


async def run(conf: cfg.Config) -> None:
    con = open_database()
    bot = Bot(conf.token)
    dp = build_dispatcher(conf, con)
    me = await bot.get_me()
    log.info("Бот @%s запущен", me.username)
    if keepawake.prevent_sleep():
        log.info("Компьютер не уйдёт в сон, пока открыто окно бота")
    await bot.set_my_commands([BotCommand(command="start", description="Начать / меню"),
                               BotCommand(command="myid", description="Мой Telegram ID"),
                               BotCommand(command="cancel", description="Отменить ввод")])
    if conf.owner_id:
        try:
            await bot.send_message(conf.owner_id, "Бот запущен. Меню: /start")
        except TelegramAPIError:
            log.info("Не смог написать владельцу: откройте бота в Telegram и нажмите Start")
    else:
        print("\n>>> В config.ini не вписан owner_id. Напишите боту /myid, впишите номер "
              "в config.ini и перезапустите start.bat\n")
    # Старые обновления не сбрасываются: формы, отправленные пока бот был выключен, обработаются
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


def main() -> int:
    try:
        conf = cfg.load()
    except cfg.ConfigError as e:
        print(f"\nОШИБКА НАСТРОЕК: {e}\n")
        return 2
    if not single.acquire(cfg.data_dir() / "bot.lock"):
        print("\nБот уже запущен в другом окне. Это окно можно закрыть.\n")
        return 2
    logsetup.setup(cfg.data_dir() / "logs", "bot", [conf.token, conf.backup_password])
    try:
        asyncio.run(run(conf))
    except TelegramUnauthorizedError:
        print("\nОШИБКА НАСТРОЕК: Telegram не принял токен. Проверьте строку token в config.ini.\n")
        return 2
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
