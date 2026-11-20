"""Excel: шаблон, проверка присланного файла, применение после подтверждения."""

import io
import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from bot import excel, schedule
from bot.access import OwnerOnly
from bot.db import tx
from bot.handlers.common import show
from bot.ui import A, kb

log = logging.getLogger("admin")
router = Router(name="admin_excel")
router.message.filter(OwnerOnly())
router.callback_query.filter(OwnerOnly())


@router.callback_query(A.filter(F.act == "excel"))
async def excel_menu(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await show(cb, "Массовая загрузка из Excel:\n"
                   "1. Нажмите «Получить шаблон».\n"
                   "2. Заполните листы «Учителя», «Группы», «Ученики» (подсказки — на листе «Справка»).\n"
                   "3. Пришлите файл в этот чат.\n"
                   "4. Бот покажет итог и применит изменения только после вашего подтверждения.",
               kb([("📄 Получить шаблон", A(act="xl_template"))], [("⬅️ Меню", A(act="menu"))]))


@router.callback_query(A.filter(F.act == "xl_template"))
async def excel_template(cb: CallbackQuery, con) -> None:
    data = excel.build_template(con)
    await cb.message.answer_document(BufferedInputFile(data, filename="shablon_zagruzki.xlsx"),
                                     caption="Шаблон. Заполните и пришлите обратно в этот чат.")
    await cb.answer()


@router.message(F.document)
async def excel_file(message: Message, state: FSMContext, bot: Bot, con) -> None:
    doc = message.document
    if not (doc.file_name or "").lower().endswith(".xlsx"):
        return await message.answer("Нужен файл Excel (.xlsx). Шаблон: меню → 📥 Excel.")
    if (doc.file_size or 0) > excel.MAX_FILE_BYTES:
        return await message.answer("Файл слишком большой (больше 3 МБ).")
    buf = io.BytesIO()
    await bot.download(doc, destination=buf)
    try:
        plan = excel.parse(con, buf.getvalue())
    except Exception as e:  # повреждённый файл или не тот формат
        log.warning("Не удалось прочитать Excel: %s", type(e).__name__)
        return await message.answer("Не смог прочитать файл. Возьмите шаблон из меню (📥 Excel) и заполните его.")
    await state.clear()
    await state.update_data(import_plan=excel.plan_to_dict(plan))
    buttons = [[("✅ Применить", A(act="xl_apply"))]] if plan.has_changes else []
    await message.answer(excel.preview_text(plan), reply_markup=kb(*buttons, [("✖️ Отмена", A(act="xl_cancel"))]))


@router.callback_query(A.filter(F.act == "xl_cancel"))
async def excel_cancel(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await show(cb, "Загрузка отменена. Ничего не изменено.", kb([("⬅️ Меню", A(act="menu"))]))


@router.callback_query(A.filter(F.act == "xl_apply"))
async def excel_apply(cb: CallbackQuery, state: FSMContext, con) -> None:
    data = await state.get_data()
    if "import_plan" not in data:
        return await show(cb, "Нет файла для загрузки (возможно, бот перезапускался). Пришлите файл ещё раз.",
                          kb([("⬅️ Меню", A(act="menu"))]))
    await state.clear()
    plan = excel.plan_from_dict(data["import_plan"])
    try:
        with tx(con):
            counts = excel.apply(con, cb.from_user.id, plan, schedule.today())
    except Exception:
        log.exception("Ошибка при загрузке Excel")
        return await show(cb, "Не удалось загрузить — ничего не изменено. Пришлите файл ещё раз; "
                              "если повторится — сообщите разработчику.", kb([("⬅️ Меню", A(act="menu"))]))
    await show(cb, f"Готово. Добавлено или обновлено: учителей {counts['teachers']}, групп {counts['groups']}, "
                   f"учеников {counts['students']}.", kb([("👥 Группы", A(act="groups"))], [("⬅️ Меню", A(act="menu"))]))
