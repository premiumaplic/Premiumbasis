"""Навыки и темы ученика, саппорт-учитель. Все данные выдуманные."""

import datetime as dt
import json
import uuid

from bot import forms, hints, hub, profiles, repo
from bot.config import Config
from bot.payload import decode_param
from tests.conftest import ACTOR, make_group, make_teacher

NOW = dt.datetime(2026, 11, 20, 10, 0, tzinfo=dt.timezone.utc)
TODAY = dt.date(2026, 11, 20)


def setup(con, n=3, subject="en"):
    tid = make_teacher(con, 600001)
    gid = make_group(con, subject=subject, teacher_id=tid, stage="a1" if subject == "en" else None)
    sids = [repo.add_student(con, ACTOR, f"Ученик{i} Тестов", "ru", True, gid, TODAY) for i in range(n)]
    return repo.teacher(con, tid), repo.group(con, gid), sids


def send(con, teacher, payload, now=NOW):
    payload = {"v": 1, "u": str(uuid.uuid4()), **payload}
    return forms.process(con, teacher, teacher["tg_id"], json.dumps(payload, ensure_ascii=False), now, now)


def cids(con, g):
    return [c["id"] for c in profiles.criteria_for(con, g["subject"])]


def test_six_language_criteria_and_math_criteria(con):
    names = [c["name_ru"] for c in profiles.criteria_for(con, "en")]
    assert len(names) == 6
    for word in ("Listening", "Reading", "Writing", "Speaking", "Grammar", "Vocabulary"):
        assert any(word in n for n in names), word
    assert len(profiles.criteria_for(con, "math")) == 6
    assert not set(cids_math := [c["id"] for c in profiles.criteria_for(con, "math")]) & {
        c["id"] for c in profiles.criteria_for(con, "en")}, cids_math


def test_save_ratings_and_topics(con):
    teacher, g, sids = setup(con)
    c = cids(con, g)
    res = send(con, teacher, {"t": "pf", "g": g["id"], "c": c, "r": [
        [sids[0], [7, 8, 6, 9, 5, 0], ["Present Simple", "Food"], ["Past Simple"], []],
        [sids[1], None, ["Present Simple"], [], []]]})
    assert res.text.startswith("Сохранено: навыки и темы 10-А — учеников: 2 (оценки: 1, изменений тем: 4)")
    last = profiles.latest_ratings(con, [sids[0]], "en")[sids[0]][0]
    assert last["v"] == dict(zip(c[:5], [7, 8, 6, 9, 5])) and last["on"] == "2026-11-20"
    assert profiles.overall(last["v"]) == 7.0
    tp = profiles.topics_of(con, [sids[0]], "en")[sids[0]]
    assert sorted(tp["learned"]) == ["Food", "Present Simple"] and tp["unclear"] == ["Past Simple"]
    # тема меняет статус, а «убрать» удаляет (без учёта регистра)
    send(con, teacher, {"t": "pf", "g": g["id"], "c": c, "r": [[sids[0], None, ["past simple"], [], ["FOOD"]]]})
    tp = profiles.topics_of(con, [sids[0]], "en")[sids[0]]
    assert tp == {"learned": ["Past Simple", "Present Simple"], "unclear": []} or \
        sorted(tp["learned"]) == ["Past Simple", "Present Simple"]
    # вторая оценка в тот же день меняет только присланные критерии, в другой день — новая запись
    send(con, teacher, {"t": "pf", "g": g["id"], "c": c, "r": [[sids[0], [0, 0, 0, 0, 0, 4], [], [], []]]})
    assert con.execute("SELECT count(*) FROM assessments").fetchone()[0] == 1
    later = NOW + dt.timedelta(days=3)
    send(con, teacher, {"t": "pf", "g": g["id"], "c": c, "r": [[sids[0], [9, 9, 9, 9, 9, 9], [], [], []]]}, later)
    items = profiles.latest_ratings(con, [sids[0]], "en")[sids[0]]
    assert len(items) == 2 and items[0]["v"][c[0]] == 9 and items[1]["v"][c[5]] == 4


