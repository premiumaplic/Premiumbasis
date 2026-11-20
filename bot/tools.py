"""Служебные команды для update.bat:
    python -m bot.tools backup <пометка>   — локальная копия базы в data\\backups
    python -m bot.tools migrate            — применить миграции базы
"""

import sys

from bot import config as cfg
from bot import db


def main(argv: list[str]) -> int:
    path = cfg.data_dir() / "school.db"
    if not argv:
        print(__doc__)
        return 1
    if argv[0] == "backup":
        if not path.exists():
            print("Базы ещё нет — копировать нечего.")
            return 0
        con = db.connect(path)
        copy = db.local_copy(con, cfg.data_dir() / "backups", argv[1] if len(argv) > 1 else "manual")
        con.close()
        print(f"Копия базы: {copy}")
        return 0
    if argv[0] == "migrate":
        con = db.connect(path)
        applied = db.migrate(con)
        print(f"База: версия {db.schema_version(con)}" + (f" (применено: {applied})" if applied else ""))
        con.close()
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
