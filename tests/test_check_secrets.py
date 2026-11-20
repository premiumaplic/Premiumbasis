"""Проверка на секреты находит токен и пропускает чистые файлы."""

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "check_secrets", Path(__file__).resolve().parents[1] / "scripts" / "check_secrets.py")
check_secrets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_secrets)


def test_finds_token(tmp_path):
    f = tmp_path / "a.py"
    token = "7012345678:" + "AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw1"  # собран из частей, чтобы не ловить сам себя
    f.write_text(f"TOKEN = '{token}'\n", encoding="utf-8")
    assert check_secrets.check([str(f)])


def test_finds_filled_config(tmp_path):
    f = tmp_path / "settings.ini"
    f.write_text("[backup]\npassword = qwerty\n", encoding="utf-8")
    assert check_secrets.check([str(f)])


def test_forbids_config_ini(tmp_path):
    f = tmp_path / "config.ini"
    f.write_text("", encoding="utf-8")
    assert check_secrets.check([str(f)])


def test_clean_example_passes():
    example = Path(__file__).resolve().parents[1] / "config.example.ini"
    assert check_secrets.check([str(example)]) == []
