# xkcd-mcp

xkcd via the **official JSON API** only (`/info.0.json`). **No** HTML scraping; **no** Explainxkcd body fetch.

**Ships with**

- **MCP** — `xkcd_comic` (`current`, `by_number`, `random`)
- **Web UI** — Vite SPA: comic-panel hero (stick SVG + speech bubble), Comic Neue headings, Current / Random / # → `POST /api/comic` (same JSON as the tool)

**Repo:** [github.com/sandraschi/xkcd-mcp](https://github.com/sandraschi/xkcd-mcp)

---

## MCP tool — `xkcd_comic`

| Argument | Values / notes |
|----------|----------------|
| `operation` | `current` · `by_number` · `random` |
| `comic_number` | Required when `operation` is `by_number` |

**Returns** (among other fields): `num`, `title`, `safe_title`, `alt`, `img`, `xkcd_url`, `explainxkcd_url` (wiki link only), `json_source`.

---

## Run

### Server (API + MCP)

```powershell
uv sync
uv run xkcd-mcp --serve
```

- **HTTP:** `http://127.0.0.1:10778` — `/health`, `/docs`
- **MCP:** `http://127.0.0.1:10778/mcp`
- **Env:** `XKCD_MCP_HOST`, `XKCD_MCP_PORT` (default **10778**), `XKCD_MCP_HTTP_PATH` (default `/mcp`)

### Web UI (SPA)

```powershell
.\web_sota\start.ps1
```

Open **http://127.0.0.1:10779/**

---

## License

MIT
