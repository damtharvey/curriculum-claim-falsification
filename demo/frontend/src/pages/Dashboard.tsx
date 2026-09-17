import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getStats, type DemoStats } from "../api";

export function Dashboard() {
  const [stats, setStats] = useState<DemoStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getStats().then(setStats).catch((e) => setError(String(e)));
  }, []);

  if (error) {
    return (
      <div className="card">
        <h2>Error loading stats</h2>
        <p style={{ color: "var(--red)" }}>{error}</p>
        <p style={{ color: "var(--text-muted)", marginTop: "0.5rem" }}>
          Make sure the API is running. For local dev, start the Lambda emulator first.
        </p>
      </div>
    );
  }

  if (!stats) return <div className="loading">Loading dashboard</div>;

  return (
    <>
      <h2 style={{ marginBottom: "1rem" }}>
        Does the Assessment Require the Skill?
      </h2>

      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-value">{stats.totalItems.toLocaleString()}</div>
          <div className="stat-label">Keyed Items</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.totalWitnesses.toLocaleString()}</div>
          <div className="stat-label">Witnesses Found</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.corpora.length}</div>
          <div className="stat-label">Corpora</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.authorities.length}</div>
          <div className="stat-label">Authorities</div>
        </div>
      </div>

      <div className="card">
        <h3>Corpora</h3>
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          {stats.corpora.map((c) => (
            <Link key={c} to={`/items?corpus=${c}`}>
              <span className="badge badge-accent">{c}</span>
            </Link>
          ))}
        </div>
      </div>

      <div className="card">
        <h3>Response Types</h3>
        <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
          {Object.entries(stats.responseTypes).map(([type, count]) => (
            <div key={type}>
              <span className="badge badge-cyan">{type}</span>{" "}
              <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                {count.toLocaleString()}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <h3>Quick Actions</h3>
        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
          <Link to="/items">
            <button>Browse Items</button>
          </Link>
          <Link to="/witnesses">
            <button>View Witnesses</button>
          </Link>
          <Link to="/runner">
            <button>Interactive Rule Runner</button>
          </Link>
        </div>
      </div>

      <div className="card" style={{ borderLeft: "3px solid var(--yellow)" }}>
        <h3>One-Sided Semantics</h3>
        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
          A program that passes refutes the claim that passing requires the tagged operation.
          A search that finds no such program does not certify the claim beyond the programs searched.
          We never say students did not learn the skill.
        </p>
      </div>
    </>
  );
}
