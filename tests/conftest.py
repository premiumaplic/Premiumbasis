"""Общие заготовки для тестов. Все данные выдуманные."""

import datetime as dt

import pytest
from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.types import ChatMemberAdministrator, Message, Update, User

from bot import db, repo

OWNER = 500001
ACTOR = OWNER


@pytest.fixture
def con():
    connection = db.connect(":memory:")
    db.migrate(connection)
    yield connection
    connection.close()


def make_teacher(con, tg_id=600001, name="Учитель Тестов", lang="ru"):
    return repo.save_teacher(con, ACTOR, tg_id, name, lang)[0]


def make_group(con, name="10-А", subject="en", teacher_id=None, stage="a1", start=dt.date(2026, 9, 1)):
    stage_row = repo.stage_by_code(con, subject, stage) if stage else None
    return repo.create_group(con, ACTOR, name, subject, teacher_id, stage_row["id"] if stage_row else None,
                             start, "1,3,5", "15:00")


class FakeSession(BaseSession):
    """Вместо Telegram: запоминает, что бот отправил."""

    def __init__(self):
        super().__init__()
        self.calls = []

    async def make_request(self, bot, method, timeout=None):
        self.calls.append(method)
        name = type(method).__name__
        if name in ("SendMessage", "EditMessageText", "SendDocument", "SendPhoto"):
            chat_id = getattr(method, "chat_id", None) or 1
            return Message.model_validate(
                {"message_id": len(self.calls), "date": dt.datetime.now(),
                 "chat": {"id": chat_id, "type": "private"}, "text": getattr(method, "text", None) or ""},
                context={"bot": bot})
        if name == "GetMe":
            return User(id=42, is_bot=True, first_name="SchoolBot", username="school_test_bot")
        if name == "GetChatMember":
            return ChatMemberAdministrator.model_validate({
                "status": "administrator", "user": {"id": 42, "is_bot": True, "first_name": "Bot"},
                **{k: False for k in ChatMemberAdministrator.model_fields
                   if k.startswith("can_") or k == "is_anonymous"},
                "can_post_messages": True})
        return True

    async def close(self):
        pass

    async def stream_content(self, *args, **kwargs):
        yield b""

    def texts(self):
        return [getattr(c, "text", None) for c in self.calls if getattr(c, "text", None)]


class Chat:
    """Мини-эмулятор переписки с ботом для сквозных тестов."""

    def __init__(self, dp, bot, session):
        self.dp, self.bot, self.session = dp, bot, session
        self.n = 0

    def _msg(self, user, chat_type="private", **extra):
        self.n += 1
        base = {"message_id": self.n, "date": int(dt.datetime.now().timestamp()),
                "chat": {"id": user if chat_type == "private" else -100, "type": chat_type},
                "from": {"id": user, "is_bot": False, "first_name": "X"}}
        base.update(extra)
        return base

    async def send(self, user, text, chat_type="private"):
        start = len(self.session.calls)
        await self.dp.feed_update(self.bot, Update(update_id=self.n + 1, message=self._msg(user, chat_type, text=text)))
        return self.session.calls[start:]

    async def press(self, user, data):
        start = len(self.session.calls)
        self.n += 1
        await self.dp.feed_update(self.bot, Update(update_id=self.n, callback_query={
            "id": str(self.n), "chat_instance": "x", "data": data,
            "from": {"id": user, "is_bot": False, "first_name": "X"},
            "message": self._msg(user, text="old")}))
        return self.session.calls[start:]


@pytest.fixture
def chat(con, tmp_path, monkeypatch):
    from bot import config as cfg
    from bot.app import build_dispatcher
    monkeypatch.setenv("SB_ROOT", str(tmp_path))
    conf = cfg.Config(token="1:x", owner_id=OWNER, backup_channel_id=None,
                      forms_url="https://example.github.io/Repo/")
    session = FakeSession()
    bot = Bot("123456:" + "A" * 35, session=session)
    return Chat(build_dispatcher(conf, con), bot, session)


def last_text(calls):
    texts = [getattr(c, "text", None) for c in calls if getattr(c, "text", None)]
    return texts[-1] if texts else ""


def buttons(calls):
    """Все inline-кнопки последнего ответа: {текст: callback_data}."""
    for c in reversed(calls):
        markup = getattr(c, "reply_markup", None)
        if markup is not None and hasattr(markup, "inline_keyboard"):
            return {b.text: b.callback_data for row in markup.inline_keyboard for b in row}
    return {}
