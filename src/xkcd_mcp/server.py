"""FastMCP 3.1 — xkcd tools."""

from __future__ import annotations

from typing import Any, Literal

from fastmcp import FastMCP

from xkcd_mcp import xkcd_api

mcp = FastMCP(
    "xkcd-mcp",
    instructions=(
        "xkcd comics via the official JSON API only (xkcd.com/.../info.0.json). "
        "Operations: current, by_number, random. Includes image URL, alt text, and explainxkcd wiki link "
        "(link only — no scraping)."
    ),
)


@mcp.tool()
async def xkcd_comic(
    operation: Literal["current", "by_number", "random"],
    comic_number: int | None = None,
) -> dict[str, Any]:
    """XKCD_COMIC — Fetch comic metadata from xkcd’s official JSON API.

    Args:
        operation: current | by_number | random.
        comic_number: Required when operation is by_number (published index).

    Returns:
        success, comic dict (num, title, alt, img, xkcd_url, explainxkcd_url, …) or error.
    """
    try:
        if operation == "current":
            return await xkcd_api.fetch_current()
        if operation == "random":
            return await xkcd_api.fetch_random()
        if operation == "by_number":
            if comic_number is None:
                return {"success": False, "error": "comic_number is required for by_number."}
            return await xkcd_api.fetch_by_number(int(comic_number))
        return {"success": False, "error": f"Unknown operation: {operation}"}
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }
