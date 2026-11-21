"""Карта, прогноз финиша и экзамены. Данные выдуманные."""

import datetime as dt
import json
import uuid

from bot import exams, forms, progress, repo
from tests.conftest import ACTOR, make_group, make_teacher

D = dt.date
START = D(2026, 9, 1)            # экзамены группы: 1 ноября, 1 января, 1 марта...
ON = D(2026, 10, 20)


def stage(con, code):
    return repo.stage_by_code(con, "en", code)


def student_in(con, stage_code="a1", start=START, scores=True):
    tid = make_teacher(con)
    gid = make_group(con, teacher_id=tid, stage=stage_code, start=start)
    if scores:
        for code in ("a1", "a2", "b1", "b2"):
            repo.set_stage_scores(con, ACTOR, stage(con, code)["id"], 60, 100)
    sid = repo.add_student(con, ACTOR, "Азиз Каримов", "ru", True, gid, start)
    return repo.teacher(con, tid), repo.group(con, gid), sid


def finishes(view):
    return {n.name_ru: (n.finish, n.finish_max, n.state) for n in view.nodes}


def test_route_and_next_stage(con):
    names = [s["name_ru"] for s in progress.route(con, "en", None)]
    assert names == ["Starter", "Roundup 1", "Roundup 2", "Roundup 3", "Roundup 4",
                     "Курс A1", "Курс A2", "Курс B1", "Курс B2"]
    assert [s["name_ru"] for s in progress.route(con, "en", "ielts")][-2:] == ["Pre-IELTS", "IELTS"]
    assert progress.next_stage(con, stage(con, "roundup4"))["code"] == "a1"
    assert progress.next_stage(con, stage(con, "b2")) is None                    # развилка
    assert progress.next_stage(con, stage(con, "b2"), "cefr")["code"] == "precefr"
    assert progress.next_stage(con, stage(con, "preielts"))["code"] == "ielts"
    assert progress.next_stage(con, stage(con, "ielts")) is None
    assert progress.is_fork(con, stage(con, "b2")) and not progress.is_fork(con, stage(con, "b1"))


def test_forecast_by_group_exam_calendar(con):
    _, g, sid = student_in(con)
    view = progress.build(con, sid, g, ON)
    f = finishes(view)
    assert f["Курс A1"] == (D(2026, 11, 1), None, "current")
    assert f["Курс B2"][0] == D(2027, 5, 1)
    assert "Starter" not in f                       # ученик начал с A1 — детские станции не показываются
    assert view.week == 8 and view.weeks_total == 8 and view.next_exam == D(2026, 11, 1)
    assert [n.state for n in view.nodes][-4:] == ["grey"] * 4   # путь после B2 не выбран — ветки серые


def test_failed_exam_shifts_forecast_by_two_months(con):
    teacher, g, sid = student_in(con)
    before = finishes(progress.build(con, sid, g, D(2026, 11, 1)))
    assert before["Курс B2"][0] == D(2027, 5, 1)
    res = forms.process(con, teacher, teacher["tg_id"], json.dumps(
        {"v": 1, "u": str(uuid.uuid4()), "t": "ex", "g": g["id"], "s": g["stage_id"],
         "r": [[sid, 40, 0, "", ""]]}), dt.datetime(2026, 11, 1, 8, tzinfo=dt.timezone.utc),
        dt.datetime(2026, 11, 1, 8, tzinfo=dt.timezone.utc))
    assert "повтор 1" in res.text
    after = finishes(progress.build(con, sid, repo.group(con, g["id"]), D(2026, 11, 1)))
    assert after["Курс A1"][0] == D(2027, 1, 1)
    assert after["Курс B2"][0] == D(2027, 7, 1)     # вся линия сдвинулась на 2 месяца


def test_roundup_has_no_date(con):
    _, g, sid = student_in(con, stage_code="roundup2")
    f = finishes(progress.build(con, sid, g, ON))
    assert f["Roundup 2"][0] is None and f["Курс A1"][0] is None
    view = progress.build(con, sid, g, ON)
    assert view.current.by_teacher


def test_cefr_range(con):
    _, g, sid = student_in(con, stage_code="b2")
    repo.set_student_stage(con, ACTOR, sid, stage(con, "precefr")["id"], D(2026, 10, 1))
    f = finishes(progress.build(con, sid, repo.group(con, g["id"]), ON))
    assert f["Pre-CEFR"][0] == D(2026, 12, 1)
    assert f["CEFR"][:2] == (D(2027, 3, 1), D(2027, 5, 1))   # 3–5 месяцев


def exam(con, teacher, g, rows, when=dt.datetime(2026, 11, 1, 8, tzinfo=dt.timezone.utc), s=None):
    return forms.process(con, teacher, teacher["tg_id"], json.dumps(
        {"v": 1, "u": str(uuid.uuid4()), "t": "ex", "g": g["id"], "s": s or g["stage_id"], "r": rows},
        ensure_ascii=False), when, when)


def test_exam_pass_moves_student_and_group(con):
    teacher, g, sid = student_in(con)
    res = exam(con, teacher, g, [[sid, 75, 1, "", ""]])
    assert "сдали 1, повтор 0" in res.text and "Группа переходит на станцию Курс A2" in res.text
    assert repo.current_stage(con, sid, "en")["code"] == "a2"
    assert repo.group(con, g["id"])["stage_code"] == "a2"
    assert con.execute("SELECT decision FROM exam_results").fetchone()[0] == "pass"


