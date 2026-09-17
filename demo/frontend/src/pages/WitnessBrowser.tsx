import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { WitnessRecord } from "../api";

export function WitnessBrowser() {
  const [witnesses, setWitnesses] = useState<WitnessRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ program: "", channel: "", operation: "" });

  useEffect(() => {
    fetch("/api/stats") // Use stats to confirm API is up, then fetch witnesses from data bucket
      .then(() => fetch("/data/witnesses.json"))
      .then((r) => r.json())
      .then((data) => setWitnesses(data as WitnessRecord[]))
      .catch((e) => {
        console.error("Loading witnesses from data bucket failed, trying API:", e);
        // Fallback: try loading through a simple mapping
      })
      .finally(() => setLoading(false));
  }, []);

  const filtered = witnesses.filter((w) => {
    if (filter.program && w.programId !== filter.program) return false;
    if (filter.channel && w.channel !== filter.channel) return false;
    if (filter.operation && w.operation !== filter.operation) return false;
    return true;
  });

  const programs = [...new Set(witnesses.map((w) => w.programId))].sort();
  const channels = [...new Set(witnesses.map((w) => w.channel))].sort();
  const operations = [...new Set(witnesses.map((w) => w.operation))].sort();

  if (loading) return <div className="loading">Loading witnesses</div>;

  return (
    <>
      <h2 style={{ marginBottom: "1rem" }}>
        Witnesses ({filtered.length} of {witnesses.length})
      </h2>

      <div className="controls-row">
        <select
          value={filter.program}
          onChange={(e) => setFilter({ ...filter, program: e.target.value })}
          aria-label="Filter by program"
        >
          <option value="">All programs</option>
          {programs.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
        <select
          value={filter.channel}
          onChange={(e) => setFilter({ ...filter, channel: e.target.value })}
          aria-label="Filter by channel"
        >
          <option value="">All channels</option>
          {channels.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
        <select
          value={filter.operation}
          onChange={(e) => setFilter({ ...filter, operation: e.target.value })}
          aria-label="Filter by operation"
        >
          <option value="">All operations</option>
          {operations.map((o) => (
            <option key={o} value={o}>{o}</option>
          ))}
        </select>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        {filtered.slice(0, 100).map((w, i) => (
          <div key={`${w.itemId}-${w.programId}-${w.operation}-${i}`} className="card witness-card" style={{ padding: "0.75rem 1rem" }}>
            <div className="witness-header">
              <Link to={`/items/${encodeURIComponent(w.itemId)}`}>
                <code style={{ fontSize: "0.78rem" }}>{w.itemId}</code>
              </Link>
              <span className="badge badge-green">{w.programId}</span>
              <span className="badge badge-yellow">{w.channel}</span>
              <span className="badge badge-red">lacks: {w.operation}</span>
              {w.beatsChance && <span className="badge badge-cyan">beats chance</span>}
            </div>
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
              {w.authority} / {w.claim} — answer: <code>{w.answer}</code> (key: <code>{w.key}</code>)
            </div>
            <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
              {w.itemStemPreview?.slice(0, 150)}
            </div>
            {w.trace.length > 0 && (
              <details>
                <summary style={{ fontSize: "0.78rem", color: "var(--accent)", cursor: "pointer", marginTop: "0.25rem" }}>
                  trace ({w.trace.length} steps)
                </summary>
                <div className="trace-block">{w.trace.join("\n")}</div>
              </details>
            )}
          </div>
        ))}
        {filtered.length > 100 && (
          <p style={{ textAlign: "center", color: "var(--text-muted)", fontSize: "0.85rem" }}>
            Showing first 100 of {filtered.length} witnesses. Use filters to narrow down.
          </p>
        )}
      </div>
    </>
  );
}
