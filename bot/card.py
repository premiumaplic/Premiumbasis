"""Карточка-отчёт для родителя: PNG 1080×1350, одна на ученика за неделю.

Родитель должен понять главное за 10 секунд, не читая цифр. Сверху вниз:
имя и группа (⭐ если «звезда недели») → карта пути: станции змейкой, где ученик сейчас,
прогноз по месяцам, недели до экзамена → посещаемость (только если владелец её включил) →
показатели недели в две колонки (полоски и стрелки) → одна фраза-вывод → похвала →
комментарий учителя. На карточке только данные одного ученика.
"""

import io
from dataclasses import dataclass, field
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from bot import progress, reports, repo, rules, schedule

W, H = 1080, 1350
M = 56  # поля
FONTS = Path(__file__).resolve().parents[1] / "assets" / "fonts"

# Спокойная палитра с одним акцентным цветом (оранжевый). Красный — не главный цвет.
C = {
    "bg": "#fff7ee", "panel": "#ffffff", "line": "#f2dfcb", "line2": "#e6cbb0",
    "text": "#3b2a1e", "muted": "#9a8572", "accent": "#ff9a3c", "accent_dark": "#e5761a",
    "accent_soft": "#ffe7cf", "ok": "#4dba6a", "ok_soft": "#dcf4e2", "ok_dark": "#369552",
    "warn": "#dd9d12", "warn_soft": "#fff1cc", "down": "#e0786b", "grey": "#efe3d6",
    "star": "#f2b630", "star_soft": "#fff4d1", "blue": "#5ab4f0",
}

MONTHS = {
    "ru": ["январь", "февраль", "март", "апрель", "май", "июнь", "июль", "август", "сентябрь", "октябрь",
           "ноябрь", "декабрь"],
    "uz": ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avgust", "sentabr", "oktabr",
           "noyabr", "dekabr"],
}
MONTHS_SHORT = {
    "ru": ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"],
    "uz": ["yan", "fev", "mar", "apr", "may", "iyn", "iyl", "avg", "sen", "okt", "noy", "dek"],
}

# Тексты карточки. Узбекский — ЧЕРНОВИК, на проверку владельцу.
TX = {
    "ru": {
        "group": "Группа", "week": "Неделя {d}", "path": "Путь", "here": "сейчас здесь",
        "now": "Сейчас: {stage}", "week_of": "неделя {n} из {total}", "week_n": "неделя {n}",
        "wk_short": "нед. {n}/{total}", "wk_short_n": "нед. {n}", "passed": "пройдено",
        "topic": "Тема: {t}", "finish": "Прогноз финиша: {stage} — {when}", "fork": "дальше — CEFR или IELTS",
        "by_teacher": "Переход — по решению учителя", "next_exam": "Следующий экзамен: {d}",
        "exam_in": "экзамен {d} · через {n} дн.", "exam_today": "экзамен сегодня",
        "on_plan": "Идёт по плану", "risk": "Есть риск повтора",
        "course": "Курс", "attendance": "Посещаемость за месяц",
        "att_line": "{a} из {n} уроков", "late": "опозданий: {k}", "excused": "по уважительной: {k}",
        "no_lessons": "отметок пока нет",
        "metrics": "Неделя в показателях", "att_good": "Посещаемость отличная.", "att_ok": "Посещаемость хорошая.",
        "att_bad": "Посещаемость нужно улучшить.", "strong": "Сильная сторона — {x}.",
        "weak": "Над чем работать — {x}.", "even_top": "Отличные результаты по всем показателям.",
        "even": "Ровные результаты по всем показателям.",
        "praise": "Молодец! Результаты растут {n} недели подряд.", "comment": "Комментарий учителя",
        "star": "⭐ Звезда недели",
    },
    "uz": {
        "group": "Guruh", "week": "{d} haftasi", "path": "Yoʻl", "here": "hozir shu yerda",
        "now": "Hozir: {stage}", "week_of": "{total} haftadan {n}-hafta", "week_n": "{n}-hafta",
        "wk_short": "{n}/{total}-hafta", "wk_short_n": "{n}-hafta", "passed": "oʻtildi",
        "topic": "Mavzu: {t}", "finish": "Yakun prognozi: {stage} — {when}", "fork": "keyin — CEFR yoki IELTS",
        "by_teacher": "Oʻtish — oʻqituvchi qarori bilan", "next_exam": "Keyingi imtihon: {d}",
        "exam_in": "imtihon {d} · {n} kundan keyin", "exam_today": "imtihon bugun",
        "on_plan": "Reja boʻyicha", "risk": "Qayta oʻqish xavfi bor",
        "course": "Kurs", "attendance": "Oylik davomat",
        "att_line": "{n} darsdan {a} tasi", "late": "kechikish: {k}", "excused": "sababli: {k}",
        "no_lessons": "hali belgilar yoʻq",
        "metrics": "Hafta koʻrsatkichlari", "att_good": "Davomat aʼlo.", "att_ok": "Davomat yaxshi.",
        "att_bad": "Davomatni yaxshilash kerak.", "strong": "Kuchli tomoni — {x}.",
        "weak": "Ustida ishlash kerak — {x}.", "even_top": "Barcha koʻrsatkichlar aʼlo.",
        "even": "Barcha koʻrsatkichlar bir xil.",
        "praise": "Barakalla! Natijalar {n} hafta ketma-ket oʻsmoqda.", "comment": "Oʻqituvchi izohi",
        "star": "⭐ Hafta yulduzi",
    },
}


