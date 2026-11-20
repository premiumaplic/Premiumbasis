"""Простые правила по данным ученика (без нейросетей).

Пороги — в настройках (settings), это стартовые предположения: владелец подстроит их
через месяц работы. Здесь — правила, которые нужны карточке: рост (похвала) и риск
не сдать экзамен. Остальные подсказки учителю — этап 4.
"""

from datetime import date, timedelta

from bot import repo, schedule


def week_averages(con, student_id: int, group_id: int, up_to: date, count: int) -> list[tuple[date, float]]:
    """Средний балл (0–3) по неделям, от новой к старой, не позже недели up_to."""
    rows = con.execute(
        "SELECT r.week_start, avg(a.value) AS level FROM weekly_reports r "
        "JOIN weekly_answers a ON a.report_id = r.id "
        "WHERE r.student_id = ? AND r.group_id = ? AND r.week_start <= ? "
        "GROUP BY r.week_start ORDER BY r.week_start DESC LIMIT ?",
        (student_id, group_id, up_to.isoformat(), count)).fetchall()
    return [(date.fromisoformat(r["week_start"]), r["level"]) for r in rows]


def growth_streak(con, student_id: int, group_id: int, week: date) -> bool:
    """Рост N недель подряд: средний балл каждой недели выше предыдущей (недели идут без пропусков)."""
    n = repo.get_int(con, "hint_growth_weeks", 3)
    levels = week_averages(con, student_id, group_id, week, n + 1)
    if len(levels) < n + 1 or levels[0][0] != week:
        return False
    for (w_new, new), (w_old, old) in zip(levels, levels[1:]):
        if w_new - w_old != timedelta(weeks=1) or not new > old:
            return False
    return True


def exam_risk(con, student_id: int, group, week: date, next_exam: date | None, on: date) -> bool:
    """За N недель до экзамена средний уровень ниже проходного (в долях от максимума)."""
    if next_exam is None:
        return False
    stage = repo.stage(con, group["stage_id"])
    if not stage or not stage["exam_transition"] or not stage["pass_score"] or not stage["max_score"]:
        return False
    weeks_left = (next_exam - on).days / 7
    if not 0 <= weeks_left <= repo.get_int(con, "hint_exam_weeks", 3):
        return False
    levels = week_averages(con, student_id, group["id"], week, 2)
    if not levels:
        return False
    level = sum(v for _, v in levels) / len(levels) / 3
    return level < stage["pass_score"] / stage["max_score"]


def next_exam_for(group, on: date) -> date | None:
    if not group["stage_id"] or not group["exam_transition"]:
        return None
    return schedule.next_exam(date.fromisoformat(group["start_date"]), on)
