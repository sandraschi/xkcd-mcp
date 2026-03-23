# xkcd-mcp

**MODEL CONTEXT PROTOCOL** — *fine print sold separately*

---

### The part humans read first

**xkcd-mcp** — Comics for your LLM. **Official** JSON API (`/info.0.json`), **unofficial** amount of stick-figure drama.

You get a small **Vite** dashboard with a comic-panel **hero**: stick people, a speech bubble that says *“MCP, explain this”*, and a box labeled **JSON** that definitely understands your feelings. The README can’t draw SVG, so imagine it badly—same energy as the web app.

> **Alt text (this repo):** A README receives a pull request titled “make it whimsical.” The CI passes. The narrator questions whether that was ever in scope.

> **Alt text (the app):** A tiny server labeled “JSON” gets enthusiastic waves while someone negotiates with the universe. Hover tooltips not included; that’s what the comic **alt** is for.

No scraping. No Explainxkcd body fetch. We’re not here to parse HTML like it’s 2003.

**Repo:** [github.com/sandraschi/xkcd-mcp](https://github.com/sandraschi/xkcd-mcp)

---

## Technical details

### What it is

- **MCP server + HTTP API** exposing xkcd metadata and image URLs via the **official** API only.
- **Web UI** calls `POST /api/comic` with the same operations as the tool (`current`, `random`, `by_number`).

### MCP tool — `xkcd_comic`

| Argument | Values / notes |
|----------|----------------|
| `operation` | `current` · `by_number` · `random` |
| `comic_number` | Required when `operation` is `by_number` |

**Returns** (among other fields): `num`, `title`, `safe_title`, `alt`, `img`, `xkcd_url`, `explainxkcd_url` (wiki link only), `json_source`, etc.

### Install

You need the repo on disk first—`uv` can’t sync a project you haven’t cloned.

```powershell
git clone https://github.com/sandraschi/xkcd-mcp.git
Set-Location xkcd-mcp
uv sync
```

All commands below assume your shell is at the **repo root** (`xkcd-mcp`).

### Run — server (API + MCP)

```powershell
uv run xkcd-mcp --serve
```

| Item | Value |
|------|--------|
| HTTP | `http://127.0.0.1:10778` — `/health`, `/docs` |
| MCP | `http://127.0.0.1:10778/mcp` |
| Env | `XKCD_MCP_HOST`, `XKCD_MCP_PORT` (default **10778**), `XKCD_MCP_HTTP_PATH` (default `/mcp`) |

### Run — web UI (SPA)

```powershell
.\web_sota\start.ps1
```

**http://127.0.0.1:10779/** (same repo root as install)

### License

MIT
