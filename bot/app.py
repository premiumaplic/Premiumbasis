"""Сборка бота: база, проверка доступа, обработчики."""

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.access import AccessMiddleware
from bot.handlers import admin, admin_excel, admin_more, common, fallback, stations, teacher


# Кнопки, которые продолжают пошаговый ввод (новая группа, учитель, ученик, загрузка Excel).
# Любая другая кнопка меню владельца — это переход на другой экран: незаконченный ввод сбрасывается,
# чтобы следующий текст не попал не туда.
WIZARD_ACTS = {"t_add_lang", "t_add_back", "g_add_subj", "g_add_teacher", "g_add_stage", "g_add_day", "g_add_ok",
               "g_add_back", "s_add_lang", "s_add_consent", "s_add_back", "xl_apply"}


# Кнопки под полем ввода, которые всегда означают «перейти», а не «ответ на вопрос бота»
NAV_TEXTS = {"☰ Меню владельца", "🔄 Обновить", "🔄 Yangilash", "🔁 Другая группа", "🔁 Boshqa guruh",
             "🛟 Все группы", "🛟 Barcha guruhlar"}


async def reset_input_on_keyboard(handler, event, data):
    if (event.text or "") in NAV_TEXTS and data.get("state") is not None:
        await data["state"].clear()
    return await handler(event, data)


async def reset_input_on_navigation(handler, event, data):
    parts = (event.data or "").split(":")
    if len(parts) > 1 and parts[0] == "a" and parts[1] not in WIZARD_ACTS and data.get("state") is not None:
        await data["state"].clear()
    return await handler(event, data)


def build_dispatcher(conf, con) -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage(), conf=conf)
    access = AccessMiddleware(conf, con)
    dp.message.outer_middleware(access)
    dp.callback_query.outer_middleware(access)
    dp.callback_query.outer_middleware(reset_input_on_navigation)
    dp.message.outer_middleware(reset_input_on_keyboard)
    routers = [common.router, admin.router, admin_excel.router, admin_more.router, stations.router,
               teacher.router, fallback.router]
    for router in routers:
        router._parent_router = None  # чтобы автотесты могли собирать бота много раз
    # Порядок важен: сначала общее, потом владелец, потом учитель, в конце — «не понял»
    dp.include_routers(*routers)
    return dp
