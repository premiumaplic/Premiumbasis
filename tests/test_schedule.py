"""Даты: недели внутри станции, экзамены каждые 2 месяца, заголовок группы."""

import datetime as dt

from bot import repo, schedule
from tests.conftest import make_group

D = dt.date


def test_add_months_clamps_day():
    assert schedule.add_months(D(2026, 12, 31), 2) == D(2027, 2, 28)
    assert schedule.add_months(D(2026, 9, 1), 2) == D(2026, 11, 1)


def test_next_exam_every_two_months():
    start = D(2026, 9, 1)
    assert schedule.next_exam(start, D(2026, 9, 2)) == D(2026, 11, 1)
    assert schedule.next_exam(start, D(2026, 11, 1)) == D(2026, 11, 1)
    assert schedule.next_exam(start, D(2026, 11, 2)) == D(2027, 1, 1)


def test_stage_week():
    start = D(2026, 9, 1)
    assert schedule.stage_week(start, D(2026, 9, 1), True) == 1
    assert schedule.stage_week(start, D(2026, 9, 29), True) == 5
    assert schedule.stage_week(start, D(2026, 10, 31), True) == 8    # не больше 8
    assert schedule.stage_week(start, D(2026, 11, 1), True) == 1     # новый цикл после экзамена
    assert schedule.stage_week(start, D(2026, 11, 20), False) == 12
    assert schedule.stage_week(start, D(2026, 8, 1), True) == 0


def test_header_exam_stage(con):
    g = repo.group(con, make_group(con, "10-А", stage="a1", start=D(2026, 10, 15)))
    assert schedule.group_header(g, "ru", D(2026, 11, 20)) == \
        "Группа 10-А · Курс A1 · неделя 6 из 8 · экзамен 15 декабря"
    assert schedule.group_header(g, "uz", D(2026, 11, 20)) == \
        "Guruh 10-А · A1 kursi · 8 haftadan 6-hafta · imtihon 15-dekabr"


def test_header_roundup_and_no_map(con):
    g = repo.group(con, make_group(con, "Kids-1", stage="roundup2", start=D(2026, 9, 1)))
    assert schedule.group_header(g, "ru", D(2026, 11, 20)) == \
        "Группа Kids-1 · Roundup 2 · неделя 12 · переход по решению учителя"
    m = repo.group(con, make_group(con, "М-1", subject="math", stage=None, start=D(2026, 12, 1)))
    assert schedule.group_header(m, "ru", D(2026, 11, 20)) == "Группа М-1 · Математика · старт 1 декабря"


def test_parsers():
    assert schedule.parse_date("1.9.2026") == D(2026, 9, 1)
    assert schedule.parse_date("2026-09-01") == D(2026, 9, 1)
    assert schedule.parse_date("31.02.2026") is None
    assert schedule.parse_time("9:05") == "09:05"
    assert schedule.parse_time("25:00") is None
    assert schedule.parse_weekdays("Пн, ср пт") == "1,3,5"
    assert schedule.parse_weekdays("Du Ju") == "1,5"
    assert schedule.parse_weekdays("пн, абв") is None
    assert schedule.weekdays_text("1,3,5") == "Пн, Ср, Пт"
