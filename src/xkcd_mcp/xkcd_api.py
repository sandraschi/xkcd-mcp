"""xkcd.com official JSON API and explainxkcd.com MediaWiki JSON API (no HTML page scraping)."""

from __future__ import annotations

import base64
import random
import re
from html.parser import HTMLParser
from typing import Any

import httpx

_BASE = "https://xkcd.com"
_EXPLAIN = "https://www.explainxkcd.com/wiki/api.php"
_UA = "xkcd-mcp/0.4 (+https://github.com/sandraschi/xkcd-mcp)"

_H2_PATTERN = re.compile(r"<h2\b[^>]*>(.*?)</h2>", re.IGNORECASE | re.DOTALL)
_H1_PATTERN = re.compile(r"<h1\b", re.IGNORECASE)
_TAG_PATTERN = re.compile(r"<[^>]+>")


class _HTMLTextExtractor(HTMLParser):
    """Convert MediaWiki parsed HTML into clean readable plain text / markdown."""

    _SKIP_TAGS = frozenset({"style", "script", "noscript"})
    _BLOCK_TAGS = frozenset({"p", "div", "ul", "ol", "dl", "table", "blockquote"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skip_depth = 0
        self._in_cell = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        t = tag.lower()
        if t in self._SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if t in ("h3", "h4", "h5"):
            level = int(t[1])
            self._parts.append(f"\n\n{'#' * level} ")
        elif t == "br":
            self._parts.append("\n")
        elif t == "li":
            self._parts.append("\n- ")
        elif t in ("dt", "dd"):
            self._parts.append("\n")
        elif t == "tr":
            self._parts.append("\n")
            self._in_cell = False
        elif t in ("td", "th"):
            if self._in_cell:
                self._parts.append(" | ")
            self._in_cell = True
        elif t in self._BLOCK_TAGS:
            self._parts.append("\n\n")

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t in self._SKIP_TAGS:
            if self._skip_depth > 0:
                self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if t in ("h3", "h4", "h5", "p", "div", "table", "blockquote"):
            self._parts.append("\n\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self._parts.append(data)

    def get_text(self) -> str:
        raw = "".join(self._parts)
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in raw.splitlines()]
        cleaned = "\n".join(lines)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()


def _html_to_text(html: str) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(html)
    parser.close()
    return parser.get_text()


def _extract_explainxkcd_sections(html: str) -> dict[str, str]:
    """Extract Explanation, Transcript, and Trivia sections from MediaWiki parsed HTML."""
    matches = list(_H2_PATTERN.finditer(html))
    sections: dict[str, str] = {}

    for idx, match in enumerate(matches):
        heading_text = _TAG_PATTERN.sub("", match.group(1)).strip().lower()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(html)
        body_html = html[start:end]

        # Truncate before any top-level <h1> (e.g. MediaWiki Discussion banner)
        h1_match = _H1_PATTERN.search(body_html)
        if h1_match:
            body_html = body_html[: h1_match.start()]

        if heading_text in ("explanation", "transcript", "trivia"):
            text = _html_to_text(body_html)
            if text:
                sections[heading_text] = text

    return sections


def _comic_dict(data: dict[str, Any]) -> dict[str, Any]:
    num = int(data["num"])
    return {
        "num": num,
        "month": data.get("month"),
        "year": data.get("year"),
        "day": data.get("day"),
        "title": data.get("title"),
        "safe_title": data.get("safe_title"),
        "alt": data.get("alt"),
        "img": data.get("img"),
        "transcript": data.get("transcript"),
        "link": data.get("link") or "",
        "news": data.get("news") or "",
        "xkcd_url": f"{_BASE}/{num}/",
        "explainxkcd_url": f"https://www.explainxkcd.com/wiki/index.php/{num}",
        "json_source": f"{_BASE}/{num}/info.0.json",
    }


async def fetch_current() -> dict[str, Any]:
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(20.0),
        headers={"User-Agent": _UA},
    ) as client:
        r = await client.get(f"{_BASE}/info.0.json")
    r.raise_for_status()
    data = r.json()
    return {"success": True, "comic": _comic_dict(data)}


async def fetch_by_number(num: int) -> dict[str, Any]:
    if num < 1:
        return {"success": False, "error": "comic_number must be >= 1"}
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(20.0),
        headers={"User-Agent": _UA},
    ) as client:
        r = await client.get(f"{_BASE}/{num}/info.0.json")
    if r.status_code == 404:
        return {"success": False, "error": f"No comic #{num} (404)."}
    r.raise_for_status()
    data = r.json()
    return {"success": True, "comic": _comic_dict(data)}


