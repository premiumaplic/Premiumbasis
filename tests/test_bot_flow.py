"""Сквозные сценарии в чате (Telegram заменён заглушкой). Все данные выдуманные."""

import asyncio

from bot import repo
from tests.conftest import OWNER, buttons, last_text, make_group, make_teacher

STRANGER = 999001
TEACHER_TG = 600001


def run(coro):
    return asyncio.run(coro)


def test_stranger_gets_no_access_and_id(chat):
    calls = run(chat.send(STRANGER, "/start"))
    text = last_text(calls)
    assert "Нет доступа" in text and str(STRANGER) in text and "Ruxsat yoʻq" in text
    assert "999001" in last_text(run(chat.send(STRANGER, "/myid")))
    # никакие кнопки владельца не срабатывают
    calls = run(chat.press(STRANGER, "a:groups:0:0"))
    assert all("Группы" not in (getattr(c, "text", "") or "") for c in calls)


def test_group_chat_is_ignored(chat):
    assert run(chat.send(OWNER, "/start", chat_type="group")) == []


def test_owner_menu_and_add_teacher(chat, con):
    calls = run(chat.send(OWNER, "/start"))
    assert "Меню владельца" in last_text(calls)
    assert "👩‍🏫 Учителя" in buttons(calls)
    run(chat.press(OWNER, "a:t_add:0:0"))
    assert "Нужны только цифры" in last_text(run(chat.send(OWNER, "двенадцать")))
    run(chat.send(OWNER, "600001"))
    calls = run(chat.send(OWNER, "Дилноза Каримова"))
    assert "Oʻzbekcha" in buttons(calls)
    calls = run(chat.press(OWNER, "a:t_add_lang:0:1"))
    assert "Учитель добавлен" in last_text(calls)
    t = repo.teacher_by_tg(con, 600001)
    assert t["name"] == "Дилноза Каримова" and t["lang"] == "uz"
    assert con.execute("SELECT count(*) FROM audit_log WHERE tg_id = ?", (OWNER,)).fetchone()[0] == 1


def test_owner_creates_group_step_by_step(chat, con):
    tid = make_teacher(con, TEACHER_TG)
    run(chat.press(OWNER, "a:g_add:0:0"))
    run(chat.send(OWNER, "10-А"))
    run(chat.press(OWNER, "a:g_add_subj:0:0"))                 # Английский
    run(chat.press(OWNER, f"a:g_add_teacher:0:{tid}"))
    a1 = repo.stage_by_code(con, "en", "a1")["id"]
    run(chat.press(OWNER, f"a:g_add_stage:0:{a1}"))
    run(chat.send(OWNER, "01.09.2026"))
    run(chat.press(OWNER, "a:g_add_day:0:1"))
    run(chat.press(OWNER, "a:g_add_day:0:3"))
    run(chat.press(OWNER, "a:g_add_day:0:0"))
    calls = run(chat.send(OWNER, "15:00"))
    assert "Пн, Ср" in last_text(calls)
    calls = run(chat.press(OWNER, "a:g_add_ok:0:0"))
    assert "Группа создана" in last_text(calls)
    g = repo.group_by_name(con, "10-А")
    assert g["teacher_id"] == tid and g["weekdays"] == "1,3" and g["lesson_time"] == "15:00"


def test_owner_adds_student_and_toggles_consent(chat, con):
    gid = make_group(con)
    run(chat.press(OWNER, f"a:s_add:{gid}:0"))
    assert "имя и фамилия" in last_text(run(chat.send(OWNER, "Азиз"))).lower()
    run(chat.send(OWNER, "Азиз Каримов"))
    run(chat.press(OWNER, "a:s_add_lang:0:1"))
    calls = run(chat.press(OWNER, "a:s_add_consent:0:0"))
    assert "Ученик добавлен" in last_text(calls) and "Курс A1" in last_text(calls)
    sid = repo.group_students(con, gid)[0]["id"]
    run(chat.press(OWNER, f"a:s_consent:{sid}:{gid}"))
    s = repo.student(con, sid)
    assert s["consent"] == 1 and s["card_lang"] == "uz"


