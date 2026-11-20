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
