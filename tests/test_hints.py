"""Все правила подсказок на выдуманных данных + жизненный цикл подсказки."""

import datetime as dt

from bot import hints, reports, repo
from tests.conftest import ACTOR, make_group, make_teacher

ON = dt.date(2026, 11, 20)            # пятница
WEEK = dt.date(2026, 11, 16)


def setup(con, stage="a1", start=dt.date(2026, 9, 1)):
    tid = make_teacher(con)
    gid = make_group(con, teacher_id=tid, stage=stage, start=start)
    sid = repo.add_student(con, ACTOR, "Азиз Каримов", "ru", True, gid, dt.date(2026, 9, 1))
    return tid, gid, sid


def att(con, gid, sid, items):
    repo.set_setting(con, ACTOR, "attendance_on", "1")   # посещаемость включена владельцем
    for day, status in items:
        reports.save_attendance(con, 1, gid, dt.date.fromisoformat(day), [(sid, status)])


def week(con, gid, sid, monday, values):
    qids = [q["id"] for q in reports.questions_for(con, "en")]
    reports.save_weekly(con, 1, gid, monday, sid, dict(zip(qids, values)), "")


def rules_of(con, gid):
    return sorted(h["rule"] for h in hints.open_hints(con, gid))


def text(con, gid):
    return "\n".join(hints.describe(con, h, "ru") for h in hints.open_hints(con, gid))


def test_two_absences_in_a_row(con):
    _, gid, sid = setup(con)
    att(con, gid, sid, [("2026-11-10", "present"), ("2026-11-12", "absent"), ("2026-11-14", "absent")])
    assert hints.evaluate_group(con, gid, ON) == 1
    assert rules_of(con, gid) == ["absent"]
    assert "Азиз Каримов — Свяжитесь с родителем\nПочему: пропуски: 12 ноября и 14 ноября" in text(con, gid)


def test_three_absences_in_month_and_excused_not_counted(con):
    _, gid, sid = setup(con)
    att(con, gid, sid, [("2026-10-25", "absent"), ("2026-11-01", "present"), ("2026-11-05", "absent"),
                        ("2026-11-07", "present"), ("2026-11-12", "excused"), ("2026-11-14", "present")])
    hints.evaluate_group(con, gid, ON)
    assert rules_of(con, gid) == []                       # 2 пропуска + уважительная — ещё нет
    att(con, gid, sid, [("2026-11-17", "absent"), ("2026-11-19", "present")])
    hints.evaluate_group(con, gid, ON)
    assert rules_of(con, gid) == ["absent"]


def test_three_lates_in_two_weeks(con):
    _, gid, sid = setup(con)
    att(con, gid, sid, [("2026-11-05", "late"), ("2026-11-12", "late"), ("2026-11-19", "late")])
    hints.evaluate_group(con, gid, ON)
    assert rules_of(con, gid) == []                       # 5 ноября — больше 2 недель назад
    att(con, gid, sid, [("2026-11-17", "late")])
    hints.evaluate_group(con, gid, ON)
    assert rules_of(con, gid) == ["late"] and "Обсудите опоздания" in text(con, gid)


def test_homework_two_weeks(con):
    _, gid, sid = setup(con)
    week(con, gid, sid, dt.date(2026, 11, 9), [1, 2, 2, 2, 2, 2])
    week(con, gid, sid, WEEK, [0, 2, 2, 2, 2, 2])
    hints.evaluate_group(con, gid, ON)
    assert "homework" in rules_of(con, gid)
    assert "Домашка проседает\nПочему: недели: 09.11–14.11, 16.11–21.11" in text(con, gid)


def test_sharp_drop(con):
    _, gid, sid = setup(con)
    for i, monday in enumerate([dt.date(2026, 10, 26), dt.date(2026, 11, 2), dt.date(2026, 11, 9)]):
        week(con, gid, sid, monday, [2, 2, 2, 2, 3, 2])
    week(con, gid, sid, WEEK, [2, 2, 2, 2, 1, 2])
    hints.evaluate_group(con, gid, ON)
    assert rules_of(con, gid) == ["drop:speaking"]
    assert "Резкий спад: говорение\nПочему: в среднем было 3, стало 1" in text(con, gid).replace("3,0", "3")


