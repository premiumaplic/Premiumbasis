"""Бэкап: шифрование, части, восстановление в другую папку. Данные выдуманные."""

import asyncio
import datetime as dt
import sqlite3

import pyzipper
import pytest

from bot import backup, db, repo, scheduler, summary, tools
from tests.conftest import ACTOR, FakeSession, make_group, make_teacher

PASSWORD = "Тестовый-пароль-123"


def filled_db(path):
    con = db.connect(path)
    db.migrate(con)
    gid = make_group(con, teacher_id=make_teacher(con))
    repo.add_student(con, ACTOR, "Азиз Каримов", "ru", True, gid, dt.date(2026, 11, 2))
    return con


def test_archive_is_encrypted_and_kept_7(tmp_path):
    con = filled_db(tmp_path / "school.db")
    paths = [backup.create(con, tmp_path, PASSWORD, "daily") for _ in range(9)]
    zips = sorted((tmp_path / "backups").glob("*.zip"))
    assert len(zips) <= 7 and paths[-1] in zips
    with pyzipper.AESZipFile(paths[-1]) as z:
        assert z.infolist()[0].flag_bits & 0x1           # зашифровано
        with pytest.raises(RuntimeError):
            z.read("school.db")                          # без пароля не открыть
    assert b"\xd0\x90\xd0\xb7\xd0\xb8\xd0\xb7" not in paths[-1].read_bytes()  # имени ученика в открытом виде нет


def test_no_password_is_refused(tmp_path):
    con = filled_db(tmp_path / "school.db")
    with pytest.raises(backup.BackupError):
        backup.create(con, tmp_path, "", "daily")


def test_wrong_password_and_parts(tmp_path):
    con = filled_db(tmp_path / "school.db")
    path = backup.create(con, tmp_path, PASSWORD, "manual")
    with pytest.raises(backup.BackupError, match="Неверный пароль"):
        backup.read_archive(path, "не тот")
    pieces = backup.parts(path, size=4000)
    assert len(pieces) >= 2 and pieces[0][0].endswith(".zip.001")
    other = tmp_path / "download"
    other.mkdir()
    for name, chunk in pieces:
        (other / name).write_bytes(chunk)
    raw = backup.read_archive(other / pieces[0][0], PASSWORD)
    assert raw[:16] == b"SQLite format 3\x00"


def test_restore_into_another_folder(tmp_path, monkeypatch):
    src = tmp_path / "pc1"
    (src / "data").mkdir(parents=True)
    con = filled_db(src / "data" / "school.db")
    archive = backup.create(con, src / "data", PASSWORD, "daily")
    con.close()

    target = tmp_path / "pc2"
    (target / "data").mkdir(parents=True)
    old = filled_db(target / "data" / "school.db")       # в другой папке уже есть своя база
    old.execute("UPDATE students SET full_name = 'Другой Ученик'")
    old.close()
    monkeypatch.setenv("SB_ROOT", str(target))
    answers = iter([str(archive), "да"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    monkeypatch.setattr(tools.getpass, "getpass", lambda prompt="": PASSWORD)
    tools.single._handle = None
    assert tools.main(["restore"]) == 0
    restored = sqlite3.connect(target / "data" / "school.db")
    assert restored.execute("SELECT full_name FROM students").fetchone()[0] == "Азиз Каримов"
    assert list((target / "data" / "backups").glob("school-before-restore-*.db"))  # прежняя база сохранена


def test_inspect_rejects_garbage(tmp_path):
    bad = tmp_path / "x.db"
    bad.write_bytes(b"not a database at all" * 100)
    with pytest.raises(backup.BackupError):
        backup.inspect(bad)


def test_send_to_channel_and_check(tmp_path):
    from aiogram import Bot
    con = filled_db(tmp_path / "school.db")
    session = FakeSession()
    bot = Bot("123456:" + "A" * 35, session=session)
    report = asyncio.run(backup.run(bot, con, tmp_path, PASSWORD, -100123, "manual"))
    sent = [c for c in session.calls if type(c).__name__ == "SendDocument"]
    assert len(sent) == 1 and sent[0].chat_id == -100123 and "Бэкап отправлен" in report
    assert PASSWORD not in report and PASSWORD not in (sent[0].caption or "")
    assert "не указан" in asyncio.run(backup.check_channel(bot, None))


def test_backup_and_summary_schedule(con):
    tz = dt.timezone(dt.timedelta(hours=5))
    assert scheduler.backup_due(con, dt.datetime(2026, 11, 20, 9, 0, tzinfo=tz))           # бэкапов ещё не было
    repo.set_setting(con, 0, "backup_last", "2026-11-19T21:30:00", quiet=True)
    assert not scheduler.backup_due(con, dt.datetime(2026, 11, 20, 21, 29, tzinfo=tz))
    assert scheduler.backup_due(con, dt.datetime(2026, 11, 20, 21, 30, tzinfo=tz))
    repo.set_setting(con, 0, "backup_last", "2026-11-18T21:30:00", quiet=True)
    assert scheduler.backup_due(con, dt.datetime(2026, 11, 20, 9, 0, tzinfo=tz))            # пропущен день
    assert scheduler.summary_due(con, dt.datetime(2026, 11, 21, 20, 0, tzinfo=tz)) == "2026-11-16"
    assert scheduler.summary_due(con, dt.datetime(2026, 11, 21, 19, 0, tzinfo=tz)) is None


def test_summary_text_flags_inflation(con):
    from bot import reports
    t1 = make_teacher(con, 600001, "Учитель Строгий")
    t2 = make_teacher(con, 600002, "Учитель Добрый")
    g1, g2 = make_group(con, "10-А", teacher_id=t1), make_group(con, "11-Б", teacher_id=t2)
    w = dt.date(2026, 11, 16)
    qids = [q["id"] for q in reports.questions_for(con, "en")]
    for i in range(5):
        a = repo.add_student(con, ACTOR, f"Ученик{i} Первый", "ru", True, g1, w)
        b = repo.add_student(con, ACTOR, f"Ученик{i} Второй", "ru", True, g2, w)
        if i < 4:
            reports.save_weekly(con, 1, g1, w, a, dict(zip(qids, [1, 2, 3, 0, 2, 1])), "")
        reports.save_weekly(con, 1, g2, w, b, dict(zip(qids, [3, 3, 3, 3, 3, 3])), "")
    text = summary.text(con, w)
    assert "Отчёты заполнены: 9 из 10" in text
    assert "10-А: 4 из 5 — нет отчёта: Ученик4 П." in text
    assert "⚠️ почти все ответы «3» (100%)" in text
    assert text.count("возможно, оценки завышены") == 1
