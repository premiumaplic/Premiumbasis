"""Проверка установки: все библиотеки на месте и пишут только внутрь папки.

Запускается из setup.bat. Каждая строка — одна проверка.
"""

import io
import os
import sqlite3
import sys
import tempfile
from pathlib import Path


def main() -> int:
    from bot.config import data_dir

    tmp = data_dir() / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    failed = 0

    def check(name, func):
        nonlocal failed
        try:
            func()
            print(f"  [OK] {name}")
        except Exception as e:  # показываем владельцу, что именно не так
            failed += 1
            print(f"  [ОШИБКА] {name}: {type(e).__name__}: {e}")

    def python_version():
        assert sys.version_info >= (3, 12), sys.version

    def temp_inside():
        assert Path(tempfile.gettempdir()).resolve().is_relative_to(data_dir().parent.resolve()), \
            f"временные файлы пишутся в {tempfile.gettempdir()}"

    def mpl_inside():
        cfg_dir = os.environ.get("MPLCONFIGDIR", "")
        assert cfg_dir and Path(cfg_dir).resolve().is_relative_to(data_dir().resolve()), \
            "MPLCONFIGDIR не задан — matplotlib писал бы в профиль пользователя"

    def sqlite():
        con = sqlite3.connect(":memory:")
        con.execute("create table t(x)")
        con.close()

    def timezone():
        from zoneinfo import ZoneInfo
        ZoneInfo("Asia/Tashkent")

    def network_libs():
        import aiogram  # noqa: F401
        import ssl  # noqa: F401

    def drawing():
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from PIL import Image
        fig, ax = plt.subplots(figsize=(2, 1))
        ax.barh(["Говорение", "Oʻqish"], [2, 3])
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        plt.close(fig)
        Image.open(io.BytesIO(buf.getvalue())).verify()

    def card_font():
        from bot.card import FONTS, font
        assert (FONTS / "Nunito_900Black.ttf").exists(), "нет шрифта для карточек"
        font(900, 40).getbbox("Oʻgʻil Жж")

    def excel():
        import openpyxl
        wb = openpyxl.Workbook()
        wb.active["A1"] = "Ученик"
        buf = io.BytesIO()
        wb.save(buf)
        assert openpyxl.load_workbook(io.BytesIO(buf.getvalue())).active["A1"].value == "Ученик"

    def encrypted_zip():
        import pyzipper
        buf = io.BytesIO()
        with pyzipper.AESZipFile(buf, "w", compression=pyzipper.ZIP_DEFLATED,
                                 encryption=pyzipper.WZ_AES) as z:
            z.setpassword(b"test-password")
            z.writestr("a.txt", "проверка")
        with pyzipper.AESZipFile(io.BytesIO(buf.getvalue())) as z:
            z.setpassword(b"test-password")
            assert z.read("a.txt").decode() == "проверка"

    print("Проверка установки:")
    check(f"Python {sys.version.split()[0]}", python_version)
    check("временные файлы внутри папки", temp_inside)
    check("настройки matplotlib внутри папки", mpl_inside)
    check("база SQLite", sqlite)
    check("часовой пояс Ташкента", timezone)
    check("связь с Telegram (aiogram, ssl)", network_libs)
    check("рисование (matplotlib, Pillow)", drawing)
    check("шрифт карточек (кириллица, oʻ gʻ)", card_font)
    check("Excel (openpyxl)", excel)
    check("шифрованный архив (pyzipper)", encrypted_zip)
    print("Всё в порядке." if not failed else f"Есть ошибки: {failed}.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