def test_settings_validation(chat, con):
    run(chat.press(OWNER, "a:set:0:2"))    # время напоминания
    assert "не позже 21:00" in last_text(run(chat.send(OWNER, "22:30")))
    run(chat.send(OWNER, "19:00"))
    assert repo.get_setting(con, "reminder_time") == "19:00"


def test_teacher_sees_only_own_groups(chat, con):
    tid = make_teacher(con, TEACHER_TG)
    other = make_teacher(con, 600002, "Другой Учитель")
    mine = make_group(con, "10-А", teacher_id=tid)
    foreign = make_group(con, "11-Б", teacher_id=other)
    calls = run(chat.send(TEACHER_TG, "/start"))
    assert list(buttons(calls)) == ["10-А · Английский"]
    calls = run(chat.press(TEACHER_TG, f"t:group:{mine}"))
    assert "Группа 10-А · Курс A1" in last_text(calls)
    keyboard = [b for row in calls[-1].reply_markup.keyboard for b in row]
    web = {b.text: b.web_app.url for b in keyboard if b.web_app}
    assert set(web) == {"✅ Посещаемость", "📝 Недельный отчёт", "🎓 Экзамен", "📚 Тема"}
    assert "📤 Карточки для родителей" in [b.text for b in keyboard]
    assert web["✅ Посещаемость"].startswith("https://example.github.io/Repo/forms/attendance.html#d=")
    assert repo.teacher(con, tid)["current_group_id"] == mine
    # подделанная кнопка чужой группы
    calls = run(chat.press(TEACHER_TG, f"t:group:{foreign}"))
    assert any(type(c).__name__ == "AnswerCallbackQuery" and c.show_alert for c in calls)
    # учитель не может пользоваться меню владельца
    calls = run(chat.press(TEACHER_TG, "a:groups:0:0"))
    assert not any("Группы (" in (getattr(c, "text", "") or "") for c in calls)


def test_disabled_teacher_loses_access(chat, con):
    tid = make_teacher(con, TEACHER_TG)
    repo.set_teacher_active(con, OWNER, tid, False)
    assert "Нет доступа" in last_text(run(chat.send(TEACHER_TG, "/start")))


def test_rate_limit_ignores_flood(chat, con):
    repo.set_setting(con, OWNER, "rate_limit_per_min", "10")
    answered = sum(1 for _ in range(15) if run(chat.send(STRANGER, "/start")))
    assert answered == 10


def test_teacher_sends_form_and_gets_fresh_keyboard(chat, con):
    import json
    import uuid
    tid = make_teacher(con, TEACHER_TG)
    gid = make_group(con, "10-А", teacher_id=tid)
    from bot import schedule
    sid = repo.add_student(con, OWNER, "Азиз Каримов", "ru", True, gid, schedule.today())
    data = json.dumps({"v": 1, "u": str(uuid.uuid4()), "t": "att", "g": gid,
                       "d": schedule.today().isoformat(), "m": [[sid, 1]]})
    chat.n += 1
    from aiogram.types import Update
    msg = chat._msg(TEACHER_TG, web_app_data={"data": data, "button_text": "✅ Посещаемость"})
    start = len(chat.session.calls)
    run(chat.dp.feed_update(chat.bot, Update(update_id=chat.n, message=msg)))
    reply = chat.session.calls[start:][-1]
    assert reply.text.startswith("Сохранено: посещаемость 10-А") and "опозданий 1" in reply.text
    assert any(b.web_app for row in reply.reply_markup.keyboard for b in row)