# ================================================================ данные карточки

@dataclass
class Metric:
    label: str
    value: int
    answer: str
    arrow: int | None = None   # +1 рост, -1 спад, 0 без изменений, None — не с чем сравнить


@dataclass
class CardData:
    lang: str
    name: str
    group: str
    center: str
    week_text: str
    subject: str
    stage_name: str | None
    week_line: str
    topic: str
    view: progress.MapView | None
    finish_line: str
    next_exam_line: str
    status: str | None          # on_plan / risk / None
    about: str = ""             # что проходят на текущей станции
    exam_days: int | None = None
    star: bool = False
    show_attendance: bool = False
    att_attended: int = 0
    att_total: int = 0
    att_late: int = 0
    att_excused: int = 0
    att_marks: list[str] = field(default_factory=list)
    metrics: list[Metric] = field(default_factory=list)
    summary: str = ""
    praise: str = ""
    comment: str = ""


def _month_year(d: date, lang: str) -> str:
    return f"{MONTHS[lang][d.month - 1]} {d.year}"


def _month_short(d: date, lang: str) -> str:
    return f"{MONTHS_SHORT[lang][d.month - 1]} {d.year}"


def _when(node, lang: str) -> str:
    if node.finish_max and node.finish_max != node.finish:
        if node.finish.year == node.finish_max.year:
            return f"{MONTHS[lang][node.finish.month - 1]}–{_month_year(node.finish_max, lang)}"
        return f"{_month_year(node.finish, lang)} – {_month_year(node.finish_max, lang)}"
    return _month_year(node.finish, lang)


def week_text(week: date, lang: str) -> str:
    end = week + timedelta(days=5)
    month = schedule.MONTHS_GEN[lang][end.month - 1]
    if lang == "uz":
        return f"{week.day}–{end.day}-{month}" if week.month == end.month else \
            f"{week.day}-{schedule.MONTHS_GEN[lang][week.month - 1]} – {end.day}-{month}"
    if week.month == end.month:
        return f"{week.day}–{end.day} {month}"
    return f"{week.day} {schedule.MONTHS_GEN[lang][week.month - 1]} – {end.day} {month}"


