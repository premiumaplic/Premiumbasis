"""Журнал работы бота: data\\logs, хранится 30 дней. Секреты из журнала вычищаются."""

import logging
import re
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

# Всё, что похоже на токен бота, заменяется звёздочками
TOKEN_PATTERN = re.compile(r"\d{5,}:[A-Za-z0-9_-]{30,}")


class SecretFilter(logging.Filter):
    def __init__(self, secrets: list[str]):
        super().__init__()
        self.secrets = [s for s in secrets if s]

    def _clean(self, text: str) -> str:
        for secret in self.secrets:
            text = text.replace(secret, "***")
        return TOKEN_PATTERN.sub("***", text)

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        if record.exc_info:
            message += "\n" + logging.Formatter().formatException(record.exc_info)
            record.exc_info = None
            record.exc_text = None
        record.msg = self._clean(message)
        record.args = None
        return True


def setup(log_dir: Path, name: str, secrets: list[str]) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    secret_filter = SecretFilter(secrets)

    file_handler = TimedRotatingFileHandler(
        log_dir / f"{name}.log", when="midnight", backupCount=30, encoding="utf-8")
    console = logging.StreamHandler()
    for handler in (file_handler, console):
        handler.setFormatter(fmt)
        handler.addFilter(secret_filter)

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.INFO)
    root.addHandler(file_handler)
    root.addHandler(console)
    # Подробности сетевой библиотеки не нужны
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
