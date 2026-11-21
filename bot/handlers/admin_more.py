"""Меню владельца, этап 4: бэкап по команде, сводка, тексты (юниты книги, вопросы недели, фразы)."""

import logging
import re

from aiogram import Bot, F, Router
from aiogram.filters import Command, Filter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot import backup, config, panel, reminders, reports, repo, schedule, summary
from bot.access import OwnerOnly
from bot.texts import all_variants, t
from bot.db import tx
from bot.handlers.admin import nav
from bot.handlers.common import show
from bot.ui import A, column, kb

log = logging.getLogger("admin")
router = Router(name="admin_more")
router.message.filter(OwnerOnly())
router.callback_query.filter(OwnerOnly())


class EditTexts(StatesGroup):
    topics = State()
    question = State()
    phrases = State()
    station = State()
    goals = State()


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
    from bot import sitecheck
    site = await sitecheck.check(conf.forms_url)
    lines.append("Сайт с формами: " + ("работает, версия совпадает ✅" if site is None else "⚠️ " + site))
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


# ================================================================ панель центра

class PanelAction(Filter):
    """Данные из панели владельца (а не из форм учителя — те обрабатывает чат учителя)."""

    async def __call__(self, message: Message) -> bool | dict:
        if not message.web_app_data:
            return False
        action = panel.parse_action(message.web_app_data.data)
        return {"action": action} if action else False


@router.message(F.text.in_(all_variants("btn_refresh")))
async def refresh_panel(message: Message, con, conf, teacher=None) -> None:
    text = "Панель центра обновлена — кнопка под полем ввода."
    if teacher is not None:
        text = t("hub_hello", teacher["lang"], name=teacher["name"])
    await message.answer(text, reply_markup=panel.keyboard(con, conf, teacher))


async def remind_now(bot: Bot, con) -> int:
    """Напоминание учителям прямо сейчас — тем, у кого есть незаполненные отчёты этой недели."""
    week = reports.week_start(schedule.today()).isoformat()
    sent = 0
    for tg_id, text in reminders.messages(con, week):
        try:
            await bot.send_message(tg_id, text)
            sent += 1
        except Exception as e:  # noqa: BLE001 — один недоступный учитель не мешает остальным
            log.warning("Напоминание учителю %s не доставлено: %s", tg_id, type(e).__name__)
    return sent


async def send_centre_export(message: Message, con) -> None:
    from datetime import timedelta
    from aiogram.types import BufferedInputFile
    from bot import export
    week = reports.week_start(schedule.today())
    data = export.weekly_xlsx(con, repo.list_groups(con), [week, week - timedelta(weeks=1)])   # база — в этом же потоке
    repo.audit(con, message.from_user.id, "export", "", week.isoformat())
    await message.answer_document(BufferedInputFile(data, filename=export.filename("centr", week)),
                                  caption="Отчёты всех групп за эту и прошлую неделю (Excel).")


@router.message(Command("export"))
async def export_cmd(message: Message, con) -> None:
    await send_centre_export(message, con)


@router.message(F.web_app_data, PanelAction())
async def panel_action(message: Message, bot: Bot, con, conf, action: str, teacher=None) -> None:
    kind, uuid = action.split(":", 1)
    if reports.submission_seen(con, uuid):
        return await message.answer("Эта команда уже выполнена.", reply_markup=panel.keyboard(con, conf, teacher))
    reports.record_submission(con, uuid, message.from_user.id, kind, "saved")
    log.info("Команда панели от владельца: %s", kind)
    if kind == "o_remind":
        sent = await remind_now(bot, con)
        repo.audit(con, message.from_user.id, "remind_now", "", f"sent={sent}")
        text = (f"⏰ Напоминание отправлено учителям: {sent}." if sent
                else "Напоминать некому: у всех учителей отчёты этой недели заполнены 👍")
    elif kind == "o_summary":
        text = summary.text(con, reports.week_start(schedule.today()))
    elif kind == "o_export":
        await send_centre_export(message, con)
        text = "Готово: файл выше. В нём лист «Сводка» по группам и по листу на каждую неделю."
    else:
        await message.answer("Делаю бэкап…")
        text = await do_backup(bot, con, conf)
    await message.answer(text, reply_markup=panel.keyboard(con, conf, teacher))


