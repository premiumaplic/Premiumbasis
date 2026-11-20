"""Меню владельца: учителя, группы, ученики, настройки, баллы экзаменов.

Всё на кнопках. Где нужно ввести текст, бот спрашивает и ждёт ответа;
/cancel или «Отмена» прерывает ввод. Каждое изменение пишется в журнал (audit_log).
"""

import logging
from datetime import date

from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot import repo, schedule
from bot.access import OwnerOnly
from bot.db import tx
from bot.handlers.common import show
from bot.ui import LANG_NAMES, A, column, kb, yes_no

log = logging.getLogger("admin")
router = Router(name="admin")
router.message.filter(OwnerOnly())
router.callback_query.filter(OwnerOnly())

CANCEL = [("✖️ Отмена", A(act="cancel"))]


def nav(back=None) -> list:
    """Строка кнопок: «⬅️ Назад» (на предыдущий шаг или экран) и «✖️ Отмена» (в главное меню)."""
    row = [("⬅️ Назад", back)] if back is not None else []
    return row + CANCEL
MAX_NAME = 60


class AddTeacher(StatesGroup):
    tg_id = State()
    name = State()


class AddGroup(StatesGroup):
    name = State()      # шаг 1: название (текст)
    pick = State()      # шаги 2–4: предмет, учитель, этап (кнопки)
    start = State()     # шаг 5: дата старта (текст)
    days = State()      # шаг 6: дни (кнопки)
    time = State()      # шаг 7: время (текст)
    confirm = State()   # проверка и «Создать»


class EditGroup(StatesGroup):
    value = State()


class AddStudent(StatesGroup):
    name = State()


class RenameStudent(StatesGroup):
    name = State()


class FindStudent(StatesGroup):
    query = State()


class EditSetting(StatesGroup):
    value = State()


class StageScores(StatesGroup):
    value = State()


# ================================================================ главное меню

def menu_markup(teacher) -> object:
    return kb(
        [("👩‍🏫 Учителя", A(act="teachers")), ("👥 Группы", A(act="groups"))],
        [("🎓 Ученики", A(act="students")), ("📥 Excel", A(act="excel"))],
        [("⚙️ Настройки", A(act="settings")), ("🎯 Баллы экзаменов", A(act="scores"))],
        [("📚 Тексты", A(act="texts")), ("📊 Сводка", A(act="summary"))],
        [("💾 Бэкап сейчас", A(act="backup"))],
        [("📚 Мои группы (как учитель)", "t:groups:0")] if teacher else [],
    )


@router.message(CommandStart())
@router.message(Command("admin"))
async def start(message: Message, state: FSMContext, teacher=None) -> None:
    await state.clear()
    await message.answer("Меню владельца. Что настроить?", reply_markup=menu_markup(teacher))


@router.message(Command("cancel"))
async def cancel_cmd(message: Message, state: FSMContext, teacher=None) -> None:
    await state.clear()
    await message.answer("Отменено.", reply_markup=menu_markup(teacher))


@router.callback_query(A.filter(F.act.in_({"menu", "cancel"})))
async def menu(cb: CallbackQuery, state: FSMContext, teacher=None) -> None:
    await state.clear()
    await show(cb, "Меню владельца. Что настроить?", menu_markup(teacher))


# ================================================================ учителя

def teacher_text(con, row) -> str:
    groups = repo.list_groups(con, teacher_id=row["id"])
    return (f"👩‍🏫 {row['name']}\n"
            f"Telegram ID: {row['tg_id']}\n"
            f"Язык интерфейса: {LANG_NAMES[row['lang']]}\n"
            f"Статус: {'активен' if row['active'] else 'отключён'}\n"
            f"Группы: {', '.join(g['name'] for g in groups) or 'нет'}")


def teacher_markup(row) -> object:
    other = "uz" if row["lang"] == "ru" else "ru"
    return kb(
        [(f"🌐 Язык → {LANG_NAMES[other]}", A(act="t_lang", id=row["id"]))],
        [("⛔ Отключить" if row["active"] else "✅ Включить", A(act="t_toggle", id=row["id"]))],
        [("⬅️ Учителя", A(act="teachers"))],
    )


@router.callback_query(A.filter(F.act == "teachers"))
async def teachers(cb: CallbackQuery, con) -> None:
    rows = repo.list_teachers(con)
    buttons = [(f"{'✅' if r['active'] else '⛔'} {r['name']}", A(act="teacher", id=r["id"])) for r in rows]
    await show(cb, f"Учителя ({len(rows)}). Нажмите на учителя, чтобы изменить.",
               kb(*column(buttons, 2), [("➕ Добавить учителя", A(act="t_add"))], [("⬅️ Меню", A(act="menu"))]))


@router.callback_query(A.filter(F.act == "teacher"))
async def teacher_card(cb: CallbackQuery, callback_data: A, con) -> None:
    row = repo.teacher(con, callback_data.id)
    await show(cb, teacher_text(con, row), teacher_markup(row))


@router.callback_query(A.filter(F.act == "t_lang"))
async def teacher_lang(cb: CallbackQuery, callback_data: A, con) -> None:
    row = repo.teacher(con, callback_data.id)
    repo.set_teacher_lang(con, cb.from_user.id, row["id"], "uz" if row["lang"] == "ru" else "ru")
    row = repo.teacher(con, row["id"])
    await show(cb, teacher_text(con, row), teacher_markup(row))


@router.callback_query(A.filter(F.act == "t_toggle"))
async def teacher_toggle(cb: CallbackQuery, callback_data: A, con) -> None:
    row = repo.teacher(con, callback_data.id)
    repo.set_teacher_active(con, cb.from_user.id, row["id"], not row["active"])
    row = repo.teacher(con, row["id"])
    note = ("\n\n⚠️ Учитель отключён и больше не видит свои группы. "
            "Назначьте группам другого учителя.") if not row["active"] else ""
    await show(cb, teacher_text(con, row) + note, teacher_markup(row))


