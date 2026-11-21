"""Данные этапа 2: посещаемость, недельные отчёты, темы, защита от повторной отправки."""

from datetime import date, timedelta

# Статусы посещаемости: код в форме -> значение в базе
ATT_CODES = ["present", "late", "absent", "excused"]
ATT_INDEX = {name: i for i, name in enumerate(ATT_CODES)}


def week_start(day: date) -> date:
    """Понедельник недели, в которую попадает день."""
    return day - timedelta(days=day.weekday())


# ---------------------------------------------------------------- вопросы и фразы

def questions_for(con, subject_code: str) -> list:
    rows = con.execute("SELECT * FROM questions WHERE active = 1 ORDER BY sort").fetchall()
    return [q for q in rows if q["subjects"] == "*" or subject_code in q["subjects"].split(",")]


def phrases(con) -> list:
    return con.execute("SELECT * FROM phrases WHERE active = 1 ORDER BY sort").fetchall()


# ---------------------------------------------------------------- посещаемость

def attendance_by_date(con, group_id: int, dates: list[date]) -> dict[str, dict[int, str]]:
    if not dates:
        return {}
    marks = "?" + ",?" * (len(dates) - 1)
    rows = con.execute(f"SELECT student_id, lesson_date, status FROM attendance "
                       f"WHERE group_id = ? AND lesson_date IN ({marks})",
                       [group_id, *[d.isoformat() for d in dates]]).fetchall()
    out: dict[str, dict[int, str]] = {}
    for r in rows:
        out.setdefault(r["lesson_date"], {})[r["student_id"]] = r["status"]
    return out


def save_attendance(con, tg_id: int, group_id: int, lesson_date: date, marks: list[tuple[int, str]]) -> None:
    con.executemany(
        "INSERT INTO attendance (student_id, group_id, lesson_date, status, marked_by) VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(student_id, group_id, lesson_date) DO UPDATE SET status = excluded.status, "
        "marked_by = excluded.marked_by, marked_at = datetime('now')",
        [(sid, group_id, lesson_date.isoformat(), status, tg_id) for sid, status in marks])


# ---------------------------------------------------------------- недельные отчёты

def reports_for_weeks(con, group_id: int, weeks: list[date]) -> dict[int, dict[str, dict]]:
    """{student_id: {week_iso: {"answers": {question_id: value}, "comment": str, "star": bool}}}"""
    if not weeks:
        return {}
    marks = "?" + ",?" * (len(weeks) - 1)
    rows = con.execute(
        f"SELECT r.id, r.student_id, r.week_start, r.comment, r.star, a.question_id, a.value "
        f"FROM weekly_reports r LEFT JOIN weekly_answers a ON a.report_id = r.id "
        f"WHERE r.group_id = ? AND r.week_start IN ({marks})",
        [group_id, *[w.isoformat() for w in weeks]]).fetchall()
    out: dict[int, dict[str, dict]] = {}
    for r in rows:
        item = out.setdefault(r["student_id"], {}).setdefault(
            r["week_start"], {"answers": {}, "comment": r["comment"], "star": bool(r["star"])})
        if r["question_id"] is not None:
            item["answers"][r["question_id"]] = r["value"]
    return out


def last_answers_before(con, group_id: int, week: date) -> dict[int, dict[int, int]]:
    """Ответы из последнего отчёта каждого ученика группы до указанной недели."""
    rows = con.execute(
        "SELECT r.student_id, a.question_id, a.value FROM weekly_reports r "
        "JOIN weekly_answers a ON a.report_id = r.id "
        "WHERE r.group_id = ? AND r.week_start = (SELECT max(week_start) FROM weekly_reports x "
        "  WHERE x.student_id = r.student_id AND x.group_id = r.group_id AND x.week_start < ?)",
        (group_id, week.isoformat())).fetchall()
    out: dict[int, dict[int, int]] = {}
    for r in rows:
        out.setdefault(r["student_id"], {})[r["question_id"]] = r["value"]
    return out


