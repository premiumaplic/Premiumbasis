"""Даты групп: неделя внутри станции, дата следующего экзамена, строка-заголовок группы.

Экзамены — каждые 2 месяца от даты старта группы (на станциях, где переход решает экзамен).
"""

import calendar
from datetime import date, datetime

from bot.timefmt import TZ

EXAM_EVERY_MONTHS = 2
WEEKS_PER_STAGE = 8

MONTHS_GEN = {
    "ru": ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа",
           "сентября", "октября", "ноября", "декабря"],
    "uz": ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avgust",
           "sentabr", "oktabr", "noyabr", "dekabr"],
}
WEEKDAYS_SHORT = {
    "ru": ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
    "uz": ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"],
}


def today() -> date:
    return datetime.now(TZ).date()


def add_months(day: date, months: int) -> date:
    month = day.month - 1 + months
    year = day.year + month // 12
    month = month % 12 + 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


def human_date(day: date, lang: str = "ru") -> str:
    """14 декабря / 14-dekabr"""
    month = MONTHS_GEN[lang][day.month - 1]
    return f"{day.day} {month}" if lang == "ru" else f"{day.day}-{month}"


def parse_date(text: str) -> date | None:
    """Принимает 14.12.2026, 14.12.26, 2026-12-14."""
    text = text.strip()
    for fmt in ("%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def parse_time(text: str) -> str | None:
    """'9:00' -> '09:00'; неправильное время -> None."""
    text = text.strip().replace(".", ":")
    try:
        t = datetime.strptime(text, "%H:%M")
    except ValueError:
        return None
    return t.strftime("%H:%M")


def parse_weekdays(text: str) -> str | None:
    """'Пн, Ср, Пт' или 'Du Ch Ju' или '1,3,5' -> '1,3,5'."""
    names = {}
    for lang in WEEKDAYS_SHORT:
        for i, name in enumerate(WEEKDAYS_SHORT[lang], start=1):
            names[name.casefold()] = i
    days = set()
    for part in text.replace(";", ",").replace(" ", ",").split(","):
        part = part.strip().casefold()
        if not part:
            continue
        if part.isdigit() and 1 <= int(part) <= 7:
            days.add(int(part))
        elif part in names:
            days.add(names[part])
        else:
            return None
    return ",".join(str(d) for d in sorted(days)) if days else None


def weekdays_text(weekdays: str, lang: str = "ru") -> str:
    if not weekdays:
        return ""
    return ", ".join(WEEKDAYS_SHORT[lang][int(d) - 1] for d in weekdays.split(",") if d)


def next_exam(start: date, on: date) -> date:
    """Ближайший экзамен (каждые 2 месяца от старта), не раньше указанного дня."""
    k = 1
    while add_months(start, EXAM_EVERY_MONTHS * k) < on:
        k += 1
    return add_months(start, EXAM_EVERY_MONTHS * k)


def stage_week(start: date, on: date, by_exam: bool) -> int:
    """Номер недели: внутри текущего 2-месячного цикла (до 8) или с даты старта."""
    if on < start:
        return 0
    cycle_start = start
    if by_exam:
        k = 0
        while add_months(start, EXAM_EVERY_MONTHS * (k + 1)) <= on:
            k += 1
        cycle_start = add_months(start, EXAM_EVERY_MONTHS * k)
    week = (on - cycle_start).days // 7 + 1
    return min(week, WEEKS_PER_STAGE) if by_exam else week


HEADER = {
    "ru": {"group": "Группа", "week": "неделя {n}", "of": "неделя {n} из {total}", "exam": "экзамен {d}",
           "start": "старт {d}", "teacher": "переход по решению учителя"},
    "uz": {"group": "Guruh", "week": "{n}-hafta", "of": "{total} haftadan {n}-hafta", "exam": "imtihon {d}",
           "start": "boshlanishi {d}", "teacher": "oʻtish oʻqituvchi qarori bilan"},
}


def anchor(g) -> date:
    """С какого дня группа идёт по текущей станции (отсюда — недели и экзамены)."""
    keys = g.keys() if hasattr(g, "keys") else g
    value = g["stage_start"] if "stage_start" in keys and g["stage_start"] else g["start_date"]
    return date.fromisoformat(value)


def group_header(g, lang: str = "ru", on: date | None = None) -> str:
    """«Группа 10-А · Курс A1 · неделя 5 из 8 · экзамен 14 декабря»"""
    on = on or today()
    words = HEADER[lang]
    start = anchor(g)
    parts = [f"{words['group']} {g['name']}"]
    stage_name = g["stage_uz" if lang == "uz" else "stage_ru"]
    parts.append(stage_name or g["subject_uz" if lang == "uz" else "subject_ru"])
    by_exam = bool(g["stage_id"] and g["exam_transition"])
    if on < start:
        parts.append(words["start"].format(d=human_date(start, lang)))
    elif by_exam:
        parts.append(words["of"].format(n=stage_week(start, on, True), total=WEEKS_PER_STAGE))
        parts.append(words["exam"].format(d=human_date(next_exam(start, on), lang)))
    else:
        parts.append(words["week"].format(n=stage_week(start, on, False)))
        if g["stage_id"] and g["has_map"]:
            parts.append(words["teacher"])
    return " · ".join(parts)
