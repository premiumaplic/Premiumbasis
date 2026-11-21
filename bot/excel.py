"""Массовая загрузка учителей, групп и учеников из Excel.

1. Бот присылает шаблон (build_template).
2. Владелец заполняет и отправляет файл обратно.
3. Бот проверяет файл (parse) и показывает итог: что будет добавлено и в каких строках ошибки.
4. Только после подтверждения применяет (apply). Строки с ошибками не загружаются.
"""

import io
import re
from dataclasses import dataclass, field
from datetime import date, datetime

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from bot import repo, schedule

SHEET_T, SHEET_G, SHEET_S, SHEET_HELP = "Учителя", "Группы", "Ученики", "Справка"
T_COLS = ["Telegram ID", "Имя", "Язык интерфейса (ru/uz)"]
G_COLS = ["Название", "Предмет", "Учитель (Telegram ID)", "Этап", "Дата старта", "Дни недели", "Время урока"]
S_COLS = ["Имя и фамилия", "Группа", "Язык карточки (ru/uz)", "Согласие родителя (да/нет)",
          "Станция (необязательно)"]
MAX_ROWS = 3000
MAX_FILE_BYTES = 3 * 1024 * 1024

YES = {"да", "yes", "ha", "1", "+", "true", "есть"}
NO = {"нет", "no", "yoʻq", "yo'q", "yoq", "0", "-", "false", ""}


# ---------------------------------------------------------------- шаблон

def build_template(con) -> bytes:
    wb = Workbook()
    head_font = Font(bold=True)
    head_fill = PatternFill("solid", fgColor="DDE7F3")
    subjects = repo.list_subjects(con)
    stages = repo.list_stages(con, "en")
    math = repo.list_stages(con, "math")
    all_names = [s["name_ru"] for s in stages] + [s["name_ru"] for s in math]
    while len(",".join(all_names)) > 250:  # ограничение Excel на список в ячейке
        all_names.pop()

    def sheet(ws, columns, widths):
        ws.append(columns)
        for i, width in enumerate(widths, start=1):
            ws.cell(row=1, column=i).font = head_font
            ws.cell(row=1, column=i).fill = head_fill
            ws.column_dimensions[chr(64 + i)].width = width
        ws.freeze_panes = "A2"

    def dropdown(ws, column: str, values: list[str]):
        dv = DataValidation(type="list", formula1='"' + ",".join(values) + '"', allow_blank=True)
        dv.error = "Выберите значение из списка"
        ws.add_data_validation(dv)
        dv.add(f"{column}2:{column}{MAX_ROWS}")

    ws = wb.active
    ws.title = SHEET_T
    sheet(ws, T_COLS, [16, 28, 24])
    dropdown(ws, "C", ["ru", "uz"])

    ws = wb.create_sheet(SHEET_G)
    sheet(ws, G_COLS, [14, 16, 22, 14, 14, 16, 12])
    dropdown(ws, "B", [s["name_ru"] for s in subjects])
    dropdown(ws, "D", all_names)

    ws = wb.create_sheet(SHEET_S)
    sheet(ws, S_COLS, [30, 14, 22, 26, 24])
    dropdown(ws, "C", ["ru", "uz"])
    dropdown(ws, "D", ["да", "нет"])
    dropdown(ws, "E", all_names)

    ws = wb.create_sheet(SHEET_HELP)
    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["B"].width = 70
    help_rows = [
        ("Как заполнять", ""),
        ("Учителя", "Telegram ID — цифры (учитель узнаёт его командой /myid в боте). Язык: ru или uz."),
        ("Группы", "Название — как в центре (10-А). Учитель — его Telegram ID из листа «Учителя» "
                   "или уже добавленный в бот. Этап — для английского обязательно, для математики — "
                   "класс (например 5 класс), можно оставить пустым."),
        ("", "Дата старта: 01.09.2026. Дни недели: Пн, Ср, Пт. Время урока: 15:00."),
        ("Ученики", "Имя и фамилия — в таком порядке (Азиз Каримов). Группа — название группы."),
        ("", "Согласие родителя: да/нет (письменное согласие центр собирает сам на бумаге). "
             "Без согласия карточки не создаются."),
        ("", "Станция — только если ученик уже знает язык. Иначе ставится этап группы."),
        ("", "Не храните здесь телефоны, адреса, даты рождения и другие лишние данные."),
        ("", ""),
        ("Предметы", ", ".join(s["name_ru"] for s in subjects)),
        ("Этапы английского", ", ".join(s["name_ru"] for s in stages)),
        ("Этапы математики", ", ".join(s["name_ru"] for s in math)),
        ("", ""),
        ("Пример (выдуманный)", "Группы: 10-А | Английский | 123456789 | Курс A1 | 01.09.2026 | Пн, Ср, Пт | 15:00"),
        ("", "Ученики: Азиз Каримов | 10-А | uz | да |"),
    ]
    for a, b in help_rows:
        ws.append([a, b])
    ws["A1"].font = head_font

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------- разбор файла

