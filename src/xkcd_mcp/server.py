"""FastMCP 3.2 - xkcd tools."""

from __future__ import annotations

import os

from fastmcp import FastMCP
from fastmcp.server import create_proxy
from fastmcp.tools import ToolResult

from xkcd_mcp import xkcd_api

# Prefab UI imports with graceful fallback
try:
    from prefab_ui.app import PrefabApp
    from prefab_ui.components import Card, CardContent, CardHeader, CardTitle, Image, Text

    HAS_PREFAB = os.environ.get("XKCD_PREFAB_APPS", "1") != "0"
except ImportError:
    HAS_PREFAB = False

_READONLY = {"readOnlyHint": True, "openWorldHint": True}
_LOCAL_READONLY = {"readOnlyHint": True, "openWorldHint": False}
_MAX_EXPLANATION_CHARS = 16000

mcp = FastMCP(
    "xkcd-mcp",
    instructions=(
        "xkcd comics via the official xkcd.com JSON API and explainxkcd.com MediaWiki JSON API. "
        "Tools: xkcd_latest, xkcd_get, xkcd_random, xkcd_search, xkcd_explain, show_comic_prefab_card, xkcd_help. "
        "Use xkcd_explain (or include_explanation=True) to fetch full explainxkcd explanations, transcripts, and trivia "
        "for obscure or technical comics."
    ),
)

# MCP Bridge: proxy tools from other MCP servers via MCP_BRIDGE_URLS
_bridge_proxies: list[str] = []
bridge_urls = os.getenv("MCP_BRIDGE_URLS", "")
if bridge_urls:
    for url in bridge_urls.split(","):
        url = url.strip()
        if url:
            try:
                mcp.add_provider(create_proxy(url))
                _bridge_proxies.append(url)
            except Exception:
                pass


@mcp.tool(annotations=_READONLY)
async def xkcd_latest(include_explanation: bool = False) -> ToolResult:
    """Fetch the latest comic from xkcd.com.

    Args:
        include_explanation (bool): If True, also fetch the explainxkcd explanation text.
    """
    try:
        res = await xkcd_api.fetch_current()
        if not res.get("success"):
            return ToolResult(content=f"Error: {res.get('error')}", is_error=True)
        return await _format_comic_result(res["comic"], include_explanation=include_explanation)
    except Exception as e:
        return ToolResult(content=f"Unexpected error: {e!s}", is_error=True)


@mcp.tool(annotations=_READONLY)
async def xkcd_get(comic_number: int, include_explanation: bool = False) -> ToolResult:
    """Fetch a specific xkcd comic by its number.

    Args:
        comic_number (int): Required. Comic index (>= 1).
        include_explanation (bool): If True, also fetch the explainxkcd explanation text.
    """
    try:
        res = await xkcd_api.fetch_by_number(comic_number)
        if not res.get("success"):
            return ToolResult(content=f"Error: {res.get('error')}", is_error=True)
        return await _format_comic_result(res["comic"], include_explanation=include_explanation)
    except Exception as e:
        return ToolResult(content=f"Unexpected error: {e!s}", is_error=True)


@mcp.tool(annotations=_READONLY)
async def xkcd_explain(
    comic_number: int | None = None,
    include_transcript: bool = True,
    include_trivia: bool = False,
) -> ToolResult:
    """Fetch the explainxkcd explanation (and optional transcript/trivia) for an xkcd comic.

    Uses the explainxkcd MediaWiki JSON API (no HTML page scraping). Essential for
    understanding obscure, technical, math, physics, or inside-joke xkcd comics.
    If comic_number is omitted, explains the latest xkcd comic.

    Args:
        comic_number (int | None): Comic number (>= 1). Defaults to the latest comic if omitted.
        include_transcript (bool): Include the explainxkcd transcript section (default True).
        include_trivia (bool): Include the explainxkcd trivia section if available (default False).
    """
    try:
        comic: dict | None = None
        if comic_number is None:
            cur = await xkcd_api.fetch_current()
            if not cur.get("success"):
                return ToolResult(content=f"Error: {cur.get('error')}", is_error=True)
            comic = cur["comic"]
            num = int(comic["num"])
        else:
            num = comic_number
            comic_res = await xkcd_api.fetch_by_number(num)
            if comic_res.get("success"):
                comic = comic_res["comic"]

        exp = await xkcd_api.fetch_explanation(num)
        if not exp.get("success"):
            return ToolResult(content=f"Error: {exp.get('error')}", is_error=True)

        explanation = exp.get("explanation", "")
        transcript = exp.get("transcript", "") if include_transcript else ""
        trivia = exp.get("trivia", "") if include_trivia else ""

        truncated = False
        if len(explanation) > _MAX_EXPLANATION_CHARS:
            explanation = explanation[:_MAX_EXPLANATION_CHARS].rstrip() + "\n\n[...truncated; see full wiki page]"
            truncated = True

        title = exp.get("title") or (f"{num}: {comic['title']}" if comic else f"xkcd #{num}")
        parts = [f"# Explain xkcd - {title}"]
        if comic:
            parts.append(f"Image: {comic['img']}")
            if comic.get("alt"):
                parts.append(f"Alt text: {comic['alt']}")
        parts.append(f"Links: {exp['xkcd_url']} | {exp['explainxkcd_url']}")

        if explanation:
            parts.append(f"\n## Explanation\n{explanation}")
        else:
            parts.append("\n## Explanation\nNo explanation section was found on explainxkcd.")

        if transcript:
            parts.append(f"\n## Transcript\n{transcript}")
        if trivia:
            parts.append(f"\n## Trivia\n{trivia}")
        if truncated:
            parts.append(f"\nFull explanation: {exp['explainxkcd_url']}")

        text_summary = "\n".join(parts)

        structured_content = None
        if HAS_PREFAB:
            with Card(css_class="max-w-2xl border-none shadow-none bg-transparent") as view:
                with CardHeader():
                    CardTitle(f"Explain xkcd: {title}")
                with CardContent():
                    if comic and comic.get("img"):
                        Image(src=comic["img"], alt=comic.get("alt", ""), css_class="rounded-lg shadow-md mb-2")
                    if comic and comic.get("alt"):
                        Text(comic["alt"], css_class="text-sm italic opacity-80 mb-3")
                    if explanation:
                        preview = explanation[:2400] + ("..." if len(explanation) > 2400 else "")
                        Text(preview, css_class="text-sm whitespace-pre-wrap mb-2")
                    Text(
                        f"[View on xkcd]({exp['xkcd_url']}) | [Full explainxkcd]({exp['explainxkcd_url']})",
                        css_class="text-xs text-primary",
                    )

            structured_content = PrefabApp(view=view, title=f"Explain xkcd #{num}")

        return ToolResult(content=text_summary, structured_content=structured_content)
    except Exception as e:
        return ToolResult(content=f"Unexpected error: {e!s}", is_error=True)


