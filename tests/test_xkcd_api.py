"""xkcd API, explainxkcd MediaWiki parsing, MCP tool, and HTTP endpoint tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from starlette.testclient import TestClient

from xkcd_mcp import server, xkcd_api
from xkcd_mcp.app import app
from xkcd_mcp.xkcd_api import _comic_dict, _extract_explainxkcd_sections, fetch_explanation


def test_comic_dict_maps_urls() -> None:
    d = _comic_dict(
        {
            "num": 2916,
            "month": "3",
            "year": "2025",
            "day": "20",
            "title": "Test",
            "safe_title": "Test",
            "alt": "Alt",
            "img": "https://imgs.xkcd.com/...",
            "transcript": "",
        }
    )
    assert d["num"] == 2916
    assert "2916" in d["xkcd_url"]
    assert "explainxkcd" in d["explainxkcd_url"]


def test_extract_explainxkcd_sections() -> None:
    sample_html = """
    <div class="mw-parser-output">
      <style>.mw-parser-output .box { color: red; }</style>
      <p>Intro boilerplate before sections.</p>
      <h2><span class="mw-headline" id="Explanation">Explanation</span></h2>
      <p>Programmers use <a href="https://en.wikipedia.org/wiki/Compiler">compilers</a> to justify sword fighting.</p>
      <h3><span class="mw-headline" id="Details">Details</span></h3>
      <ul><li>First point</li><li>Second point</li></ul>
      <h2><span class="mw-headline" id="Transcript">Transcript</span></h2>
      <dl><dd>[Cueball and friend sword fighting on office chairs.]</dd></dl>
      <h2><span class="mw-headline" id="Trivia">Trivia</span></h2>
      <p>Classic comic #303.</p>
      <h1><span class="mw-headline" id="Discussion">Discussion</span></h1>
      <p>User comment that must not leak into trivia.</p>
    </div>
    """
    sections = _extract_explainxkcd_sections(sample_html)
    assert "compilers" in sections["explanation"]
    assert "### Details" in sections["explanation"]
    assert "- First point" in sections["explanation"]
    assert ".box" not in sections["explanation"]
    assert "sword fighting" in sections["transcript"]
    assert "Classic comic #303." in sections["trivia"]
    assert "User comment" not in sections["trivia"]


@pytest.mark.asyncio
async def test_fetch_explanation_validation() -> None:
    res = await fetch_explanation(0)
    assert res["success"] is False
    assert res["error_type"] == "validation"


@pytest.mark.asyncio
async def test_fetch_explanation_success_and_missingtitle() -> None:
    class _FakeResponse:
        def __init__(self, payload: dict[str, Any]) -> None:
            self._payload = payload

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return self._payload

    ok_payload = {
        "parse": {
            "title": "303: Compiling",
            "sections": [{"line": "Explanation"}, {"line": "Transcript"}],
            "text": {
                "*": (
                    '<h2><span class="mw-headline" id="Explanation">Explanation</span></h2>'
                    "<p>Compiling takes time.</p>"
                    '<h2><span class="mw-headline" id="Transcript">Transcript</span></h2>'
                    "<p>My code is compiling.</p>"
                )
            },
        }
    }

    with patch("xkcd_mcp.xkcd_api.httpx.AsyncClient.get", new=AsyncMock(return_value=_FakeResponse(ok_payload))):
        res = await fetch_explanation(303)
        assert res["success"] is True
        assert res["num"] == 303
        assert res["title"] == "303: Compiling"
        assert "Compiling takes time." in res["explanation"]
        assert "My code is compiling." in res["transcript"]

    err_payload = {"error": {"code": "missingtitle", "info": "The page you specified doesn't exist."}}
    with patch("xkcd_mcp.xkcd_api.httpx.AsyncClient.get", new=AsyncMock(return_value=_FakeResponse(err_payload))):
        res = await fetch_explanation(999999)
        assert res["success"] is False
        assert res["error_type"] == "not_found"


@pytest.mark.asyncio
async def test_mcp_tools_registered_with_annotations() -> None:
    tools = await server.mcp.list_tools()
    names = {t.name for t in tools}
    assert "xkcd_explain" in names
    assert "xkcd_get" in names
    assert "xkcd_latest" in names
    assert "xkcd_search" in names
    for tool in tools:
        assert tool.annotations is not None, f"Tool {tool.name} missing annotations"
        assert tool.annotations.readOnlyHint is not None, f"Tool {tool.name} missing readOnlyHint"


@pytest.mark.asyncio
async def test_xkcd_explain_handles_404_comic_gracefully() -> None:
    fake_exp = {
        "success": True,
        "num": 404,
        "title": "404: Not Found",
        "xkcd_url": "https://xkcd.com/404/",
        "explainxkcd_url": "https://www.explainxkcd.com/wiki/index.php/404",
        "explanation": "Comic 404 is an intentional HTTP 404 Not Found joke.",
        "transcript": "",
        "trivia": "Skipped intentionally.",
        "sections": ["Explanation", "Trivia"],
    }
    with (
        patch.object(
            xkcd_api, "fetch_by_number", new=AsyncMock(return_value={"success": False, "error": "No comic #404 (404)."})
        ),
        patch.object(xkcd_api, "fetch_explanation", new=AsyncMock(return_value=fake_exp)),
    ):
        result = await server.xkcd_explain(comic_number=404, include_trivia=True)
        assert not result.is_error
        text = str(result.content)
        assert "404: Not Found" in text
        assert "intentional HTTP 404" in text
        assert "Skipped intentionally." in text


def test_http_api_explain_routes() -> None:
    fake_exp = {
        "success": True,
        "num": 303,
        "title": "303: Compiling",
        "xkcd_url": "https://xkcd.com/303/",
        "explainxkcd_url": "https://www.explainxkcd.com/wiki/index.php/303",
        "explanation": "Sword fighting excuse.",
        "transcript": "",
        "trivia": "",
        "sections": ["Explanation"],
    }
    with patch("xkcd_mcp.app.fetch_explanation", new=AsyncMock(return_value=fake_exp)):
        client = TestClient(app)
        r_post = client.post("/api/comic", json={"operation": "explain", "comic_number": 303})
        assert r_post.status_code == 200
        assert r_post.json()["explanation"] == "Sword fighting excuse."

        r_get = client.get("/api/explain/303")
        assert r_get.status_code == 200
        assert r_get.json()["num"] == 303
