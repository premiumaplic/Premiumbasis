"""Приём данных форм: проверки, отсутствие дублей, чужие ученики, даты. Данные выдуманные."""

import datetime as dt
import json
import uuid

from bot import forms, repo, reports
from bot.payload import decode_param
from tests.conftest import ACTOR, make_group, make_teacher

NOW = dt.datetime(2026, 11, 20, 10, 0, tzinfo=dt.timezone.utc)   # пятница, 15:00 в Ташкенте
TODAY = dt.date(2026, 11, 20)
MONDAY = dt.date(2026, 11, 16)
NAMES = ["Азиз Каримов", "Мадина Юсупова", "Жасур Ахмедов", "Камила Рахимова", "Отабек Саидов",
         "Севара Олимова", "Тимур Назаров", "Лола Турсунова", "Бехруз Умаров", "Нигора Хасанова",
         "Ислом Мирзаев", "Зарина Валиева", "Шерзод Холматов", "Малика Собирова", "Ильхом Эргашев",
         "Дилноза Каримова", "Санжар Алиев", "Феруза Исмоилова", "Бобур Ташкентов", "Гулнора Азимова"]


def setup(con, n=15, lang="ru", attendance=True):
    if attendance:
        repo.set_setting(con, ACTOR, "attendance_on", "1")
    tid = make_teacher(con, 600001, lang=lang)
    gid = make_group(con, teacher_id=tid)
    sids = [repo.add_student(con, ACTOR, NAMES[i], "uz" if i % 2 else "ru", True, gid, TODAY) for i in range(n)]
    return repo.teacher(con, tid), repo.group(con, gid), sids


def send(con, teacher, payload, sent_at=NOW):
    payload.setdefault("u", str(uuid.uuid4()))
    payload.setdefault("v", 1)
    return forms.process(con, teacher, teacher["tg_id"], json.dumps(payload, ensure_ascii=False), sent_at, NOW)


def qids(con, g):
    return [q["id"] for q in reports.questions_for(con, g["subject"])]


def code(six: str) -> str:
    """Ответы на 6 обязательных вопросов английского -> строка формы (аудирование, чтение, письмо пропущены)."""
    return six[:5] + "---" + six[5:]


# ---------------------------------------------------------------- посещаемость

def test_attendance_saved_and_summary(con):
    teacher, g, sids = setup(con, 14)
    marks = [[sid, 1 if i < 2 else 0] for i, sid in enumerate(sids)]
    res = send(con, teacher, {"t": "att", "g": g["id"], "d": "2026-11-20", "m": marks})
    assert res.text == "Сохранено: посещаемость 10-А за 20.11 — 14 учеников, опозданий 2, пропусков 0."
    assert con.execute("SELECT count(*) FROM attendance").fetchone()[0] == 14


def test_resubmission_creates_no_duplicates(con):
    teacher, g, sids = setup(con, 3)
    payload = {"u": str(uuid.uuid4()), "t": "att", "g": g["id"], "d": "2026-11-20", "m": [[s, 0] for s in sids]}
    send(con, teacher, dict(payload))
    res = send(con, teacher, dict(payload))
    assert "уже были сохранены" in res.text
    # новая отправка за тот же день исправляет отметки, а не добавляет строки
    send(con, teacher, {"t": "att", "g": g["id"], "d": "2026-11-20", "m": [[sids[0], 2]]})
    assert con.execute("SELECT count(*) FROM attendance").fetchone()[0] == 3
    assert con.execute("SELECT status FROM attendance WHERE student_id = ?", (sids[0],)).fetchone()[0] == "absent"
    assert con.execute("SELECT count(*) FROM submissions").fetchone()[0] == 2


def test_attendance_dates(con):
    teacher, g, sids = setup(con, 2)
    for day, ok in (("2026-11-13", True), ("2026-11-12", False), ("2026-11-21", False)):
        res = send(con, teacher, {"t": "att", "g": g["id"], "d": day, "m": [[sids[0], 0]]})
        assert ("Сохранено" in res.text) == ok, day
    assert "не раньше чем 7 дней" in send(con, teacher, {"t": "att", "g": g["id"], "d": "2026-11-01",
                                                         "m": [[sids[0], 0]]}).text