def test_profile_form_is_validated(con):
    teacher, g, sids = setup(con)
    c = cids(con, g)
    bad = [
        {"c": c[:-1], "r": [[sids[0], [5] * 5, [], [], []]]},           # критерии не совпадают
        {"c": c, "r": [[sids[0], [11, 1, 1, 1, 1, 1], [], [], []]]},     # больше 10
        {"c": c, "r": [[sids[0], [0] * 6, [], [], []]]},                 # пустая оценка
        {"c": c, "r": [[sids[0], [True, 1, 1, 1, 1, 1], [], [], []]]},   # не число
        {"c": c, "r": [[sids[0], None, [], [], []]]},                    # ничего не меняет
        {"c": c, "r": [[sids[0], None, ["x" * 61], [], []]]},            # длинная тема
        {"c": c, "r": [[sids[0], None, ["Тема"], ["тема"], []]]},        # одна тема дважды
        {"c": c, "r": [[sids[0], None, [" "], [], []]]},                 # пустая тема
        {"c": c, "r": [[sids[0], None, [], []]]},                        # не та длина строки
    ]
    for body in bad:
        res = send(con, teacher, {"t": "pf", "g": g["id"], **body})
        assert "Форма не сохранена" in res.text, body
    assert "критерии оценки изменились" in send(con, teacher, {"t": "pf", "g": g["id"], **bad[0]}).text
    assert con.execute("SELECT count(*) FROM assessments").fetchone()[0] == 0
    assert con.execute("SELECT count(*) FROM student_topics").fetchone()[0] == 0
    # чужой ученик отбрасывается
    other = make_group(con, "11-Б")
    stranger = repo.add_student(con, ACTOR, "Чужой Ученик", "ru", True, other, TODAY)
    res = send(con, teacher, {"t": "pf", "g": g["id"], "c": c, "r": [[stranger, None, ["Тема"], [], []]]})
    assert "ни один ученик" in res.text


def test_topic_limit_rolls_back(con):
    teacher, g, sids = setup(con, 1)
    c = cids(con, g)
    for k in range(2):
        send(con, teacher, {"t": "pf", "g": g["id"], "c": c,
                            "r": [[sids[0], None, [f"Тема {k}-{i}" for i in range(30)], [], []]]})
    assert profiles.topic_count(con, sids[0], "en") == 60
    res = send(con, teacher, {"t": "pf", "g": g["id"], "c": c, "r": [[sids[0], [5] * 6, ["Ещё одна"], [], []]]})
    assert "слишком много тем" in res.text
    assert profiles.topic_count(con, sids[0], "en") == 60
    assert con.execute("SELECT count(*) FROM assessments").fetchone()[0] == 0   # откат всей формы


def test_unclear_topics_hint(con):
    teacher, g, sids = setup(con, 1)
    c = cids(con, g)
    res = send(con, teacher, {"t": "pf", "g": g["id"], "c": c,
                              "r": [[sids[0], None, [], ["Артикли", "Past Simple", "Предлоги"], []]]})
    assert "подсказ" in res.text.lower()
    h = hints.open_hints(con, g["id"])[0]
    title, why = hints.parts(con, h, "ru")
    assert title == "Повторите непонятные темы" and "Артикли" in why


def test_topic_form_logs_lesson_topics(con):
    teacher, g, sids = setup(con, 1)
    for text in ("Present Simple", "Food", "present simple"):
        send(con, teacher, {"t": "tp", "g": g["id"], "text": text})
    assert profiles.topic_log(con, g["id"]) == ["present simple", "Food"]