def save_weekly(con, tg_id: int, group_id: int, week: date, student_id: int,
                answers: dict[int, int], comment: str, star: bool = False) -> None:
    """Сохраняет отчёт ученика за неделю. Пустой комментарий не стирает прежний.

    answers — только оценённые вопросы (необязательный вопрос можно пропустить).
    star — «звезда недели» (значок на карточке родителю).
    """
    row = con.execute("SELECT id, comment FROM weekly_reports WHERE student_id = ? AND group_id = ? "
                      "AND week_start = ?", (student_id, group_id, week.isoformat())).fetchone()
    if row:
        report_id = row["id"]
        con.execute("UPDATE weekly_reports SET comment = ?, star = ?, created_by = ?, created_at = datetime('now') "
                    "WHERE id = ?", (comment or row["comment"], int(star), tg_id, report_id))
        con.execute("DELETE FROM weekly_answers WHERE report_id = ?", (report_id,))
    else:
        report_id = con.execute(
            "INSERT INTO weekly_reports (student_id, group_id, week_start, comment, star, created_by) "
            "VALUES (?, ?, ?, ?, ?, ?)", (student_id, group_id, week.isoformat(), comment, int(star),
                                          tg_id)).lastrowid
    con.executemany("INSERT INTO weekly_answers (report_id, question_id, value) VALUES (?, ?, ?)",
                    [(report_id, qid, value) for qid, value in answers.items()])


def students_without_report(con, group_id: int, week: date) -> list:
    return con.execute(
        "SELECT s.* FROM students s JOIN enrollments e ON e.student_id = s.id "
        "WHERE e.group_id = ? AND e.date_to IS NULL AND s.active = 1 AND NOT EXISTS ("
        "  SELECT 1 FROM weekly_reports r WHERE r.student_id = s.id AND r.group_id = ? AND r.week_start = ?) "
        "ORDER BY s.full_name", (group_id, group_id, week.isoformat())).fetchall()


def week_levels(con, group_id: int, weeks: list[date]) -> dict[int, dict[str, float]]:
    """Средний уровень (0–3) каждого ученика группы по неделям: {student_id: {week_iso: level}}."""
    if not weeks:
        return {}
    marks = "?" + ",?" * (len(weeks) - 1)
    rows = con.execute(
        f"SELECT r.student_id, r.week_start, avg(a.value) AS level FROM weekly_reports r "
        f"JOIN weekly_answers a ON a.report_id = r.id "
        f"WHERE r.group_id = ? AND r.week_start IN ({marks}) GROUP BY r.student_id, r.week_start",
        [group_id, *[w.isoformat() for w in weeks]]).fetchall()
    out: dict[int, dict[str, float]] = {}
    for r in rows:
        out.setdefault(r["student_id"], {})[r["week_start"]] = r["level"]
    return out


def level_char(level: float | None) -> str:
    """Уровень 0–3 одним знаком для ссылки приложения: 0…9, «-» — отчёта нет."""
    return "-" if level is None else str(min(9, max(0, round(level * 3))))


# ---------------------------------------------------------------- темы

def topics_for_stage(con, stage_id: int | None) -> list:
    if not stage_id:
        return []
    return con.execute("SELECT * FROM topics WHERE stage_id = ? ORDER BY unit_no", (stage_id,)).fetchall()


def set_topic(con, group_id: int, text: str) -> None:
    con.execute("UPDATE groups SET current_topic = ? WHERE id = ?", (text, group_id))


# ---------------------------------------------------------------- повторная отправка

def submission_seen(con, uuid: str) -> bool:
    return con.execute("SELECT 1 FROM submissions WHERE uuid = ?", (uuid,)).fetchone() is not None


def record_submission(con, uuid: str, tg_id: int, kind: str, status: str) -> None:
    con.execute("INSERT INTO submissions (uuid, tg_id, kind, status) VALUES (?, ?, ?, ?)",
                (uuid, tg_id, kind, status))


def set_current_group(con, teacher_id: int, group_id: int) -> None:
    con.execute("UPDATE teachers SET current_group_id = ? WHERE id = ?", (group_id, teacher_id))
