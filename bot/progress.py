"""Карта ученика: порядок станций, следующая станция, прогноз финиша.

Станции берутся из таблицы stages (данные, а не код), поэтому у других предметов
позже появятся свои карты без переделки.

Прогноз считается по календарю экзаменов группы (каждые 2 месяца от даты старта)
в предположении, что ученик сдаёт всё с первого раза. Повтор оставляет ученика на
станции до следующего экзамена — вся линия сдвигается на 2 месяца.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta

from bot import repo, schedule

BRANCH_ORDER = {"kids": 0, "main": 1, "cefr": 2, "ielts": 2}
FORK_BRANCHES = ("cefr", "ielts")


def ordered(con, subject: str) -> list:
    return sorted(repo.list_stages(con, subject), key=lambda s: (BRANCH_ORDER[s["branch"]], s["sort"], s["branch"]))


def route(con, subject: str, path: str | None) -> list:
    """Станции по порядку: общая часть + выбранная ветка (если путь не выбран — без веток)."""
    stages = ordered(con, subject)
    common = [s for s in stages if s["branch"] not in FORK_BRANCHES]
    if path in FORK_BRANCHES:
        return common + [s for s in stages if s["branch"] == path]
    return common


def is_fork(con, stage) -> bool:
    """После этой станции — развилка (CEFR или IELTS)."""
    common = route(con, stage["subject"], None)
    has_branches = any(s["branch"] in FORK_BRANCHES for s in repo.list_stages(con, stage["subject"]))
    return has_branches and bool(common) and common[-1]["id"] == stage["id"]


def next_stage(con, stage, path: str | None = None):
    """Следующая станция или None (конец пути, или развилка без выбранного пути)."""
    if stage["branch"] in FORK_BRANCHES:
        path = stage["branch"]
    seq = route(con, stage["subject"], path)
    ids = [s["id"] for s in seq]
    if stage["id"] not in ids:
        return None
    i = ids.index(stage["id"])
    return seq[i + 1] if i + 1 < len(seq) else None


@dataclass
class Node:
    stage_id: int
    name_ru: str
    name_uz: str
    state: str                     # done, current, future, grey (ветка ещё не выбрана)
    finish: date | None = None     # прогноз окончания станции
    finish_max: date | None = None # верхняя граница (CEFR, IELTS: 3–5 месяцев)
    by_teacher: bool = False       # переход по решению учителя, даты нет


@dataclass
class MapView:
    nodes: list[Node] = field(default_factory=list)
    current: Node | None = None
    path_known: bool = False
    week: int = 0                  # неделя внутри станции
    weeks_total: int | None = None # 8 для станций с экзаменом
    next_exam: date | None = None


def last_exam_date(con, student_id: int, stage_id: int) -> date | None:
    row = con.execute("SELECT max(e.exam_date) FROM exam_results r JOIN exams e ON e.id = r.exam_id "
                      "WHERE r.student_id = ? AND e.stage_id = ?", (student_id, stage_id)).fetchone()
    return date.fromisoformat(row[0]) if row and row[0] else None


def _advance(stage, cursor: date | None) -> tuple[date | None, date | None]:
    """Окончание станции, если она начинается в cursor."""
    if cursor is None:
        return None, None
    if stage["exam_transition"]:
        return schedule.add_months(cursor, schedule.EXAM_EVERY_MONTHS), None
    if stage["months"]:
        low = schedule.add_months(cursor, stage["months"])
        high = schedule.add_months(cursor, stage["months_max"]) if stage["months_max"] else None
        return low, high
    return None, None


def build(con, student_id: int, group, on: date) -> MapView | None:
    """Карта ученика в группе. None — у предмета нет карты или ученик не стоит на ней."""
    if not group["has_map"]:
        return None
    cur = repo.current_stage(con, student_id, group["subject"])
    if not cur:
        return None
    path = cur["path"]
    seq = route(con, group["subject"], path)
    ids = [s["id"] for s in seq]
    if cur["stage_id"] not in ids:
        return None
    view = MapView(path_known=path in FORK_BRANCHES)
    current_index = ids.index(cur["stage_id"])
    current_stage = seq[current_index]
    start = date.fromisoformat(group["start_date"])

    # окончание текущей станции
    if current_stage["exam_transition"]:
        after = on
        last = last_exam_date(con, student_id, current_stage["id"])
        if last and last >= on:
            after = last + timedelta(days=1)  # экзамен уже был (повтор) — ждём следующий
        finish, finish_max = schedule.next_exam(start, after), None
        view.next_exam = finish
        view.week, view.weeks_total = schedule.stage_week(start, on, True), schedule.WEEKS_PER_STAGE
    else:
        stage_start = date.fromisoformat(cur["date_from"])
        finish, finish_max = _advance(current_stage, stage_start)
        view.week = max(1, (on - stage_start).days // 7 + 1)

    # станции до первой станции ученика не показываем (новичок старше 11 лет начинает с A1)
    first = con.execute("SELECT stage_id FROM student_stage WHERE student_id = ? AND subject = ? "
                        "ORDER BY id LIMIT 1", (student_id, group["subject"])).fetchone()
    first_index = ids.index(first["stage_id"]) if first and first["stage_id"] in ids else 0
    first_index = min(first_index, current_index)

    for i, s in enumerate(seq):
        if i < first_index:
            continue
        node = Node(s["id"], s["name_ru"], s["name_uz"], "future",
                    by_teacher=not s["exam_transition"] and not s["months"])
        if i < current_index:
            node.state = "done"
        elif i == current_index:
            node.state = "current"
            node.finish, node.finish_max = finish, finish_max
            view.current = node
        view.nodes.append(node)

    cursor = finish
    shown_current = current_index - first_index
    for node, s in zip(view.nodes[shown_current + 1:], seq[current_index + 1:]):
        node.finish, node.finish_max = _advance(s, cursor)
        cursor = node.finish_max or node.finish  # диапазон: дальше считаем от верхней границы

    if not view.path_known:
        # развилка ещё не выбрана: обе ветки серые, без дат
        for s in ordered(con, group["subject"]):
            if s["branch"] in FORK_BRANCHES:
                view.nodes.append(Node(s["id"], s["name_ru"], s["name_uz"], "grey"))
    return view


def finish_of_route(view: MapView) -> Node | None:
    """Последняя станция с прогнозом (финиш выбранного пути или станция перед развилкой)."""
    known = [n for n in view.nodes if n.state != "grey"]
    return known[-1] if known else None
