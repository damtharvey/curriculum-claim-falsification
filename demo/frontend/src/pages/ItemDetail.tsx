import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getItem, runRules, type ItemDetail as ItemDetailType, type RunRulesResponse } from "../api";

export function ItemDetail() {
  const { itemId } = useParams<{ itemId: string }>();
  const [item, setItem] = useState<ItemDetailType | null>(null);
  const [ruleResults, setRuleResults] = useState<RunRulesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!itemId) return;
    setLoading(true);
    getItem(itemId)
      .then(setItem)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [itemId]);

  const handleRunRules = async () => {
    if (!itemId) return;
    setRunning(true);
    try {
      const res = await runRules(itemId);
      setRuleResults(res);
    } catch (e) {
      setError(String(e));
    } finally {
      setRunning(false);
    }
  };

  if (loading) return <div className="loading">Loading item</div>;
  if (error) return <div className="card"><p style={{ color: "var(--red)" }}>{error}</p></div>;
  if (!item) return <div className="card"><p>Item not found</p></div>;

  const choices = item.choices ?? {};
  const choiceKeys = Object.keys(choices).sort();

  return (
    <>
      <div style={{ marginBottom: "1rem" }}>
        <Link to="/items" style={{ fontSize: "0.85rem" }}>← Back to items</Link>
      </div>

      <div className="card">
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap", marginBottom: "0.75rem" }}>
          <h2 style={{ margin: 0 }}>{item.id}</h2>
          <span className="badge badge-accent">{item.corpus}</span>
          <span className="badge badge-cyan">{item.responseType}</span>
          {item.grade && <span className="badge badge-muted">Grade {item.grade}</span>}
          {item.year && <span className="badge badge-muted">{item.year}</span>}
        </div>

        <div style={{ marginBottom: "0.75rem" }}>
          <strong>Claim:</strong>{" "}
          <span style={{ color: "var(--text-muted)" }}>{item.authority} / {item.claim}</span>
        </div>

        <div style={{ marginBottom: "0.75rem" }}>
          <strong>Stem:</strong>
          <div className="trace-block" style={{ marginTop: "0.25rem", whiteSpace: "pre-wrap" }}>
            {item.stem}
          </div>
        </div>

        {choiceKeys.length > 0 && (
          <div style={{ marginBottom: "0.75rem" }}>
            <strong>Choices:</strong>
            <div className="choice-grid" style={{ marginTop: "0.25rem" }}>
              {choiceKeys.map((k) => (
                <div key={k} style={{ display: "contents" }}>
                  <span className={`choice-key ${k === item.key ? "choice-correct" : "choice-wrong"}`}>
                    {k}{k === item.key ? " ✓" : ""}
                  </span>
                  <span className={k === item.key ? "choice-correct" : ""}>{choices[k]}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div>
          <strong>Published Key:</strong>{" "}
          <code style={{ color: "var(--green)" }}>{item.key}</code>
          {item.percentCorrect != null && (
            <span style={{ marginLeft: "1rem", color: "var(--text-muted)" }}>
              ({item.percentCorrect}% correct)
            </span>
          )}
        </div>
      </div>

      {/* Witnesses */}
      {item.witnesses.length > 0 && (
        <div className="card witness-card">
          <h3>Witnesses ({item.witnesses.length})</h3>
          {item.witnesses.map((w, i) => (
            <div key={i} style={{ padding: "0.5rem 0", borderBottom: i < item.witnesses.length - 1 ? "1px solid var(--border)" : "none" }}>
              <div className="witness-header">
                <span className="badge badge-green">{w.programId}</span>
                <span className="badge badge-yellow">{w.channel}</span>
                <span className="badge badge-red">lacks: {w.operation}</span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  answer: <code>{w.answer}</code> → {w.answer === w.key ? "✓" : "✗"}
                </span>
              </div>
              <div className="trace-block">{w.trace.join("\n")}</div>
            </div>
          ))}
        </div>
      )}

      {/* Interactive runner */}
      <div className="card">
        <h3>Run A Priori Rules</h3>
        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "0.75rem" }}>
          Execute all 15 a priori programs against this item in real time.
          Each program operates on a restricted view (no access to the key).
        </p>
        <button onClick={handleRunRules} disabled={running}>
          {running ? "Running…" : "Run All Rules"}
        </button>

        {ruleResults && (
          <div className="runner-result" style={{ marginTop: "1rem" }}>
            <div style={{ marginBottom: "0.5rem", fontSize: "0.8rem", color: "var(--text-muted)" }}>
              Correct key: <code style={{ color: "var(--green)" }}>{ruleResults.key}</code>
            </div>
            {ruleResults.results.map((r) => (
              <div key={r.ruleId} style={{ padding: "0.5rem 0", borderBottom: "1px solid var(--border)" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
                  <code style={{ fontSize: "0.78rem", fontWeight: 600 }}>{r.ruleId}</code>
                  <span className="badge badge-muted">{r.channel}</span>
                  {r.skipped ? (
                    <span className="badge badge-muted">skipped</span>
                  ) : r.correct ? (
                    <span className="badge badge-green">✓ {r.answer}</span>
                  ) : (
                    <span className="badge badge-red">✗ {r.answer ?? "null"}</span>
                  )}
                  {r.skipReason && (
                    <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>{r.skipReason}</span>
                  )}
                </div>
                {r.trace.length > 0 && !r.skipped && (
                  <div className="trace-block" style={{ marginTop: "0.25rem" }}>
                    {r.trace.join("\n")}
                  </div>
                )}
              </div>
            ))}
            <div style={{ marginTop: "0.75rem", fontSize: "0.85rem" }}>
              <strong>Summary:</strong>{" "}
              {ruleResults.results.filter((r) => r.correct).length} correct,{" "}
              {ruleResults.results.filter((r) => !r.skipped && !r.correct).length} wrong,{" "}
              {ruleResults.results.filter((r) => r.skipped).length} skipped
            </div>
          </div>
        )}
      </div>
    </>
  );
}
