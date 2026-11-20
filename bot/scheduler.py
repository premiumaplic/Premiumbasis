"""Дела по расписанию (проверка раз в 30 секунд, пока бот работает):
  • напоминание учителям в конце недели;
  • сводка владельцу в тот же день;
  • ежедневный бэкап (и сразу после запуска, если последнему больше суток);
  • раз в день — пересчёт подсказок (например, когда до экзамена осталось 3 недели).
"""

import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from bot import backup, config, hints, reminders, reports, repo, summary
from bot.timefmt import TZ

log = logging.getLogger("scheduler")
SYSTEM = 0  # «действие самого бота» в журнале


def backup_due(con, now: datetime) -> bool:
    local = now.astimezone(TZ).replace(tzinfo=None)
    last = repo.get_setting(con, "backup_last")
    if not last:
        return True
    last_dt = datetime.fromisoformat(last)
    if local - last_dt > timedelta(hours=26):
        return True  # ПК был выключен в обычное время бэкапа
    at = repo.get_setting(con, "backup_time", "21:30")
    return local.strftime("%H:%M") >= at and last_dt.date() < local.date()


def summary_due(con, now: datetime) -> str | None:
    local = now.astimezone(TZ)
    if local.isoweekday() != repo.get_int(con, "reminder_day", 6):
        return None
    if local.strftime("%H:%M") < repo.get_setting(con, "summary_time", "20:00"):
        return None
    week = reports.week_start(local.date()).isoformat()
    return None if repo.get_setting(con, "summary_last_week") == week else week


async def tick(bot: Bot, con, conf, now: datetime | None = None) -> None:
    now = now or datetime.now(TZ)
    local = now.astimezone(TZ)

    await reminders.send_due(bot, con, now)

    week = summary_due(con, now)
    if week and conf.owner_id:
        repo.set_setting(con, SYSTEM, "summary_last_week", week, quiet=True)
        from datetime import date
        try:
            await bot.send_message(conf.owner_id, summary.text(con, date.fromisoformat(week)))
        except TelegramAPIError as e:
            log.warning("Сводка не доставлена: %s", type(e).__name__)

    if backup_due(con, now):
        repo.set_setting(con, SYSTEM, "backup_last", local.replace(tzinfo=None).isoformat(timespec="seconds"),
                         quiet=True)
        try:
            report = await backup.run(bot, con, config.data_dir(), conf.backup_password, conf.backup_channel_id, "daily")
            log.info(report)
            if report.startswith("⚠️") and conf.owner_id:
                await bot.send_message(conf.owner_id, report)
        except backup.BackupError as e:
            log.warning("Бэкап не сделан: нет пароля")
            if conf.owner_id:
                await bot.send_message(conf.owner_id, str(e))

    today = local.date().isoformat()
    if repo.get_setting(con, "hints_last_day") != today:
        repo.set_setting(con, SYSTEM, "hints_last_day", today, quiet=True)
        for g in repo.list_groups(con):
            hints.evaluate_group(con, g["id"], local.date())


async def loop(bot: Bot, con, conf) -> None:
    while True:
        try:
            await tick(bot, con, conf)
        except Exception:
            log.exception("Ошибка в делах по расписанию")
        await asyncio.sleep(30)
