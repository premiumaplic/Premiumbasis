"""Карточка для родителя: данные, вывод, скорость и размер. Данные выдуманные."""

import datetime as dt
import io
import time

from PIL import Image

from bot import card, repo, reports
from tests.conftest import ACTOR, make_group, make_teacher

WEEKS = [dt.date(2026, 10, 26), dt.date(2026, 11, 2), dt.date(2026, 11, 9), dt.date(2026, 11, 16)]
ON = dt.date(2026, 11, 20)


def setup(con, lang="ru", name="Мухаммадали Каримов", comment="", subject="en"):
    tid = make_teacher(con)
    gid = make_group(con, teacher_id=tid, subject=subject, stage="a1" if subject == "en" else None,
                     start=dt.date(2026, 10, 15))
    sid = repo.add_student(con, ACTOR, name, lang, True, gid, dt.date(2026, 10, 15))
    q = [x["id"] for x in reports.questions_for(con, subject)]
    levels = [[1, 1, 1, 0, 1, 2], [1, 2, 1, 1, 1, 2], [2, 2, 2, 1, 2, 2], [3, 2, 3, 1, 3, 2]]
    for w, lv in zip(WEEKS, levels):
        reports.save_weekly(con, 1, gid, w, sid, dict(zip(q, lv)), comment if w == WEEKS[-1] else "")
    for i in range(13):
        reports.save_attendance(con, 1, gid, dt.date(2026, 10, 23) + dt.timedelta(days=2 * i),
                                [(sid, "late" if i == 4 else "absent" if i == 9 else "present")])
    return sid, gid


def test_collect_ru(con):
    sid, gid = setup(con)
    data = card.collect(con, sid, gid, WEEKS[-1], ON)
    assert (data.att_attended, data.att_total, data.att_late) == (12, 13, 1)
    assert data.summary == ("Посещаемость хорошая. Сильная сторона — домашнее задание. "
                            "Над чем работать — грамматика темы.")
    assert data.praise == "Молодец! Результаты растут 3 недели подряд."
    assert data.metrics[0].arrow == 1 and data.metrics[1].arrow == 0
    assert data.stage_name == "Курс A1" and data.week_line == "неделя 6 из 8"
    assert data.next_exam_line == "Следующий экзамен: 15 декабря"
    assert data.finish_line == "Прогноз финиша: Курс B2 — июнь 2027, дальше — CEFR или IELTS"
    assert data.status == "on_plan"


def test_collect_uz_and_no_report(con):
    sid, gid = setup(con, lang="uz", name="Shahzoda Nurmatova")
    data = card.collect(con, sid, gid, WEEKS[-1], ON)
    assert data.metrics[0].label == "Uy vazifasi" and data.summary.startswith("Davomat yaxshi.")
    assert data.week_text == "16–21-noyabr"
    assert card.collect(con, sid, gid, dt.date(2026, 11, 23), ON) is None


def test_exam_risk_status(con):
    sid, gid = setup(con)
    repo.set_stage_scores(con, ACTOR, repo.stage_by_code(con, "en", "a1")["id"], 90, 100)
    data = card.collect(con, sid, gid, WEEKS[-1], dt.date(2026, 12, 1))  # 2 недели до экзамена
    assert data.status == "risk"


def test_render_fast_and_fits(con):
    for lang, name in (("ru", "Абдурахмонова Шахзода Ильхомжоновна"), ("uz", "Oʻgʻiloy Gʻulomova")):
        sid, gid = setup(con, lang=lang, name=name, comment="ж" * 80)
        data = card.collect(con, sid, gid, WEEKS[-1], ON)
        started = time.perf_counter()
        png = card.render(data)
        assert time.perf_counter() - started < 2.0
        assert card.render.last_height <= card.H - 16
        assert Image.open(io.BytesIO(png)).size == (1080, 1350)


def test_card_without_map(con):
    sid, gid = setup(con, subject="math")
    data = card.collect(con, sid, gid, WEEKS[-1], ON)
    assert data.view is None and data.week_line.startswith("неделя") and len(data.metrics) == 4
    card.render(data)


def test_card_has_only_this_student(con):
    sid, gid = setup(con)
    other = repo.add_student(con, ACTOR, "Чужой Ученик", "ru", True, gid, dt.date(2026, 10, 15))
    reports.save_weekly(con, 1, gid, WEEKS[-1], other, {1: 0}, "секрет другого")
    data = card.collect(con, sid, gid, WEEKS[-1], ON)
    assert "Чужой" not in repr(data) and "секрет" not in repr(data)


def test_old_cards_are_removed(tmp_path):
    old = dt.date(2026, 8, 3)
    card.save(b"png", tmp_path, old, 1, 1)
    card.save(b"png", tmp_path, WEEKS[-1], 1, 1)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["2026-11-16"]
