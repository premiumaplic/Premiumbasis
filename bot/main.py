"""Основной бот. Запуск: start.bat (python -m bot)."""

import asyncio
import logging
import sys

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramUnauthorizedError
from aiogram.types import BotCommand

from bot import config as cfg
from bot import backup, db, keepawake, logsetup, scheduler, single
from bot.app import build_dispatcher

log = logging.getLogger("bot")


def clean_tmp() -> None:
    """Временные файлы старше суток удаляются (они только внутри data\\tmp)."""
    import time
    tmp = cfg.data_dir() / "tmp"
    if not tmp.exists():
        return
    for f in tmp.rglob("*"):
        try:
            if f.is_file() and time.time() - f.stat().st_mtime > 86400:
                f.unlink()
        except OSError:
            pass


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


async def set_description(bot: Bot) -> None:
    """Описание бота (до «Старт») на русском и узбекском — только если владелец не задал своё."""
    from bot.texts import BOT_DESCRIPTION, BOT_SHORT_DESCRIPTION
    for lang, code in (("ru", None), ("uz", "uz")):
        try:
            if not (await bot.get_my_description(language_code=code)).description:
                await bot.set_my_description(description=BOT_DESCRIPTION[lang], language_code=code)
            if not (await bot.get_my_short_description(language_code=code)).short_description:
                await bot.set_my_short_description(short_description=BOT_SHORT_DESCRIPTION[lang], language_code=code)
        except TelegramAPIError as e:
            log.info("Описание бота не обновлено: %s", type(e).__name__)


async def run(conf: cfg.Config) -> None:
    clean_tmp()
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
    # /backup и /summary — команды владельца, в общий список не выносим
    await set_description(bot)
    if conf.owner_id:
        try:
            from bot import __version__
            await bot.send_message(conf.owner_id, f"Бот запущен (версия {__version__}). Меню: /start")
        except TelegramAPIError:
            log.info("Не смог написать владельцу: откройте бота в Telegram и нажмите Start")
    else:
        print("\n>>> В config.ini не вписан owner_id. Напишите боту /myid, впишите номер "
              "в config.ini и перезапустите start.bat\n")
    problem = await backup.check_channel(bot, conf.backup_channel_id)
    if problem:
        log.warning("Канал бэкапов: %s", problem)
        if conf.owner_id:
            try:
                await bot.send_message(conf.owner_id, "⚠️ " + problem)
            except TelegramAPIError:
                pass
    from bot import sitecheck
    site_problem = await sitecheck.check(conf.forms_url)
    if site_problem:
        log.warning("Сайт с формами: %s", site_problem)
        if conf.owner_id:
            try:
                await bot.send_message(conf.owner_id, "⚠️ " + site_problem)
            except TelegramAPIError:
                pass
    jobs = asyncio.create_task(scheduler.loop(bot, con, conf))  # noqa: F841 — живёт, пока работает бот
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