def test_hub_payload_has_skills_and_fits(con):
    teacher, g, sids = setup(con, 25)
    c = cids(con, g)
    long_topics = [f"Unit {i}. Очень длинное название темы урока номер {i}" for i in range(20)]
    for sid in sids:
        send(con, teacher, {"t": "pf", "g": g["id"], "c": c, "r": [[sid, [7, 6, 5, 8, 6, 7], long_topics, [], []]]})
        send(con, teacher, {"t": "pf", "g": g["id"], "c": c,
                            "r": [[sid, None, [f"Своя тема {sid}-{i}" for i in range(20)], [], []]]})
    data = hub.payload(con, g, "ru", TODAY, teacher)
    assert [x[0] for x in data["cr"]] == c and len(data["pf"]) == 25
    rec = data["pf"][str(sids[0])]
    assert rec[0] == [7, 6, 5, 8, 6, 7] and rec[2] == "2026-11-20" and rec[3] == "Учитель Т."
    assert rec[6] == [40, 0] and data["rl"] == 0
    conf = Config(token="x", owner_id=1, backup_channel_id=None, forms_url="https://example.github.io/Premiumbasis/")
    link = hub.url(con, conf, g, "ru", TODAY, teacher)
    assert link is not None and len(link) <= hub.HUB_LIMIT
    back = decode_param(link.split("#d=", 1)[1])
    assert back["pf"][str(sids[0])][6] == [40, 0]     # счётчики остаются, даже если списки урезаны


def test_support_teacher_works_in_any_group(con):
    teacher, g, sids = setup(con, 2)
    sup_id = make_teacher(con, 600009, "Саппорт Учитель")
    sup = repo.teacher(con, sup_id)
    c = cids(con, g)
    body = {"t": "pf", "g": g["id"], "c": c, "r": [[sids[0], [6] * 6, [], [], []]]}
    assert "эта группа вам не назначена" in send(con, sup, dict(body)).text
    repo.set_teacher_role(con, ACTOR, sup_id, "support")
    sup = repo.teacher(con, sup_id)
    assert repo.is_support(sup) and repo.can_teach(sup, g) and not repo.can_teach(teacher, repo.group(con, make_group(con, "Чужая")))
    assert "Сохранено" in send(con, sup, dict(body)).text
    rec = hub.payload(con, g, "ru", TODAY, sup)
    assert rec["rl"] == 1 and rec["tn"] == "Учитель Т." and rec["pf"][str(sids[0])][3] == "Саппорт У."
    # архивная группа — нельзя даже саппорту
    repo.archive_group(con, ACTOR, g["id"], TODAY)
    assert "не назначена" in send(con, sup, dict(body)).text


def test_cyrillic_topics_match_without_case(con):
    teacher, g, sids = setup(con, 1)
    c = cids(con, g)
    send(con, teacher, {"t": "pf", "g": g["id"], "c": c, "r": [[sids[0], None, ["Артикли"], [], []]]})
    send(con, teacher, {"t": "pf", "g": g["id"], "c": c, "r": [[sids[0], None, [], ["АРТИКЛИ"], []]]})
    assert profiles.topics_of(con, sids[0:1], "en")[sids[0]] == {"learned": [], "unclear": ["Артикли"]}
    send(con, teacher, {"t": "pf", "g": g["id"], "c": c, "r": [[sids[0], None, [], [], ["артикли"]]]})
    assert profiles.topic_count(con, sids[0], "en") == 0


def test_excel_keeps_formula_like_text_as_text(con):
    import io
    from openpyxl import load_workbook
    from bot import export
    teacher, g, sids = setup(con, 1)
    c = cids(con, g)
    send(con, teacher, {"t": "pf", "g": g["id"], "c": c, "r": [[sids[0], [5] * 6, ["=HYPERLINK(1)"], [], []]]})
    wb = load_workbook(io.BytesIO(export.weekly_xlsx(con, [g], [dt.date(2026, 11, 16)])))
    ws = wb["Навыки и темы"]
    cell = [x for x in ws[2] if x.value and "HYPERLINK" in str(x.value)][0]
    assert cell.data_type == "s" and cell.value.startswith("'=")
