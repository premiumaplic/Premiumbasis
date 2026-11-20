"""Сборка бота: база, проверка доступа, обработчики."""

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.access import AccessMiddleware
from bot.handlers import admin, admin_excel, admin_more, common, fallback, teacher


def build_dispatcher(conf, con) -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage(), conf=conf)
    access = AccessMiddleware(conf, con)
    dp.message.outer_middleware(access)
    dp.callback_query.outer_middleware(access)
    routers = [common.router, admin.router, admin_excel.router, admin_more.router, teacher.router, fallback.router]
    for router in routers:
        router._parent_router = None  # чтобы автотесты могли собирать бота много раз
    # Порядок важен: сначала общее, потом владелец, потом учитель, в конце — «не понял»
    dp.include_routers(*routers)
    return dp
