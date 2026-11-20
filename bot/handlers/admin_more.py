"""Меню владельца, этап 4: бэкап по команде, сводка, тексты (юниты книги, вопросы недели, фразы)."""

import logging
import re

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot import backup, config, reports, repo, schedule, summary
from bot.access import OwnerOnly
from bot.db import tx
from bot.handlers.common import show
from bot.ui import A, column, kb

log = logging.getLogger("admin")
router = Router(name="admin_more")
router.message.filter(OwnerOnly())
router.callback_query.filter(OwnerOnly())
CANCEL = [("✖️ Отмена", A(act="cancel"))]


class EditTexts(StatesGroup):
    topics = State()
    question = State()
    phrases = State()


# ================================================================ бэкап и сводка

async def do_backup(bot: Bot, con, conf) -> str:
    try:
        report = await backup.run(bot, con, config.data_dir(), conf.backup_password, conf.backup_channel_id, "manual")
    except backup.BackupError as e:
        return str(e)
    repo.audit(con, conf.owner_id or 0, "backup", "", "manual")
    from datetime import datetime
    repo.set_setting(con, 0, "backup_ok", datetime.now().isoformat(timespec="seconds"), quiet=True)
    return report


@router.message(Command("backup"))
async def backup_cmd(message: Message, bot: Bot, con, conf) -> None:
    await message.answer("Делаю бэкап…")
    await message.answer(await do_backup(bot, con, conf))


@router.callback_query(A.filter(F.act == "backup"))
async def backup_button(cb: CallbackQuery, bot: Bot, con, conf) -> None:
    await cb.answer("Делаю бэкап…")
    await cb.message.answer(await do_backup(bot, con, conf), reply_markup=kb([("⬅️ Меню", A(act="menu"))]))


@router.message(Command("status"))
async def status(message: Message, bot: Bot, con, conf) -> None:
    """Состояние бота для проверки: версия, канал бэкапов, пароль, последний бэкап."""
    from bot import __version__
    lines = [f"Версия бота: {__version__}", f"Ваш ID (владелец): {conf.owner_id}"]
    if conf.backup_channel_id:
        problem = await backup.check_channel(bot, conf.backup_channel_id)
        lines.append(f"Канал бэкапов: {conf.backup_channel_id} — " + ("бот может публиковать ✅" if not problem
                                                                     else "⚠️ " + problem))
    else:
        lines.append("Канал бэкапов: не выбран — добавьте бота администратором в закрытый канал")
    lines.append("Пароль бэкапа: " + ("задан ✅" if conf.backup_password else "⚠️ не задан (config.ini, [backup] password)"))
    ok = repo.get_setting(con, "backup_ok")
    lines.append(f"Последний удачный бэкап: {ok.replace('T', ' ') if ok else 'ещё не было'}")
    await message.answer("\n".join(lines))


@router.message(Command("log"))
async def last_log(message: Message) -> None:
    """Последние строки журнала — чтобы переслать разработчику. Секреты из журнала уже вычищены."""
    path = config.data_dir() / "logs" / "bot.log"
    if not path.exists():
        return await message.answer("Журнала пока нет.")
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-25:]
    text = "\n".join(line[:300] for line in lines)
    await message.answer("Последние строки журнала:\n\n" + text[-3800:])


@router.message(Command("summary"))
@router.callback_query(A.filter(F.act == "summary"))
async def summary_now(event, con) -> None:
    week = reports.week_start(schedule.today())
    text = summary.text(con, week)
    if isinstance(event, CallbackQuery):
        await event.answer()
        await event.message.answer(text, reply_markup=kb([("⬅️ Меню", A(act="menu"))]))
    else:
        await event.answer(text)


# ================================================================ тексты