@dataclass
class Plan:
    teachers: list[dict] = field(default_factory=list)
    groups: list[dict] = field(default_factory=list)
    students: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    skipped_groups: int = 0
    skipped_students: int = 0

    @property
    def has_changes(self) -> bool:
        return bool(self.teachers or self.groups or self.students)


def _text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, datetime):
        return value.strftime("%d.%m.%Y")
    if isinstance(value, date):
        return value.strftime("%d.%m.%Y")
    return " ".join(str(value).split())


def _date(value) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return schedule.parse_date(_text(value))


def _time(value) -> str | None:
    if hasattr(value, "strftime") and not isinstance(value, (date, datetime)):
        return value.strftime("%H:%M")  # ячейка с форматом времени
    if isinstance(value, float) and 0 <= value < 1:  # время как доля суток
        minutes = round(value * 24 * 60)
        return f"{minutes // 60:02d}:{minutes % 60:02d}"
    return schedule.parse_time(_text(value))


def _key(text: str) -> str:
    """'Курс A1', 'a1', 'A1 kursi' -> 'a1'; 'Pre-CEFR' -> 'precefr'."""
    return re.sub(r"курс|kursi|[\s\-_]", "", text.casefold())


def _rows(wb, name: str, width: int):
    if name not in wb.sheetnames:
        return []
    out = []
    for number, row in enumerate(wb[name].iter_rows(min_row=2, max_row=MAX_ROWS + 1, values_only=True), start=2):
        cells = list(row[:width]) + [None] * (width - len(row[:width]))
        if all(_text(c) == "" for c in cells):
            continue
        out.append((number, cells))
    return out


