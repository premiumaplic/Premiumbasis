"""Защита от двух копий бота: второе окно start.bat сразу закроется с понятным сообщением.

Бот держит блокировку файла data\\bot.lock, пока работает. update.bat по ней же
понимает, что бот ещё запущен. Блокировка снимается сама при закрытии окна.
"""

import os
import sys
from pathlib import Path

_handle = None


def acquire(path: Path) -> bool:
    global _handle
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(path, "a+b")
    try:
        if sys.platform == "win32":
            import msvcrt
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return False
    handle.seek(0)
    handle.truncate()
    handle.write(str(os.getpid()).encode("ascii"))
    handle.flush()
    _handle = handle
    return True