@router.callback_query(A.filter(F.act == "texts"))
async def texts_menu(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await show(cb, "Тексты для учителей и карточек:", kb(
        [("📚 Юниты книги (темы)", A(act="topics"))],
        [("❓ Вопросы недели", A(act="questions"))],
        [("💬 Готовые фразы", A(act="phrases"))],
        [("⬅️ Меню", A(act="menu"))]))


# ---- юниты книги

@router.callback_query(A.filter(F.act == "topics"))
async def topics_menu(cb: CallbackQuery, con) -> None:
    buttons = []
    for subj in repo.list_subjects(con):
        for s in repo.list_stages(con, subj["code"]):
            n = len(reports.topics_for_stage(con, s["id"]))
            buttons.append((f"{s['name_ru']} ({n})", A(act="topics_stage", id=s["id"])))
    await show(cb, "Список юнитов книги для этапа. Учитель выбирает юнит в форме «Тема».\n"
                   "В скобках — сколько юнитов загружено.",
               kb(*column(buttons, 3), [("⬅️ Тексты", A(act="texts"))]))


@router.callback_query(A.filter(F.act == "topics_stage"))
async def topics_stage(cb: CallbackQuery, callback_data: A, state: FSMContext, con) -> None:
    stage = repo.stage(con, callback_data.id)
    current = reports.topics_for_stage(con, stage["id"])
    listing = "\n".join(f"{u['unit_no']}. {u['title']}" for u in current) or "пока пусто"
    await state.set_state(EditTexts.topics)
    await state.update_data(stage_id=stage["id"])
    await show(cb, f"{stage['name_ru']} — юниты сейчас:\n{listing}\n\n"
                   "Пришлите новый список: каждый юнит с новой строки, например\n"
                   "1. Family\n2. My day\n3. Food and drinks\n\n"
                   "Список заменит прежний. Пустой список не принимается.", kb(CANCEL))


def parse_topics(text: str) -> tuple[list[tuple[int, str]] | None, str]:
    items, auto = [], 1
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        number, title = None, line
        head = line.split(maxsplit=1)
        if head and head[0].rstrip(".)").isdigit() and len(head) == 2:
            number, title = int(head[0].rstrip(".)")), head[1].strip()
        number = number or auto
        if not title or len(title) > 80:
            return None, f"Строка «{line[:40]}»: название юнита — от 1 до 80 знаков."
        if any(n == number for n, _ in items):
            return None, f"Номер {number} повторяется."
        items.append((number, title))
        auto = number + 1
    if not items:
        return None, "Список пуст."
    if len(items) > 100:
        return None, "Слишком много юнитов (больше 100)."
    return items, ""


@router.message(EditTexts.topics)
async def topics_save(message: Message, state: FSMContext, con) -> None:
    items, error = parse_topics(message.text or "")
    if error:
        return await message.answer(error, reply_markup=kb(CANCEL))
    stage_id = (await state.get_data())["stage_id"]
    await state.clear()
    with tx(con):
        con.execute("DELETE FROM topics WHERE stage_id = ?", (stage_id,))
        con.executemany("INSERT INTO topics (stage_id, unit_no, title) VALUES (?, ?, ?)",
                        [(stage_id, n, title) for n, title in items])
        repo.audit(con, message.from_user.id, "topics", f"stage:{stage_id}", f"units={len(items)}")
    await message.answer(f"Сохранено: юнитов {len(items)}.",
                         reply_markup=kb([("📚 Юниты книги", A(act="topics"))], [("⬅️ Меню", A(act="menu"))]))


# ---- вопросы недели

FIELDS = {1: ("text_ru", "вопрос по-русски"), 2: ("opts_ru", "4 варианта по-русски"),
          3: ("text_uz", "вопрос по-узбекски"), 4: ("opts_uz", "4 варианта по-узбекски")}


def question_text(q) -> str:
    subjects = "все предметы" if q["subjects"] == "*" else q["subjects"].replace("math", "математика")
    lines = [f"❓ {q['text_ru']}  ({subjects})"]
    lines += [f"   {i} — {q[f'opt{i}_ru']}" for i in range(4)]
    lines.append(f"🇺🇿 {q['text_uz']}" + ("" if q["uz_checked"] else "  (черновик, не проверен)"))
    lines += [f"   {i} — {q[f'opt{i}_uz']}" for i in range(4)]
    return "\n".join(lines)


@router.callback_query(A.filter(F.act == "questions"))
async def questions_menu(cb: CallbackQuery, state: FSMContext, con) -> None:
    await state.clear()
    rows = con.execute("SELECT * FROM questions WHERE active = 1 ORDER BY sort").fetchall()
    buttons = [(q["text_ru"] + ("" if q["uz_checked"] else " ✎"), A(act="question", id=q["id"])) for q in rows]
    await show(cb, "Вопросы недели. ✎ — узбекский текст ещё не проверен.\n"
                   "Варианты идут от худшего (0) к лучшему (3).",
               kb(*column(buttons, 2), [("⬅️ Тексты", A(act="texts"))]))


@router.callback_query(A.filter(F.act == "question"))
async def question_card(cb: CallbackQuery, callback_data: A, state: FSMContext, con) -> None:
    await state.clear()
    q = con.execute("SELECT * FROM questions WHERE id = ?", (callback_data.id,)).fetchone()
    qid = q["id"]
    await show(cb, question_text(q), kb(
        [("✏️ Вопрос RU", A(act="q_edit", id=qid, arg=1)), ("✏️ Варианты RU", A(act="q_edit", id=qid, arg=2))],
        [("✏️ Вопрос UZ", A(act="q_edit", id=qid, arg=3)), ("✏️ Варианты UZ", A(act="q_edit", id=qid, arg=4))],
        [("✅ Узбекский проверен" if not q["uz_checked"] else "↩️ Снять отметку «проверен»",
          A(act="q_checked", id=qid))],
        [("⬅️ Вопросы", A(act="questions"))]))


@router.callback_query(A.filter(F.act == "q_checked"))
async def question_checked(cb: CallbackQuery, callback_data: A, state: FSMContext, con) -> None:
    con.execute("UPDATE questions SET uz_checked = 1 - uz_checked WHERE id = ?", (callback_data.id,))
    repo.audit(con, cb.from_user.id, "question_uz_checked", f"question:{callback_data.id}")
    await question_card(cb, callback_data, state, con)


@router.callback_query(A.filter(F.act == "q_edit"))
async def question_edit(cb: CallbackQuery, callback_data: A, state: FSMContext) -> None:
    await state.set_state(EditTexts.question)
    await state.update_data(qid=callback_data.id, field=callback_data.arg)
    hint = "4 строки: вариант 0 (худший), 1, 2, 3 (лучший)" if callback_data.arg in (2, 4) else "одна строка"
    await show(cb, f"Пришлите {FIELDS[callback_data.arg][1]} — {hint}.\n"
                   "Изменение сразу появится в новых формах; старые отчёты не меняются.", kb(CANCEL))


@router.message(EditTexts.question)
async def question_save(message: Message, state: FSMContext, con) -> None:
    data = await state.get_data()
    field = FIELDS[data["field"]][0]
    text = (message.text or "").strip()
    if field.startswith("opts"):
        # номер в начале строки («0 — », «1.», «2)») необязателен и убирается
        options = [re.sub(r"^[0-3]\s*[.)\-—–:]?\s+", "", " ".join(line.split()))
                   for line in text.splitlines() if line.strip()]
        if len(options) != 4 or any(not o or len(o) > 60 for o in options):
            return await message.answer("Нужно ровно 4 строки, каждая до 60 знаков.", reply_markup=kb(CANCEL))
        lang = field[-2:]
        con.execute(f"UPDATE questions SET opt0_{lang} = ?, opt1_{lang} = ?, opt2_{lang} = ?, opt3_{lang} = ? "
                    f"WHERE id = ?", (*options, data["qid"]))
    else:
        text = " ".join(text.split())
        if not text or len(text) > 40:
            return await message.answer("Вопрос — от 1 до 40 знаков (он виден на карточке).", reply_markup=kb(CANCEL))
        con.execute(f"UPDATE questions SET {field} = ? WHERE id = ?", (text, data["qid"]))
    repo.audit(con, message.from_user.id, "question_text", f"question:{data['qid']}", field)
    await state.clear()
    q = con.execute("SELECT * FROM questions WHERE id = ?", (data["qid"],)).fetchone()
    await message.answer("Сохранено.\n\n" + question_text(q),
                         reply_markup=kb([("❓ Вопросы", A(act="questions"))], [("⬅️ Меню", A(act="menu"))]))


# ---- готовые фразы

@router.callback_query(A.filter(F.act == "phrases"))
async def phrases_menu(cb: CallbackQuery, state: FSMContext, con) -> None:
    rows = reports.phrases(con)
    listing = "\n".join(f"{p['text_ru']} | {p['text_uz']}" for p in rows) or "пусто"
    await state.set_state(EditTexts.phrases)
    await show(cb, f"Готовые фразы для комментария (русский | узбекский):\n{listing}\n\n"
                   "Чтобы заменить, пришлите новый список: каждая фраза с новой строки, "
                   "русский и узбекский через «|». Каждая фраза — до 40 знаков.", kb(CANCEL))


@router.message(EditTexts.phrases)
async def phrases_save(message: Message, state: FSMContext, con) -> None:
    items = []
    for line in (message.text or "").splitlines():
        if not line.strip():
            continue
        if line.count("|") != 1:
            return await message.answer(f"В строке «{line[:40]}» нужен ровно один знак «|».", reply_markup=kb(CANCEL))
        ru, uz = (" ".join(x.split()) for x in line.split("|"))
        if not ru or not uz or len(ru) > 40 or len(uz) > 40:
            return await message.answer(f"Строка «{line[:40]}»: обе части от 1 до 40 знаков.", reply_markup=kb(CANCEL))
        items.append((ru, uz))
    if not items or len(items) > 12:
        return await message.answer("Нужно от 1 до 12 фраз.", reply_markup=kb(CANCEL))
    await state.clear()
    with tx(con):
        con.execute("UPDATE phrases SET active = 0")
        con.executemany("INSERT INTO phrases (sort, text_ru, text_uz) VALUES (?, ?, ?)",
                        [(10 * (i + 1), ru, uz) for i, (ru, uz) in enumerate(items)])
        repo.audit(con, message.from_user.id, "phrases", "", f"count={len(items)}")
    await message.answer(f"Сохранено: фраз {len(items)}.", reply_markup=kb([("⬅️ Меню", A(act="menu"))]))