def test_foreign_student_is_rejected(con):
    teacher, g, sids = setup(con, 2)
    other_group = make_group(con, "11-Б")
    stranger = repo.add_student(con, ACTOR, "Чужой Ученик", "ru", True, other_group, TODAY)
    res = send(con, teacher, {"t": "att", "g": g["id"], "d": "2026-11-20", "m": [[sids[0], 0], [stranger, 2]]})
    assert "Не сохранено для 1 учеников" in res.text
    assert con.execute("SELECT count(*) FROM attendance WHERE student_id = ?", (stranger,)).fetchone()[0] == 0
    res = send(con, teacher, {"t": "att", "g": g["id"], "d": "2026-11-20", "m": [[stranger, 2]]})
    assert "Форма не сохранена" in res.text


def test_foreign_group_is_rejected(con):
    teacher, g, sids = setup(con, 2)
    other_teacher = make_teacher(con, 600009, "Другой Учитель")
    foreign = make_group(con, "11-Б", teacher_id=other_teacher)
    res = send(con, teacher, {"t": "att", "g": foreign, "d": "2026-11-20", "m": [[sids[0], 0]]})
    assert "не назначена" in res.text


def test_bad_data_rejected(con):
    teacher, g, sids = setup(con, 1)
    bad = [
        "не json", json.dumps([1, 2]),
        json.dumps({"v": 1, "u": "abc", "t": "att", "g": g["id"]}),
        json.dumps({"v": 1, "u": str(uuid.uuid4()), "t": "att", "g": g["id"], "d": "2026-11-20", "m": [[sids[0], 7]]}),
        json.dumps({"v": 1, "u": str(uuid.uuid4()), "t": "att", "g": g["id"], "d": "2026-11-20",
                    "m": [[sids[0], 0], [sids[0], 1]]}),
        "x" * 5000,
    ]
    for raw in bad:
        assert "Форма не сохранена" in forms.process(con, teacher, 1, raw, NOW, NOW).text


def test_late_delivery_message(con):
    teacher, g, sids = setup(con, 1)
    res = send(con, teacher, {"t": "att", "g": g["id"], "d": "2026-11-19", "m": [[sids[0], 0]]},
               sent_at=dt.datetime(2026, 11, 19, 17, 40, tzinfo=dt.timezone.utc))
    assert res.text.startswith("Получено вчера в 22:40, сохранено.")


# ---------------------------------------------------------------- недельный отчёт

def test_weekly_saved_and_left_list(con):
    teacher, g, sids = setup(con, 3)
    rows = [[sids[0], code("321023"), "Молодец!"], [sids[1], code("000000"), ""]]
    res = send(con, teacher, {"t": "wk", "g": g["id"], "w": "2026-11-16", "q": qids(con, g), "r": rows})
    assert "недельный отчёт 10-А, неделя 16.11–21.11 — 2 учеников" in res.text
    assert "Ещё не заполнены (1)" in res.text
    saved = reports.reports_for_weeks(con, g["id"], [MONDAY])
    assert saved[sids[0]]["2026-11-16"]["comment"] == "Молодец!"
    assert list(saved[sids[0]]["2026-11-16"]["answers"].values()) == [3, 2, 1, 0, 2, 3]
    # повтор с пустым комментарием не стирает прежний и не плодит отчёты
    send(con, teacher, {"t": "wk", "g": g["id"], "w": "2026-11-16", "q": qids(con, g),
                        "r": [[sids[0], code("333333"), ""], [sids[2], code("111111"), ""]]})
    saved = reports.reports_for_weeks(con, g["id"], [MONDAY])
    assert saved[sids[0]]["2026-11-16"]["comment"] == "Молодец!"
    assert con.execute("SELECT count(*) FROM weekly_reports").fetchone()[0] == 3
    assert con.execute("SELECT count(*) FROM weekly_answers").fetchone()[0] == 18


def test_weekly_checks(con):
    teacher, g, sids = setup(con, 1)
    q = qids(con, g)
    cases = [
        ({"w": "2026-11-17", "q": q, "r": [[sids[0], code("000000"), ""]]}, "текущую или прошлую"),   # не понедельник
        ({"w": "2026-11-02", "q": q, "r": [[sids[0], code("000000"), ""]]}, "текущую или прошлую"),
        ({"w": "2026-11-16", "q": q[:-1], "r": [[sids[0], code("000000")[:-1], ""]]}, "вопросы недели изменились"),
        ({"w": "2026-11-16", "q": q, "r": [[sids[0], code("000004"), ""]]}, "повреждены"),
        ({"w": "2026-11-16", "q": q, "r": [[sids[0], code("000000"), "ж" * 81]]}, "повреждены"),
    ]
    for extra, reason in cases:
        res = send(con, teacher, {"t": "wk", "g": g["id"], **extra})
        assert reason in res.text, extra
    assert "Сохранено" in send(con, teacher, {"t": "wk", "g": g["id"], "w": "2026-11-09", "q": q,
                                               "r": [[sids[0], code("000000"), ""]]}).text


