"""Профиль ученика: рейтинг по критериям (1–10), выученные и непонятные темы.

Учитель заполняет это в приложении группы, меню «Навыки и темы».
Рейтинг хранится историей (одна оценка в день), профиль показывает последнюю и прошлую.
"""

from datetime import date

from bot import repo

SCALE_MAX = 10
TITLE_MAX = 60          # длина названия темы
TOPICS_MAX = 60         # тем на ученика в одном предмете (больше — сначала удалите старые)
LOG_KEEP = 12           # сколько последних тем уроков группы показывать подсказками
STATUSES = ("learned", "unclear")


def criteria_for(con, subject: str, only_active: bool = True) -> list:
    rows = con.execute("SELECT * FROM criteria" + (" WHERE active = 1" if only_active else "") +
                       " ORDER BY sort, id").fetchall()
    return [c for c in rows if c["subjects"] == "*" or subject in c["subjects"].split(",")]


def clean_title(text) -> str | None:
    """Название темы без лишних пробелов или None, если оно пустое или слишком длинное."""
    if not isinstance(text, str):
        return None
    title = " ".join(text.split())
    return title if 0 < len(title) <= TITLE_MAX else None


# ---------------------------------------------------------------- чтение

def latest_ratings(con, student_ids: list[int], subject: str) -> dict[int, list[dict]]:
    """{ученик: [последняя оценка, предыдущая]}; оценка — {"on", "by", "v": {критерий: значение}}."""
    if not student_ids:
        return {}
    marks = ",".join("?" * len(student_ids))
    rows = con.execute(
        f"SELECT a.id, a.student_id, a.rated_on, a.rated_by, v.criterion_id, v.value "
        f"FROM assessments a LEFT JOIN assessment_values v ON v.assessment_id = a.id "
        f"WHERE a.subject = ? AND a.student_id IN ({marks}) AND a.id IN ("
        f"  SELECT x.id FROM assessments x WHERE x.student_id = a.student_id AND x.subject = a.subject "
        f"  ORDER BY x.rated_on DESC, x.id DESC LIMIT 2) "
        f"ORDER BY a.student_id, a.rated_on DESC, a.id DESC", [subject, *student_ids]).fetchall()
    out: dict[int, list[dict]] = {}
    by_id: dict[int, dict] = {}
    for r in rows:
        item = by_id.get(r["id"])
        if item is None:
            item = by_id[r["id"]] = {"on": r["rated_on"], "by": r["rated_by"], "v": {}}
            out.setdefault(r["student_id"], []).append(item)
        if r["criterion_id"] is not None:
            item["v"][r["criterion_id"]] = r["value"]
    return out


def topics_of(con, student_ids: list[int], subject: str) -> dict[int, dict[str, list[str]]]:
    """{ученик: {"learned": [...], "unclear": [...]}} — сначала недавние."""
    if not student_ids:
        return {}
    marks = ",".join("?" * len(student_ids))
    out: dict[int, dict[str, list[str]]] = {}
    for r in con.execute(f"SELECT student_id, title, status FROM student_topics WHERE subject = ? "
                         f"AND student_id IN ({marks}) ORDER BY updated_on DESC, id DESC", [subject, *student_ids]):
        out.setdefault(r["student_id"], {"learned": [], "unclear": []})[r["status"]].append(r["title"])
    return out


def topic_log(con, group_id: int) -> list[str]:
    """Последние темы уроков группы, без повторов, от новой к старой."""
    seen, out = set(), []
    for r in con.execute("SELECT title FROM topic_log WHERE group_id = ? ORDER BY id DESC LIMIT 60", (group_id,)):
        key = r["title"].casefold()
        if key not in seen:
            seen.add(key)
            out.append(r["title"])
        if len(out) >= LOG_KEEP:
            break
    return out


def overall(values: dict) -> float | None:
    """Общий рейтинг — среднее по оценённым критериям (1–10)."""
    vals = [v for v in values.values() if v]
    return round(sum(vals) / len(vals), 1) if vals else None


# ---------------------------------------------------------------- запись

def log_topic(con, group_id: int, title: str, on: date) -> None:
    con.execute("INSERT INTO topic_log (group_id, title, set_on) VALUES (?, ?, ?)", (group_id, title, on.isoformat()))


def save_ratings(con, tg_id: int, student_id: int, subject: str, group_id: int, on: date,
                 values: dict[int, int]) -> None:
    """Оценка за день: повторная в тот же день меняет только присланные критерии."""
    row = con.execute("SELECT id FROM assessments WHERE student_id = ? AND subject = ? AND rated_on = ?",
                      (student_id, subject, on.isoformat())).fetchone()
    if row is None:
        aid = con.execute("INSERT INTO assessments (student_id, subject, group_id, rated_on, rated_by) "
                          "VALUES (?, ?, ?, ?, ?)", (student_id, subject, group_id, on.isoformat(), tg_id)).lastrowid
    else:
        aid = row["id"]
        con.execute("UPDATE assessments SET rated_by = ?, group_id = ? WHERE id = ?", (tg_id, group_id, aid))
    con.executemany("INSERT INTO assessment_values (assessment_id, criterion_id, value) VALUES (?, ?, ?) "
                    "ON CONFLICT(assessment_id, criterion_id) DO UPDATE SET value = excluded.value",
                    [(aid, cid, v) for cid, v in values.items()])


def set_topics(con, tg_id: int, student_id: int, subject: str, on: date,
               learned: list[str], unclear: list[str], removed: list[str]) -> int:
    """Применяет изменения тем. Возвращает, сколько тем изменено.

    Тема узнаётся без учёта регистра (в Python: lower() в SQLite не знает кириллицу).
    """
    existing = {r["title"].casefold(): r["id"] for r in con.execute(
        "SELECT id, title FROM student_topics WHERE student_id = ? AND subject = ?", (student_id, subject))}
    n = 0
    for title in removed:
        row_id = existing.pop(title.casefold(), None)
        if row_id is not None:
            con.execute("DELETE FROM student_topics WHERE id = ?", (row_id,))
            n += 1
    for status, titles in (("learned", learned), ("unclear", unclear)):
        for title in titles:
            row_id = existing.get(title.casefold())
            if row_id is not None:
                con.execute("UPDATE student_topics SET status = ?, updated_on = ?, updated_by = ? WHERE id = ?",
                            (status, on.isoformat(), tg_id, row_id))
            else:
                existing[title.casefold()] = con.execute(
                    "INSERT INTO student_topics (student_id, subject, title, status, updated_on, updated_by) "
                    "VALUES (?, ?, ?, ?, ?, ?)", (student_id, subject, title, status, on.isoformat(), tg_id)).lastrowid
            n += 1
    return n


def topic_count(con, student_id: int, subject: str) -> int:
    return con.execute("SELECT count(*) FROM student_topics WHERE student_id = ? AND subject = ?",
                       (student_id, subject)).fetchone()[0]


def rater_names(con, tg_ids: set[int]) -> dict[int, str]:
    """Кто ставил оценку: имя учителя (коротко) по Telegram ID."""
    out = {}
    for tg in tg_ids:
        row = repo.teacher_by_tg(con, tg)
        out[tg] = repo.short_name(row["name"]) if row else ""
    return out
