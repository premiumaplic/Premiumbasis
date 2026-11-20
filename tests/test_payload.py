"""Упаковка данных для ссылок форм и размеры отправки (выдуманные данные)."""

from bot.payload import SEND_DATA_LIMIT, byte_size, decode_param, encode_param, to_json
from bot.probe_data import LONG_COMMENT, form_input, weekly_output


def test_roundtrip_compressed_and_plain():
    data = form_input(20, with_questions=True)
    assert decode_param(encode_param(data)) == data
    assert decode_param(encode_param(data, compress=False)) == data


def test_param_is_url_safe():
    text = encode_param(form_input(30, with_questions=True))
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
    assert set(text) <= allowed


def test_compression_helps_for_20_students():
    data = form_input(20, with_questions=True)
    assert len(encode_param(data)) < len(encode_param(data, compress=False)) * 0.6


def test_cyrillic_is_not_escaped():
    assert to_json({"a": "Ж"}) == '{"a":"Ж"}'
    assert byte_size("Ж") == 2


def test_weekly_report_20_students_fits_limit():
    assert len(LONG_COMMENT) == 80
    assert byte_size(to_json(weekly_output(20))) <= SEND_DATA_LIMIT


def test_weekly_report_30_students_needs_split():
    # 30 учеников с длинными комментариями в один пакет не влезают — форма должна делить отправку
    assert byte_size(to_json(weekly_output(30))) > SEND_DATA_LIMIT
