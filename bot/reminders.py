"""Напоминание учителям в конце учебной недели: по каким ученикам нет недельного отчёта.

День и время — в настройках (по умолчанию суббота, 18:00, не позже 21:00).
Если в это время бот был выключен, напоминание уйдёт после запуска в тот же день (до 22:00).
"""

import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from bot import repo, reports
from bot.texts import t
from bot.timefmt import TZ

log = logging.getLogger("reminders")
LATEST = "22:00"


def due_week(con, now: datetime) -> str | None:
    """Неделя (понедельник), за которую пора напомнить, или None."""
    local = now.astimezone(TZ)
    day = repo.get_int(con, "reminder_day", 6)
    at = repo.get_setting(con, "reminder_time", "18:00")
    if local.isoweekday() != day or not at <= local.strftime("%H:%M") < LATEST:
        return None
    week = reports.week_start(local.date()).isoformat()
    if repo.get_setting(con, "reminder_last_week") == week:
        return None
    return week


def messages(con, week_iso: str) -> list[tuple[int, str]]:
    """[(Telegram ID учителя, текст)] — только тем, у кого есть незаполненные ученики."""
    from datetime import date
    week = date.fromisoformat(week_iso)
    out = []
    for teacher in repo.list_teachers(con, only_active=True):
        lang = teacher["lang"]
        lines = []
        for g in repo.list_groups(con, teacher_id=teacher["id"]):
            total = g["student_count"]
            left = reports.students_without_report(con, g["id"], week)
            if left:
                names = ", ".join(repo.short_name(s["full_name"]) for s in left)
                lines.append(t("reminder_group", lang, group=g["name"], names=names, k=len(left), total=total))
        if lines:
            week_text = f"{week.strftime('%d.%m')}–{(week + timedelta(days=5)).strftime('%d.%m')}"
            out.append((teacher["tg_id"], t("reminder", lang, week=week_text) + "\n\n" + "\n".join(lines)))
    return out


async def send_due(bot: Bot, con, now: datetime | None = None) -> int:
    now = now or datetime.now(TZ)
    week = due_week(con, now)
    if not week:
        return 0
    repo.set_setting(con, 0, "reminder_last_week", week, quiet=True)  # 0 — действие самого бота
    sent = 0
    for tg_id, text in messages(con, week):
        try:
            await bot.send_message(tg_id, text)
            sent += 1
        except TelegramAPIError as e:
            log.warning("Напоминание учителю %s не доставлено: %s", tg_id, type(e).__name__)
    log.info("Напоминания за неделю %s отправлены: %s", week, sent)
    return sent


async def loop(bot: Bot, con) -> None:
    while True:
        try:
            await send_due(bot, con)
        except Exception:
            log.exception("Ошибка при отправке напоминаний")
        await asyncio.sleep(30)