async def fetch_random() -> dict[str, Any]:
    cur = await fetch_current()
    if not cur.get("success"):
        return cur
    n = int(cur["comic"]["num"])
    if n < 1:
        return {"success": False, "error": "Could not determine latest comic number."}
    pick = random.randint(1, n)
    return await fetch_by_number(pick)


async def fetch_image_data_uri(url: str) -> str | None:
    """Fetch image from URL and return as base64 data URI (capped at 512KB)."""
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(20.0),
            headers={"User-Agent": _UA},
        ) as client:
            # Use stream=True and a byte limit to prevent huge payloads
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                content_type = response.headers.get("content-type", "image/png")
                chunks = []
                bytes_received = 0
                max_bytes = 512 * 1024  # 512 KB SOTA cap

                async for chunk in response.aiter_bytes():
                    bytes_received += len(chunk)
                    if bytes_received > max_bytes:
                        # Too big; abort
                        return None
                    chunks.append(chunk)

                image_data = b"".join(chunks)
                b64_data = base64.b64encode(image_data).decode("utf-8")
                return f"data:{content_type};base64,{b64_data}"
    except Exception:
        return None


async def search_explain_xkcd(query: str, limit: int = 5) -> list[int]:
    """
    Search explainxkcd.com for a topic and return up to `limit` comic numbers.
    Uses the MediaWiki API: action=query&list=search.
    """
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": limit,
        "srwhat": "text",
    }

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(20.0),
            headers={"User-Agent": _UA},
        ) as client:
            r = await client.get(_EXPLAIN, params=params)
            r.raise_for_status()
            data = r.json()

        search_results = data.get("query", {}).get("search", [])
        comic_nums = []

        # Regex to find "NUM:" in titles like "1732: Earth Temperature Timeline"
        num_pattern = re.compile(r"(\d+):")

        for result in search_results:
            title = result.get("title", "")
            match = num_pattern.search(title)
            if match:
                comic_nums.append(int(match.group(1)))

        return comic_nums
    except Exception:
        return []


async def fetch_explanation(num: int) -> dict[str, Any]:
    """Fetch the explainxkcd explanation, transcript, and trivia for a comic via MediaWiki JSON API."""
    if num < 1:
        return {
            "success": False,
            "error": "comic_number must be >= 1",
            "error_type": "validation",
        }

    params = {
        "action": "parse",
        "page": str(num),
        "redirects": 1,
        "prop": "text|sections",
        "disableeditsection": 1,
        "disabletoc": 1,
        "format": "json",
    }

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(20.0),
            headers={"User-Agent": _UA},
        ) as client:
            r = await client.get(_EXPLAIN, params=params)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as exc:
        return {
            "success": False,
            "error": f"explainxkcd HTTP error {exc.response.status_code} for comic #{num}.",
            "error_type": "upstream_error",
        }
    except Exception as exc:
        return {
            "success": False,
            "error": f"Failed to reach explainxkcd for comic #{num}: {exc!s}",
            "error_type": "upstream_error",
        }

    if "error" in data:
        err_info = data["error"].get("info", "Unknown MediaWiki error")
        err_code = data["error"].get("code", "error")
        return {
            "success": False,
            "error": f"No explainxkcd page for comic #{num}: {err_info}",
            "error_type": "not_found" if err_code == "missingtitle" else "upstream_error",
        }

    parse = data.get("parse", {})
    html = parse.get("text", {}).get("*", "")
    sections = _extract_explainxkcd_sections(html)
    section_names = [s.get("line", "") for s in parse.get("sections", []) if s.get("line")]

    return {
        "success": True,
        "num": num,
        "title": parse.get("title", f"xkcd #{num}"),
        "explainxkcd_url": f"https://www.explainxkcd.com/wiki/index.php/{num}",
        "xkcd_url": f"{_BASE}/{num}/",
        "explanation": sections.get("explanation", ""),
        "transcript": sections.get("transcript", ""),
        "trivia": sections.get("trivia", ""),
        "sections": section_names,
    }
