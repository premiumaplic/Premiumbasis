"""Карточка-отчёт для родителя: PNG 1080×1350, одна на ученика за неделю.

Родитель должен понять главное за 10 секунд, не читая цифр. Сверху вниз:
имя и группа → путь по станциям (или курс и тема) → посещаемость за месяц →
показатели недели (полоски и стрелки) → одна фраза-вывод → похвала → комментарий учителя.
На карточке только данные одного ученика.
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
}

MONTHS = {
    "ru": ["январь", "февраль", "март", "апрель", "май", "июнь", "июль", "август", "сентябрь", "октябрь",
           "ноябрь", "декабрь"],
    "uz": ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avgust", "sentabr", "oktabr",
           "noyabr", "dekabr"],
}

# Тексты карточки. Узбекский — ЧЕРНОВИК, на проверку владельцу.
TX = {
    "ru": {
        "group": "Группа", "week": "Неделя {d}", "path": "Путь", "here": "сейчас здесь",
        "now": "Сейчас: {stage}", "week_of": "неделя {n} из {total}", "week_n": "неделя {n}",
        "topic": "Тема: {t}", "finish": "Прогноз финиша: {stage} — {when}", "fork": "дальше — CEFR или IELTS",
        "by_teacher": "Переход — по решению учителя", "next_exam": "Следующий экзамен: {d}",
        "on_plan": "Идёт по плану", "risk": "Есть риск повтора",
        "course": "Курс", "attendance": "Посещаемость за месяц",
        "att_line": "{a} из {n} уроков", "late": "опозданий: {k}", "excused": "по уважительной: {k}",
        "no_lessons": "отметок пока нет",
        "metrics": "Неделя в показателях", "att_good": "Посещаемость отличная.", "att_ok": "Посещаемость хорошая.",
        "att_bad": "Посещаемость нужно улучшить.", "strong": "Сильная сторона — {x}.",
        "weak": "Над чем работать — {x}.", "even_top": "Отличные результаты по всем показателям.",
        "even": "Ровные результаты по всем показателям.",
        "praise": "Молодец! Результаты растут {n} недели подряд.", "comment": "Комментарий учителя",
    },
    "uz": {
        "group": "Guruh", "week": "{d} haftasi", "path": "Yoʻl", "here": "hozir shu yerda",
        "now": "Hozir: {stage}", "week_of": "{total} haftadan {n}-hafta", "week_n": "{n}-hafta",
        "topic": "Mavzu: {t}", "finish": "Yakun prognozi: {stage} — {when}", "fork": "keyin — CEFR yoki IELTS",
        "by_teacher": "Oʻtish — oʻqituvchi qarori bilan", "next_exam": "Keyingi imtihon: {d}",
        "on_plan": "Reja boʻyicha", "risk": "Qayta oʻqish xavfi bor",
        "course": "Kurs", "attendance": "Oylik davomat",
        "att_line": "{n} darsdan {a} tasi", "late": "kechikish: {k}", "excused": "sababli: {k}",
        "no_lessons": "hali belgilar yoʻq",
        "metrics": "Hafta koʻrsatkichlari", "att_good": "Davomat aʼlo.", "att_ok": "Davomat yaxshi.",
        "att_bad": "Davomatni yaxshilash kerak.", "strong": "Kuchli tomoni — {x}.",
        "weak": "Ustida ishlash kerak — {x}.", "even_top": "Barcha koʻrsatkichlar aʼlo.",
        "even": "Barcha koʻrsatkichlar bir xil.",
        "praise": "Barakalla! Natijalar {n} hafta ketma-ket oʻsmoqda.", "comment": "Oʻqituvchi izohi",
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
    stage_name, week_line, finish_line, exam_line, status = None, "", "", "", None
    if view and view.current:
        stage_name = getattr(view.current, f"name_{suffix}")
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
            status = "risk" if rules.exam_risk(con, student_id, g, week, view.next_exam, on) else "on_plan"
    else:
        start = date.fromisoformat(g["start_date"])
        week_line = tx["week_n"].format(n=max(1, schedule.stage_week(start, on, False)))

    data = CardData(
        lang=lang, name=s["full_name"], group=g["name"], center=repo.get_setting(con, "center_name"),
        week_text=week_text(week, lang), subject=g[f"subject_{suffix}"], stage_name=stage_name,
        week_line=week_line, topic=g["current_topic"], view=view, finish_line=finish_line,
        next_exam_line=exam_line, status=status, comment=report["comment"])

    # посещаемость за месяц (30 дней до конца недели)
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
    """Одна фраза: посещаемость + самый сильный и самый слабый показатель."""
    tx = TX[data.lang]
    parts = []
    if data.att_total:
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

@lru_cache(maxsize=32)
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


def _panel(draw, y: int, h: int, fill: str = C["panel"]) -> None:
    draw.rounded_rectangle((M, y, W - M, y + h), radius=28, fill=C["line2"])          # «толщина»
    draw.rounded_rectangle((M, y, W - M, y + h - 6), radius=28, fill=fill, outline=C["line"], width=3)


def _check(draw, cx: int, cy: int, r: int, color: str = "#ffffff") -> None:
    draw.line([(cx - r * 0.45, cy), (cx - r * 0.1, cy + r * 0.38), (cx + r * 0.5, cy - r * 0.35)],
              fill=color, width=max(3, r // 5), joint="curve")


def _arrow(draw, x: int, y: int, up: bool) -> None:
    color = C["ok"] if up else C["down"]
    if up:
        draw.polygon([(x, y + 20), (x + 13, y), (x + 26, y + 20)], fill=color)
        draw.rectangle((x + 9, y + 18, x + 17, y + 30), fill=color)
    else:
        draw.polygon([(x, y + 10), (x + 13, y + 30), (x + 26, y + 10)], fill=color)
        draw.rectangle((x + 9, y, x + 17, y + 12), fill=color)


def _short(name: str) -> str:
    return name.replace("Курс ", "").replace(" kursi", "")


def _ribbon(draw, data: CardData, y: int) -> None:
    """Лента станций слева направо с отметкой «сейчас здесь». y — центр кружков."""
    suffix = "uz" if data.lang == "uz" else "ru"
    nodes = [n for n in data.view.nodes if n.state != "grey"]
    grey = [n for n in data.view.nodes if n.state == "grey"]
    items = [(_short(getattr(n, f"name_{suffix}")), n.state) for n in nodes]
    cur = next((i for i, n in enumerate(nodes) if n.state == "current"), 0)
    if grey:
        items.append(("CEFR / IELTS", "grey"))
    if len(items) > 7:
        start = max(0, min(cur - 2, len(items) - 6))
        window = items[start:start + 6]
        if start + 6 < len(items):
            window = window[:5] + [("…", "gap"), items[-1]]
        items = window
    n = len(items)
    left, right = M + 80, W - M - 80
    step = (right - left) / max(1, n - 1)
    xs = [int(left + i * step) for i in range(n)]
    cy = y
    for i in range(n - 1):
        color = C["accent"] if items[i + 1][1] in ("done", "current") else C["line2"]
        draw.line((xs[i], cy, xs[i + 1], cy), fill=color, width=8)
    for x, (label, state) in zip(xs, items):
        if state == "gap":
            draw.rectangle((x - 30, cy - 10, x + 30, cy + 10), fill=C["panel"])
            draw.text((x, cy), "• • •", font=font(900, 26), fill=C["line2"], anchor="mm")
            continue
        r = 32 if state == "current" else 22
        if state == "done":
            draw.ellipse((x - r, cy - r, x + r, cy + r), fill=C["accent"])
            _check(draw, x, cy, r)
        elif state == "current":
            draw.ellipse((x - r - 10, cy - r - 10, x + r + 10, cy + r + 10), fill=C["accent_soft"])
            draw.ellipse((x - r, cy - r, x + r, cy + r), fill=C["accent"], outline=C["accent_dark"], width=4)
            draw.ellipse((x - 10, cy - 10, x + 10, cy + 10), fill="#ffffff")
            draw.text((x, cy - r - 16), TX[data.lang]["here"], font=font(900, 22), fill=C["accent_dark"], anchor="mb")
        elif state == "grey":
            draw.ellipse((x - r, cy - r, x + r, cy + r), fill=C["grey"], outline=C["line2"], width=3)
        else:
            draw.ellipse((x - r, cy - r, x + r, cy + r), fill=C["panel"], outline=C["line2"], width=5)
        color = C["text"] if state in ("done", "current") else C["muted"]
        draw.text((x, cy + 46), label, font=font(900 if state == "current" else 800, 25 if state == "current" else 22),
                  fill=color, anchor="mt")


def render(data: CardData) -> bytes:
    """Рисует карточку. Если не помещается (длинное имя и комментарий) — компактный вариант."""
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
    gap = 10 if compact else 14

    # ---- 1. шапка: имя крупно (защита от ошибки пересылки)
    y = 40
    draw.text((M, y), data.center or "", font=font(800, 27), fill=C["accent_dark"])
    draw.text((W - M, y), tx["week"].format(d=data.week_text), font=font(800, 27), fill=C["muted"], anchor="ra")
    y += 44
    size = 68
    while size > 50 and draw.textlength(data.name, font=font(900, size)) > inner:
        size -= 2
    for line in _wrap(draw, data.name, font(900, size), inner, 2):
        draw.text((M, y), line, font=font(900, size), fill=C["text"])
        y += int(size * 1.1)
    chip = f"{tx['group']} {data.group}  ·  {data.stage_name or data.subject}"
    cw = int(draw.textlength(chip, font=font(800, 27))) + 40
    draw.rounded_rectangle((M, y + 4, M + cw, y + 50), radius=23, fill=C["accent_soft"])
    draw.text((M + 20, y + 27), chip, font=font(800, 27), fill=C["accent_dark"], anchor="lm")
    y += 50 + gap + 4

    # ---- 2. путь по станциям (или курс и тема)
    body, lh = font(600, 26), 36
    if data.view and data.view.current:
        first = tx["now"].format(stage=data.stage_name) + " · " + data.week_line
        lines = [first]
        if data.topic:
            lines.append(tx["topic"].format(t=data.topic))
        if data.finish_line:
            lines.append(data.finish_line)
        if data.next_exam_line:
            lines.append(data.next_exam_line)
        wrapped = [w for line in lines for w in _wrap(draw, line, body, inner - 60, 1 if compact else 2)]
        top = 200
        h = top + lh * len(wrapped) + 14
        _panel(draw, y, h)
        draw.text((M + 30, y + 22), tx["path"], font=font(900, 30), fill=C["text"])
        if data.status:
            label = tx[data.status]
            fill, color = (C["ok_soft"], C["ok_dark"]) if data.status == "on_plan" else (C["warn_soft"], C["warn"])
            pw = int(draw.textlength(label, font=font(900, 23))) + 36
            draw.rounded_rectangle((W - M - 28 - pw, y + 18, W - M - 28, y + 60), radius=21, fill=fill)
            draw.text((W - M - 28 - pw / 2, y + 39), label, font=font(900, 23), fill=color, anchor="mm")
        _ribbon(draw, data, y + 130)
        ty = y + top
        for line in wrapped:
            draw.text((M + 30, ty), line, font=body, fill=C["text"])
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
            draw.text((M + 30, ty), line, font=body, fill=C["text"])
            ty += lh
        y += h + gap

    # ---- 3. посещаемость за месяц
    h = 108
    _panel(draw, y, h)
    draw.text((M + 30, y + 18), tx["attendance"], font=font(800, 24), fill=C["muted"])
    if data.att_total:
        big = tx["att_line"].format(a=data.att_attended, n=data.att_total)
        draw.text((M + 30, y + 48), big, font=font(900, 38), fill=C["text"])
        extra = []
        if data.att_late:
            extra.append(tx["late"].format(k=data.att_late))
        if data.att_excused:
            extra.append(tx["excused"].format(k=data.att_excused))
        if extra:
            bx = M + 30 + draw.textlength(big, font=font(900, 38)) + 20
            draw.text((bx, y + 60), ", ".join(extra), font=font(600, 25), fill=C["muted"])
        dot_colors = {"present": C["ok"], "late": C["warn"], "absent": C["down"], "excused": "#5ab4f0"}
        marks = data.att_marks[-14:]
        dx = W - M - 30 - len(marks) * 26
        for i, m in enumerate(marks):
            draw.ellipse((dx + i * 26, y + 24, dx + i * 26 + 18, y + 42), fill=dot_colors[m])
    else:
        draw.text((M + 30, y + 52), tx["no_lessons"], font=font(800, 30), fill=C["muted"])
    y += h + gap

    # ---- 4. показатели недели: полоски 0–3 и стрелки относительно 4 недель
    row_h = 40 if compact else 54
    h = 58 + row_h * len(data.metrics) + 8
    _panel(draw, y, h)
    draw.text((M + 30, y + 18), tx["metrics"], font=font(800, 24), fill=C["muted"])
    ry = y + 58
    bar_x, bar_w = M + 400, inner - 400 - 84
    for m in data.metrics:
        draw.text((M + 30, ry), m.label, font=font(800, 25), fill=C["text"])
        if not compact:
            draw.text((M + 30, ry + 29), m.answer, font=font(600, 19), fill=C["muted"])
        seg_w = (bar_w - 2 * 8) / 3
        for k in range(3):
            x0 = bar_x + k * (seg_w + 8)
            draw.rounded_rectangle((x0, ry + 6, x0 + seg_w, ry + 30), radius=12,
                                   fill=C["accent"] if k < m.value else C["grey"])
        if m.arrow in (1, -1):
            _arrow(draw, W - M - 28 - 26, ry + 3, m.arrow == 1)
        ry += row_h
    y += h + gap + 4

    # ---- 5–7. вывод, похвала, комментарий учителя
    for line in _wrap(draw, data.summary, font(800, 28), inner, 3):
        draw.text((M + 4, y), line, font=font(800, 28), fill=C["text"])
        y += 37
    if data.praise:
        y += 6
        pw = min(inner, int(draw.textlength(data.praise, font=font(900, 26))) + 40)
        draw.rounded_rectangle((M, y, M + pw, y + 48), radius=24, fill=C["ok_soft"])
        draw.text((M + 20, y + 24), data.praise, font=font(900, 26), fill=C["ok_dark"], anchor="lm")
        y += 56
    if data.comment:
        y += 6
        draw.text((M + 4, y), tx["comment"], font=font(800, 22), fill=C["muted"])
        y += 30
        for line in _wrap(draw, f"«{data.comment}»", font(600, 28), inner, 2):
            draw.text((M + 4, y), line, font=font(600, 28), fill=C["text"])
            y += 36

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