def collect(con, student_id: int, group_id: int, week: date, on: date | None = None) -> CardData | None:
    """Всё для карточки. None — за эту неделю нет отчёта."""
    on = on or schedule.today()
    s = repo.student(con, student_id)
    g = repo.group(con, group_id)
    lang = s["card_lang"]
    tx = TX[lang]
    suffix = "uz" if lang == "uz" else "ru"
    report = reports.reports_for_weeks(con, group_id, [week]).get(student_id, {}).get(week.isoformat())
    if report is None:
        return None

    view = progress.build(con, student_id, g, on)
    stage_name, week_line, finish_line, exam_line, status, about, exam_days = None, "", "", "", None, "", None
    if view and view.current:
        stage_name = getattr(view.current, f"name_{suffix}")
        stage_row = repo.stage(con, view.current.stage_id)
        about = stage_row[f"about_{suffix}"] if stage_row else ""
        week_line = tx["week_of"].format(n=view.week, total=view.weeks_total) if view.weeks_total \
            else tx["week_n"].format(n=view.week)
        final = progress.finish_of_route(view)
        if final and final.finish:
            finish_line = tx["finish"].format(stage=getattr(final, f"name_{suffix}"), when=_when(final, lang))
            if not view.path_known:
                finish_line += f", {tx['fork']}"
        elif view.current.by_teacher:
            finish_line = tx["by_teacher"]
        if view.next_exam:
            exam_line = tx["next_exam"].format(d=schedule.human_date(view.next_exam, lang))
            exam_days = (view.next_exam - on).days
            status = "risk" if rules.exam_risk(con, student_id, g, week, view.next_exam, on) else "on_plan"
    else:
        start = date.fromisoformat(g["start_date"])
        week_line = tx["week_n"].format(n=max(1, schedule.stage_week(start, on, False)))

    data = CardData(
        lang=lang, name=s["full_name"], group=g["name"], center=repo.get_setting(con, "center_name"),
        week_text=week_text(week, lang), subject=g[f"subject_{suffix}"], stage_name=stage_name,
        week_line=week_line, topic=g["current_topic"], view=view, finish_line=finish_line,
        next_exam_line=exam_line, status=status, comment=report["comment"], about=about,
        exam_days=exam_days, star=bool(report.get("star")), show_attendance=repo.attendance_on(con))

    # посещаемость за месяц (30 дней до конца недели) — только если владелец её включил
    if data.show_attendance:
        end = min(week + timedelta(days=6), on)
        rows = con.execute("SELECT status FROM attendance WHERE student_id = ? AND group_id = ? "
                           "AND lesson_date BETWEEN ? AND ? ORDER BY lesson_date",
                           (student_id, group_id, (end - timedelta(days=29)).isoformat(), end.isoformat())).fetchall()
        data.att_marks = [r["status"] for r in rows]
        data.att_total = len(rows)
        data.att_attended = sum(1 for r in rows if r["status"] in ("present", "late"))
        data.att_late = sum(1 for r in rows if r["status"] == "late")
        data.att_excused = sum(1 for r in rows if r["status"] == "excused")

    # показатели недели и стрелки относительно среднего за 4 предыдущие недели
    # (вопрос, который учитель на этой неделе не оценивал, на карточку не попадает)
    questions = reports.questions_for(con, g["subject"])
    history = reports.reports_for_weeks(con, group_id, [week - timedelta(weeks=i) for i in range(1, 5)])
    past = history.get(student_id, {})
    for q in questions:
        if q["id"] not in report["answers"]:
            continue
        value = report["answers"][q["id"]]
        old = [w["answers"][q["id"]] for w in past.values() if q["id"] in w["answers"]]
        arrow = None
        if old:
            diff = value - sum(old) / len(old)
            arrow = 1 if diff >= 0.5 else -1 if diff <= -0.5 else 0
        data.metrics.append(Metric(q[f"text_{suffix}"], value, q[f"opt{value}_{suffix}"], arrow))

    data.summary = summary(data)
    if rules.growth_streak(con, student_id, group_id, week):
        data.praise = tx["praise"].format(n=repo.get_int(con, "hint_growth_weeks", 3))
    return data


