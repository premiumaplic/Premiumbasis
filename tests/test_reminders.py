"""Напоминание учителю в конце недели."""

import datetime as dt

from bot import reminders, repo, reports
from tests.conftest import ACTOR, make_group, make_teacher

TZ = dt.timezone(dt.timedelta(hours=5))


def test_due_only_on_day_and_once(con):
    sat_17 = dt.datetime(2026, 11, 21, 17, 59, tzinfo=TZ)
    sat_18 = dt.datetime(2026, 11, 21, 18, 0, tzinfo=TZ)
    assert reminders.due_week(con, sat_17) is None
    assert reminders.due_week(con, sat_18) == "2026-11-16"
    assert reminders.due_week(con, dt.datetime(2026, 11, 21, 22, 30, tzinfo=TZ)) is None  # поздно
    assert reminders.due_week(con, dt.datetime(2026, 11, 20, 18, 30, tzinfo=TZ)) is None  # пятница
    repo.set_setting(con, 0, "reminder_last_week", "2026-11-16")
    assert reminders.due_week(con, sat_18) is None


def test_messages_list_missing_students(con):
    tid = make_teacher(con, 600001)
    done_teacher = make_teacher(con, 600002, "Учитель Два")
    gid = make_group(con, teacher_id=tid)
    g2 = make_group(con, "11-Б", teacher_id=done_teacher)
    day = dt.date(2026, 11, 16)
    a = repo.add_student(con, ACTOR, "Азиз Каримов", "ru", True, gid, day)
    repo.add_student(con, ACTOR, "Мадина Юсупова", "ru", True, gid, day)
    c = repo.add_student(con, ACTOR, "Жасур Ахмедов", "ru", True, g2, day)
    reports.save_weekly(con, 600001, gid, day, a, {1: 3}, "")
    reports.save_weekly(con, 600002, g2, day, c, {1: 3}, "")
    msgs = reminders.messages(con, "2026-11-16")
    assert len(msgs) == 1 and msgs[0][0] == 600001
    assert "10-А: Мадина Ю. (1 из 2)" in msgs[0][1] and "Азиз" not in msgs[0][1]
