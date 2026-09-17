import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { getItems, runRules, type ItemSummary, type RunRulesResponse } from "../api";

export function InteractiveRunner() {
  const [search, setSearch] = useState("");
  const [items, setItems] = useState<ItemSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [results, setResults] = useState<RunRulesResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [searching, setSearching] = useState(false);

  const doSearch = useCallback(async () => {
    if (!search.trim()) return;
    setSearching(true);
    try {
      const res = await getItems({ search, pageSize: "10" });
      setItems(res.items);
    } catch (e) {
      console.error(e);
    } finally {
      setSearching(false);
    }
  }, [search]);

  const handleRun = async (itemId: string) => {
    setSelectedId(itemId);
    setRunning(true);
    setResults(null);
    try {
      const res = await runRules(itemId);
      setResults(res);
    } catch (e) {
      console.error(e);
    } finally {
      setRunning(false);
    }
  };

  // Load a random sample on mount
  useEffect(() => {
    getItems({ pageSize: "10" }).then((res) => setItems(res.items)).catch(console.error);
  }, []);

  const nCorrect = results?.results.filter((r) => r.correct).length ?? 0;
  const nWrong = results?.results.filter((r) => !r.skipped && !r.correct).length ?? 0;
  const nSkipped = results?.results.filter((r) => r.skipped).length ?? 0;

  return (
    <>
      <h2 style={{ marginBottom: "0.5rem" }}>Interactive Rule Runner</h2>
      <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "1rem" }}>
        Search for an item, then run all 15 a priori programs against it in real time.
        Each program sees only a restricted view — never the answer key.
      </p>

      <div className="controls-row">
        <input
          type="search"
          placeholder="Search items by ID, stem, or claim…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && doSearch()}
          style={{ flex: 1, minWidth: "250px" }}
          aria-label="Search items to test"
        />
        <button onClick={doSearch} disabled={searching}>
          {searching ? "Searching…" : "Search"}
        </button>
      </div>

      {/* Item picker */}
      {items.length > 0 && (
        <div className="card" style={{ marginBottom: "1rem" }}>
          <h3>Select an item</h3>
          <div style={{ maxHeight: "300px", overflowY: "auto" }}>
            {items.map((item) => (
              <div
                key={item.id}
                style={{
                  padding: "0.5rem",
                  borderBottom: "1px solid var(--border)",
                  cursor: "pointer",
                  background: selectedId === item.id ? "var(--bg-hover)" : "transparent",
                  borderRadius: "var(--radius)",
                }}
                onClick={() => handleRun(item.id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === "Enter" && handleRun(item.id)}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <code style={{ fontSize: "0.75rem" }}>{item.id}</code>
                  <span className="badge badge-accent" style={{ fontSize: "0.65rem" }}>{item.corpus}</span>
                  <span className="badge badge-cyan" style={{ fontSize: "0.65rem" }}>{item.responseType}</span>
                </div>
                <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "0.15rem" }}>
                  {item.stem.slice(0, 100)}…
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Results */}
      {running && <div className="loading">Running rules</div>}

      {results && (
        <div className="card">
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.75rem", flexWrap: "wrap" }}>
            <h3 style={{ margin: 0 }}>Results for{" "}
              <Link to={`/items/${encodeURIComponent(results.itemId)}`}>
                {results.itemId}
              </Link>
            </h3>
            <span style={{ fontSize: "0.85rem" }}>
              Key: <code style={{ color: "var(--green)" }}>{results.key}</code>
            </span>
          </div>

          <div className="stat-grid" style={{ marginBottom: "1rem" }}>
            <div className="stat-card">
              <div className="stat-value" style={{ color: "var(--green)" }}>{nCorrect}</div>
              <div className="stat-label">Correct (witnesses)</div>
            </div>
            <div className="stat-card">
              <div className="stat-value" style={{ color: "var(--red)" }}>{nWrong}</div>
              <div className="stat-label">Wrong</div>
            </div>
            <div className="stat-card">
              <div className="stat-value" style={{ color: "var(--text-muted)" }}>{nSkipped}</div>
              <div className="stat-label">Skipped</div>
            </div>
          </div>

          <div style={{ marginBottom: "0.5rem" }}>
            <div className="trace-block" style={{ marginBottom: "0.5rem" }}>
              {results.stem.slice(0, 300)}
            </div>
          </div>

          {results.results.map((r) => (
            <div key={r.ruleId} style={{ padding: "0.5rem 0", borderBottom: "1px solid var(--border)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
                <code style={{ fontSize: "0.78rem", fontWeight: 600 }}>{r.ruleId}</code>
                <span className="badge badge-muted">{r.channel}</span>
                {r.lacks.map((op) => (
                  <span key={op} className="badge badge-red" style={{ fontSize: "0.65rem" }}>
                    −{op}
                  </span>
                ))}
                {r.skipped ? (
                  <span className="badge badge-muted">skipped</span>
                ) : r.correct ? (
                  <span className="badge badge-green">✓ {r.answer}</span>
                ) : (
                  <span className="badge badge-red">✗ {r.answer ?? "∅"}</span>
                )}
              </div>
              {r.trace.length > 0 && !r.skipped && (
                <details>
                  <summary style={{ fontSize: "0.75rem", color: "var(--accent)", cursor: "pointer", marginTop: "0.15rem" }}>
                    trace
                  </summary>
                  <div className="trace-block">{r.trace.join("\n")}</div>
                </details>
              )}
            </div>
          ))}
        </div>
      )}
    </>
  );
}