def summary(data: CardData) -> str:
    """Одна фраза: посещаемость (если включена) + самый сильный и самый слабый показатель."""
    tx = TX[data.lang]
    parts = []
    if data.show_attendance and data.att_total:
        rate = data.att_attended / data.att_total
        parts.append(tx["att_good"] if rate >= 0.95 else tx["att_ok"] if rate >= 0.8 else tx["att_bad"])
    if data.metrics:
        best = max(data.metrics, key=lambda m: m.value)
        worst = min(data.metrics, key=lambda m: m.value)
        if best.value == worst.value:
            parts.append(tx["even_top"] if best.value == 3 else tx["even"])
        else:
            parts.append(tx["strong"].format(x=best.label.lower()))
            parts.append(tx["weak"].format(x=worst.label.lower()))
    return " ".join(parts)


# ================================================================ рисование

@lru_cache(maxsize=48)
def font(weight: int, size: int) -> ImageFont.FreeTypeFont:
    name = {600: "Nunito_600SemiBold.ttf", 800: "Nunito_800ExtraBold.ttf", 900: "Nunito_900Black.ttf"}[weight]
    return ImageFont.truetype(str(FONTS / name), size)


def _wrap(draw, text: str, fnt, width: int, max_lines: int = 3) -> list[str]:
    words, lines, line = text.split(), [], ""
    for w in words:
        test = f"{line} {w}".strip()
        if draw.textlength(test, font=fnt) <= width:
            line = test
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        while lines[-1] and draw.textlength(lines[-1] + "…", font=fnt) > width:
            lines[-1] = lines[-1][:-1]
        lines[-1] += "…"
    return lines


def _fit(draw, text: str, fnt, width: int) -> str:
    """Одна строка: если не помещается — обрезать с «…»."""
    if draw.textlength(text, font=fnt) <= width:
        return text
    while text and draw.textlength(text + "…", font=fnt) > width:
        text = text[:-1]
    return text + "…"


def _panel(draw, y: int, h: int, fill: str = C["panel"]) -> None:
    draw.rounded_rectangle((M, y, W - M, y + h), radius=28, fill=C["line2"])          # «толщина»
    draw.rounded_rectangle((M, y, W - M, y + h - 6), radius=28, fill=fill, outline=C["line"], width=3)


