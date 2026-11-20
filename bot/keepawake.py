"""Пока бот работает, просим Windows не уходить в сон.

Это обычный системный вызов SetThreadExecutionState: настройки электропитания
не меняются, после закрытия окна бота всё возвращается как было.
"""

import sys

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001


def prevent_sleep() -> bool:
    if sys.platform != "win32":
        return False
    import ctypes
    result = ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
    return result != 0
