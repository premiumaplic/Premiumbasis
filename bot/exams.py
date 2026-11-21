"""Экзамены и переходы по станциям карты.

На станциях с экзаменом: балл не ниже проходного — следующая станция, ниже — повтор.
Учитель может изменить решение, указав причину. На станциях без экзамена (Roundup и др.)
переход решает учитель. После B2 — развилка: путь CEFR или IELTS выбирает учитель или владелец.
"""

from datetime import date

from bot import progress, repo


def auto_decision(score: float, pass_score: float) -> str:
    return "pass" if score >= pass_score else "repeat"


def save_exam(con, group_id: int, stage, exam_date: date, tg_id: int) -> int:
    """Экзамен группы по станции за день. Повторная отправка в тот же день — тот же экзамен."""
    row = con.execute("SELECT id FROM exams WHERE group_id = ? AND stage_id = ? AND exam_date = ?",
                      (group_id, stage["id"], exam_date.isoformat())).fetchone()
    if row:
        con.execute("UPDATE exams SET pass_score = ?, max_score = ? WHERE id = ?",
                    (stage["pass_score"], stage["max_score"], row["id"]))
        return row["id"]
    return con.execute("INSERT INTO exams (group_id, stage_id, exam_date, pass_score, max_score) "
                       "VALUES (?, ?, ?, ?, ?)", (group_id, stage["id"], exam_date.isoformat(),
                                                  stage["pass_score"], stage["max_score"])).lastrowid


def save_result(con, exam_id: int, student_id: int, score: float, decision: str, reason: str, tg_id: int) -> None:
    con.execute(
        "INSERT INTO exam_results (exam_id, student_id, score, decision, reason, decided_by) VALUES (?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(exam_id, student_id) DO UPDATE SET score = excluded.score, decision = excluded.decision, "
        "reason = excluded.reason, decided_by = excluded.decided_by",
        (exam_id, student_id, score, decision, reason, tg_id))


def _undo_move_today(con, student_id: int, from_stage, on: date) -> None:
    """Если сегодня ученик уже был переведён с этой станции (исправление решения) — вернуть."""
    moved = con.execute(
        "SELECT ss.id FROM student_stage ss WHERE ss.student_id = ? AND ss.subject = ? AND ss.status = 'current' "
        "AND ss.date_from = ? AND EXISTS (SELECT 1 FROM student_stage p WHERE p.student_id = ss.student_id "
        "AND p.stage_id = ? AND p.status = 'done')", (student_id, from_stage["subject"], on.isoformat(),
                                                      from_stage["id"])).fetchone()
    if not moved:
        return
    con.execute("DELETE FROM student_stage WHERE id = ?", (moved["id"],))
    last_done = con.execute("SELECT id FROM student_stage WHERE student_id = ? AND stage_id = ? AND status = 'done' "
                            "ORDER BY id DESC LIMIT 1", (student_id, from_stage["id"])).fetchone()
    con.execute("UPDATE student_stage SET status = 'current' WHERE id = ?", (last_done["id"],))


def apply_decision(con, student_id: int, stage, passed: bool, path: str | None, on: date) -> str:
    """Переводит ученика по карте. Возвращает: moved, stay, fork_wait (сдал, путь не выбран), finished."""
    cur = repo.current_stage(con, student_id, stage["subject"])
    if cur is None:
        return "stay"
    if cur["stage_id"] != stage["id"]:
        # ученика уже перевели сегодня этим же экзаменом — возможно, решение исправили
        _undo_move_today(con, student_id, stage, on)
        cur = repo.current_stage(con, student_id, stage["subject"])
        if cur is None or cur["stage_id"] != stage["id"]:
            return "stay"
    if not passed:
        return "stay"
    if progress.is_fork(con, stage) and path in progress.FORK_BRANCHES:
        con.execute("UPDATE student_stage SET path = ? WHERE id = ?", (path, cur["id"]))
    nxt = progress.next_stage(con, stage, path or cur["path"])
    if nxt is None:
        return "fork_wait" if progress.is_fork(con, stage) else "finished"
    con.execute("UPDATE student_stage SET status = 'done' WHERE id = ?", (cur["id"],))
    new_path = nxt["branch"] if nxt["branch"] in progress.FORK_BRANCHES else cur["path"]
    con.execute("INSERT INTO student_stage (student_id, subject, stage_id, date_from, path) VALUES (?, ?, ?, ?, ?)",
                (student_id, stage["subject"], nxt["id"], on.isoformat(), new_path))
    return "moved"


def maybe_advance_group(con, group, stage, passed: int, total: int, on: date | None = None) -> object | None:
    """Если сдала хотя бы половина — группа переходит на следующую станцию (не на развилке)."""
    if total == 0 or passed * 2 < total or progress.is_fork(con, stage):
        return None
    nxt = progress.next_stage(con, stage)
    if nxt is None or group["stage_id"] != stage["id"]:
        return None
    # экзамены новой станции считаются от дня этого экзамена
    con.execute("UPDATE groups SET stage_id = ?, stage_start = ? WHERE id = ?",
                (nxt["id"], (on or date.today()).isoformat(), group["id"]))
    return nxt


def passed_today(con, group_id: int, stage_id: int, on: date) -> int:
    """Сколько учеников группы сегодня перешли с этой станции (по всем отправкам формы за день)."""
    return con.execute(
        "SELECT count(DISTINCT n.student_id) FROM student_stage n "
        "JOIN enrollments e ON e.student_id = n.student_id AND e.group_id = ? AND e.date_to IS NULL "
        "WHERE n.status = 'current' AND n.date_from = ? AND EXISTS ("
        "  SELECT 1 FROM student_stage p WHERE p.student_id = n.student_id AND p.stage_id = ? AND p.status = 'done')",
        (group_id, on.isoformat(), stage_id)).fetchone()[0]
