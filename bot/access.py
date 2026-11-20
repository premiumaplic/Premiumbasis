"""Кто есть кто: владелец, учитель или посторонний. Плюс ограничение частоты сообщений.

Проверка идёт на КАЖДОМ сообщении, нажатии кнопки и данных формы.
Посторонним бот не показывает никаких данных — только их Telegram ID.
"""

import logging
import time
from collections import defaultdict, deque

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from bot import repo
from bot.texts import t

log = logging.getLogger("access")


class RateLimiter:
    """Не больше `limit` событий от одного человека за 60 секунд; лишнее молча игнорируется."""

    def __init__(self, window: float = 60.0):
        self.window = window
        self.events: dict[int, deque] = defaultdict(deque)
        self.warned: dict[int, float] = {}

    def allow(self, user_id: int, limit: int, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        q = self.events[user_id]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= limit:
            if now - self.warned.get(user_id, -1e9) > self.window:
                self.warned[user_id] = now
                log.warning("Слишком много сообщений от %s — лишние игнорируются", user_id)
            return False
        q.append(now)
        return True


def is_command(message: Message, name: str) -> bool:
    text = (message.text or "").strip()
    return bool(text) and text.split()[0].split("@")[0].lower() == f"/{name}"


class AccessMiddleware(BaseMiddleware):
    def __init__(self, conf, con):
        self.conf = conf
        self.con = con
        self.limiter = RateLimiter()

    async def __call__(self, handler, event, data):
        if isinstance(event, Message):
            chat = event.chat
        elif isinstance(event, CallbackQuery):
            chat = event.message.chat if event.message else None
        else:
            return await handler(event, data)
        user = event.from_user
        # Бот работает только в личных чатах
        if user is None or chat is None or chat.type != "private":
            return None
        if not self.limiter.allow(user.id, repo.get_int(self.con, "rate_limit_per_min", 30)):
            return None

        is_owner = self.conf.owner_id is not None and user.id == self.conf.owner_id
        teacher = repo.teacher_by_tg(self.con, user.id)
        if teacher is not None and not teacher["active"]:
            teacher = None
        data.update(con=self.con, conf=self.conf, is_owner=is_owner, teacher=teacher,
                    lang=teacher["lang"] if teacher else "ru")

        if is_owner or teacher is not None:
            return await handler(event, data)
        if isinstance(event, Message) and is_command(event, "myid"):
            return await handler(event, data)
        log.info("Отказано в доступе: %s", user.id)
        if isinstance(event, Message):
            await event.answer(t("no_access", "ru", id=user.id) + "\n\n" + t("no_access", "uz", id=user.id))
        else:
            await event.answer("Нет доступа", show_alert=True)
        return None


class OwnerOnly:
    """Фильтр: обработчик срабатывает только для владельца."""

    async def __call__(self, event, is_owner: bool = False) -> bool:
        return is_owner


class TeacherOnly:
    async def __call__(self, event, teacher=None) -> bool:
        return teacher is not None