def test_math_has_its_own_questions(con):
    teacher, g, sids = setup(con, 1)
    math = make_group(con, "М-1", subject="math", teacher_id=teacher["id"], stage=None)
    assert len(qids(con, repo.group(con, math))) == 7
    texts = [q["text_ru"] for q in reports.questions_for(con, "math")]
    assert "Решение задач" in texts and "Новые слова" not in texts


# ---------------------------------------------------------------- тема

def test_topic(con):
    teacher, g, _ = setup(con, 1)
    res = send(con, teacher, {"t": "tp", "g": g["id"], "text": "  Present   Simple "})
    assert res.text == "Сохранено: тема 10-А — Present Simple"
    assert repo.group(con, g["id"])["current_topic"] == "Present Simple"
    con.execute("INSERT INTO topics (stage_id, unit_no, title) VALUES (?, 5, 'My day')", (g["stage_id"],))
    unit = con.execute("SELECT id FROM topics").fetchone()[0]
    send(con, teacher, {"t": "tp", "g": g["id"], "unit": unit})
    assert repo.group(con, g["id"])["current_topic"] == "Unit 5. My day"
    assert "Форма не сохранена" in send(con, teacher, {"t": "tp", "g": g["id"], "text": "ж" * 101}).text


# ---------------------------------------------------------------- ссылки форм

def test_payloads_fit_and_contain_minimum(con):
    teacher, g, sids = setup(con, 20)
    q = qids(con, g)
    send(con, teacher, {"t": "wk", "g": g["id"], "w": "2026-11-09", "q": q,
                        "r": [[s, code("321023"), "Комментарий для проверки длины"] for s in sids]})
    order = [s["id"] for s in repo.group_students(con, g["id"])]  # в форме ученики по алфавиту
    send(con, teacher, {"t": "att", "g": g["id"], "d": "2026-11-18", "m": [[s, i % 4] for i, s in enumerate(order)]})
    payload = forms.weekly_payload(con, g, "ru", TODAY)
    url = forms.form_url("https://premiumaplic.github.io/Premiumbasis/", "weekly", payload)
    assert len(url) < 2000, len(url)
    assert payload["st"][0][1] == "Азиз К."                 # только имя и первая буква фамилии
    assert len(payload["st"]) == 20
    assert "Каримов" not in json.dumps(payload, ensure_ascii=False)
    assert payload["a"][str(sids[0])]["1"] == "32102xxx3"  # прошлая неделя; x — вопрос пропущен
    att = forms.attendance_payload(con, g, "ru", TODAY)
    assert att["h"]["2"] == "01230123012301230123"
    assert decode_param(url.split("#d=")[1])["wk"] == "2026-11-16"


def test_big_group_is_split_into_parts(con):
    teacher, g, sids = setup(con, 20)
    urls = forms.split_urls("https://example.github.io/R/", "weekly",
                            lambda chunk: forms.weekly_payload(con, g, "ru", TODAY, chunk),
                            repo.group_students(con, g["id"]), 1600)
    assert len(urls) >= 2 and all(len(u) <= 1600 for u in urls)
    parts = [decode_param(u.split("#d=")[1]) for u in urls]
    assert sum(len(p["st"]) for p in parts) == 20 and parts[0]["part"] == [1, len(urls)]


def test_uzbek_teacher_gets_uzbek_texts(con):
    teacher, g, sids = setup(con, 1, lang="uz")
    payload = forms.weekly_payload(con, g, "uz", TODAY)
    assert payload["q"][0][1] == "Uy vazifasi"
    res = send(con, teacher, {"t": "att", "g": g["id"], "d": "2026-11-20", "m": [[sids[0], 0]]})
    assert res.text.startswith("Saqlandi")


def test_hub_payload_fits_and_is_minimal(con):
    from bot import hub
    from bot.payload import decode_param
    teacher, g, sids = setup(con, 20)
    send(con, teacher, {"t": "wk", "g": g["id"], "w": "2026-11-16", "q": qids(con, g),
                        "r": [[s, code("321023"), "Комментарий"] for s in sids]})

    class Conf:
        forms_url = "https://premiumaplic.github.io/Premiumbasis/"
    link = hub.url(con, Conf, g, "ru", TODAY)
    assert link and len(link) < hub.HUB_LIMIT, len(link)
    data = decode_param(link.split("#d=")[1])
    assert len(data["st"]) == 20 and data["st"][0][1] == "Азиз К."
    assert "Каримов" not in json.dumps(data, ensure_ascii=False)
    assert data["ex"]["sn"] == "Курс A1" and data["stg"][0][1] == "Starter"
    assert data["stg"][0][2] == "Для детей" and data["att"]["today"] == "2026-11-20"
    assert data["st"][0][5] == "-------6"            # уровень по неделям (0…9): только текущая
    assert data["wkn"] == 12 or data["wkt"] == 8