@mcp.tool(annotations=_READONLY)
async def xkcd_search(query: str) -> ToolResult:
    """
    Search for xkcd comics by topic (e.g., 'aliens', 'global warming').
    Uses explainxkcd semantic indexing to find relevant comic numbers.
    """
    try:
        # 1. Search explainxkcd for comic numbers
        comic_nums = await xkcd_api.search_explain_xkcd(query)
        if not comic_nums:
            return ToolResult(content=f"No xkcd comics found for topic: '{query}'", is_error=False)

        # 2. Fetch full metadata for each found comic
        comics = []
        for num in comic_nums:
            res = await xkcd_api.fetch_by_number(num)
            if res.get("success"):
                comics.append(res["comic"])

        if not comics:
            return ToolResult(
                content=f"Found references for '{query}', but could not fetch metadata.",
                is_error=True,
            )

        # 3. Format result (Text + Prefab)
        text_results = [f"Found {len(comics)} comics for '{query}':"]
        for c in comics:
            text_results.append(f"- #{c['num']}: {c['title']} ({c['xkcd_url']})")

        text_summary = "\n".join(text_results)

        structured_content = None
        if HAS_PREFAB:
            # We'll use a vertical stack of comic cards
            with Text(css_class="flex flex-col gap-6") as view:
                Text(f"Search Results for: **{query}**", css_class="text-xl font-bold mb-4")
                for c in comics:
                    with Card(css_class="border-none shadow-none bg-secondary/10 p-4 rounded-xl"):
                        with CardHeader():
                            CardTitle(f"#{c['num']}: {c['title']}")
                        with CardContent():
                            Image(
                                src=c["img"],
                                alt=c["alt"],
                                css_class="rounded-lg mb-2 max-h-64 object-contain",
                            )
                            Text(c["alt"], css_class="text-sm italic opacity-80 mb-2")
                            Text(
                                f"[View on xkcd]({c['xkcd_url']}) | [Explanation]({c['explainxkcd_url']})",
                                css_class="text-xs text-primary",
                            )

            structured_content = PrefabApp(view=view, title=f"xkcd Search: {query}")

        return ToolResult(content=text_summary, structured_content=structured_content)
    except Exception as e:
        return ToolResult(content=f"Search failed: {e!s}", is_error=True)


@mcp.tool(annotations=_READONLY)
async def xkcd_random(include_explanation: bool = False) -> ToolResult:
    """Fetch a random comic from the entire xkcd collection.

    Args:
        include_explanation (bool): If True, also fetch the explainxkcd explanation text.
    """
    try:
        res = await xkcd_api.fetch_random()
        if not res.get("success"):
            return ToolResult(content=f"Error: {res.get('error')}", is_error=True)
        return await _format_comic_result(res["comic"], include_explanation=include_explanation)
    except Exception as e:
        return ToolResult(content=f"Unexpected error: {e!s}", is_error=True)


