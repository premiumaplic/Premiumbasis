"""Ищет в файлах репозитория строки, похожие на секреты (токен бота и т.п.).

Запускается перед каждым коммитом (git-хук) и в GitHub Actions.
Использование:  python scripts/check_secrets.py [файлы...]
Без аргументов проверяет все файлы, которые отслеживает git.
"""

import re
import subprocess
import sys
from pathlib import Path

PATTERNS = {
    "токен Telegram-бота": re.compile(r"\b\d{6,12}:AA[A-Za-z0-9_-]{30,}\b"),
    "заполненный token в настройках": re.compile(r"^[ \t]*token[ \t]*=[ \t]*\S{10,}", re.M),
    "заполненный password в настройках": re.compile(r"^[ \t]*password[ \t]*=[ \t]*\S+", re.M),
    "ключ GitHub": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    "закрытый ключ": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}
# Файлы, которые нельзя коммитить вообще
FORBIDDEN_NAMES = {"config.ini"}
FORBIDDEN_SUFFIXES = {".db", ".sqlite"}
# Правила «заполненный ... в настройках» относятся только к файлам настроек, не к коду
CODE_SUFFIXES = {".py", ".js", ".html", ".css"}
# Тесты специально содержат поддельный токен вида 123456789:AAFake...
ALLOWED = re.compile(r"AAFake")


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True)
    return [line for line in out.stdout.splitlines() if line]


def check(paths: list[str]) -> list[str]:
    problems = []
    for name in paths:
        path = Path(name)
        if path.name in FORBIDDEN_NAMES or path.suffix in FORBIDDEN_SUFFIXES:
            problems.append(f"{name}: этот файл нельзя класть в GitHub")
            continue
        if not path.is_file() or path.stat().st_size > 2_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in PATTERNS.items():
            if "в настройках" in label and path.suffix in CODE_SUFFIXES:
                continue
            for match in pattern.finditer(text):
                if not ALLOWED.search(match.group(0)):
                    line = text.count("\n", 0, match.start()) + 1
                    problems.append(f"{name}:{line}: похоже на {label}")
    return problems


def main() -> int:
    paths = sys.argv[1:] or tracked_files()
    problems = check(paths)
    for p in problems:
        print(p)
    if problems:
        print("\nНайдены возможные секреты — коммит остановлен.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