# ================================================================ тексты

@router.callback_query(A.filter(F.act == "texts"))
async def texts_menu(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await show(cb, "Тексты для учителей и карточек:", kb(
        [("📚 Юниты книги (темы)", A(act="topics"))],
        [("❓ Вопросы недели", A(act="questions"))],
        [("💬 Готовые фразы", A(act="phrases"))],
        [("🎯 Цели на неделю", A(act="goals"))],
        [("🗺 Станции карты (описания)", A(act="stations_txt"))],
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
                   "Список заменит прежний. Пустой список не принимается.", kb(nav(A(act="topics"))))


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
        return await message.answer(error, reply_markup=kb(nav(A(act="topics"))))
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
    flags = []
    if q["optional"]:
        flags.append("можно пропустить")
    if not q["active"]:
        flags.append("ВЫКЛЮЧЕН")
    lines = [f"❓ {q['text_ru']}  ({subjects})" + (f" — {', '.join(flags)}" if flags else "")]
    lines += [f"   {i} — {q[f'opt{i}_ru']}" for i in range(4)]
    lines.append(f"🇺🇿 {q['text_uz']}" + ("" if q["uz_checked"] else "  (черновик, не проверен)"))
    lines += [f"   {i} — {q[f'opt{i}_uz']}" for i in range(4)]
    return "\n".join(lines)


@router.callback_query(A.filter(F.act == "questions"))
async def questions_menu(cb: CallbackQuery, state: FSMContext, con) -> None:
    await state.clear()
    rows = con.execute("SELECT * FROM questions ORDER BY active DESC, sort").fetchall()
    buttons = [(("🚫 " if not q["active"] else "⏭ " if q["optional"] else "") + q["text_ru"]
                + ("" if q["uz_checked"] else " ✎"), A(act="question", id=q["id"])) for q in rows]
    await show(cb, "Вопросы недели. ✎ — узбекский текст ещё не проверен; ⏭ — учитель может пропустить "
                   "(«не оценивал»); 🚫 — вопрос выключен.\n"
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
        [("⏭ Сделать обязательным" if q["optional"] else "⏭ Разрешить пропускать", A(act="q_optional", id=qid)),
         ("✅ Включить" if not q["active"] else "🚫 Выключить", A(act="q_active", id=qid))],
        [("⬅️ Вопросы", A(act="questions"))]))


@router.callback_query(A.filter(F.act.in_({"q_optional", "q_active"})))
async def question_toggle(cb: CallbackQuery, callback_data: A, state: FSMContext, con) -> None:
    column_name = "optional" if callback_data.act == "q_optional" else "active"
    if column_name == "active":
        q = con.execute("SELECT * FROM questions WHERE id = ?", (callback_data.id,)).fetchone()
        left = con.execute("SELECT count(*) FROM questions WHERE active = 1 AND id != ? AND (subjects = '*' "
                           "OR subjects = ?)", (q["id"], q["subjects"])).fetchone()[0]
        if q["active"] and left < 2:
            return await cb.answer("Нельзя: должно остаться хотя бы 2 вопроса.", show_alert=True)
    con.execute(f"UPDATE questions SET {column_name} = 1 - {column_name} WHERE id = ?", (callback_data.id,))
    repo.audit(con, cb.from_user.id, f"question_{column_name}", f"question:{callback_data.id}")
    await question_card(cb, callback_data, state, con)


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
                   "Изменение сразу появится в новых формах; старые отчёты не меняются.", kb(nav(A(act="question", id=callback_data.id))))


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
            return await message.answer("Нужно ровно 4 строки, каждая до 60 знаков.", reply_markup=kb(nav(A(act="question", id=data["qid"]))))
        lang = field[-2:]
        con.execute(f"UPDATE questions SET opt0_{lang} = ?, opt1_{lang} = ?, opt2_{lang} = ?, opt3_{lang} = ? "
                    f"WHERE id = ?", (*options, data["qid"]))
    else:
        text = " ".join(text.split())
        if not text or len(text) > 40:
            return await message.answer("Вопрос — от 1 до 40 знаков (он виден на карточке).", reply_markup=kb(nav(A(act="question", id=data["qid"]))))
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
                   "русский и узбекский через «|». Каждая фраза — до 40 знаков.", kb(nav(A(act="texts"))))


