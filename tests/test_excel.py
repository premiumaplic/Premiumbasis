"""Загрузка из Excel: шаблон, итог перед применением, ошибки по строкам, повторная загрузка."""

import datetime as dt
import io

from openpyxl import load_workbook

from bot import excel, repo
from tests.conftest import ACTOR

FIRST = ["Азиз", "Мадина", "Жасур", "Камила", "Отабек", "Севара", "Тимур", "Лола", "Бехруз", "Нигора",
         "Ислом", "Зарина", "Шерзод", "Малика", "Ильхом"]
LAST = ["Каримов", "Юсупова", "Ахмедов", "Рахимова", "Саидов", "Олимова", "Назаров", "Турсунова",
        "Умаров", "Хасанова", "Мирзаев", "Валиева", "Холматов", "Собирова", "Эргашев"]


def filled_template(con, students_per_group=15, extra_rows=()):
    wb = load_workbook(io.BytesIO(excel.build_template(con)))
    wb[excel.SHEET_T].append([700001, "Учитель Первый", "ru"])
    wb[excel.SHEET_T].append([700002, "Учитель Второй", "uz"])
    wb[excel.SHEET_G].append(["10-А", "Английский", 700001, "Курс A1", dt.datetime(2026, 9, 1), "Пн, Ср, Пт", "15:00"])
    wb[excel.SHEET_G].append(["11-Б", "Английский", 700002, "A2", "01.10.2026", "Вт, Чт", dt.time(16, 30)])
    wb[excel.SHEET_G].append(["М-1", "Математика", 700001, None, "15.09.2026", "Сб", "10:00"])
    for g in ("10-А", "11-Б", "М-1"):
        for i in range(students_per_group):
            wb[excel.SHEET_S].append([f"{FIRST[i]} {LAST[i]}", g, "uz" if i % 2 else "ru", "да" if i % 3 else "нет", None])
    for sheet, row in extra_rows:
        wb[sheet].append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_template_has_sheets_and_no_real_data(con):
    wb = load_workbook(io.BytesIO(excel.build_template(con)))
    assert wb.sheetnames == [excel.SHEET_T, excel.SHEET_G, excel.SHEET_S, excel.SHEET_HELP]
    assert wb[excel.SHEET_S].max_row == 1  # только заголовки
    plan = excel.parse(con, excel.build_template(con))
    assert not plan.has_changes and not plan.errors


def test_import_3_groups_by_15(con):
    plan = excel.parse(con, filled_template(con))
    assert plan.errors == []
    text = excel.preview_text(plan)
    assert "учителей 2, групп 3, учеников 45" in text
    # пока не подтвердили — в базе ничего нет
    assert repo.list_groups(con) == []
    counts = excel.apply(con, ACTOR, plan, dt.date(2026, 11, 20))
    assert counts == {"teachers": 2, "groups": 3, "students": 45}
    groups = {g["name"]: g for g in repo.list_groups(con)}
    assert groups["10-А"]["student_count"] == 15 and groups["11-Б"]["lesson_time"] == "16:30"
    assert groups["11-Б"]["stage_code"] == "a2" and groups["М-1"]["stage_id"] is None
    assert groups["10-А"]["teacher_tg"] == 700001
    s = repo.group_students(con, groups["11-Б"]["id"])[0]
    assert repo.current_stage(con, s["id"], "en")["code"] == "a2"


def test_second_import_skips_existing(con):
    data = filled_template(con)
    excel.apply(con, ACTOR, excel.parse(con, data), dt.date(2026, 11, 20))
    plan = excel.parse(con, data)
    assert plan.groups == [] and plan.students == []
    assert plan.skipped_groups == 3
    assert "добавлено: учителей 0, групп 0, учеников 0" in excel.preview_text(plan)


def test_errors_reported_by_row(con):
    extra = [
        (excel.SHEET_S, ["Азиз", "10-А", "ru", "да", None]),                 # строка 47: нет фамилии
        (excel.SHEET_S, ["Нодир Алиев", "99-Я", "ru", "да", None]),          # 48: нет группы
        (excel.SHEET_S, ["Нодир Алиев", "10-А", "en", "да", None]),          # 49: язык
        (excel.SHEET_S, ["Нодир Алиев", "М-1", "ru", "да", "A1"]),           # 50: станция у математики
        (excel.SHEET_G, ["12-В", "Химия", None, None, "01.09.2026", None, None]),  # 5: предмет
        (excel.SHEET_G, ["12-Г", "Английский", 999999, "A1", "01.09.2026", None, None]),  # 6: учитель
        (excel.SHEET_T, ["abc", "Кто-то", "ru"]),                             # 4: ID
    ]
    plan = excel.parse(con, filled_template(con, extra_rows=extra))
    assert len(plan.students) == 45 and len(plan.groups) == 3
    rows = sorted(e.split(":")[0] for e in plan.errors)
    assert rows == ["Группы, строка 5", "Группы, строка 6", "Ученики, строка 47", "Ученики, строка 48",
                    "Ученики, строка 49", "Ученики, строка 50", "Учителя, строка 4"]
    assert "НЕ будут загружены (7)" in excel.preview_text(plan)


def test_broken_file_raises(con):
    import pytest
    with pytest.raises(Exception):
        excel.parse(con, b"not an excel file")
