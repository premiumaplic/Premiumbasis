"""Чтение настроек из config.ini (лежит в корне папки, например D:\\SchoolBot\\config.ini).

В config.ini хранятся секреты: токен бота, ID владельца, ID канала, пароль бэкапа.
Этот файл никогда не попадает в GitHub (см. .gitignore).
"""

import configparser
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

TOKEN_RE = re.compile(r"^\d{5,}:[A-Za-z0-9_-]{30,}$")


class ConfigError(Exception):
    """Понятное владельцу сообщение о том, что не так в config.ini."""


def root_dir() -> Path:
    """Корень системы. Батники задают SB_ROOT; при разработке — папка репозитория."""
    env = os.environ.get("SB_ROOT")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parents[1]


def data_dir() -> Path:
    path = root_dir() / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _parse_ids(text: str) -> list[int]:
    ids = []
    for part in re.split(r"[,\s;]+", text.strip()):
        if part:
            if not part.lstrip("-").isdigit():
                raise ConfigError(f"«{part}» — это не Telegram ID (нужны только цифры).")
            ids.append(int(part))
    return ids


@dataclass
class Config:
    token: str
    owner_id: int | None
    backup_channel_id: int | None
    forms_url: str
    backup_password: str = field(repr=False, default="")
    testers: list[int] = field(default_factory=list)

    def __repr__(self) -> str:  # чтобы токен и пароль случайно не попали в лог
        return f"Config(owner_id={self.owner_id}, forms_url={self.forms_url!r})"


def load(path: Path | None = None) -> Config:
    path = path or root_dir() / "config.ini"
    if not path.exists():
        raise ConfigError(f"Не найден файл настроек {path}. Запустите setup.bat ещё раз.")
    parser = configparser.ConfigParser()
    # utf-8-sig: Блокнот иногда добавляет в начало файла невидимую метку
    parser.read(path, encoding="utf-8-sig")

    def get(section: str, key: str) -> str:
        return parser.get(section, key, fallback="").strip()

    token = get("telegram", "token")
    if not token:
        raise ConfigError("В config.ini не вписан токен бота (строка token = ...).")
    if not TOKEN_RE.match(token):
        raise ConfigError("Токен бота в config.ini выглядит неправильно. "
                          "Скопируйте его из @BotFather целиком, без пробелов и кавычек.")

    owner = get("telegram", "owner_id")
    owner_ids = _parse_ids(owner) if owner else []
    channel = get("telegram", "backup_channel_id")
    channel_ids = _parse_ids(channel) if channel else []

    forms_url = get("forms", "base_url") or "https://premiumaplic.github.io/Premiumbasis/"
    if not forms_url.startswith("https://"):
        raise ConfigError("Адрес форм (base_url) должен начинаться с https://")
    if not forms_url.endswith("/"):
        forms_url += "/"

    return Config(
        token=token,
        owner_id=owner_ids[0] if owner_ids else None,
        backup_channel_id=channel_ids[0] if channel_ids else None,
        forms_url=forms_url,
        backup_password=get("backup", "password"),
        testers=_parse_ids(get("probe", "testers")),
    )


def save_value(section: str, key: str, value: str, path: Path | None = None) -> None:
    """Записывает одно значение в config.ini, не трогая остальной текст и комментарии."""
    path = path or root_dir() / "config.ini"
    text = path.read_text(encoding="utf-8-sig") if path.exists() else ""
    lines = text.splitlines()
    current, section_end, done = None, None, False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if current == section and not done:
                section_end = i
                break
            current = stripped[1:-1].strip()
            continue
        if current == section and re.match(rf"^\s*{re.escape(key)}\s*=", line):
            lines[i] = f"{key} = {value}"
            done = True
    if not done:
        if current == section and section_end is None:
            lines.append(f"{key} = {value}")
        elif section_end is not None:
            lines.insert(section_end, f"{key} = {value}")
        else:
            lines += ["", f"[{section}]", f"{key} = {value}"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\r\n")  # переводы строк Windows
