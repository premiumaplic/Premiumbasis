"""Время по-человечески: «сегодня в 10:41», «вчера в 22:40». Часовой пояс — Ташкент."""

from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Tashkent")


def human_time(moment: datetime, now: datetime) -> str:
    moment, now = moment.astimezone(TZ), now.astimezone(TZ)
    days = (now.date() - moment.date()).days
    clock = moment.strftime("%H:%M")
    if days == 0:
        return f"сегодня в {clock}"
    if days == 1:
        return f"вчера в {clock}"
    return f"{moment.strftime('%d.%m')} в {clock}"


def human_duration(seconds: float) -> str:
    minutes = int(seconds // 60)
    if minutes < 60:
        return f"{minutes} мин"
    hours, minutes = divmod(minutes, 60)
    return f"{hours} ч {minutes} мин"