async def teacher_step(target, state: FSMContext, step: int) -> None:
    """Шаги добавления учителя: 1 — Telegram ID, 2 — имя, 3 — язык."""
    if step == 1:
        await state.set_state(AddTeacher.tg_id)
        return await show(target, "Новый учитель. Шаг 1 из 3: пришлите его Telegram ID (только цифры).\n"
                                  "Учитель узнаёт его так: пишет этому боту /myid.", kb(nav(A(act="teachers"))))
    if step == 2:
        await state.set_state(AddTeacher.name)
        return await show(target, "Шаг 2 из 3: как зовут учителя? (так он будет виден в списках)",
                          kb(nav(A(act="t_add_back", arg=1))))
    await state.set_state(AddTeacher.name)
    await show(target, "Шаг 3 из 3: язык интерфейса для учителя:", kb(
        [("Русский", A(act="t_add_lang", arg=0)), ("Oʻzbekcha", A(act="t_add_lang", arg=1))],
        nav(A(act="t_add_back", arg=2))))


@router.callback_query(A.filter(F.act == "t_add"))
async def teacher_add(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await teacher_step(cb, state, 1)


@router.callback_query(A.filter(F.act == "t_add_back"), StateFilter(AddTeacher))
async def teacher_add_back(cb: CallbackQuery, callback_data: A, state: FSMContext) -> None:
    await teacher_step(cb, state, callback_data.arg)


@router.message(AddTeacher.tg_id)
async def teacher_add_id(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text.isdigit() or not 5 <= len(text) <= 15:
        return await message.answer("Нужны только цифры, например 123456789. Попробуйте ещё раз.",
                                    reply_markup=kb(nav(A(act="teachers"))))
    await state.update_data(tg_id=int(text))
    await teacher_step(message, state, 2)


@router.message(AddTeacher.name)
async def teacher_add_name(message: Message, state: FSMContext) -> None:
    name = " ".join((message.text or "").split())
    if not name or len(name) > MAX_NAME:
        return await message.answer(f"Напишите имя (до {MAX_NAME} букв).", reply_markup=kb(nav(A(act="t_add_back", arg=1))))
    await state.update_data(name=name)
    await teacher_step(message, state, 3)


@router.callback_query(A.filter(F.act == "t_add_lang"), StateFilter(AddTeacher.name))
async def teacher_add_lang(cb: CallbackQuery, callback_data: A, state: FSMContext, con) -> None:
    data = await state.get_data()
    if "name" not in data:
        return await teacher_step(cb, state, 2)
    await state.clear()
    lang = "uz" if callback_data.arg else "ru"
    with tx(con):
        teacher_id, created = repo.save_teacher(con, cb.from_user.id, data["tg_id"], data["name"], lang)
    row = repo.teacher(con, teacher_id)
    head = "Учитель добавлен." if created else "Учитель с таким ID уже был — данные обновлены."
    await show(cb, f"{head} Теперь он может нажать /start в боте.\n\n" + teacher_text(con, row),
               teacher_markup(row))


# ================================================================ группы

def group_text(con, g) -> str:
    lines = [f"👥 {schedule.group_header(g, 'ru')}", "",
             f"Предмет: {g['subject_ru']}",
             f"Учитель: {g['teacher_name'] or 'не назначен'}"]
    if g["has_map"]:
        lines.append(f"Этап: {g['stage_ru'] or 'не указан'}")
    lines += [f"Дата старта: {date.fromisoformat(g['start_date']).strftime('%d.%m.%Y')}"
              + (f"   Начало станции: {schedule.anchor(g).strftime('%d.%m.%Y')}"
                 if g["stage_start"] and g["stage_start"] != g["start_date"] else ""),
              f"Дни: {schedule.weekdays_text(g['weekdays']) or '—'}   Время: {g['lesson_time'] or '—'}",
              f"Учеников: {g['student_count']}"]
    if not g["active"]:
        lines.append("📦 В архиве")
    return "\n".join(lines)


def group_markup(g) -> object:
    gid = g["id"]
    if not g["active"]:
        return kb([("⬅️ Группы", A(act="groups"))])
    return kb(
        [(f"🎓 Ученики ({g['student_count']})", A(act="g_students", id=gid)),
         ("➕ Ученик", A(act="s_add", id=gid))],
        [("👩‍🏫 Сменить учителя", A(act="g_teacher", id=gid))]
        + ([("🗺 Этап группы", A(act="g_stage", id=gid))] if g["has_map"] else []),
        [("✏️ Название / даты / дни / время", A(act="g_edit", id=gid))],
        [("📦 В архив", A(act="g_archive", id=gid)), ("⬅️ Группы", A(act="groups"))],
    )


@router.callback_query(A.filter(F.act == "groups"))
async def groups(cb: CallbackQuery, callback_data: A, con) -> None:
    archived = callback_data.arg == 1
    rows = repo.list_groups(con, active=not archived)
    buttons = [(f"{g['name']} · {g['subject_ru']} · {g['teacher_name'] or '—'}", A(act="group", id=g["id"]))
               for g in rows[:90]]
    title = f"Группы в архиве ({len(rows)})" if archived else f"Группы ({len(rows)})"
    bottom = [("👥 Активные", A(act="groups"))] if archived else \
        [("➕ Создать группу", A(act="g_add")), ("📦 Архив", A(act="groups", arg=1))]
    await show(cb, title, kb(*column(buttons), bottom, [("⬅️ Меню", A(act="menu"))]))


@router.callback_query(A.filter(F.act == "group"))
async def group_card(cb: CallbackQuery, callback_data: A, con) -> None:
    g = repo.group(con, callback_data.id)
    await show(cb, group_text(con, g), group_markup(g))


@router.callback_query(A.filter(F.act == "g_teacher"))
async def group_teacher(cb: CallbackQuery, callback_data: A, con) -> None:
    buttons = [(t["name"], A(act="g_set_teacher", id=callback_data.id, arg=t["id"]))
               for t in repo.list_teachers(con, only_active=True)]
    await show(cb, "Кто будет вести группу? (замена на время болезни — тоже здесь)",
               kb(*column(buttons, 2), [("⬅️ Назад", A(act="group", id=callback_data.id))]))


@router.callback_query(A.filter(F.act == "g_set_teacher"))
async def group_set_teacher(cb: CallbackQuery, callback_data: A, con) -> None:
    repo.set_group_teacher(con, cb.from_user.id, callback_data.id, callback_data.arg)
    g = repo.group(con, callback_data.id)
    await show(cb, "Учитель назначен.\n\n" + group_text(con, g), group_markup(g))


@router.callback_query(A.filter(F.act == "g_stage"))
async def group_stage(cb: CallbackQuery, callback_data: A, con) -> None:
    g = repo.group(con, callback_data.id)
    buttons = [(s["name_ru"], A(act="g_set_stage", id=g["id"], arg=s["id"]))
               for s in repo.list_stages(con, g["subject"])]
    await show(cb, "На какую станцию перевести группу? Ученики, которые сейчас на станции группы, перейдут "
                   "вместе с ней (пропущенные станции не появятся на их карте). Экзамены новой станции — "
                   "каждые 2 месяца с сегодняшнего дня; дату можно поправить: «✏️ … → Начало текущей станции».",
               kb(*column(buttons, 3), [("⬅️ Назад", A(act="group", id=g["id"]))]))


@router.callback_query(A.filter(F.act == "g_set_stage"))
async def group_set_stage(cb: CallbackQuery, callback_data: A, con) -> None:
    with tx(con):
        moved = repo.move_group_station(con, cb.from_user.id, callback_data.id, callback_data.arg, schedule.today())
    g = repo.group(con, callback_data.id)
    await show(cb, f"Группа переведена, учеников вместе с ней: {len(moved)}.\n\n" + group_text(con, g), group_markup(g))


@router.callback_query(A.filter(F.act == "g_archive"))
async def group_archive(cb: CallbackQuery, callback_data: A, con) -> None:
    g = repo.group(con, callback_data.id)
    if callback_data.arg != 1:
        return await show(cb, f"Отправить группу {g['name']} в архив? Ученики останутся в базе, "
                              "история сохранится, но в группе их больше не будет.",
                          kb([("📦 Да, в архив", A(act="g_archive", id=g["id"], arg=1)),
                              ("⬅️ Нет", A(act="group", id=g["id"]))]))
    with tx(con):
        repo.archive_group(con, cb.from_user.id, g["id"], schedule.today())
    await show(cb, f"Группа {g['name']} в архиве.", kb([("⬅️ Группы", A(act="groups"))]))


# ---- изменение полей группы

GROUP_FIELDS = {1: ("name", "новое название группы"),
                2: ("start_date", "дату старта, например 01.09.2026"),
                3: ("weekdays", "дни занятий, например: Пн, Ср, Пт"),
                4: ("lesson_time", "время урока, например 15:00"),
                5: ("stage_start", "дату начала текущей станции, например 20.11.2026 "
                                   "(от неё считаются «неделя X из 8» и экзамены)")}


@router.callback_query(A.filter(F.act == "g_edit"))
async def group_edit(cb: CallbackQuery, callback_data: A, state: FSMContext) -> None:
    gid = callback_data.id
    if not callback_data.arg:
        return await show(cb, "Что изменить?", kb(
            [("Название", A(act="g_edit", id=gid, arg=1)), ("Дату старта", A(act="g_edit", id=gid, arg=2))],
            [("Дни", A(act="g_edit", id=gid, arg=3)), ("Время", A(act="g_edit", id=gid, arg=4))],
            [("Начало текущей станции", A(act="g_edit", id=gid, arg=5))],
            [("⬅️ Назад", A(act="group", id=gid))]))
    await state.set_state(EditGroup.value)
    await state.update_data(group_id=gid, field=callback_data.arg)
    await show(cb, f"Пришлите {GROUP_FIELDS[callback_data.arg][1]}.", kb(nav(A(act="g_edit", id=gid))))


def check_group_value(con, field: str, text: str, group_id: int | None = None) -> tuple[str | None, str]:
    """Проверка значения поля группы. Возвращает (значение для базы, ошибка)."""
    text = " ".join(text.split())
    if field == "name":
        if not text or len(text) > 30:
            return None, "Название — от 1 до 30 знаков."
        other = repo.group_by_name(con, text)
        if other and other["id"] != group_id:
            return None, "Группа с таким названием уже есть."
        return text, ""
    if field in ("start_date", "stage_start"):
        d = schedule.parse_date(text)
        return (d.isoformat(), "") if d else (None, "Не понял дату. Пример: 01.09.2026")
    if field == "weekdays":
        w = schedule.parse_weekdays(text)
        return (w, "") if w else (None, "Не понял дни. Пример: Пн, Ср, Пт")
    if field == "lesson_time":
        t = schedule.parse_time(text)
        return (t, "") if t else (None, "Не понял время. Пример: 15:00")
    raise ValueError(field)


@router.message(EditGroup.value)
async def group_edit_value(message: Message, state: FSMContext, con) -> None:
    data = await state.get_data()
    field = GROUP_FIELDS[data["field"]][0]
    value, error = check_group_value(con, field, message.text or "", data["group_id"])
    if error:
        return await message.answer(error, reply_markup=kb(nav(A(act="g_edit", id=data["group_id"]))))
    await state.clear()
    repo.set_group_field(con, message.from_user.id, data["group_id"], field, value)
    g = repo.group(con, data["group_id"])
    await message.answer("Сохранено.\n\n" + group_text(con, g), reply_markup=group_markup(g))


# ---- создание группы: название → предмет → учитель → этап → дата → дни → время → проверка

def weekday_markup(selected: set[int]) -> object:
    names = schedule.WEEKDAYS_SHORT["ru"]
    row = [((("✅ " if i + 1 in selected else "") + n), A(act="g_add_day", arg=i + 1)) for i, n in enumerate(names)]
    return kb(row[:4], row[4:], [("Готово ➡️", A(act="g_add_day", arg=0))], nav(A(act="g_add_back", arg=5)))


async def group_step(target, state: FSMContext, con, step: int) -> None:
    """Показывает шаг создания группы. «Назад» на каждом шаге ведёт на предыдущий."""
    d = await state.get_data()
    back = lambda n: nav(A(act="g_add_back", arg=n))  # noqa: E731
    if step == 1:
        await state.set_state(AddGroup.name)
        return await show(target, "Новая группа. Шаг 1 из 7: название (например 10-А)."
                          + (f"\nСейчас: {d['name']}" if d.get("name") else ""), kb(nav(A(act="groups"))))
    if step == 2:
        await state.set_state(AddGroup.pick)
        buttons = [(s["name_ru"], A(act="g_add_subj", arg=i)) for i, s in enumerate(repo.list_subjects(con))]
        return await show(target, "Шаг 2 из 7: предмет.", kb(*column(buttons, 2), back(1)))
    if step == 3:
        await state.set_state(AddGroup.pick)
        buttons = [(t["name"], A(act="g_add_teacher", arg=t["id"])) for t in repo.list_teachers(con, only_active=True)]
        return await show(target, "Шаг 3 из 7: учитель.",
                          kb(*column(buttons, 2), [("Пока без учителя", A(act="g_add_teacher", arg=0))], back(2)))
    if step == 4:
        if not d.get("has_map"):
            await state.update_data(stage_id=None)
            return await group_step(target, state, con, 5)
        await state.set_state(AddGroup.pick)
        buttons = [(s["name_ru"], A(act="g_add_stage", arg=s["id"])) for s in repo.list_stages(con, d["subject"])]
        return await show(target, "Шаг 4 из 7: этап (станция карты), с которого группа начинает.",
                          kb(*column(buttons, 3), back(3)))
    if step == 5:
        await state.set_state(AddGroup.start)
        note = "" if d.get("has_map") else "У этого предмета нет карты этапов — шаг 4 пропущен.\n"
        return await show(target, note + "Шаг 5 из 7: дата старта группы, например 01.09.2026\n"
                                         "От неё считаются недели и экзамены (каждые 2 месяца).",
                          kb(back(4 if d.get("has_map") else 3)))
    if step == 6:
        await state.set_state(AddGroup.days)
        return await show(target, "Шаг 6 из 7: дни занятий — нажмите нужные и «Готово».",
                          weekday_markup(set(d.get("days", []))))
    if step == 7:
        await state.set_state(AddGroup.time)
        return await show(target, "Шаг 7 из 7: время урока, например 15:00", kb(back(6)))
    await state.set_state(AddGroup.confirm)
    teacher = repo.teacher(con, d["teacher_id"]) if d.get("teacher_id") else None
    stage = repo.stage(con, d.get("stage_id"))
    text = (f"Проверьте:\nГруппа: {d['name']}\nПредмет: {repo.subject(con, d['subject'])['name_ru']}\n"
            f"Учитель: {teacher['name'] if teacher else 'не назначен'}\n"
            + (f"Этап: {stage['name_ru']}\n" if stage else "")
            + f"Старт: {date.fromisoformat(d['start_date']).strftime('%d.%m.%Y')}\n"
              f"Дни: {schedule.weekdays_text(','.join(map(str, d['days'])))}   Время: {d['lesson_time']}")
    await show(target, text, kb([("✅ Создать", A(act="g_add_ok"))], back(7)))


@router.callback_query(A.filter(F.act == "g_add"))
async def group_add(cb: CallbackQuery, state: FSMContext, con) -> None:
    await state.clear()
    await group_step(cb, state, con, 1)


@router.callback_query(A.filter(F.act == "g_add_back"), StateFilter(AddGroup))
async def group_add_back(cb: CallbackQuery, callback_data: A, state: FSMContext, con) -> None:
    await group_step(cb, state, con, callback_data.arg)


@router.message(AddGroup.name)
async def group_add_name(message: Message, state: FSMContext, con) -> None:
    value, error = check_group_value(con, "name", message.text or "")
    if error:
        return await message.answer(error, reply_markup=kb(nav(A(act="groups"))))
    await state.update_data(name=value)
    await group_step(message, state, con, 2)


@router.callback_query(A.filter(F.act == "g_add_subj"), StateFilter(AddGroup.pick))
async def group_add_subject(cb: CallbackQuery, callback_data: A, state: FSMContext, con) -> None:
    subj = repo.list_subjects(con)[callback_data.arg]
    await state.update_data(subject=subj["code"], has_map=subj["has_map"])
    await group_step(cb, state, con, 3)


@router.callback_query(A.filter(F.act == "g_add_teacher"), StateFilter(AddGroup.pick))
async def group_add_teacher(cb: CallbackQuery, callback_data: A, state: FSMContext, con) -> None:
    await state.update_data(teacher_id=callback_data.arg or None)
    await group_step(cb, state, con, 4)


@router.callback_query(A.filter(F.act == "g_add_stage"), StateFilter(AddGroup.pick))
async def group_add_stage(cb: CallbackQuery, callback_data: A, state: FSMContext, con) -> None:
    await state.update_data(stage_id=callback_data.arg)
    await group_step(cb, state, con, 5)


@router.message(AddGroup.start)
async def group_add_start(message: Message, state: FSMContext, con) -> None:
    d = schedule.parse_date(message.text or "")
    if not d:
        return await message.answer("Не понял дату. Пример: 01.09.2026", reply_markup=kb(nav(A(act="g_add_back", arg=4))))
    await state.update_data(start_date=d.isoformat())
    await group_step(message, state, con, 6)


@router.callback_query(A.filter(F.act == "g_add_day"), StateFilter(AddGroup.days))
async def group_add_day(cb: CallbackQuery, callback_data: A, state: FSMContext, con) -> None:
    days = set((await state.get_data()).get("days", []))
    if callback_data.arg:
        days ^= {callback_data.arg}
        await state.update_data(days=sorted(days))
        return await group_step(cb, state, con, 6)
    if not days:
        return await cb.answer("Выберите хотя бы один день", show_alert=True)
    await group_step(cb, state, con, 7)


@router.message(AddGroup.time)
async def group_add_time(message: Message, state: FSMContext, con) -> None:
    t = schedule.parse_time(message.text or "")
    if not t:
        return await message.answer("Не понял время. Пример: 15:00", reply_markup=kb(nav(A(act="g_add_back", arg=6))))
    await state.update_data(lesson_time=t)
    await group_step(message, state, con, 8)


@router.callback_query(A.filter(F.act == "g_add_ok"), StateFilter(AddGroup.confirm))
async def group_add_ok(cb: CallbackQuery, state: FSMContext, con) -> None:
    d = await state.get_data()
    await state.clear()
    with tx(con):
        gid = repo.create_group(con, cb.from_user.id, d["name"], d["subject"], d["teacher_id"], d["stage_id"],
                                date.fromisoformat(d["start_date"]), ",".join(map(str, d["days"])),
                                d["lesson_time"])
    g = repo.group(con, gid)
    await show(cb, "Группа создана.\n\n" + group_text(con, g), group_markup(g))


# ================================================================ ученики

def student_text(con, s) -> str:
    lines = [f"🎓 {s['full_name']}"]
    groups = repo.student_groups(con, s["id"])
    lines.append("Группы: " + (", ".join(f"{g['name']} ({g['subject_ru']})" for g in groups) or "нет"))
    for code in sorted({g["subject"] for g in groups if g["has_map"]}):
        cur = repo.current_stage(con, s["id"], code)
        lines.append(f"Станция карты: {cur['name_ru'] if cur else 'не указана'}"
                     + (f" (путь: {cur['path'].upper()})" if cur and cur["path"] else ""))
    lines.append(f"Язык карточки: {LANG_NAMES[s['card_lang']]}")
    lines.append(f"Согласие родителя: {yes_no(s['consent'])}"
                 + ("" if s["consent"] else " — карточки для него не создаются"))
    if not s["active"]:
        lines.append("📦 В архиве")
    return "\n".join(lines)


def student_markup(con, s, back_group: int = 0) -> object:
    sid = s["id"]
    back = A(act="g_students", id=back_group) if back_group else A(act="students")
    if not s["active"]:
        return kb([("⬅️ Назад", back)])
    has_map = any(g["has_map"] for g in repo.student_groups(con, sid))
    other = "uz" if s["card_lang"] == "ru" else "ru"
    return kb(
        [("🔀 Перевести в группу", A(act="s_move", id=sid, arg=back_group))]
        + ([("🗺 Станция", A(act="s_stage", id=sid, arg=back_group))] if has_map else []),
        [(f"🌐 Карточка → {LANG_NAMES[other]}", A(act="s_lang", id=sid, arg=back_group)),
         ("📝 Согласие: " + ("снять" if s["consent"] else "есть"), A(act="s_consent", id=sid, arg=back_group))],
        [("✏️ Имя", A(act="s_rename", id=sid, arg=back_group)),
         ("📦 В архив", A(act="s_archive", id=sid, arg=back_group))],
        [("⬅️ Назад", back)],
    )


@router.callback_query(A.filter(F.act == "students"))
async def students_menu(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await show(cb, "Ученики. Найдите ученика по имени или откройте группу (Группы → группа → Ученики).",
               kb([("🔎 Найти ученика", A(act="s_find"))], [("➕ Добавить ученика", A(act="s_add"))],
                  [("⬅️ Меню", A(act="menu"))]))


@router.callback_query(A.filter(F.act == "s_find"))
async def student_find(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(FindStudent.query)
    await show(cb, "Напишите часть имени или фамилии.", kb(nav(A(act="students"))))


@router.message(FindStudent.query)
async def student_find_query(message: Message, state: FSMContext, con) -> None:
    found = repo.find_students(con, message.text or "")
    if not found:
        return await message.answer("Никого не нашёл. Попробуйте иначе.", reply_markup=kb(nav(A(act="students"))))
    await state.clear()
    buttons = [(s["full_name"], A(act="student", id=s["id"])) for s in found]
    await message.answer(f"Найдено: {len(found)}", reply_markup=kb(*column(buttons), [("⬅️ Меню", A(act="menu"))]))


@router.callback_query(A.filter(F.act == "g_students"))
async def group_students(cb: CallbackQuery, callback_data: A, con) -> None:
    g = repo.group(con, callback_data.id)
    rows = repo.group_students(con, g["id"])
    buttons = [(f"{s['full_name']}{'' if s['consent'] else ' ⚪'}", A(act="student", id=s["id"], arg=g["id"]))
               for s in rows]
    await show(cb, f"Группа {g['name']}: {len(rows)} учеников.\n⚪ — нет отметки о согласии родителя.",
               kb(*column(buttons), [("➕ Добавить ученика", A(act="s_add", id=g["id"]))],
                  [("⬅️ Группа", A(act="group", id=g["id"]))]))


@router.callback_query(A.filter(F.act == "student"))
async def student_card(cb: CallbackQuery, callback_data: A, con) -> None:
    s = repo.student(con, callback_data.id)
    await show(cb, student_text(con, s), student_markup(con, s, callback_data.arg))


async def refresh_student(cb: CallbackQuery, con, sid: int, back: int, note: str = "") -> None:
    s = repo.student(con, sid)
    await show(cb, (note + "\n\n" if note else "") + student_text(con, s), student_markup(con, s, back))


@router.callback_query(A.filter(F.act == "s_lang"))
async def student_lang(cb: CallbackQuery, callback_data: A, con) -> None:
    s = repo.student(con, callback_data.id)
    repo.set_student_field(con, cb.from_user.id, s["id"], "card_lang", "uz" if s["card_lang"] == "ru" else "ru")
    await refresh_student(cb, con, s["id"], callback_data.arg)


@router.callback_query(A.filter(F.act == "s_consent"))
async def student_consent(cb: CallbackQuery, callback_data: A, con) -> None:
    s = repo.student(con, callback_data.id)
    repo.set_student_field(con, cb.from_user.id, s["id"], "consent", 0 if s["consent"] else 1)
    await refresh_student(cb, con, s["id"], callback_data.arg)


@router.callback_query(A.filter(F.act == "s_archive"))
async def student_archive(cb: CallbackQuery, callback_data: A, con) -> None:
    s = repo.student(con, callback_data.id)
    await show(cb, f"Отправить {s['full_name']} в архив? Ученик уйдёт из всех групп, история сохранится.",
               kb([("📦 Да, в архив", A(act="s_archive_ok", id=s["id"], arg=callback_data.arg)),
                   ("⬅️ Нет", A(act="student", id=s["id"], arg=callback_data.arg))]))


@router.callback_query(A.filter(F.act == "s_archive_ok"))
async def student_archive_ok(cb: CallbackQuery, callback_data: A, con) -> None:
    with tx(con):
        repo.archive_student(con, cb.from_user.id, callback_data.id, schedule.today())
    await refresh_student(cb, con, callback_data.id, callback_data.arg, "Ученик в архиве.")


@router.callback_query(A.filter(F.act == "s_rename"))
async def student_rename(cb: CallbackQuery, callback_data: A, state: FSMContext) -> None:
    await state.set_state(RenameStudent.name)
    await state.update_data(student_id=callback_data.id, back=callback_data.arg)
    await show(cb, "Напишите имя и фамилию ученика (в таком порядке: Имя Фамилия).",
               kb(nav(A(act="student", id=callback_data.id, arg=callback_data.arg))))


def check_student_name(text: str) -> tuple[str | None, str]:
    name = " ".join(text.split())
    if len(name.split()) < 2 or len(name) > MAX_NAME:
        return None, f"Нужны имя и фамилия через пробел (до {MAX_NAME} букв), например: Азиз Каримов"
    return name, ""


@router.message(RenameStudent.name)
async def student_rename_value(message: Message, state: FSMContext, con) -> None:
    data = await state.get_data()
    name, error = check_student_name(message.text or "")
    if error:
        return await message.answer(error, reply_markup=kb(nav(A(act="student", id=data["student_id"],
                                                                  arg=data["back"]))))
    await state.clear()
    repo.set_student_field(con, message.from_user.id, data["student_id"], "full_name", name)
    s = repo.student(con, data["student_id"])
    await message.answer("Сохранено.\n\n" + student_text(con, s),
                         reply_markup=student_markup(con, s, data["back"]))


# ---- перевод в другую группу

@router.callback_query(A.filter(F.act == "s_move"))
async def student_move(cb: CallbackQuery, callback_data: A, con) -> None:
    sid = callback_data.id
    current = repo.student_groups(con, sid)
    if len(current) > 1 and callback_data.arg not in [g["id"] for g in current]:
        buttons = [(g["name"], A(act="s_move", id=sid, arg=g["id"])) for g in current]
        return await show(cb, "Из какой группы перевести?", kb(*column(buttons, 2), nav(A(act="student", id=sid))))
    from_group = callback_data.arg if len(current) > 1 else (current[0]["id"] if current else 0)
    buttons = [(f"{g['name']} · {g['subject_ru']}", A(act="s_move_to", id=sid, arg=g["id"]))
               for g in repo.list_groups(con) if g["id"] != from_group]
    await show(cb, "В какую группу перевести? История прежней группы сохранится.",
               kb(*column(buttons, 2), [("⬅️ Назад", A(act="student", id=sid))]))


@router.callback_query(A.filter(F.act == "s_move_to"))
async def student_move_to(cb: CallbackQuery, callback_data: A, con) -> None:
    sid, to_group = callback_data.id, callback_data.arg
    current = [g for g in repo.student_groups(con, sid)]
    target = repo.group(con, to_group)
    same_subject = [g for g in current if g["subject"] == target["subject"]]
    from_group = (same_subject or current or [None])[0]
    with tx(con):
        if from_group:
            repo.transfer_student(con, cb.from_user.id, sid, from_group["id"], to_group, schedule.today())
        else:
            repo.enroll(con, cb.from_user.id, sid, to_group, schedule.today())
            repo.place_on_map_if_needed(con, cb.from_user.id, sid, to_group, schedule.today())
    note = f"Переведён в группу {target['name']}."
    if target["has_map"] and target["stage_id"]:
        cur = repo.current_stage(con, sid, target["subject"])
        if cur and cur["stage_id"] != target["stage_id"]:
            s = repo.student(con, sid)
            return await show(cb, note + f"\nСтанция ученика ({cur['name_ru']}) отличается от этапа группы "
                                         f"({target['stage_ru']}). Поставить станцию группы?\n\n"
                                         + student_text(con, s),
                              kb([("✅ Да", A(act="s_set_stage", id=sid, arg=target["stage_id"])),
                                  ("Нет, оставить", A(act="student", id=sid))]))
    await refresh_student(cb, con, sid, 0, note)


# ---- станция карты

@router.callback_query(A.filter(F.act == "s_stage"))
async def student_stage(cb: CallbackQuery, callback_data: A, con) -> None:
    sid = callback_data.id
    subjects = sorted({g["subject"] for g in repo.student_groups(con, sid) if g["has_map"]})
    buttons = [(s["name_ru"], A(act="s_set_stage", id=sid, arg=s["id"]))
               for code in subjects for s in repo.list_stages(con, code)]
    await show(cb, "На какую станцию карты поставить ученика? (если он уже знает язык — можно на любую)",
               kb(*column(buttons, 3), [("⬅️ Назад", A(act="student", id=sid))]))


@router.callback_query(A.filter(F.act == "s_set_stage"))
async def student_set_stage(cb: CallbackQuery, callback_data: A, con) -> None:
    with tx(con):
        repo.set_student_stage(con, cb.from_user.id, callback_data.id, callback_data.arg, schedule.today())
    await refresh_student(cb, con, callback_data.id, 0, "Станция изменена.")


# ---- добавление ученика: группа → имя → язык карточки → согласие

async def student_step(target, state: FSMContext, con, step: int) -> None:
    d = await state.get_data()
    gid = d["group_id"]
    if step == 1:
        await state.set_state(AddStudent.name)
        g = repo.group(con, gid)
        return await show(target, f"Группа {g['name']}. Шаг 1 из 3: имя и фамилия ученика (в таком порядке), "
                                  "например: Азиз Каримов", kb(nav(A(act="group", id=gid))))
    if step == 2:
        return await show(target, f"{d['name']}. Шаг 2 из 3: язык карточки для родителя:", kb(
            [("Русский", A(act="s_add_lang", arg=0)), ("Oʻzbekcha", A(act="s_add_lang", arg=1))],
            nav(A(act="s_add_back", arg=1))))
    await show(target, f"{d['name']}. Шаг 3 из 3: есть письменное согласие родителя на карточки-отчёты?", kb(
        [("✅ Да, есть", A(act="s_add_consent", arg=1)), ("Пока нет", A(act="s_add_consent", arg=0))],
        nav(A(act="s_add_back", arg=2))))


@router.callback_query(A.filter(F.act == "s_add"))
async def student_add(cb: CallbackQuery, callback_data: A, state: FSMContext, con) -> None:
    await state.clear()
    if not callback_data.id:
        buttons = [(f"{g['name']} · {g['subject_ru']}", A(act="s_add", id=g["id"])) for g in repo.list_groups(con)]
        if not buttons:
            return await show(cb, "Сначала создайте группу.", kb([("⬅️ Меню", A(act="menu"))]))
        return await show(cb, "В какую группу добавить ученика?", kb(*column(buttons, 2), nav(A(act="students"))))
    await state.update_data(group_id=callback_data.id)
    await student_step(cb, state, con, 1)


@router.callback_query(A.filter(F.act == "s_add_back"), StateFilter(AddStudent.name))
async def student_add_back(cb: CallbackQuery, callback_data: A, state: FSMContext, con) -> None:
    await student_step(cb, state, con, callback_data.arg)


@router.message(AddStudent.name)
async def student_add_name(message: Message, state: FSMContext, con) -> None:
    data = await state.get_data()
    name, error = check_student_name(message.text or "")
    if error:
        return await message.answer(error, reply_markup=kb(nav(A(act="group", id=data["group_id"]))))
    dup = [s for s in repo.students_by_name(con, name) if repo.is_enrolled(con, s["id"], data["group_id"])]
    if dup:
        return await message.answer("Ученик с таким именем уже есть в этой группе. Напишите другое имя.",
                                    reply_markup=kb(nav(A(act="group", id=data["group_id"]))))
    await state.update_data(name=name)
    await student_step(message, state, con, 2)


@router.callback_query(A.filter(F.act == "s_add_lang"), StateFilter(AddStudent.name))
async def student_add_lang(cb: CallbackQuery, callback_data: A, state: FSMContext, con) -> None:
    await state.update_data(card_lang="uz" if callback_data.arg else "ru")
    await student_step(cb, state, con, 3)


@router.callback_query(A.filter(F.act == "s_add_consent"), StateFilter(AddStudent.name))
async def student_add_consent(cb: CallbackQuery, callback_data: A, state: FSMContext, con) -> None:
    d = await state.get_data()
    if "name" not in d or "card_lang" not in d:
        return await student_step(cb, state, con, 1)
    await state.clear()
    with tx(con):
        sid = repo.add_student(con, cb.from_user.id, d["name"], d["card_lang"], bool(callback_data.arg),
                               d["group_id"], schedule.today())
    s = repo.student(con, sid)
    await show(cb, "Ученик добавлен.\n\n" + student_text(con, s), kb(
        [("➕ Ещё ученика в эту группу", A(act="s_add", id=d["group_id"]))],
        [("🗺 Другая станция", A(act="s_stage", id=sid, arg=d["group_id"]))]
        if repo.group(con, d["group_id"])["has_map"] else [],
        [("⬅️ Группа", A(act="group", id=d["group_id"]))]))


# ================================================================ настройки

SETTINGS = {
    "center_name": ("Название центра (на карточке)", "text"),
    "reminder_day": ("День напоминания учителям", "weekday"),
    "reminder_time": ("Время напоминания (не позже 21:00)", "time21"),
    "backup_time": ("Время ежедневного бэкапа", "time"),
    "summary_time": ("Время сводки владельцу (в день напоминаний)", "time"),
    "rate_limit_per_min": ("Сколько сообщений в минуту от одного человека принимать", "int:10:200"),
    "url_safe_length": ("Длина ссылки формы, после которой форма делится на части", "int:800:8000"),
    "hint_absent_streak": ("Подсказка: пропусков подряд", "int:1:10"),
    "hint_absent_month": ("Подсказка: пропусков за месяц", "int:1:20"),
    "hint_late_2weeks": ("Подсказка: опозданий за 2 недели", "int:1:20"),
    "hint_homework_weeks": ("Подсказка: недель подряд слабой домашки", "int:1:8"),
    "hint_drop_steps": ("Подсказка: падение показателя на столько ступеней", "int:1:3"),
    "hint_exam_weeks": ("Подсказка: за сколько недель до экзамена проверять риск", "int:1:8"),
    "hint_growth_weeks": ("Похвала: недель роста подряд", "int:2:8"),
}
WEEKDAY_FULL = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]


def setting_view(key: str, value: str) -> str:
    kind = SETTINGS[key][1]
    if kind == "weekday" and value.isdigit() and 1 <= int(value) <= 7:
        return WEEKDAY_FULL[int(value) - 1]
    return value or "не задано"


def check_setting(key: str, text: str) -> tuple[str | None, str]:
    kind = SETTINGS[key][1]
    text = " ".join(text.split())
    if kind == "text":
        return (text, "") if 0 < len(text) <= 60 else (None, "Нужен текст до 60 знаков.")
    if kind == "weekday":
        w = schedule.parse_weekdays(text)
        if w is None:
            low = text.casefold()
            w = next((str(i + 1) for i, n in enumerate(WEEKDAY_FULL) if n.startswith(low[:3])), None) if low else None
        return (w, "") if w and "," not in w else (None, "Нужен один день, например: суббота")
    if kind.startswith("time"):
        t = schedule.parse_time(text)
        if not t:
            return None, "Не понял время. Пример: 18:00"
        if kind == "time21" and t > "21:00":
            return None, "Напоминание — не позже 21:00."
        return t, ""
    if kind.startswith("int"):
        _, low, high = kind.split(":")
        if text.isdigit() and int(low) <= int(text) <= int(high):
            return text, ""
        return None, f"Нужно целое число от {low} до {high}."
    raise ValueError(kind)


@router.callback_query(A.filter(F.act == "settings"))
async def settings(cb: CallbackQuery, state: FSMContext, con) -> None:
    await state.clear()
    values = repo.all_settings(con)
    keys = list(SETTINGS)
    lines = ["Настройки. Пороги подсказок — стартовые предположения, через месяц их стоит подстроить.", ""]
    lines += [f"• {SETTINGS[k][0]}: {setting_view(k, values.get(k, ''))}" for k in keys]
    buttons = [(SETTINGS[k][0][:40], A(act="set", arg=i)) for i, k in enumerate(keys)]
    await show(cb, "\n".join(lines), kb(*column(buttons), [("⬅️ Меню", A(act="menu"))]))


@router.callback_query(A.filter(F.act == "set"))
async def setting_edit(cb: CallbackQuery, callback_data: A, state: FSMContext, con) -> None:
    key = list(SETTINGS)[callback_data.arg]
    await state.set_state(EditSetting.value)
    await state.update_data(key=key)
    await show(cb, f"{SETTINGS[key][0]}.\nСейчас: {setting_view(key, repo.get_setting(con, key))}\n\n"
                   "Пришлите новое значение.", kb(nav(A(act="settings"))))


@router.message(EditSetting.value)
async def setting_value(message: Message, state: FSMContext, con) -> None:
    key = (await state.get_data())["key"]
    value, error = check_setting(key, message.text or "")
    if error:
        return await message.answer(error, reply_markup=kb(nav(A(act="settings"))))
    await state.clear()
    repo.set_setting(con, message.from_user.id, key, value)
    await message.answer(f"Сохранено: {SETTINGS[key][0]} — {setting_view(key, value)}",
                         reply_markup=kb([("⚙️ Настройки", A(act="settings"))], [("⬅️ Меню", A(act="menu"))]))


# ================================================================ баллы экзаменов по этапам

def fmt_score(x) -> str:
    return "—" if x is None else (str(int(x)) if float(x).is_integer() else str(x))


@router.callback_query(A.filter(F.act == "scores"))
async def scores(cb: CallbackQuery, state: FSMContext, con) -> None:
    await state.clear()
    rows = [s for s in repo.list_stages(con, "en")]
    lines = ["Проходной / максимальный балл по этапам (английский).",
             "Экзамен решает переход там, где отмечено 🎯.", ""]
    lines += [f"{'🎯' if s['exam_transition'] else '•'} {s['name_ru']}: "
              f"{fmt_score(s['pass_score'])} / {fmt_score(s['max_score'])}" for s in rows]
    buttons = [(s["name_ru"], A(act="score", id=s["id"])) for s in rows]
    await show(cb, "\n".join(lines), kb(*column(buttons, 3), [("⬅️ Меню", A(act="menu"))]))


@router.callback_query(A.filter(F.act == "score"))
async def score_edit(cb: CallbackQuery, callback_data: A, state: FSMContext, con) -> None:
    s = repo.stage(con, callback_data.id)
    await state.set_state(StageScores.value)
    await state.update_data(stage_id=s["id"])
    await show(cb, f"{s['name_ru']}: пришлите проходной и максимальный балл через пробел, например: 60 100",
               kb(nav(A(act="scores"))))


def parse_scores(text: str) -> tuple[tuple[float, float] | None, str]:
    parts = text.replace(",", ".").replace("/", " ").split()
    try:
        pass_score, max_score = (float(p) for p in parts)
    except ValueError:
        return None, "Нужно два числа через пробел, например: 60 100"
    if not 0 < pass_score <= max_score <= 1000:
        return None, "Проходной балл должен быть больше 0 и не больше максимального."
    return (pass_score, max_score), ""


@router.message(StageScores.value)
async def score_value(message: Message, state: FSMContext, con) -> None:
    values, error = parse_scores(message.text or "")
    if error:
        return await message.answer(error, reply_markup=kb(nav(A(act="scores"))))
    stage_id = (await state.get_data())["stage_id"]
    await state.clear()
    repo.set_stage_scores(con, message.from_user.id, stage_id, *values)
    s = repo.stage(con, stage_id)
    await message.answer(f"Сохранено: {s['name_ru']} — {fmt_score(values[0])} из {fmt_score(values[1])}",
                         reply_markup=kb([("🎯 Баллы экзаменов", A(act="scores"))], [("⬅️ Меню", A(act="menu"))]))
