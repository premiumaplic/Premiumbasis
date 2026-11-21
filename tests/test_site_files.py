"""Все файлы сайта с формами действительно попадают в GitHub (иначе на телефоне будет «404»)."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_site_files_are_not_ignored():
    files = [p for p in (ROOT / "docs").rglob("*") if p.is_file()]
    assert any(p.parts[-2:] == ("app", "index.html") for p in files)
    result = subprocess.run(["git", "check-ignore", *[str(p) for p in files]], cwd=ROOT,
                            capture_output=True, text=True)
    assert result.stdout.strip() == "", f"эти файлы сайта не попадут в GitHub: {result.stdout}"


def test_html_pages_reference_existing_files():
    import re
    for page in (ROOT / "docs").rglob("*.html"):
        for ref in re.findall(r'(?:src|href)="([^"#?]+)"', page.read_text(encoding="utf-8")):
            if ref.startswith(("http", "mailto:")):
                continue
            assert (page.parent / ref).resolve().exists(), f"{page.name}: нет файла {ref}"
