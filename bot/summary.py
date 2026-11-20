"""Сводка владельцу в конце недели: кто не заполнил отчёты и как распределены оценки у учителей.

Если у учителя почти все ответы «3», это сигнал, что оценки могут быть завышены.
"""

from datetime import date, timedelta

from bot import hints, repo, reports

INFLATION_SHARE = 0.8      # доля ответов «3», начиная с которой предупреждаем
INFLATION_MIN_ANSWERS = 20  # на малом числе ответов вывод не делаем


def week_line(week: date) -> str:
    return f"{week.strftime('%d.%m')}–{(week + timedelta(days=5)).strftime('%d.%m')}"


def text(con, week: date) -> str:
    lines = [f"📊 Сводка за неделю {week_line(week)}", ""]
    total_students = total_done = 0
    for teacher in repo.list_teachers(con, only_active=True):
        groups = repo.list_groups(con, teacher_id=teacher["id"])
        if not groups:
            continue
        lines.append(f"👩‍🏫 {teacher['name']}")
        counts = [0, 0, 0, 0]
        for g in groups:
            n = g["student_count"]
            left = reports.students_without_report(con, g["id"], week)
            done = n - len(left)
            total_students += n
            total_done += done
            line = f"   {g['name']}: {done} из {n}"
            if left:
                names = ", ".join(repo.short_name(s["full_name"]) for s in left[:8])
                line += f" — нет отчёта: {names}" + ("…" if len(left) > 8 else "")
            lines.append(line)
            for r in con.execute("SELECT a.value, count(*) AS k FROM weekly_answers a "
                                 "JOIN weekly_reports r ON r.id = a.report_id "
                                 "WHERE r.group_id = ? AND r.week_start = ? GROUP BY a.value",
                                 (g["id"], week.isoformat())):
                counts[r["value"]] += r["k"]
        answers = sum(counts)
        if answers:
            shares = [round(100 * c / answers) for c in counts]
            lines.append("   оценки: " + ", ".join(f"«{v}» — {shares[v]}%" for v in range(4)))
            if answers >= INFLATION_MIN_ANSWERS and counts[3] / answers >= INFLATION_SHARE:
                lines.append(f"   ⚠️ почти все ответы «3» ({shares[3]}%) — возможно, оценки завышены")
        lines.append("")
    lines.insert(1, f"Отчёты заполнены: {total_done} из {total_students}")

    att = con.execute("SELECT status, count(*) AS k FROM attendance WHERE lesson_date BETWEEN ? AND ? "
                      "GROUP BY status", (week.isoformat(), (week + timedelta(days=6)).isoformat())).fetchall()
    by = {r["status"]: r["k"] for r in att}
    lines.append(f"Посещаемость за неделю: пропусков {by.get('absent', 0)}, опозданий {by.get('late', 0)}, "
                 f"по уважительной {by.get('excused', 0)}")
    open_count = sum(len(hints.open_hints(con, g["id"])) for g in repo.list_groups(con))
    lines.append(f"Открытых подсказок у учителей: {open_count}")
    return "\n".join(lines)
