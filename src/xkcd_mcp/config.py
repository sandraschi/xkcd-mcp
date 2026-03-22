"""Settings from environment."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    mcp_http_path: str

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            host=os.getenv("XKCD_MCP_HOST", "127.0.0.1"),
            port=int(os.getenv("XKCD_MCP_PORT", "10778")),
            mcp_http_path=os.getenv("XKCD_MCP_HTTP_PATH", "/mcp"),
        )


def load_settings() -> Settings:
    return Settings.from_env()
