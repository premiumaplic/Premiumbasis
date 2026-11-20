"""Разбор отправок тестовой формы этапа 0."""

import json
from datetime import datetime, timedelta, timezone

import pytest

from bot.payload import byte_size, decode_param
from bot.probe_bot import describe, padded_url, parse_probe, summarize

NOW = datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc)
BASE = "https://example.github.io/Repo/"


def packet(**extra):
    data = {"v": 1, "t": "probe", "m": "short", "k": "hash", "h": True, "q": False, "ok": True,
            "dm": "встроенная", "dn": True, "ul": 900, "L": 0, "p": "android", "tv": "8.0",
            "tz": 300, "n": 0}
    data.update(extra)
    for _ in range(3):
        data["n"] = byte_size(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def test_parse_ok():
    rec = parse_probe(packet(), NOW, NOW)
    assert rec["intact"] and rec["hash_ok"] and rec["platform"] == "android"
    assert rec["delay"] == 0


def test_detects_damaged_size():
    text = packet().replace('"tv":"8.0"', '"tv":"8"')
    assert parse_probe(text, NOW, NOW)["intact"] is False


def test_rejects_too_big_and_foreign():
    with pytest.raises(ValueError):
        parse_probe("x" * 4097, NOW, NOW)
    with pytest.raises(ValueError):
        parse_probe('{"t":"other"}', NOW, NOW)


def test_offline_delivery_is_reported():
    sent = NOW - timedelta(minutes=14)
    rec = parse_probe(packet(), sent, NOW)
    text = describe(rec, sent, NOW)
    assert "бот был выключен" in text and "14 мин" in text


def test_padded_url_length_and_decodes():
    for target in (1000, 4000, 16000):
        url = padded_url(BASE, "hash", target)
        assert abs(len(url) - target) <= 40
        data = decode_param(url.split("#d=")[1])
        assert data["L"] == target


def test_summary_mentions_all_checks():
    sent = NOW - timedelta(hours=2)
    recs = [parse_probe(packet(), NOW, NOW), parse_probe(packet(p="ios"), sent, NOW)]
    text = summarize(recs, {"hash": {"accepted": [1000, 2000], "rejected": {"4000": "x"}}}, None)
    for n in range(1, 7):
        assert f"{n}." in text
    assert "iPhone: работает" in text
    assert "Telegram Desktop: ещё не проверяли" in text
    assert "отказал на 4000" in text