@router.message(EditTexts.phrases)
async def phrases_save(message: Message, state: FSMContext, con) -> None:
    items = []
    for line in (message.text or "").splitlines():
        if not line.strip():
            continue
        if line.count("|") != 1:
            return await message.answer(f"В строке «{line[:40]}» нужен ровно один знак «|».", reply_markup=kb(nav(A(act="texts"))))
        ru, uz = (" ".join(x.split()) for x in line.split("|"))
        if not ru or not uz or len(ru) > 40 or len(uz) > 40:
            return await message.answer(f"Строка «{line[:40]}»: обе части от 1 до 40 знаков.", reply_markup=kb(nav(A(act="texts"))))
        items.append((ru, uz))
    if not items or len(items) > 12:
        return await message.answer("Нужно от 1 до 12 фраз.", reply_markup=kb(nav(A(act="texts"))))
    await state.clear()
    with tx(con):
        con.execute("UPDATE phrases SET active = 0")
        con.executemany("INSERT INTO phrases (sort, text_ru, text_uz) VALUES (?, ?, ?)",
                        [(10 * (i + 1), ru, uz) for i, (ru, uz) in enumerate(items)])
        repo.audit(con, message.from_user.id, "phrases", "", f"count={len(items)}")
    await message.answer(f"Сохранено: фраз {len(items)}.", reply_markup=kb([("⬅️ Меню", A(act="menu"))]))


# ---- описания станций карты

@router.callback_query(A.filter(F.act == "stations_txt"))
async def stations_texts(cb: CallbackQuery, state: FSMContext, con) -> None:
    await state.clear()
    buttons = []
    for subj in repo.list_subjects(con):
        for st in repo.list_stages(con, subj["code"]):
            buttons.append((f"{st['name_ru']}" + ("" if st["about_ru"] else " ·"), A(act="station_txt", id=st["id"])))
    await show(cb, "Описание станции видно учителю на карте и родителю на карточке: что проходят на этой станции. "
                   "Точка — описания нет.", kb(*column(buttons, 3), [("⬅️ Тексты", A(act="texts"))]))


@router.callback_query(A.filter(F.act == "station_txt"))
async def station_text(cb: CallbackQuery, callback_data: A, state: FSMContext, con) -> None:
    st = repo.stage(con, callback_data.id)
    await state.set_state(EditTexts.station)
    await state.update_data(stage_id=st["id"])
    await show(cb, f"🗺 {st['name_ru']} ({st['section_ru'] or 'без раздела'})\n"
                   f"RU: {st['about_ru'] or '—'}\nUZ: {st['about_uz'] or '—'}\n\n"
                   "Чтобы изменить, пришлите описание: русский и узбекский через «|», каждое до 60 знаков. Например:\n"
                   "Таблица умножения и деление | Karra jadvali va boʻlish",
               kb(nav(A(act="stations_txt"))))