def parse(con, data: bytes) -> Plan:
    plan = Plan()
    wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)

    def err(sheet: str, row: int, text: str):
        plan.errors.append(f"{sheet}, строка {row}: {text}")

    # ---- учителя
    file_teachers: dict[int, dict] = {}
    for row, (tg, name, lang) in _rows(wb, SHEET_T, 3):
        tg_text, name, lang = _text(tg), _text(name), _text(lang).lower() or "ru"
        if not tg_text.isdigit() or not 5 <= len(tg_text) <= 15:
            err(SHEET_T, row, "Telegram ID — только цифры")
            continue
        if not name or len(name) > 60:
            err(SHEET_T, row, "не указано имя")
            continue
        if lang not in ("ru", "uz"):
            err(SHEET_T, row, "язык — ru или uz")
            continue
        if int(tg_text) in file_teachers:
            err(SHEET_T, row, "этот Telegram ID уже есть выше в файле")
            continue
        item = {"row": row, "tg_id": int(tg_text), "name": name, "lang": lang,
                "new": repo.teacher_by_tg(con, int(tg_text)) is None}
        file_teachers[item["tg_id"]] = item
        plan.teachers.append(item)

    # ---- группы
    subjects = {}
    for s in repo.list_subjects(con):
        for k in (s["code"], s["name_ru"], s["name_uz"]):
            subjects[k.casefold()] = s
    file_groups: dict[str, dict] = {}
    for row, (name, subj, tg, stage, start, days, time) in _rows(wb, SHEET_G, 7):
        name = _text(name)
        if not name or len(name) > 30:
            err(SHEET_G, row, "не указано название (до 30 знаков)")
            continue
        if name.casefold() in file_groups:
            err(SHEET_G, row, f"группа «{name}» уже есть выше в файле")
            continue
        if repo.group_by_name(con, name):
            plan.skipped_groups += 1
            plan.notes.append(f"{SHEET_G}, строка {row}: группа «{name}» уже есть в боте — пропущу")
            continue
        s = subjects.get(_text(subj).casefold())
        if not s:
            err(SHEET_G, row, f"неизвестный предмет «{_text(subj)}»")
            continue
        teacher_tg = None
        tg_text = _text(tg)
        if tg_text:
            known = repo.teacher_by_tg(con, int(tg_text)) if tg_text.isdigit() else None
            if not tg_text.isdigit() or not (int(tg_text) in file_teachers or (known and known["active"])):
                err(SHEET_G, row, f"учитель с Telegram ID {tg_text} не найден (добавьте его на лист «Учителя»)")
                continue
            teacher_tg = int(tg_text)
        stage_id = None
        if s["has_map"]:
            match = [st for st in repo.list_stages(con, s["code"])
                     if _key(_text(stage)) in (_key(st["code"]), _key(st["name_ru"]), _key(st["name_uz"]))]
            if (_text(stage) and not match) or (not _text(stage) and s["code"] == "en"):
                err(SHEET_G, row, "укажите этап из списка (например Курс A1)"
                    if s["code"] == "en" else f"неизвестный этап «{_text(stage)}» (пример: 5 класс)")
                continue
            stage_id = match[0]["id"] if match else None
        elif _text(stage):
            err(SHEET_G, row, f"у предмета «{s['name_ru']}» нет этапов — оставьте ячейку «Этап» пустой")
            continue
        start_date = _date(start)
        if not start_date:
            err(SHEET_G, row, "не понял дату старта (пример: 01.09.2026)")
            continue
        weekdays = schedule.parse_weekdays(_text(days)) if _text(days) else ""
        if weekdays is None:
            err(SHEET_G, row, "не понял дни недели (пример: Пн, Ср, Пт)")
            continue
        lesson_time = _time(time) if _text(time) else ""
        if lesson_time is None:
            err(SHEET_G, row, "не понял время урока (пример: 15:00)")
            continue
        item = {"row": row, "name": name, "subject": s["code"], "has_map": s["has_map"],
                "teacher_tg": teacher_tg, "stage_id": stage_id, "start_date": start_date.isoformat(),
                "weekdays": weekdays, "lesson_time": lesson_time}
        file_groups[name.casefold()] = item
        plan.groups.append(item)

    # ---- ученики
    seen: set[tuple[str, str]] = set()
    for row, (name, grp, lang, consent, stage) in _rows(wb, SHEET_S, 5):
        name, grp = _text(name), _text(grp)
        lang, consent_text = _text(lang).lower() or "ru", _text(consent).casefold()
        if len(name.split()) < 2 or len(name) > 60:
            err(SHEET_S, row, "нужны имя и фамилия")
            continue
        db_group = repo.group_by_name(con, grp) if grp else None
        file_group = file_groups.get(grp.casefold()) if grp else None
        if not db_group and not file_group:
            err(SHEET_S, row, f"не найдена группа «{grp}»" if grp else "не указана группа")
            continue
        if lang not in ("ru", "uz"):
            err(SHEET_S, row, "язык карточки — ru или uz")
            continue
        if consent_text not in YES | NO:
            err(SHEET_S, row, "согласие — да или нет")
            continue
        key = (name.casefold(), grp.casefold())
        if key in seen:
            err(SHEET_S, row, "этот ученик в этой группе уже есть выше в файле")
            continue
        seen.add(key)
        if db_group and any(repo.is_enrolled(con, s["id"], db_group["id"])
                            for s in repo.students_by_name(con, name)):
            plan.skipped_students += 1
            continue
        subject_code = db_group["subject"] if db_group else file_group["subject"]
        has_map = db_group["has_map"] if db_group else file_group["has_map"]
        stage_id = None
        if _text(stage):
            if not has_map:
                err(SHEET_S, row, "у предмета этой группы нет станций — оставьте ячейку пустой")
                continue
            match = [st for st in repo.list_stages(con, subject_code)
                     if _key(_text(stage)) in (_key(st["code"]), _key(st["name_ru"]), _key(st["name_uz"]))]
            if not match:
                err(SHEET_S, row, f"неизвестная станция «{_text(stage)}»")
                continue
            stage_id = match[0]["id"]
        if repo.students_by_name(con, name):
            plan.notes.append(f"{SHEET_S}, строка {row}: ученик с таким именем уже есть в другой группе — "
                              "будет отдельной записью")
        plan.students.append({"row": row, "name": name, "group": grp, "card_lang": lang,
                              "consent": consent_text in YES, "stage_id": stage_id})
    wb.close()
    return plan


