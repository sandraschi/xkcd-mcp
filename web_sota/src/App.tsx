import { useCallback, useState } from "react";

type Comic = {
  num: number;
  title?: string;
  safe_title?: string;
  alt?: string;
  img?: string;
  xkcd_url?: string;
  explainxkcd_url?: string;
};

export default function App() {
  const [busy, setBusy] = useState(false);
  const [comic, setComic] = useState<Comic | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [numInput, setNumInput] = useState("");

  const load = useCallback(async (operation: "current" | "random" | "by_number", n?: number) => {
    setBusy(true);
    setErr(null);
    setComic(null);
    try {
      const r = await fetch("/api/comic", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          operation,
          comic_number: n,
        }),
      });
      const j = (await r.json()) as { success?: boolean; comic?: Comic; error?: string };
      if (!j.success || !j.comic) {
        setErr(j.error ?? "Failed");
        return;
      }
      setComic(j.comic);
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  }, []);

  return (
    <div style={{ maxWidth: 720, margin: "0 auto", padding: "1.5rem" }}>
      <header
        style={{
          marginBottom: "1.25rem",
          padding: "1.1rem 1.25rem",
          borderRadius: 12,
          background: "linear-gradient(145deg, rgba(40,48,64,.9), rgba(20,24,32,.95))",
          border: "1px solid rgba(120,140,180,.25)",
        }}
      >
        <h1 style={{ margin: "0 0 .35rem", fontSize: "1.35rem" }}>xkcd-mcp</h1>
        <p style={{ margin: 0, opacity: 0.88, fontSize: "0.92rem" }}>
          Official JSON API only — no scraping.{" "}
          <a href="https://github.com/sandraschi/xkcd-mcp" target="_blank" rel="noopener noreferrer">
            Repo
          </a>
        </p>
      </header>

      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 16 }}>
        <button
          type="button"
          disabled={busy}
          onClick={() => void load("current")}
          style={{ padding: "8px 14px", borderRadius: 8, cursor: busy ? "wait" : "pointer" }}
        >
          Current
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => void load("random")}
          style={{ padding: "8px 14px", borderRadius: 8, cursor: busy ? "wait" : "pointer" }}
        >
          Random
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => {
            const n = parseInt(numInput, 10);
            if (!Number.isFinite(n) || n < 1) {
              setErr("Enter a comic number ≥ 1");
              return;
            }
            void load("by_number", n);
          }}
          style={{ padding: "8px 14px", borderRadius: 8, cursor: busy ? "wait" : "pointer" }}
        >
          #
        </button>
        <input
          type="number"
          min={1}
          placeholder="e.g. 2916"
          value={numInput}
          onChange={(e) => setNumInput(e.target.value)}
          style={{ width: 100, padding: 8, borderRadius: 6, background: "#1a1e26", color: "#fff", border: "1px solid #333" }}
        />
      </div>

      {err && <p style={{ color: "#f88" }}>{err}</p>}

      {comic && (
        <article
          style={{
            padding: "1rem",
            borderRadius: 12,
            background: "#151922",
            border: "1px solid #2a3140",
          }}
        >
          <h2 style={{ margin: "0 0 12px", fontSize: "1.15rem" }}>
            #{comic.num}. {comic.title ?? comic.safe_title}
          </h2>
          {comic.img && (
            <img
              src={comic.img}
              alt={comic.alt ?? ""}
              style={{ maxWidth: "100%", height: "auto", borderRadius: 8 }}
            />
          )}
          {comic.alt && (
            <p style={{ marginTop: 12, fontSize: 14, lineHeight: 1.5, opacity: 0.92 }}>{comic.alt}</p>
          )}
          <p style={{ marginTop: 14, fontSize: 13 }}>
            <a href={comic.xkcd_url} target="_blank" rel="noopener noreferrer">
              xkcd
            </a>
            {" · "}
            <a href={comic.explainxkcd_url} target="_blank" rel="noopener noreferrer">
              explainxkcd
            </a>
          </p>
        </article>
      )}

      <details style={{ marginTop: 24 }}>
        <summary style={{ cursor: "pointer", opacity: 0.75 }}>MCP</summary>
        <p style={{ fontSize: 13 }}>
          Streamable HTTP: <code>http://127.0.0.1:10778/mcp</code>
        </p>
      </details>
    </div>
  );
}
