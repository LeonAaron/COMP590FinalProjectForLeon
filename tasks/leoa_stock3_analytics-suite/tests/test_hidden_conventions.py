"""Codebase-wide conventions (see "Codebase conventions" in the instructions).

Which endpoints, pages, panels and tables a release adds comes from conventions.json,
merged from each feature's task_src/<feature>/conventions.json by build_tasks.py.
"""

import json
import re
from pathlib import Path

import pytest
from flask.testing import FlaskClient

SPEC = json.loads((Path(__file__).parent / "conventions.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def isolated_watchlist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WATCHLIST_PATH", str(tmp_path / "watchlist.json"))


@pytest.mark.parametrize("url", SPEC["api"])
def test_new_api_endpoint_is_no_store(client: FlaskClient, url: str) -> None:
    resp = client.get(url)
    assert resp.status_code == 200, f"{url} should exist"
    directives = [d.strip().lower() for d in resp.headers.get("Cache-Control", "").split(",")]
    assert "no-store" in directives


@pytest.mark.parametrize("url", list(SPEC["pages"]))
def test_new_page_title(client: FlaskClient, url: str) -> None:
    resp = client.get(url)
    assert resp.status_code == 200
    title = re.search(r"<title[^>]*>(.*?)</title>", resp.get_data(as_text=True), re.S)
    assert title, "page has no <title>"
    assert " ".join(title.group(1).split()) == f"{SPEC['pages'][url]} · Stock Chart Viewer"


@pytest.mark.parametrize("url", list(SPEC["pages"]))
def test_new_page_reuses_header(client: FlaskClient, url: str) -> None:
    resp = client.get(url)
    assert resp.status_code == 200
    page = resp.get_data(as_text=True)
    header = re.search(r'<header[^>]*\bclass="[^"]*\btopbar\b[^"]*"[^>]*>(.*?)</header>', page, re.S)
    assert header, "no <header class=topbar>"
    assert re.search(r'<a[^>]*\bclass="[^"]*\bbrand\b[^"]*"[^>]*\bhref="/[^"]*"|<a[^>]*\bhref="/[^"]*"[^>]*\bclass="[^"]*\bbrand\b',
                     header.group(1)), "header has no brand link back to the app"


@pytest.mark.parametrize(("url", "table_id"), list(SPEC["tables"].items()))
def test_new_table_has_caption(client: FlaskClient, url: str, table_id: str) -> None:
    resp = client.get(url)
    assert resp.status_code == 200
    table = re.search(rf'<table[^>]*\bid="{table_id}"[^>]*>(.*?)</table>', resp.get_data(as_text=True), re.S)
    assert table, f"no <table id={table_id}>"
    caption = re.search(r"<caption[^>]*>(.*?)</caption>", table.group(1), re.S)
    assert caption and re.sub(r"<[^>]+>", "", caption.group(1)).strip()


@pytest.mark.parametrize("section_id", SPEC["sections"])
def test_new_panel_has_aria_label(client: FlaskClient, section_id: str) -> None:
    page = client.get("/").get_data(as_text=True)
    tag = re.search(rf'<section[^>]*\bid="{section_id}"[^>]*>', page)
    assert tag, f"no <section id={section_id}>"
    label = re.search(r'\baria-label="([^"]*)"', tag.group(0))
    assert label and label.group(1).strip()