def test_exam_risk(con):
    _, gid, sid = setup(con, start=dt.date(2026, 10, 7))  # экзамен 7 декабря
    repo.set_stage_scores(con, ACTOR, repo.stage_by_code(con, "en", "a1")["id"], 70, 100)
    week(con, gid, sid, dt.date(2026, 11, 9), [2, 2, 1, 1, 2, 2])
    week(con, gid, sid, WEEK, [2, 2, 1, 1, 2, 2])
    hints.evaluate_group(con, gid, ON)
    assert "exam_risk" in rules_of(con, gid)
    assert "экзамен 7 декабря, уровень 56% при проходном 70%" in text(con, gid)
    # за 5 недель до экзамена — рано
    assert "exam_risk" not in hints.check_student(con, sid, repo.group(con, gid), dt.date(2026, 11, 2))


def test_growth(con):
    _, gid, sid = setup(con)
    for monday, v in zip([dt.date(2026, 10, 26), dt.date(2026, 11, 2), dt.date(2026, 11, 9), WEEK], [0, 1, 2, 3]):
        week(con, gid, sid, monday, [v] * 6)
    hints.evaluate_group(con, gid, ON)
    assert "growth" in rules_of(con, gid) and "🌟 Азиз Каримов — Похвалите" in text(con, gid)


def test_stale_reports_do_not_fire(con):
    _, gid, sid = setup(con)
    week(con, gid, sid, dt.date(2026, 10, 19), [0, 2, 2, 2, 2, 2])
    week(con, gid, sid, dt.date(2026, 10, 26), [0, 2, 2, 2, 2, 2])
    hints.evaluate_group(con, gid, ON)
    assert rules_of(con, gid) == []


def test_lifecycle_no_repeat_until_closed_or_condition_gone(con):
    tid, gid, sid = setup(con)
    att(con, gid, sid, [("2026-11-12", "absent"), ("2026-11-14", "absent")])
    assert hints.evaluate_group(con, gid, ON) == 1
    assert hints.evaluate_group(con, gid, ON) == 0          # открыта — не повторяется
    hint_id = hints.open_hints(con, gid)[0]["id"]
    other_teacher = make_teacher(con, 600777, "Другой Учитель")
    assert not hints.close(con, hint_id, other_teacher)     # чужой учитель закрыть не может
    assert hints.close(con, hint_id, tid)
    assert hints.evaluate_group(con, gid, ON) == 0          # закрыта, условие ещё есть — не повторяется
    assert rules_of(con, gid) == []
    att(con, gid, sid, [("2026-11-17", "present")])         # условие исчезло
    hints.evaluate_group(con, gid, ON)
    att(con, gid, sid, [("2026-11-19", "absent"), ("2026-11-20", "absent")])  # и появилось снова
    assert hints.evaluate_group(con, gid, ON) == 1
    assert con.execute("SELECT count(*) FROM hints").fetchone()[0] == 2


def test_hint_closes_itself_when_condition_disappears(con):
    _, gid, sid = setup(con)
    att(con, gid, sid, [("2026-11-12", "absent"), ("2026-11-14", "absent")])
    hints.evaluate_group(con, gid, ON)
    att(con, gid, sid, [("2026-11-14", "excused")])         # учитель исправил отметку
    hints.evaluate_group(con, gid, ON)
    assert rules_of(con, gid) == []


def test_uzbek_text(con):
    _, gid, sid = setup(con)
    att(con, gid, sid, [("2026-11-12", "absent"), ("2026-11-14", "absent")])
    hints.evaluate_group(con, gid, ON)
    h = hints.open_hints(con, gid)[0]
    assert "Ota-ona bilan bogʻlaning\nSababi: kelmagan kunlar: 12-noyabr va 14-noyabr" in hints.describe(con, h, "uz")