def test_stranger_form_data_is_ignored(chat, con):
    from aiogram.types import Update
    make_group(con)
    msg = chat._msg(STRANGER, web_app_data={"data": '{"v":1}', "button_text": "x"})
    start = len(chat.session.calls)
    run(chat.dp.feed_update(chat.bot, Update(update_id=99, message=msg)))
    assert "Нет доступа" in chat.session.calls[start:][-1].text
    assert con.execute("SELECT count(*) FROM attendance").fetchone()[0] == 0


def test_cards_for_parents(chat, con):
    from bot import reports, schedule
    tid = make_teacher(con, TEACHER_TG)
    gid = make_group(con, "10-А", teacher_id=tid)
    today = schedule.today()
    a = repo.add_student(con, OWNER, "Азиз Каримов", "ru", True, gid, today)
    repo.add_student(con, OWNER, "Мадина Юсупова", "uz", True, gid, today)
    c = repo.add_student(con, OWNER, "Жасур Ахмедов", "ru", False, gid, today)   # нет согласия
    week = reports.week_start(today)
    for sid in (a, c):
        reports.save_weekly(con, TEACHER_TG, gid, week, sid, {1: 3, 2: 2}, "")
    assert "Сначала выберите группу" in last_text(run(chat.send(TEACHER_TG, "📤 Карточки для родителей")))
    run(chat.press(TEACHER_TG, f"t:group:{gid}"))
    calls = run(chat.send(TEACHER_TG, "📤 Карточки для родителей"))
    photos = [x for x in calls if type(x).__name__ == "SendPhoto"]
    assert len(photos) == 1 and photos[0].caption.startswith("Азиз Каримов — неделя")
    final = last_text(calls)
    assert "карточек 1" in final
    assert "Мадина Юсупова — нет отчёта за неделю" in final
    assert "Жасур Ахмедов — нет отметки о согласии родителя" in final


def test_owner_backup_without_password(chat):
    calls = run(chat.send(OWNER, "/backup"))
    assert "не задан пароль бэкапа" in last_text(calls)


def test_owner_uploads_book_units_and_edits_phrases(chat, con):
    a1 = repo.stage_by_code(con, "en", "a1")["id"]
    run(chat.press(OWNER, f"a:topics_stage:{a1}:0"))
    calls = run(chat.send(OWNER, "1. Family\n2. My day\nFood and drinks"))
    assert "юнитов 3" in last_text(calls)
    assert [r["title"] for r in con.execute("SELECT title FROM topics ORDER BY unit_no")] == \
        ["Family", "My day", "Food and drinks"]
    run(chat.press(OWNER, "a:phrases:0:0"))
    assert "ровно один знак" in last_text(run(chat.send(OWNER, "Молодец без перевода")))
    run(chat.send(OWNER, "Молодец! | Barakalla!\nЧитай больше. | Koʻproq oʻqi."))
    from bot import reports
    assert [p["text_uz"] for p in reports.phrases(con)] == ["Barakalla!", "Koʻproq oʻqi."]


def test_owner_edits_question_options(chat, con):
    qid = con.execute("SELECT id FROM questions WHERE code = 'homework'").fetchone()[0]
    run(chat.press(OWNER, f"a:q_edit:{qid}:4"))
    assert "ровно 4 строки" in last_text(run(chat.send(OWNER, "bir\nikki")))
    run(chat.send(OWNER, "0 — qilinmagan\n1 — qisman\n2 — xatolar bilan\n3 — yaxshi"))
    q = con.execute("SELECT opt0_uz, opt3_uz FROM questions WHERE id = ?", (qid,)).fetchone()
    assert tuple(q) == ("qilinmagan", "yaxshi")


