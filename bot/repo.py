"""Работа с данными: учителя, группы, ученики, настройки, журнал действий.

Все изменения, которые делает владелец, записываются в audit_log (кто, что, когда).
В журнал пишутся только внутренние номера и Telegram ID, без имён учеников.
"""

import sqlite3
from datetime import date

Row = sqlite3.Row


# ---------------------------------------------------------------- журнал и настройки

def audit(con, actor: int, action: str, obj: str = "", details: str = "") -> None:
    con.execute("INSERT INTO audit_log (tg_id, action, object, details) VALUES (?, ?, ?, ?)",
                (actor, action, obj, details))


def get_setting(con, key: str, default: str = "") -> str:
    row = con.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def get_int(con, key: str, default: int) -> int:
    try:
        return int(get_setting(con, key, str(default)))
    except ValueError:
        return default


def all_settings(con) -> dict[str, str]:
    return {r["key"]: r["value"] for r in con.execute("SELECT key, value FROM settings ORDER BY key")}


def set_setting(con, actor: int, key: str, value: str, quiet: bool = False) -> None:
    """quiet=True — служебная отметка самого бота (без записи в журнал владельца)."""
    con.execute("INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))
    if not quiet:
        audit(con, actor, "setting", key, value)


# ---------------------------------------------------------------- учителя

def teacher_by_tg(con, tg_id: int) -> Row | None:
    return con.execute("SELECT * FROM teachers WHERE tg_id = ?", (tg_id,)).fetchone()


def teacher(con, teacher_id: int) -> Row | None:
    return con.execute("SELECT * FROM teachers WHERE id = ?", (teacher_id,)).fetchone()


def list_teachers(con, only_active: bool = False) -> list[Row]:
    sql = "SELECT * FROM teachers" + (" WHERE active = 1" if only_active else "")
    return con.execute(sql + " ORDER BY active DESC, name").fetchall()


def save_teacher(con, actor: int, tg_id: int, name: str, lang: str) -> tuple[int, bool]:
    """Добавляет учителя или обновляет существующего (по Telegram ID). Возвращает (id, создан ли)."""
    existing = teacher_by_tg(con, tg_id)
    if existing:
        con.execute("UPDATE teachers SET name = ?, lang = ?, active = 1 WHERE id = ?",
                    (name, lang, existing["id"]))
        audit(con, actor, "teacher_update", f"teacher:{existing['id']}", f"tg={tg_id} lang={lang}")
        return existing["id"], False
    cur = con.execute("INSERT INTO teachers (tg_id, name, lang) VALUES (?, ?, ?)", (tg_id, name, lang))
    audit(con, actor, "teacher_add", f"teacher:{cur.lastrowid}", f"tg={tg_id} lang={lang}")
    return cur.lastrowid, True


def set_teacher_active(con, actor: int, teacher_id: int, active: bool) -> None:
    con.execute("UPDATE teachers SET active = ? WHERE id = ?", (int(active), teacher_id))
    audit(con, actor, "teacher_enable" if active else "teacher_disable", f"teacher:{teacher_id}")


def set_teacher_lang(con, actor: int, teacher_id: int, lang: str) -> None:
    con.execute("UPDATE teachers SET lang = ? WHERE id = ?", (lang, teacher_id))
    audit(con, actor, "teacher_lang", f"teacher:{teacher_id}", lang)


# ---------------------------------------------------------------- предметы и станции

def list_subjects(con) -> list[Row]:
    return con.execute("SELECT * FROM subjects ORDER BY sort").fetchall()


def subject(con, code: str) -> Row | None:
    return con.execute("SELECT * FROM subjects WHERE code = ?", (code,)).fetchone()


def list_stages(con, subject_code: str) -> list[Row]:
    return con.execute("SELECT * FROM stages WHERE subject = ? ORDER BY sort, branch",
                       (subject_code,)).fetchall()


def stage(con, stage_id: int | None) -> Row | None:
    if stage_id is None:
        return None
    return con.execute("SELECT * FROM stages WHERE id = ?", (stage_id,)).fetchone()


def stage_by_code(con, subject_code: str, code: str) -> Row | None:
    return con.execute("SELECT * FROM stages WHERE subject = ? AND lower(code) = lower(?)",
                       (subject_code, code.strip())).fetchone()


def set_stage_scores(con, actor: int, stage_id: int, pass_score: float, max_score: float) -> None:
    con.execute("UPDATE stages SET pass_score = ?, max_score = ? WHERE id = ?",
                (pass_score, max_score, stage_id))
    audit(con, actor, "stage_scores", f"stage:{stage_id}", f"{pass_score}/{max_score}")


# ---------------------------------------------------------------- группы

GROUP_SELECT = """
    SELECT g.*, t.name AS teacher_name, t.tg_id AS teacher_tg,
           s.name_ru AS subject_ru, s.name_uz AS subject_uz, s.has_map,
           st.name_ru AS stage_ru, st.name_uz AS stage_uz, st.code AS stage_code,
           st.months AS stage_months, st.exam_transition,
           (SELECT count(*) FROM enrollments e JOIN students x ON x.id = e.student_id
             WHERE e.group_id = g.id AND e.date_to IS NULL AND x.active = 1) AS student_count
    FROM groups g
    JOIN subjects s ON s.code = g.subject
    LEFT JOIN teachers t ON t.id = g.teacher_id
    LEFT JOIN stages st ON st.id = g.stage_id
"""


def group(con, group_id: int) -> Row | None:
    return con.execute(GROUP_SELECT + " WHERE g.id = ?", (group_id,)).fetchone()


def list_groups(con, teacher_id: int | None = None, active: bool = True) -> list[Row]:
    sql, args = GROUP_SELECT + " WHERE g.active = ?", [int(active)]
    if teacher_id is not None:
        sql += " AND g.teacher_id = ?"
        args.append(teacher_id)
    return con.execute(sql + " ORDER BY g.name", args).fetchall()


def group_by_name(con, name: str) -> Row | None:
    return con.execute(GROUP_SELECT + " WHERE g.active = 1 AND lower(g.name) = lower(?)",
                       (name.strip(),)).fetchone()


def create_group(con, actor: int, name: str, subject_code: str, teacher_id: int | None,
                 stage_id: int | None, start_date: date, weekdays: str, lesson_time: str) -> int:
    cur = con.execute(
        "INSERT INTO groups (name, subject, teacher_id, stage_id, start_date, weekdays, lesson_time) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (name, subject_code, teacher_id, stage_id, start_date.isoformat(), weekdays, lesson_time))
    audit(con, actor, "group_add", f"group:{cur.lastrowid}",
          f"subject={subject_code} teacher={teacher_id} stage={stage_id}")
    return cur.lastrowid


def set_group_teacher(con, actor: int, group_id: int, teacher_id: int) -> None:
    con.execute("UPDATE groups SET teacher_id = ? WHERE id = ?", (teacher_id, group_id))
    audit(con, actor, "group_teacher", f"group:{group_id}", f"teacher={teacher_id}")


def set_group_stage(con, actor: int, group_id: int, stage_id: int) -> None:
    con.execute("UPDATE groups SET stage_id = ? WHERE id = ?", (stage_id, group_id))
    audit(con, actor, "group_stage", f"group:{group_id}", f"stage={stage_id}")


def set_group_field(con, actor: int, group_id: int, field: str, value: str) -> None:
    if field not in ("name", "start_date", "weekdays", "lesson_time"):
        raise ValueError(field)
    con.execute(f"UPDATE groups SET {field} = ? WHERE id = ?", (value, group_id))
    audit(con, actor, f"group_{field}", f"group:{group_id}", value if field != "name" else "")


def archive_group(con, actor: int, group_id: int, on_date: date) -> None:
    """Группа в архив; записи учеников в ней закрываются (история сохраняется)."""
    con.execute("UPDATE groups SET active = 0 WHERE id = ?", (group_id,))
    con.execute("UPDATE enrollments SET date_to = ? WHERE group_id = ? AND date_to IS NULL",
                (on_date.isoformat(), group_id))
    audit(con, actor, "group_archive", f"group:{group_id}")


# ---------------------------------------------------------------- ученики

def student(con, student_id: int) -> Row | None:
    return con.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()


def find_students(con, text: str, limit: int = 30) -> list[Row]:
    rows = con.execute("SELECT * FROM students WHERE active = 1 ORDER BY full_name").fetchall()
    needle = text.strip().casefold()  # casefold: SQLite lower() не понимает кириллицу
    return [r for r in rows if needle in r["full_name"].casefold()][:limit]


def students_by_name(con, full_name: str) -> list[Row]:
    needle = " ".join(full_name.split()).casefold()
    return [r for r in con.execute("SELECT * FROM students WHERE active = 1")
            if " ".join(r["full_name"].split()).casefold() == needle]


def group_students(con, group_id: int) -> list[Row]:
    """Ученики, которые сейчас записаны в группу."""
    return con.execute(
        "SELECT s.* FROM students s JOIN enrollments e ON e.student_id = s.id "
        "WHERE e.group_id = ? AND e.date_to IS NULL AND s.active = 1 ORDER BY s.full_name",
        (group_id,)).fetchall()


def student_groups(con, student_id: int) -> list[Row]:
    return con.execute(
        GROUP_SELECT + " JOIN enrollments e ON e.group_id = g.id "
        "WHERE e.student_id = ? AND e.date_to IS NULL ORDER BY g.name", (student_id,)).fetchall()


def is_enrolled(con, student_id: int, group_id: int) -> bool:
    return con.execute("SELECT 1 FROM enrollments WHERE student_id = ? AND group_id = ? "
                       "AND date_to IS NULL", (student_id, group_id)).fetchone() is not None


def enroll(con, actor: int, student_id: int, group_id: int, on_date: date) -> bool:
    if is_enrolled(con, student_id, group_id):
        return False
    con.execute("INSERT INTO enrollments (student_id, group_id, date_from) VALUES (?, ?, ?)",
                (student_id, group_id, on_date.isoformat()))
    audit(con, actor, "enroll", f"student:{student_id}", f"group={group_id}")
    return True


def current_stage(con, student_id: int, subject_code: str) -> Row | None:
    return con.execute(
        "SELECT ss.*, st.name_ru, st.name_uz, st.code FROM student_stage ss "
        "JOIN stages st ON st.id = ss.stage_id "
        "WHERE ss.student_id = ? AND ss.subject = ? AND ss.status = 'current' "
        "ORDER BY ss.id DESC LIMIT 1", (student_id, subject_code)).fetchone()


def set_student_stage(con, actor: int, student_id: int, stage_id: int, on_date: date,
                      path: str | None = None) -> None:
    """Ставит ученика на станцию карты вручную (предыдущая закрывается как 'left')."""
    st = stage(con, stage_id)
    if path is None and st["branch"] in ("cefr", "ielts"):
        path = st["branch"]
    con.execute("UPDATE student_stage SET status = 'left' "
                "WHERE student_id = ? AND subject = ? AND status = 'current'", (student_id, st["subject"]))
    con.execute("INSERT INTO student_stage (student_id, subject, stage_id, date_from, path) "
                "VALUES (?, ?, ?, ?, ?)", (student_id, st["subject"], stage_id, on_date.isoformat(), path))
    audit(con, actor, "student_stage", f"student:{student_id}", f"stage={stage_id}")


def default_stage_id(con, group_row: Row) -> int | None:
    """Станция новичка: станция группы, иначе A1 (новичок старше 11 лет)."""
    if not group_row["has_map"]:
        return None
    if group_row["stage_id"]:
        return group_row["stage_id"]
    a1 = stage_by_code(con, group_row["subject"], "a1")
    return a1["id"] if a1 else None


def add_student(con, actor: int, full_name: str, card_lang: str, consent: bool,
                group_id: int, on_date: date, stage_id: int | None = None) -> int:
    cur = con.execute("INSERT INTO students (full_name, card_lang, consent) VALUES (?, ?, ?)",
                      (" ".join(full_name.split()), card_lang, int(consent)))
    student_id = cur.lastrowid
    audit(con, actor, "student_add", f"student:{student_id}", f"lang={card_lang} consent={int(consent)}")
    enroll(con, actor, student_id, group_id, on_date)
    place_on_map_if_needed(con, actor, student_id, group_id, on_date, stage_id)
    return student_id


def place_on_map_if_needed(con, actor: int, student_id: int, group_id: int, on_date: date,
                           stage_id: int | None = None) -> None:
    """Если у предмета группы есть карта, а ученик на ней ещё не стоит — ставим."""
    g = group(con, group_id)
    if not g["has_map"]:
        return
    if stage_id is None and current_stage(con, student_id, g["subject"]):
        return
    stage_id = stage_id or default_stage_id(con, g)
    if stage_id:
        set_student_stage(con, actor, student_id, stage_id, on_date)


def transfer_student(con, actor: int, student_id: int, from_group: int, to_group: int,
                     on_date: date) -> None:
    """Перевод с сохранением истории: старая запись закрывается, новая открывается."""
    con.execute("UPDATE enrollments SET date_to = ? WHERE student_id = ? AND group_id = ? "
                "AND date_to IS NULL", (on_date.isoformat(), student_id, from_group))
    audit(con, actor, "transfer", f"student:{student_id}", f"from={from_group} to={to_group}")
    enroll(con, actor, student_id, to_group, on_date)
    place_on_map_if_needed(con, actor, student_id, to_group, on_date)


def set_student_field(con, actor: int, student_id: int, field: str, value) -> None:
    if field not in ("card_lang", "consent", "full_name"):
        raise ValueError(field)
    con.execute(f"UPDATE students SET {field} = ? WHERE id = ?", (value, student_id))
    audit(con, actor, f"student_{field}", f"student:{student_id}",
          "" if field == "full_name" else str(value))


def archive_student(con, actor: int, student_id: int, on_date: date) -> None:
    con.execute("UPDATE students SET active = 0 WHERE id = ?", (student_id,))
    con.execute("UPDATE enrollments SET date_to = ? WHERE student_id = ? AND date_to IS NULL",
                (on_date.isoformat(), student_id))
    con.execute("UPDATE student_stage SET status = 'left' WHERE student_id = ? AND status = 'current'",
                (student_id,))
    audit(con, actor, "student_archive", f"student:{student_id}")


def short_name(full_name: str) -> str:
    """«Азиз Каримов» -> «Азиз К.»: для ссылок форм — только имя и первая буква фамилии.

    Полное имя хранится в порядке «Имя Фамилия» (так его и подписывает карточка).
    """
    parts = full_name.split()
    if len(parts) < 2:
        return full_name
    return f"{parts[0]} {parts[1][0]}."
