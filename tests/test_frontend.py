"""Static contract checks between the workbench HTML and JavaScript."""

from __future__ import annotations

import re
from pathlib import Path

WEB = Path(__file__).resolve().parents[1] / "c4" / "web"


def test_every_element_id_used_by_the_script_exists_in_the_page() -> None:
    html = (WEB / "index.html").read_text(encoding="utf-8")
    script = (WEB / "app.js").read_text(encoding="utf-8")
    page_ids = set(re.findall(r'\bid="([^"]+)"', html))
    used = set(re.findall(r'\$\("#([\w-]+)"\)', script))
    used |= set(re.findall(r'\$\(`#tab-\$\{id\}`\)', script) and ["tab-verify", "tab-eval"])
    assert used - page_ids == set(), f"ids missing from index.html: {used - page_ids}"


def test_script_never_assigns_html_strings() -> None:
    script = (WEB / "app.js").read_text(encoding="utf-8")
    assert "innerHTML" not in script and "outerHTML" not in script and "insertAdjacentHTML" not in script


def test_page_references_only_local_assets() -> None:
    html = (WEB / "index.html").read_text(encoding="utf-8")
    sources = re.findall(r'(?:src|href)="([^"]+)"', html)
    assert all(not item.startswith(("http://", "https://", "//")) for item in sources)
