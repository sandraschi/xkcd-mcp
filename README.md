# xkcd-mcp

**xkcd comics via the official JSON API only** (`/info.0.json`) — **no HTML scraping**, no Explainxkcd body fetch. MCP tool + small Vite UI.

**Repo:** [github.com/sandraschi/xkcd-mcp](https://github.com/sandraschi/xkcd-mcp)

## MCP tool

| `xkcd_comic` | Args |
|--------------|------|
| `operation` | `current` \| `by_number` \| `random` |
| `comic_number` | Required for `by_number` |

Returns `comic`: `num`, `title`, `safe_title`, `alt`, `img`, `xkcd_url`, `explainxkcd_url` (wiki link only), `json_source`, etc.

## Run

```powershell
uv sync
uv run xkcd-mcp --serve
```

- **API:** `http://127.0.0.1:10778` — `/health`, `/docs`, MCP **`http://127.0.0.1:10778/mcp`**
- **Env:** `XKCD_MCP_HOST`, `XKCD_MCP_PORT` (default **10778**), `XKCD_MCP_HTTP_PATH` (default `/mcp`)

**SPA:** `.\web_sota\start.ps1` → `http://127.0.0.1:10779/`

## License

MIT