def test_teacher_hints_button_and_close(chat, con):
    import datetime as dt
    from bot import reports, schedule
    tid = make_teacher(con, TEACHER_TG)
    gid = make_group(con, "10-А", teacher_id=tid)
    sid = repo.add_student(con, OWNER, "Азиз Каримов", "ru", True, gid, schedule.today())
    for back in (2, 1):
        reports.save_attendance(con, 1, gid, schedule.today() - dt.timedelta(days=back), [(sid, "absent")])
    run(chat.press(TEACHER_TG, f"t:group:{gid}"))
    calls = run(chat.send(TEACHER_TG, "⚠️ Подсказки"))
    texts = [c.text for c in calls if getattr(c, "text", None)]
    assert "Подсказки по группе 10-А: 1" in texts[0] and "Свяжитесь с родителем" in texts[1]
    close_cb = next(b for b in buttons(calls).values())
    run(chat.press(TEACHER_TG, close_cb))
    assert "подсказок нет" in last_text(run(chat.send(TEACHER_TG, "⚠️ Подсказки")))


def test_forwarded_channel_post_shows_channel_id(chat):
    from aiogram.types import Update
    msg = chat._msg(OWNER, text="пост", forward_origin={
        "type": "channel", "date": 1795000000, "message_id": 5,
        "chat": {"id": -1001234567890, "type": "channel", "title": "Бэкапы"}})
    start = len(chat.session.calls)
    run(chat.dp.feed_update(chat.bot, Update(update_id=500, message=msg)))
    assert "backup_channel_id = -1001234567890" in chat.session.calls[start:][-1].text


def _membership(chat, chat_obj, status, rights=None):
    from aiogram.types import Update
    new = {"status": status, "user": {"id": 42, "is_bot": True, "first_name": "Bot"}}
    if status == "administrator":
        new.update({"can_be_edited": False, "is_anonymous": False, "can_manage_chat": True,
                    "can_delete_messages": True, "can_manage_video_chats": False, "can_restrict_members": False,
                    "can_promote_members": False, "can_change_info": False, "can_invite_users": True,
                    "can_post_stories": False, "can_edit_stories": False, "can_delete_stories": False,
                    "can_send_welcome_messages": False,
                    **(rights or {})})
    upd = {"chat": chat_obj, "from": {"id": OWNER, "is_bot": False, "first_name": "Owner"}, "date": 1795000000,
           "old_chat_member": {"status": "left", "user": {"id": 42, "is_bot": True, "first_name": "Bot"}},
           "new_chat_member": new}
    start = len(chat.session.calls)
    run(chat.dp.feed_update(chat.bot, Update(update_id=900, my_chat_member=upd)))
    return chat.session.calls[start:]


def test_bot_added_to_channel_tells_owner_the_id(chat):
    calls = _membership(chat, {"id": -1009876543210, "type": "channel", "title": "Бэкапы"}, "administrator",
                        {"can_post_messages": True})
    msg = [c for c in calls if type(c).__name__ == "SendMessage"][-1]
    assert msg.chat_id == OWNER and "backup_channel_id = -1009876543210" in msg.text
    assert "нет права публиковать" not in msg.text
    calls = _membership(chat, {"id": -1009876543210, "type": "channel", "title": "Бэкапы"}, "administrator",
                        {"can_post_messages": False})
    assert "нет права публиковать" in [c for c in calls if type(c).__name__ == "SendMessage"][-1].text


def test_bot_added_to_group_leaves_and_explains(chat):
    calls = _membership(chat, {"id": -100555, "type": "supergroup", "title": "Бэкапы"}, "member")
    names = [type(c).__name__ for c in calls]
    assert "LeaveChat" in names
    assert "нужен закрытый КАНАЛ" in [c for c in calls if type(c).__name__ == "SendMessage"][-1].text


def test_forward_from_group_is_explained(chat):
    from aiogram.types import Update
    msg = chat._msg(OWNER, text="пост", forward_origin={
        "type": "chat", "date": 1795000000, "sender_chat": {"id": -100555, "type": "supergroup", "title": "Г"}})
    start = len(chat.session.calls)
    run(chat.dp.feed_update(chat.bot, Update(update_id=901, message=msg)))
    assert "нужен закрытый КАНАЛ" in chat.session.calls[start:][-1].text
