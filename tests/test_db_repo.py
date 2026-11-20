"""База, миграции и операции с учителями, группами, учениками."""

import datetime as dt

import pytest

from bot import db, repo
from tests.conftest import ACTOR, make_group, make_teacher

D = dt.date(2026, 11, 20)


def test_migrations_apply_once(con):
    assert db.schema_version(con) == len(db.migrations())
    assert db.migrate(con) == []
    assert len(repo.list_subjects(con)) == 5
    assert repo.get_setting(con, "reminder_time") == "18:00"


def test_seed_matches_spec(con):
    codes = [s["code"] for s in repo.list_stages(con, "en")]
    assert codes[:9] == ["starter", "roundup1", "roundup2", "roundup3", "roundup4", "a1", "a2", "b1", "b2"]
    a1 = repo.stage_by_code(con, "en", "A1")
    assert a1["exam_transition"] == 1 and a1["months"] == 2 and a1["name_ru"] == "Курс A1"
    assert repo.stage_by_code(con, "en", "roundup2")["months"] is None
    cefr = repo.stage_by_code(con, "en", "cefr")
    assert (cefr["months"], cefr["months_max"]) == (3, 5)
    # вопросы: языки 1–6, математика 1, 2, 7, 6
    rows = con.execute("SELECT subjects, text_ru FROM questions ORDER BY sort").fetchall()
    lang = [r["text_ru"] for r in rows if r["subjects"] == "*" or "en" in r["subjects"].split(",")]
    math = [r["text_ru"] for r in rows if r["subjects"] == "*" or "math" in r["subjects"].split(",")]
    assert lang == ["Домашнее задание", "Работа на уроке", "Новые слова", "Грамматика темы", "Говорение", "Дисциплина"]
    assert math == ["Домашнее задание", "Работа на уроке", "Понимание темы", "Дисциплина"]
    uz = con.execute("SELECT opt1_uz, uz_checked FROM questions WHERE sort = 20").fetchone()
    assert uz["opt1_uz"] == "soʻralganda javob beradi" and uz["uz_checked"] == 0  # черновик


def test_tx_rolls_back(con):
    with pytest.raises(RuntimeError):
        with db.tx(con):
            make_teacher(con)
            raise RuntimeError("сбой")
    assert repo.list_teachers(con) == []


def test_local_copy(tmp_path):
    con = db.connect(tmp_path / "school.db")
    db.migrate(con)
    make_teacher(con)
    copy = db.local_copy(con, tmp_path / "backups", "test")
    other = db.connect(copy)
    assert len(repo.list_teachers(other)) == 1


def test_teacher_save_updates_by_tg(con):
    tid, created = repo.save_teacher(con, ACTOR, 600001, "Учитель Один", "ru")
    tid2, created2 = repo.save_teacher(con, ACTOR, 600001, "Учитель Один", "uz")
    assert created and not created2 and tid == tid2
    assert repo.teacher(con, tid)["lang"] == "uz"
    assert con.execute("SELECT count(*) FROM audit_log").fetchone()[0] == 2


def test_new_student_gets_group_stage(con):
    gid = make_group(con, stage="a2")
    sid = repo.add_student(con, ACTOR, "Азиз  Каримов", "uz", True, gid, D)
    assert repo.student(con, sid)["full_name"] == "Азиз Каримов"
    assert repo.current_stage(con, sid, "en")["code"] == "a2"
    assert repo.group(con, gid)["student_count"] == 1


def test_student_explicit_stage_and_non_map_subject(con):
    gid = make_group(con, stage="a1")
    sid = repo.add_student(con, ACTOR, "Мадина Юсупова", "ru", False, gid, D,
                           repo.stage_by_code(con, "en", "b1")["id"])
    assert repo.current_stage(con, sid, "en")["code"] == "b1"
    math = make_group(con, name="М-1", subject="math", stage=None)
    sid2 = repo.add_student(con, ACTOR, "Тимур Ахмедов", "ru", True, math, D)
    assert con.execute("SELECT count(*) FROM student_stage WHERE student_id = ?", (sid2,)).fetchone()[0] == 0


def test_transfer_keeps_history(con):
    g1, g2 = make_group(con, "10-А"), make_group(con, "10-Б", stage="a2")
    sid = repo.add_student(con, ACTOR, "Лола Рахимова", "ru", True, g1, D)
    repo.transfer_student(con, ACTOR, sid, g1, g2, D + dt.timedelta(days=7))
    hist = con.execute("SELECT group_id, date_from, date_to FROM enrollments WHERE student_id = ? ORDER BY id",
                       (sid,)).fetchall()
    assert [tuple(r) for r in hist] == [(g1, "2026-11-20", "2026-11-27"), (g2, "2026-11-27", None)]
    assert [s["id"] for s in repo.group_students(con, g2)] == [sid]
    assert repo.group_students(con, g1) == []
    # станция ученика при переводе сама не меняется
    assert repo.current_stage(con, sid, "en")["code"] == "a1"


def test_set_stage_and_path(con):
    gid = make_group(con)
    sid = repo.add_student(con, ACTOR, "Шахзода Нурматова", "ru", True, gid, D)
    repo.set_student_stage(con, ACTOR, sid, repo.stage_by_code(con, "en", "preielts")["id"], D)
    cur = repo.current_stage(con, sid, "en")
    assert cur["code"] == "preielts" and cur["path"] == "ielts"
    assert con.execute("SELECT count(*) FROM student_stage WHERE student_id = ? AND status = 'current'",
                       (sid,)).fetchone()[0] == 1


def test_archive(con):
    gid = make_group(con)
    sid = repo.add_student(con, ACTOR, "Бехруз Олимов", "ru", True, gid, D)
    repo.archive_student(con, ACTOR, sid, D)
    assert repo.group_students(con, gid) == []
    assert repo.find_students(con, "бех") == []
    sid2 = repo.add_student(con, ACTOR, "Севара Каримова", "ru", True, gid, D)
    repo.archive_group(con, ACTOR, gid, D)
    assert repo.list_groups(con) == [] and repo.student_groups(con, sid2) == []


def test_find_is_case_insensitive_for_cyrillic(con):
    gid = make_group(con)
    repo.add_student(con, ACTOR, "Отабек Саидов", "ru", True, gid, D)
    assert len(repo.find_students(con, "отаБЕК")) == 1


def test_short_name():
    assert repo.short_name("Азиз Каримов") == "Азиз К."
    assert repo.short_name("Азиз") == "Азиз"


def test_teacher_groups_only_own(con):
    t1, t2 = make_teacher(con, 600001), make_teacher(con, 600002, "Учитель Два")
    make_group(con, "10-А", teacher_id=t1)
    make_group(con, "11-Б", teacher_id=t2)
    assert [g["name"] for g in repo.list_groups(con, teacher_id=t1)] == ["10-А"]