def _check(draw, cx: int, cy: int, r: int, color: str = "#ffffff") -> None:
    draw.line([(cx - r * 0.45, cy), (cx - r * 0.1, cy + r * 0.38), (cx + r * 0.5, cy - r * 0.35)],
              fill=color, width=max(3, r // 5), joint="curve")


def _star(draw, cx: float, cy: float, r: float, fill: str) -> None:
    import math
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.45
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    draw.polygon(pts, fill=fill)


def _arrow(draw, x: int, y: int, up: bool) -> None:
    color = C["ok"] if up else C["down"]
    if up:
        draw.polygon([(x, y + 16), (x + 11, y), (x + 22, y + 16)], fill=color)
        draw.rectangle((x + 7, y + 14, x + 15, y + 25), fill=color)
    else:
        draw.polygon([(x, y + 9), (x + 11, y + 25), (x + 22, y + 9)], fill=color)
        draw.rectangle((x + 7, y, x + 15, y + 11), fill=color)


def _short(name: str) -> str:
    return name.replace("Курс ", "").replace(" kursi", "")


# ---------------------------------------------------------------- карта-змейка

PER_ROW = 5
MAX_ITEMS = 10
ROW_GAP = 150


def _route_items(data: CardData) -> list[dict]:
    """Станции для карты: [{label, state, sub, gap_before}], не больше 10 (окно вокруг «сейчас»)."""
    tx = TX[data.lang]
    suffix = "uz" if data.lang == "uz" else "ru"
    nodes = [n for n in data.view.nodes if n.state != "grey"]
    items = []
    for n in nodes:
        sub = ""
        if n.state == "done":
            sub = tx["passed"]
        elif n.state == "current":
            sub = tx["wk_short"].format(n=data.view.week, total=data.view.weeks_total) if data.view.weeks_total \
                else tx["wk_short_n"].format(n=data.view.week)
        elif n.finish:
            sub = _month_short(n.finish_max or n.finish, data.lang)
        items.append({"label": _short(getattr(n, f"name_{suffix}")), "state": n.state, "sub": sub, "gap": False})
    if any(n.state == "grey" for n in data.view.nodes):
        items.append({"label": "CEFR / IELTS", "state": "grey", "sub": "", "gap": False})
    if len(items) > MAX_ITEMS:
        cur = next((i for i, it in enumerate(items) if it["state"] == "current"), 0)
        start = max(0, min(cur - 2, len(items) - MAX_ITEMS))
        window = items[start:start + MAX_ITEMS]
        if start + MAX_ITEMS < len(items):
            window = window[:MAX_ITEMS - 1] + [dict(items[-1], gap=True)]
        items = window
    return items


def _snake(draw, data: CardData, top: int) -> int:
    """Рисует станции змейкой (до 2 рядов по 5). Возвращает высоту нарисованного."""
    items = _route_items(data)
    rows = 1 if len(items) <= PER_ROW else 2
    left, right = M + 100, W - M - 100
    n_cols = min(PER_ROW, len(items)) if rows == 1 else PER_ROW
    step = (right - left) / max(1, n_cols - 1) if n_cols > 1 else 0
    pos = []
    for i in range(len(items)):
        row, col = divmod(i, PER_ROW)
        x = left + col * step if row == 0 else right - col * step
        if n_cols == 1:
            x = (left + right) / 2
        pos.append((int(x), top + row * ROW_GAP))

    def travelled(i: int) -> bool:   # отрезок к станции i уже пройден
        return items[i]["state"] in ("done", "current")

    # дорога
    for i in range(len(items) - 1):
        (x1, y1), (x2, y2) = pos[i], pos[i + 1]
        color = C["accent"] if travelled(i + 1) else C["line2"]
        if y1 == y2:
            if items[i + 1]["gap"]:
                for xx in range(min(x1, x2) + 10, max(x1, x2) - 10, 28):
                    draw.line((xx, y1, xx + 14, y1), fill=C["line2"], width=10)
            else:
                draw.line((x1, y1, x2, y2), fill=color, width=12)
        else:  # разворот справа
            r = (y2 - y1) // 2
            draw.arc((x1 - r, y1, x1 + r, y2), start=-90, end=90, fill=color, width=12)

    # станции
    for (x, y), it in zip(pos, items):
        state = it["state"]
        if state == "done":
            r = 28
            draw.ellipse((x - r, y - r + 5, x + r, y + r + 5), fill=C["accent_dark"])
            draw.ellipse((x - r, y - r, x + r, y + r), fill=C["accent"])
            _check(draw, x, y, r)
        elif state == "current":
            r = 38
            frac = 0.0
            if data.view.weeks_total:
                frac = min(1.0, data.view.week / data.view.weeks_total)
            draw.ellipse((x - r - 16, y - r - 16, x + r + 16, y + r + 16), fill=C["accent_soft"])
            if frac:
                draw.arc((x - r - 12, y - r - 12, x + r + 12, y + r + 12), start=-90, end=-90 + 360 * frac,
                         fill=C["accent_dark"], width=8)
            draw.ellipse((x - r, y - r + 6, x + r, y + r + 6), fill=C["accent_dark"])
            draw.ellipse((x - r, y - r, x + r, y + r), fill=C["accent"])
            _star(draw, x, y, 20, "#ffffff")
            label = TX[data.lang]["here"]
            lw = draw.textlength(label, font=font(900, 21)) + 24
            draw.rounded_rectangle((x - lw / 2, y - r - 52, x + lw / 2, y - r - 20), radius=16, fill=C["text"])
            draw.polygon([(x - 8, y - r - 22), (x + 8, y - r - 22), (x, y - r - 13)], fill=C["text"])
            draw.text((x, y - r - 36), label, font=font(900, 21), fill="#ffffff", anchor="mm")
        elif state == "grey":
            r = 26
            draw.ellipse((x - r, y - r, x + r, y + r), fill=C["grey"], outline=C["line2"], width=4)
            draw.text((x, y), "?", font=font(900, 26), fill=C["muted"], anchor="mm")
        else:
            r = 26
            draw.ellipse((x - r, y - r + 5, x + r, y + r + 5), fill=C["line2"])
            draw.ellipse((x - r, y - r, x + r, y + r), fill=C["panel"], outline=C["line2"], width=5)
        big = state == "current"
        name_font = font(900, 26 if big else 22)
        label = _fit(draw, it["label"], name_font, int(step or 200) - 12)
        ly = y + (54 if big else 40)
        draw.text((x, ly), label, font=name_font, fill=C["text"] if state in ("done", "current") else C["muted"],
                  anchor="mt")
        if it["sub"]:
            draw.text((x, ly + (31 if big else 27)), it["sub"], font=font(800 if big else 600, 19),
                      fill=C["accent_dark"] if big else C["muted"], anchor="mt")
    return (rows - 1) * ROW_GAP + 110


def _week_track(draw, data: CardData, y: int, inner_left: int, inner_right: int) -> int:
    """Недели внутри станции до экзамена: 8 полосок и флажок с датой. Возвращает высоту."""
    view = data.view
    if not view or not view.weeks_total:
        return 0
    tx = TX[data.lang]
    if data.exam_days is not None and view.next_exam:
        right_text = tx["exam_today"] if data.exam_days == 0 else \
            tx["exam_in"].format(d=schedule.human_date(view.next_exam, data.lang), n=data.exam_days)
    else:
        right_text = ""
    draw.text((inner_left, y), tx["week_of"].format(n=view.week, total=view.weeks_total).capitalize(),
              font=font(900, 23), fill=C["text"])
    if right_text:
        draw.text((inner_right - 44, y + 2), right_text, font=font(800, 21), fill=C["accent_dark"], anchor="ra")
    by = y + 36
    n = view.weeks_total
    gap = 8
    seg = (inner_right - inner_left - 44 - gap * (n - 1)) / n
    for i in range(n):
        x0 = inner_left + i * (seg + gap)
        fill = C["accent"] if i + 1 < view.week else C["accent_dark"] if i + 1 == view.week else C["grey"]
        draw.rounded_rectangle((x0, by, x0 + seg, by + 16), radius=8, fill=fill)
    fx = inner_right - 30
    draw.line((fx, by - 10, fx, by + 22), fill=C["text"], width=4)               # флажок экзамена
    draw.polygon([(fx + 2, by - 10), (fx + 26, by - 3), (fx + 2, by + 5)], fill=C["accent_dark"])
    return 64


def render(data: CardData) -> bytes:
    """Рисует карточку. Если не помещается (длинное имя, много показателей) — компактный вариант."""
    png, height = _render(data, compact=False)
    if height > H - 16:
        png, height = _render(data, compact=True)
    render.last_height = height  # для автотестов: всё поместилось
    return png


def _render(data: CardData, compact: bool) -> tuple[bytes, int]:
    img = Image.new("RGB", (W, H), C["bg"])
    draw = ImageDraw.Draw(img)
    tx = TX[data.lang]
    inner = W - 2 * M
    gap = 10 if compact else 16

    # ---- 1. шапка: имя крупно (защита от ошибки пересылки)
    y = 36
    draw.text((M, y), _fit(draw, data.center or "", font(800, 27), inner // 2), font=font(800, 27), fill=C["accent_dark"])
    draw.text((W - M, y), tx["week"].format(d=data.week_text), font=font(800, 27), fill=C["muted"], anchor="ra")
    y += 42
    size = 66
    while size > 48 and draw.textlength(data.name, font=font(900, size)) > inner:
        size -= 2
    for line in _wrap(draw, data.name, font(900, size), inner, 2):
        draw.text((M, y), line, font=font(900, size), fill=C["text"])
        y += int(size * 1.08)
    chip = f"{tx['group']} {data.group}  ·  {data.stage_name or data.subject}"
    cw = int(draw.textlength(chip, font=font(800, 26))) + 40
    draw.rounded_rectangle((M, y + 4, M + cw, y + 50), radius=23, fill=C["accent_soft"])
    draw.text((M + 20, y + 27), chip, font=font(800, 26), fill=C["accent_dark"], anchor="lm")
    if data.star:
        label = tx["star"].replace("⭐ ", "")
        sw = int(draw.textlength(label, font=font(900, 26))) + 76
        sx = M + cw + 12
        draw.rounded_rectangle((sx, y + 4, sx + sw, y + 50), radius=23, fill=C["star_soft"], outline=C["star"], width=3)
        _star(draw, sx + 28, y + 27, 15, C["star"])
        draw.text((sx + 52, y + 27), label, font=font(900, 26), fill="#a77300", anchor="lm")
    y += 50 + gap + 2

    # ---- 2. карта пути (или курс и тема)
    body, lh = font(600, 25), 34
    inner_left, inner_right = M + 30, W - M - 30
    if data.view and data.view.current:
        lines = []
        now = tx["now"].format(stage=data.stage_name) + (f" — {data.about}" if data.about else "")
        lines.append(now)
        if data.topic:
            lines.append(tx["topic"].format(t=data.topic))
        if data.finish_line:
            lines.append(data.finish_line)
        if not data.view.weeks_total and data.next_exam_line:
            lines.append(data.next_exam_line)
        wrapped = [w for line in lines for w in _wrap(draw, line, body, inner - 60, 1 if compact else 2)]
        items = _route_items(data)
        snake_h = (ROW_GAP if len(items) > PER_ROW else 0) + 100
        track_h = 64 if data.view.weeks_total else 0
        head_h = 150
        h = head_h + snake_h + 18 + track_h + lh * len(wrapped) + 20
        _panel(draw, y, h)
        draw.text((M + 30, y + 22), tx["path"], font=font(900, 30), fill=C["text"])
        if data.status:
            label = tx[data.status]
            fill, color = (C["ok_soft"], C["ok_dark"]) if data.status == "on_plan" else (C["warn_soft"], C["warn"])
            pw = int(draw.textlength(label, font=font(900, 23))) + 36
            draw.rounded_rectangle((W - M - 28 - pw, y + 18, W - M - 28, y + 60), radius=21, fill=fill)
            draw.text((W - M - 28 - pw / 2, y + 39), label, font=font(900, 23), fill=color, anchor="mm")
        _snake(draw, data, y + head_h)
        ty = y + head_h + snake_h + 18
        ty += _week_track(draw, data, ty, inner_left, inner_right)
        for line in wrapped:
            draw.text((inner_left, ty), line, font=body, fill=C["text"])
            ty += lh
        y += h + gap
    else:
        lines = [f"{tx['course']}: {data.subject} · {data.week_line}"]
        if data.topic:
            lines.append(tx["topic"].format(t=data.topic))
        wrapped = [w for line in lines for w in _wrap(draw, line, body, inner - 60, 2)]
        h = 24 + lh * len(wrapped) + 20
        _panel(draw, y, h)
        ty = y + 22
        for line in wrapped:
            draw.text((inner_left, ty), line, font=body, fill=C["text"])
            ty += lh
        y += h + gap

    # ---- 3. посещаемость за месяц (если владелец её включил)
    if data.show_attendance:
        h = 100
        _panel(draw, y, h)
        draw.text((M + 30, y + 16), tx["attendance"], font=font(800, 23), fill=C["muted"])
        if data.att_total:
            big = tx["att_line"].format(a=data.att_attended, n=data.att_total)
            draw.text((M + 30, y + 44), big, font=font(900, 36), fill=C["text"])
            extra = []
            if data.att_late:
                extra.append(tx["late"].format(k=data.att_late))
            if data.att_excused:
                extra.append(tx["excused"].format(k=data.att_excused))
            if extra:
                bx = M + 30 + draw.textlength(big, font=font(900, 36)) + 20
                draw.text((bx, y + 56), ", ".join(extra), font=font(600, 24), fill=C["muted"])
            dot_colors = {"present": C["ok"], "late": C["warn"], "absent": C["down"], "excused": C["blue"]}
            marks = data.att_marks[-14:]
            dx = W - M - 30 - len(marks) * 26
            for i, m in enumerate(marks):
                draw.ellipse((dx + i * 26, y + 22, dx + i * 26 + 18, y + 40), fill=dot_colors[m])
        else:
            draw.text((M + 30, y + 50), tx["no_lessons"], font=font(800, 28), fill=C["muted"])
        y += h + gap

    # ---- 4. показатели недели: две колонки, полоски 0–3 и стрелки относительно 4 недель
    two = len(data.metrics) > 4
    cols = 2 if two else 1
    rows = -(-len(data.metrics) // cols) if data.metrics else 0
    cell_h = (62 if compact else 74) if two else (48 if compact else 62)
    h = 52 + rows * cell_h + 6
    _panel(draw, y, h)
    draw.text((M + 30, y + 14), tx["metrics"], font=font(800, 23), fill=C["muted"])
    col_w = (inner - 60 - (30 if two else 0)) / cols
    for i, m in enumerate(data.metrics):
        col, row = (i // rows, i % rows) if two else (0, i)
        x0 = M + 30 + col * (col_w + 30)
        y0 = y + 50 + row * cell_h
        if two:
            label_w = col_w - 40
            draw.text((x0, y0), _fit(draw, m.label, font(900, 23), int(label_w)), font=font(900, 23), fill=C["text"])
            bar_y = y0 + 32
            seg_w = (col_w - 40 - 2 * 6) / 3
            for k in range(3):
                bx = x0 + k * (seg_w + 6)
                draw.rounded_rectangle((bx, bar_y, bx + seg_w, bar_y + 14), radius=7,
                                       fill=C["accent"] if k < m.value else C["grey"])
            if m.arrow in (1, -1):
                _arrow(draw, int(x0 + col_w - 24), y0 + 2, m.arrow == 1)
            if not compact:
                draw.text((x0, bar_y + 17), _fit(draw, m.answer, font(600, 17), int(col_w)), font=font(600, 17),
                          fill=C["muted"])
        else:
            bar_x, bar_w = M + 400, inner - 400 - 84
            draw.text((x0, y0), m.label, font=font(800, 25), fill=C["text"])
            if not compact:
                draw.text((x0, y0 + 29), m.answer, font=font(600, 19), fill=C["muted"])
            seg_w = (bar_w - 2 * 8) / 3
            for k in range(3):
                bx = bar_x + k * (seg_w + 8)
                draw.rounded_rectangle((bx, y0 + 6, bx + seg_w, y0 + 30), radius=12,
                                       fill=C["accent"] if k < m.value else C["grey"])
            if m.arrow in (1, -1):
                _arrow(draw, W - M - 28 - 24, y0 + 4, m.arrow == 1)
    y += h + gap + 2

    # ---- 5–7. вывод, похвала, комментарий учителя
    for line in _wrap(draw, data.summary, font(800, 27), inner, 2 if compact else 3):
        draw.text((M + 4, y), line, font=font(800, 27), fill=C["text"])
        y += 36
    if data.praise:
        y += 6
        pw = min(inner, int(draw.textlength(data.praise, font=font(900, 25))) + 40)
        draw.rounded_rectangle((M, y, M + pw, y + 46), radius=23, fill=C["ok_soft"])
        draw.text((M + 20, y + 23), data.praise, font=font(900, 25), fill=C["ok_dark"], anchor="lm")
        y += 54
    if data.comment:
        y += 6
        draw.text((M + 4, y), tx["comment"], font=font(800, 21), fill=C["muted"])
        y += 29
        for line in _wrap(draw, f"«{data.comment}»", font(600, 27), inner, 2):
            draw.text((M + 4, y), line, font=font(600, 27), fill=C["text"])
            y += 35

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue(), y


KEEP_WEEKS = 8  # карточки старше 8 недель удаляются: их всегда можно нарисовать заново


def save(png: bytes, folder: Path, week: date, student_id: int, group_id: int) -> Path:
    target = folder / week.isoformat()
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"{student_id}-{group_id}.png"
    path.write_bytes(png)
    oldest = (week - timedelta(weeks=KEEP_WEEKS)).isoformat()
    for old in folder.iterdir():
        if old.is_dir() and old.name < oldest:
            for f in old.glob("*.png"):
                f.unlink(missing_ok=True)
            old.rmdir()
    return path