@mcp.tool(annotations=_READONLY)
async def show_comic_prefab_card(comic_number: int | None = None, include_explanation: bool = False) -> ToolResult:
    """Show a rich prefab card for an xkcd comic. Fetches random if no number given.

    This tool renders an interactive UI in the chat. Prefer it over text output
    when displaying data from other xkcd-mcp tools.

    Args:
        comic_number (int | None): Optional comic number (>= 1). Random if omitted.
        include_explanation (bool): If True, also fetch and include the explainxkcd explanation.
    """
    try:
        if comic_number is None:
            res = await xkcd_api.fetch_random()
        else:
            res = await xkcd_api.fetch_by_number(comic_number)
        if not res.get("success"):
            return ToolResult(content=f"Error: {res.get('error')}", is_error=True)
        return await _format_comic_result(res["comic"], include_explanation=include_explanation)
    except Exception as e:
        return ToolResult(content=f"Unexpected error: {e!s}", is_error=True)


@mcp.tool(annotations=_LOCAL_READONLY)
async def xkcd_help() -> ToolResult:
    """Get help and usage information for xkcd-mcp tools and configuration."""
    help_text = (
        "# xkcd-mcp Help\n\n"
        "This server uses the official xkcd.com JSON API for comics and the explainxkcd.com MediaWiki JSON API "
        "for topic search, explanations, transcripts, and trivia.\n\n"
        "### Available Tools\n"
        "- `xkcd_latest(include_explanation=False)`: Fetch the most recent comic.\n"
        "- `xkcd_get(comic_number, include_explanation=False)`: Fetch a specific comic by number.\n"
        "- `xkcd_explain(comic_number=None, include_transcript=True, include_trivia=False)`: Fetch the full explainxkcd explanation (defaults to latest).\n"
        "- `xkcd_random(include_explanation=False)`: Get a random surprise comic.\n"
        "- `xkcd_search(query)`: Search comics by topic (e.g., 'aliens').\n"
        "- `show_comic_prefab_card(comic_number=None, include_explanation=False)`: Render a rich in-chat Prefab card.\n\n"
        "### Configuration\n"
        "- **Backend Port**: 10778 (API + MCP HTTP)\n"
        "- **Web UI Port**: 10779 (Vite Dashboard)\n"
        "- **Prefab UI**: Enabled by default in compatible clients.\n\n"
        "### Links\n"
        "- [Official xkcd](https://xkcd.com)\n"
        "- [explainxkcd Wiki](https://www.explainxkcd.com)\n"
    )

    structured_content = None
    if HAS_PREFAB:
        with Card(css_class="max-w-xl border-none shadow-none bg-transparent") as view:
            with CardHeader():
                CardTitle("xkcd-mcp Help Center")
            with CardContent():
                Text(
                    "Official xkcd metadata, explainxkcd explanations, and rich in-chat comic rendering.",
                    css_class="text-lg font-bold mb-4",
                )
                with Text(css_class="grid grid-cols-2 gap-4"):
                    with Text():
                        Text("Backend API", css_class="font-mono text-sm opacity-60")
                        Text("Port 10778", css_class="text-xl")
                    with Text():
                        Text("Web UI", css_class="font-mono text-sm opacity-60")
                        Text("Port 10779", css_class="text-xl")
                Text("\nUse `xkcd_latest`, `xkcd_explain`, or `xkcd_random` to get started!", css_class="mt-4 italic")

        structured_content = PrefabApp(view=view, title="xkcd-mcp Help")

    return ToolResult(content=help_text, structured_content=structured_content)


async def _format_comic_result(comic: dict, include_explanation: bool = False) -> ToolResult:
    """Common formatting for comic results (Text + Prefab)."""
    title = comic["title"]
    alt = comic["alt"]
    img_url = comic["img"]
    num = comic["num"]

    label = f"xkcd #{num}: {title}"
    text_summary = f"{label}\nImage: {img_url}\nAlt: {alt}\nLinks: {comic['xkcd_url']} | {comic['explainxkcd_url']}"

    explanation_text = ""
    if include_explanation:
        exp = await xkcd_api.fetch_explanation(num)
        if exp.get("success") and exp.get("explanation"):
            explanation_text = exp["explanation"]
            if len(explanation_text) > _MAX_EXPLANATION_CHARS:
                explanation_text = (
                    explanation_text[:_MAX_EXPLANATION_CHARS].rstrip() + "\n\n[...truncated; see full wiki page]"
                )
            text_summary += f"\n\n## Explanation (explainxkcd)\n{explanation_text}"

    structured_content = None
    if HAS_PREFAB:
        with Card(css_class="max-w-2xl border-none shadow-none bg-transparent") as view:
            with CardHeader():
                CardTitle(label)
            with CardContent():
                Image(src=img_url, alt=alt, css_class="rounded-lg shadow-md mb-2")
                Text(alt, css_class="text-sm italic opacity-80")
                if explanation_text:
                    preview = explanation_text[:2000] + ("..." if len(explanation_text) > 2000 else "")
                    Text(preview, css_class="text-sm whitespace-pre-wrap mt-3")

        structured_content = PrefabApp(view=view, title=label)

    return ToolResult(content=text_summary, structured_content=structured_content)
