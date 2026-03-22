"""xkcd API helpers (structure)."""

from xkcd_mcp.xkcd_api import _comic_dict


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