def test_optional_questions_and_star(con):
    teacher, g, sids = setup(con, 2)
    q = qids(con, g)
    # обязательный вопрос пропустить нельзя, необязательный — можно
    bad = "-" + code("21023")
    assert "повреждены" in send(con, teacher, {"t": "wk", "g": g["id"], "w": "2026-11-16", "q": q,
                                                "r": [[sids[0], bad, ""]]}).text
    full = "321023210"[:len(q)]
    res = send(con, teacher, {"t": "wk", "g": g["id"], "w": "2026-11-16", "q": q,
                              "r": [[sids[0], full, "", 1], [sids[1], code("111111"), "", 0]]})
    assert "Сохранено" in res.text
    saved = reports.reports_for_weeks(con, g["id"], [MONDAY])
    assert saved[sids[0]]["2026-11-16"]["star"] and not saved[sids[1]]["2026-11-16"]["star"]
    assert len(saved[sids[0]]["2026-11-16"]["answers"]) == 9 and len(saved[sids[1]]["2026-11-16"]["answers"]) == 6
    assert forms.weekly_payload(con, g, "ru", TODAY)["sr"] == {"0": [sids[0]]}
    for star in (2, True, "1"):
        assert "повреждены" in send(con, teacher, {"t": "wk", "g": g["id"], "w": "2026-11-16", "q": q,
                                                    "r": [[sids[0], full, "", star]]}).text


def test_attendance_switched_off(con):
    teacher, g, sids = setup(con, 2, attendance=False)
    res = send(con, teacher, {"t": "att", "g": g["id"], "d": "2026-11-20", "m": [[sids[0], 0]]})
    assert "посещаемость выключена" in res.text

    class Conf:
        forms_url = "https://premiumaplic.github.io/Premiumbasis/"
    from bot import hub
    data = decode_param(hub.url(con, Conf, g, "ru", TODAY).split("#d=")[1])
    assert data["att"] is None
    kb = forms.group_keyboard(con, Conf, g, "ru", TODAY)
    assert not any("Посещаемость" in b.text for row in kb.keyboard for b in row)


def test_cards_subset(con):
    teacher, g, sids = setup(con, 3)
    other = repo.add_student(con, ACTOR, "Чужой Ученик", "ru", True, make_group(con, "11-Б"), TODAY)
    res = send(con, teacher, {"t": "cards", "g": g["id"], "ids": [sids[1], other, sids[1]]})
    assert res.action == "cards" and res.ids == [sids[1]]
    assert send(con, teacher, {"t": "cards", "g": g["id"]}).ids is None
    assert "Форма не сохранена" in send(con, teacher, {"t": "cards", "g": g["id"], "ids": [other]}).text
    assert "Форма не сохранена" in send(con, teacher, {"t": "cards", "g": g["id"], "ids": "1"}).text


def test_weekly_goal(con):
    teacher, g, sids = setup(con, 2)
    q = qids(con, g)
    goals = reports.goals_for(con, "en")
    math_goal = next(x["id"] for x in reports.goals_for(con, "math") if x["subjects"] == "math")
    ok = send(con, teacher, {"t": "wk", "g": g["id"], "w": "2026-11-16", "q": q,
                             "r": [[sids[0], code("321023"), "", 0, goals[0]["id"]], [sids[1], code("111111"), "", 1, 0]]})
    assert "Сохранено" in ok.text
    saved = reports.reports_for_weeks(con, g["id"], [MONDAY])
    assert saved[sids[0]]["2026-11-16"]["goal"] == goals[0]["id"] and saved[sids[1]]["2026-11-16"]["goal"] == 0
    payload = forms.weekly_payload(con, g, "ru", TODAY)
    assert payload["go"] == {"0": [[sids[0], goals[0]["id"]]]} and payload["gl"][0][1] == goals[0]["text_ru"]
    # чужая цель (другого предмета), не число, несуществующая — отказ
    for bad in (math_goal, "1", 9999, True):
        res = send(con, teacher, {"t": "wk", "g": g["id"], "w": "2026-11-16", "q": q,
                                  "r": [[sids[0], code("321023"), "", 0, bad]]})
        assert "повреждены" in res.text, bad