def test_exam_override_needs_reason_and_correction_same_day(con):
    teacher, g, sid = student_in(con)
    other = repo.add_student(con, ACTOR, "Мадина Юсупова", "ru", True, g["id"], START)
    assert "укажите причину" in exam(con, teacher, g, [[sid, 75, 0, "", ""]]).text
    exam(con, teacher, g, [[sid, 75, 1, "", ""], [other, 70, 1, "", ""]])
    assert repo.current_stage(con, sid, "en")["code"] == "a2"
    # учитель исправил решение в тот же день: Азиз остаётся на повтор
    res = exam(con, teacher, repo.group(con, g["id"]), [[sid, 75, 0, "болел на устной части", ""]],
               s=stage(con, "a1")["id"])
    assert "Сохранено" in res.text, res.text
    assert repo.current_stage(con, sid, "en")["code"] == "a1"
    assert con.execute("SELECT count(*) FROM exams").fetchone()[0] == 1
    assert con.execute("SELECT reason FROM exam_results WHERE student_id = ?", (sid,)).fetchone()[0] == \
        "болел на устной части"


def test_exam_requires_scores(con):
    teacher, g, sid = student_in(con, scores=False)
    assert "не задал проходной" in exam(con, teacher, g, [[sid, 75, 1, "", ""]]).text
    payload = forms.exam_payload(con, g, "ru", ON)
    assert payload["pass"] is None and payload["mode"] == "score"


def test_fork_path_choice(con):
    teacher, g, sid = student_in(con, stage_code="b2")
    other = repo.add_student(con, ACTOR, "Мадина Юсупова", "ru", True, g["id"], START)
    res = exam(con, teacher, g, [[sid, 90, 1, "", "ielts"], [other, 90, 1, "", ""]])
    assert repo.current_stage(con, sid, "en")["code"] == "preielts"
    assert repo.current_stage(con, other, "en")["code"] == "b2"
    assert "путь не выбран: Мадина Ю." in res.text
    assert repo.group(con, g["id"])["stage_code"] == "b2"      # группа на развилке сама не переходит


def test_teacher_decision_on_roundup(con):
    teacher, g, sid = student_in(con, stage_code="roundup4")
    payload = forms.exam_payload(con, g, "ru", ON)
    assert payload["mode"] == "teacher" and payload["nx"] == "Курс A1"
    res = exam(con, teacher, g, [[sid, None, 1, "", ""]])
    assert "переходят 1, остаются 0" in res.text
    assert repo.current_stage(con, sid, "en")["code"] == "a1"
    assert con.execute("SELECT count(*) FROM exams").fetchone()[0] == 0


def test_exam_rejects_bad_scores_and_foreign(con):
    teacher, g, sid = student_in(con)
    assert "повреждены" in exam(con, teacher, g, [[sid, 150, 1, "", ""]]).text
    other = make_group(con, "11-Б")
    stranger = repo.add_student(con, ACTOR, "Чужой Ученик", "ru", True, other, START)
    assert "Форма не сохранена" in exam(con, teacher, g, [[stranger, 70, 1, "", ""]]).text
    assert exams.auto_decision(60, 60) == "pass" and exams.auto_decision(59.5, 60) == "repeat"


def test_jump_from_roundup3_to_a1_skips_stations_and_restarts_exam_calendar(con):
    teacher, g, sid = student_in(con, stage_code="roundup3")
    other = repo.add_student(con, ACTOR, "Мадина Юсупова", "ru", True, g["id"], START)
    ahead = repo.add_student(con, ACTOR, "Жасур Ахмедов", "ru", True, g["id"], START)
    repo.move_station(con, ACTOR, ahead, stage(con, "a2")["id"], START)        # особый случай — не трогаем
    moved = repo.move_group_station(con, ACTOR, g["id"], stage(con, "a1")["id"], D(2026, 11, 20))
    assert sorted(moved) == sorted([sid, other])
    assert repo.current_stage(con, ahead, "en")["code"] == "a2"
    g = repo.group(con, g["id"])
    assert g["stage_code"] == "a1" and g["stage_start"] == "2026-11-20"
    view = progress.build(con, sid, g, D(2026, 11, 20))
    names = [n.name_ru for n in view.nodes if n.state != "grey"]
    assert "Roundup 4" not in names and names[:2] == ["Roundup 3", "Курс A1"]   # пропущенная станция убрана
    assert view.next_exam == D(2027, 1, 20)      # экзамены A1 — каждые 2 месяца с дня перевода
    assert view.week == 1


def test_teacher_moves_student_back(con):
    teacher, g, sid = student_in(con, stage_code="a2")
    assert repo.move_station(con, ACTOR, sid, stage(con, "a1")["id"], ON)
    assert not repo.move_station(con, ACTOR, sid, stage(con, "a1")["id"], ON)  # уже там
    statuses = [r["status"] for r in con.execute("SELECT status FROM student_stage WHERE student_id = ? ORDER BY id",
                                                 (sid,))]
    assert statuses == ["left", "current"]       # назад: прежняя станция «оставлена», не «пройдена»


def test_group_does_not_advance_on_partial_scores(con):
    teacher, g, sid = student_in(con)
    others = [repo.add_student(con, ACTOR, f"Ученик{i} Тестов", "ru", True, g["id"], START) for i in range(3)]
    res = exam(con, teacher, g, [[sid, 90, 1, "", ""]])            # введён балл только одного из четырёх
    assert "Группа переходит" not in res.text and repo.group(con, g["id"])["stage_code"] == "a1"
    res = exam(con, teacher, g, [[others[0], 80, 1, "", ""]])       # теперь сдали двое из четырёх
    assert "Группа переходит на станцию Курс A2" in res.text