# ---------------------------------------------------------------- итог и применение

def _short_list(lines: list[str], limit: int) -> list[str]:
    if len(lines) <= limit:
        return lines
    return lines[:limit] + [f"…и ещё {len(lines) - limit}"]


def preview_text(plan: Plan) -> str:
    new_t = sum(1 for t in plan.teachers if t["new"])
    upd_t = len(plan.teachers) - new_t
    lines = ["Проверка файла.", "",
             f"Будет добавлено: учителей {new_t}, групп {len(plan.groups)}, учеников {len(plan.students)}."]
    if upd_t:
        lines.append(f"Будут обновлены данные учителей: {upd_t}.")
    if plan.skipped_groups or plan.skipped_students:
        lines.append(f"Уже есть в боте, пропущу: групп {plan.skipped_groups}, учеников {plan.skipped_students}.")
    if plan.errors:
        lines += ["", f"❌ Ошибки — эти строки НЕ будут загружены ({len(plan.errors)}):"]
        lines += ["• " + e for e in _short_list(plan.errors, 25)]
    if plan.notes:
        lines += ["", "ℹ️ Обратите внимание:"]
        lines += ["• " + n for n in _short_list(plan.notes, 10)]
    if plan.has_changes:
        lines += ["", "Применить? Можно сначала исправить файл и прислать заново."]
    else:
        lines += ["", "Добавлять нечего."]
    return "\n".join(lines)


def apply(con, actor: int, plan: Plan, on_date: date) -> dict:
    """Применяет проверенный план. Вызывать внутри транзакции (db.tx)."""
    counts = {"teachers": 0, "groups": 0, "students": 0}
    for t in plan.teachers:
        repo.save_teacher(con, actor, t["tg_id"], t["name"], t["lang"])
        counts["teachers"] += 1
    for g in plan.groups:
        teacher = repo.teacher_by_tg(con, g["teacher_tg"]) if g["teacher_tg"] else None
        repo.create_group(con, actor, g["name"], g["subject"], teacher["id"] if teacher else None,
                          g["stage_id"], date.fromisoformat(g["start_date"]), g["weekdays"], g["lesson_time"])
        counts["groups"] += 1
    for s in plan.students:
        group_row = repo.group_by_name(con, s["group"])
        repo.add_student(con, actor, s["name"], s["card_lang"], s["consent"], group_row["id"], on_date,
                         s["stage_id"])
        counts["students"] += 1
    repo.audit(con, actor, "excel_import", "",
               f"teachers={counts['teachers']} groups={counts['groups']} students={counts['students']}")
    return counts


def plan_to_dict(plan: Plan) -> dict:
    return plan.__dict__.copy()


def plan_from_dict(data: dict) -> Plan:
    return Plan(**data)
