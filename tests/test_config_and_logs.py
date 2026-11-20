"""Настройки и защита секретов в журнале."""

import logging

import pytest

from bot import config as cfg
from bot.logsetup import SecretFilter

FAKE_TOKEN = "123456789:AAFakeTokenForTestsOnly_abcdefghijklmn"


def write(tmp_path, text):
    path = tmp_path / "config.ini"
    path.write_text(text, encoding="utf-8-sig")
    return path


def test_load_good(tmp_path):
    path = write(tmp_path, f"[telegram]\ntoken = {FAKE_TOKEN}\nowner_id = 42\n[probe]\ntesters = 7, 8\n")
    conf = cfg.load(path)
    assert conf.owner_id == 42 and conf.testers == [7, 8]
    assert conf.forms_url.endswith("/")
    assert FAKE_TOKEN not in repr(conf)


@pytest.mark.parametrize("text", [
    "[telegram]\ntoken =\n",
    "[telegram]\ntoken = 'abc'\n",
    f"[telegram]\ntoken = {FAKE_TOKEN}\nowner_id = Иван\n",
])
def test_load_bad(tmp_path, text):
    with pytest.raises(cfg.ConfigError):
        cfg.load(write(tmp_path, text))


def test_token_never_in_log():
    record = logging.LogRecord("x", logging.ERROR, "", 0, "ошибка %s", (f"https://api/bot{FAKE_TOKEN}/getMe",), None)
    SecretFilter([FAKE_TOKEN]).filter(record)
    assert FAKE_TOKEN not in record.getMessage()
    assert "***" in record.getMessage()


def test_password_never_in_log():
    record = logging.LogRecord("x", logging.INFO, "", 0, "pw=Secret-Pass-1", None, None)
    SecretFilter(["Secret-Pass-1"]).filter(record)
    assert "Secret-Pass-1" not in record.getMessage()


def test_save_value_keeps_comments(tmp_path):
    path = write(tmp_path, f"; комментарий\n[telegram]\ntoken = {FAKE_TOKEN}\n; ID канала\nbackup_channel_id =\n\n[backup]\npassword = x\n")
    cfg.save_value("telegram", "backup_channel_id", "-100123", path)
    text = path.read_text(encoding="utf-8")
    assert "backup_channel_id = -100123" in text and "; ID канала" in text and "password = x" in text
    assert cfg.load(path).backup_channel_id == -100123
    cfg.save_value("forms", "base_url", "https://example.org/", path)
    assert cfg.load(path).forms_url == "https://example.org/"
    cfg.save_value("telegram", "owner_id", "77", path)          # ключа не было — добавится в свой раздел
    assert cfg.load(path).owner_id == 77
