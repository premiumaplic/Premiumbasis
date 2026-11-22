"""Знак центра: векторный рисунок совпадает с исходным макетом, файлы сайта — с bot/logo.py."""

from pathlib import Path

from PIL import Image, ImageChops

from bot import logo

ROOT = Path(__file__).resolve().parents[1]


def test_vector_matches_original_artwork():
    for name, scheme in (("logo-dark.png", "dark"), ("logo-light.png", "light"), ("logo-orange.png", "orange")):
        src = Image.open(ROOT / "assets" / "logo" / name).convert("RGB")
        out = Image.new("RGB", src.size, logo.SCHEMES[scheme]["bg"])
        logo.draw(out, 0, 0, src.size[0], scheme, frame=(0, 0, logo.SIZE))
        diff = ImageChops.difference(src, out).convert("L").point(lambda v: 255 if v > 80 else 0)
        share = diff.histogram()[255] / (src.size[0] * src.size[1])
        assert share < 0.005, f"{name}: отличается {share:.2%} точек"


def test_site_files_are_generated_from_vector():
    assert (ROOT / "docs/assets/logo.svg").read_text(encoding="utf-8") == logo.svg("light")
    assert (ROOT / "docs/assets/logo-dark.svg").read_text(encoding="utf-8") == logo.svg("dark")
    common = (ROOT / "docs/assets/common.js").read_text(encoding="utf-8")
    for name, d in logo.paths().items():
        assert f'"{name}": "{d}"' in common, name
