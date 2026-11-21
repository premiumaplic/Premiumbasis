"""Выгрузка недельных отчётов в Excel: учителю — по своей группе, владельцу — по всему центру.

Файл уходит только в личный чат того, кто его запросил. Лист «Сводка» — по группам,
дальше по листу на каждую неделю: ученик, ответы по каждому вопросу (с цветом уровня),
средний уровень, звезда недели, цель на следующую неделю, комментарий.
"""

import io
from datetime import date, timedelta

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from bot import repo, reports

LEVEL_FILL = ["F8D3CD", "FBE7B5", "DCEFC9", "BFE5CC"]   # 0 → 3: красноватый → зелёный
HEAD_FILL = "F3E3D3"
THIN = Side(style="thin", color="E2D6CA")


def _week_title(week: date) -> str:
    return f"{week.strftime('%d.%m')}–{(week + timedelta(days=5)).strftime('%d.%m')}"


def _head(ws, columns: list[str], widths: list[int]) -> None:
    ws.append(columns)
    for i, width in enumerate(widths, start=1):
        cell = ws.cell(row=1, column=i)
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor=HEAD_FILL)
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        cell.border = Border(bottom=THIN)
        ws.column_dimensions[get_column_letter(i)].width = width
    ws.row_dimensions[1].height = 32
    ws.freeze_panes = "C2"


def weekly_xlsx(con, groups: list, weeks: list[date]) -> bytes:
    """Excel с отчётами групп за недели (от новой к старой)."""
    wb = Workbook()
    summary = wb.active
    summary.title = "Сводка"
    _head(summary, ["Неделя", "Группа", "Предмет", "Учитель", "Учеников", "Заполнено", "Средний уровень, %",
                    "Звёзд недели"], [13, 14, 14, 22, 10, 11, 12, 10])
    summary.freeze_panes = "A2"

    subjects = sorted({g["subject"] for g in groups})
    questions = []
    seen = set()
    for code in subjects:
        for q in reports.questions_for(con, code):
            if q["id"] not in seen:
                seen.add(q["id"])
                questions.append(q)

    for week in weeks:
        ws = wb.create_sheet(_week_title(week).replace(".", "-"))
        _head(ws, ["Группа", "Ученик"] + [q["text_ru"] for q in questions] +
              ["Уровень, %", "Звезда", "Цель на неделю", "Комментарий"],
              [12, 26] + [16] * len(questions) + [10, 8, 30, 40])
        for g in groups:
            students = repo.group_students(con, g["id"])
            saved = reports.reports_for_weeks(con, g["id"], [week])
            levels, stars = [], 0
            for s in students:
                item = saved.get(s["id"], {}).get(week.isoformat())
                row = [g["name"], s["full_name"]]
                fills = []
                if item:
                    for q in questions:
                        v = item["answers"].get(q["id"])
                        row.append(f"{v} · {q[f'opt{v}_ru']}" if v is not None else "")
                        fills.append(v)
                    vals = list(item["answers"].values())
                    level = round(sum(vals) / len(vals) / 3 * 100) if vals else None
                    if level is not None:
                        levels.append(level)
                    stars += int(item.get("star", False))
                    goal = reports.goal(con, item.get("goal") or 0)
                    row += [level, "★" if item.get("star") else "", goal["text_ru"] if goal else "", item["comment"]]
                else:
                    row += [""] * len(questions) + ["", "", "", "нет отчёта"]
                    fills = [None] * len(questions)
                ws.append(row)
                r = ws.max_row
                for i, v in enumerate(fills):
                    if v is not None:
                        ws.cell(row=r, column=3 + i).fill = PatternFill("solid", fgColor=LEVEL_FILL[v])
                for c in range(1, len(row) + 1):
                    ws.cell(row=r, column=c).border = Border(bottom=THIN)
                    ws.cell(row=r, column=c).alignment = Alignment(vertical="top", wrap_text=True)
            done = sum(1 for s in students if saved.get(s["id"], {}).get(week.isoformat()))
            teacher = repo.teacher(con, g["teacher_id"]) if g["teacher_id"] else None
            summary.append([_week_title(week), g["name"], g["subject_ru"], teacher["name"] if teacher else "",
                            len(students), done, round(sum(levels) / len(levels)) if levels else "", stars])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def filename(prefix: str, week: date) -> str:
    """Имя файла без имён людей: otchety-10A-2026-11-16.xlsx"""
    safe = "".join(ch for ch in prefix if ch.isalnum() or ch in "-_")[:20] or "otchety"
    return f"otchety-{safe}-{week.isoformat()}.xlsx"