@router.message(EditTexts.station)
async def station_text_save(message: Message, state: FSMContext, con) -> None:
    text = message.text or ""
    parts = [" ".join(x.split()) for x in text.split("|")]
    if len(parts) != 2 or not all(0 < len(p) <= 60 for p in parts):
        return await message.answer("Нужно две части через «|», каждая от 1 до 60 знаков.",
                                    reply_markup=kb(nav(A(act="stations_txt"))))
    stage_id = (await state.get_data())["stage_id"]
    await state.clear()
    con.execute("UPDATE stages SET about_ru = ?, about_uz = ? WHERE id = ?", (*parts, stage_id))
    repo.audit(con, message.from_user.id, "station_about", f"stage:{stage_id}")
    await message.answer("Сохранено.", reply_markup=kb([("🗺 Станции карты", A(act="stations_txt"))],
                                                      [("⬅️ Меню", A(act="menu"))]))


# ---- цели на неделю (выбираются в недельном отчёте, видны родителю на карточке)

GOAL_SCOPES = {"все": "*", "языки": "en,ar,ru,ko", "математика": "math", "английский": "en", "арабский": "ar",
               "русский": "ru", "корейский": "ko"}
SCOPE_NAMES = {v: k.capitalize() for k, v in GOAL_SCOPES.items()}


def goal_line(g) -> str:
    scope = SCOPE_NAMES.get(g["subjects"], g["subjects"])
    return f"{scope}: {g['text_ru']} | {g['text_uz']}"


def parse_goals(text: str) -> tuple[list[tuple[str, str, str]] | None, str]:
    items = []
    for raw in text.splitlines():
        line = " ".join(raw.split())
        if not line:
            continue
        scope = "*"
        head, sep, rest = line.partition(":")
        if sep and head.strip().casefold() in GOAL_SCOPES and "|" in rest:
            scope, line = GOAL_SCOPES[head.strip().casefold()], rest.strip()
        if line.count("|") != 1:
            return None, f"В строке «{line[:40]}» нужен ровно один знак «|»."
        ru, uz = (x.strip() for x in line.split("|"))
        if not ru or not uz or len(ru) > 50 or len(uz) > 50:
            return None, f"Строка «{line[:40]}»: обе части от 1 до 50 знаков."
        items.append((scope, ru, uz))
    if not items or len(items) > 40:
        return None, "Нужно от 1 до 40 целей."
    return items, ""


@router.callback_query(A.filter(F.act == "goals"))
async def goals_menu(cb: CallbackQuery, state: FSMContext, con) -> None:
    rows = con.execute("SELECT * FROM goals WHERE active = 1 ORDER BY sort, id").fetchall()
    listing = "\n".join(goal_line(g) for g in rows) or "пусто"
    await state.set_state(EditTexts.goals)
    await show(cb, "Цели на следующую неделю — учитель выбирает одну для ученика в недельном отчёте, "
                   "родитель видит её на карточке.\n\nСейчас:\n" + listing + "\n\n"
                   "Чтобы заменить, пришлите новый список: каждая цель с новой строки, русский и узбекский "
                   "через «|», до 50 знаков. В начале строки можно указать, для кого: «Все:», «Языки:», "
                   "«Математика:», «Английский:» и т. п. Без указания — для всех предметов.",
               kb(nav(A(act="texts"))))


@router.message(EditTexts.goals)
async def goals_save(message: Message, state: FSMContext, con) -> None:
    items, error = parse_goals(message.text or "")
    if error:
        return await message.answer(error, reply_markup=kb(nav(A(act="texts"))))
    await state.clear()
    with tx(con):
        con.execute("UPDATE goals SET active = 0")   # старые не удаляются: на них ссылаются прошлые отчёты
        con.executemany("INSERT INTO goals (subjects, sort, text_ru, text_uz) VALUES (?, ?, ?, ?)",
                        [(scope, 10 * (i + 1), ru, uz) for i, (scope, ru, uz) in enumerate(items)])
        repo.audit(con, message.from_user.id, "goals", "", f"count={len(items)}")
    await message.answer(f"Сохранено: целей {len(items)}. Учителя увидят их после «🔄 Обновить».",
                         reply_markup=kb([("⬅️ Меню", A(act="menu"))]))
