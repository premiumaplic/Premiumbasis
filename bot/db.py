"""База SQLite: подключение, миграции, локальная копия.

Схема меняется только файлами bot/migrations/NNNN_название.sql.
Номер последней применённой миграции хранится в PRAGMA user_version.
"""

import logging
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

log = logging.getLogger("db")

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"
MIGRATION_RE = re.compile(r"^(\d{4})_[\w-]+\.sql$")
KEEP_LOCAL_COPIES = 7


def connect(path: Path | str) -> sqlite3.Connection:
    con = sqlite3.connect(str(path), isolation_level=None, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA busy_timeout = 5000")
    if str(path) != ":memory:":
        con.execute("PRAGMA journal_mode = WAL")
    return con


@contextmanager
def tx(con: sqlite3.Connection):
    """Несколько изменений как одно: либо все сохраняются, либо ни одно."""
    con.execute("BEGIN IMMEDIATE")
    try:
        yield con
    except BaseException:
        con.execute("ROLLBACK")
        raise
    con.execute("COMMIT")


def migrations() -> list[tuple[int, Path]]:
    found = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        match = MIGRATION_RE.match(path.name)
        if match:
            found.append((int(match.group(1)), path))
    numbers = [n for n, _ in found]
    if numbers != list(range(1, len(numbers) + 1)):
        raise RuntimeError(f"нарушена нумерация миграций: {numbers}")
    return found


def schema_version(con: sqlite3.Connection) -> int:
    return con.execute("PRAGMA user_version").fetchone()[0]


def migrate(con: sqlite3.Connection) -> list[int]:
    """Применяет недостающие миграции. Каждая — целиком или никак."""
    applied = []
    current = schema_version(con)
    for number, path in migrations():
        if number <= current:
            continue
        script = path.read_text(encoding="utf-8")
        try:
            con.executescript(f"BEGIN;\n{script}\nPRAGMA user_version = {number};\nCOMMIT;")
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK")
            raise
        log.info("Применена миграция %s", path.name)
        applied.append(number)
    return applied


def local_copy(con: sqlite3.Connection, folder: Path, reason: str) -> Path:
    """Согласованная копия базы встроенным механизмом SQLite (можно при работающем боте)."""
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = folder / f"school-{stamp}-{reason}.db"
    dest = sqlite3.connect(str(target))
    try:
        con.backup(dest)
    finally:
        dest.close()
    copies = sorted(folder.glob(f"school-*-{reason}.db"))
    for old in copies[:-KEEP_LOCAL_COPIES]:
        old.unlink(missing_ok=True)
    return target
