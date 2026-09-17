import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getItem, runRules, type RuleResult, type RunRulesResponse } from "../api";
import { LacksPills, Pill } from "../components/bits";
import { useAsync } from "../components/useAsync";

function host(url?: string): string {
  if (!url) return "";
  try { return new URL(url).host; } catch { return url; }
}

function resultPill(r: RuleResult) {
  if (r.skipped && r.skipReason?.startsWith("responseType")) return <Pill kind="none">N/A</Pill>;
  if (r.skipped) return <Pill kind="none">Abstain</Pill>;
  if (r.correct) return <Pill kind="wit">Witness</Pill>;
  return <Pill kind="none">Miss</Pill>;
}

/** Item detail: the item on the left, a live a priori run on the right. */
export function ItemPage() {
  const { itemId = "" } = useParams();
  const item = useAsync(() => getItem(itemId), [itemId]);
  const [run, setRun] = useState<RunRulesResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);

  const doRun = async () => {
    setRunning(true);
    setRunError(null);
    try {
      setRun(await runRules(itemId));
    } catch (e) {
      setRunError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  };
  useEffect(() => { setRun(null); void doRun(); /* eslint-disable-line react-hooks/exhaustive-deps */ }, [itemId]);

  if (item.error) return <div className="error">Could not load {itemId}: {item.error}</div>;
  const it = item.data;

  const results = run?.results ?? [];
  const hits = results.filter((r) => r.correct);
  const lacked = [...new Set(hits.flatMap((r) => r.lacks))];
  const shown = results.filter((r) => !(r.skipped && r.skipReason?.startsWith("responseType")));
  const notApplicable = results.length - shown.length;
  const stemChoices = it?.choices ? Object.entries(it.choices) : [];

  return (
    <div className="page">
      <div className="crumbs">
        <Link to="/items">Items</Link><span>/</span><span className="mono" style={{ color: "var(--ink)" }}>{itemId}</span>
      </div>

      <div className="two-col">
        <div className="card pad stack" style={{ padding: 28 }}>
          {!it ? <p className="muted">Loading item…</p> : (
            <>
              <div className="row wrap" style={{ gap: 8 }}>
                <Pill kind="tag">{it.authority} · {it.claim}</Pill>
                <Pill kind="tag">{it.corpus}{it.year ? ` ${it.year}` : ""}{it.grade ? ` · grade ${it.grade}` : ""}{it.contentDomain ? ` · ${it.contentDomain}` : ""}</Pill>
                <Pill kind="tag">{it.responseType}{it.figureDependent ? " · figure" : ""}</Pill>
              </div>
              <p className="stem">{it.stem}</p>
              <div className="stack" style={{ gap: 8, marginTop: 8 }}>
                {stemChoices.length > 0 ? stemChoices.map(([k, text]) => (
                  <div key={k} className={`choice${k === it.key ? " key" : ""}`}>
                    <span className="letter">{k}</span>
                    <span style={{ flexGrow: 1 }}>{text}</span>
                    {k === it.key && <Pill kind="tag strong">Key</Pill>}
                  </div>
                )) : (
                  <div className="choice key">
                    <span className="letter" style={{ width: "auto" }}>Key</span>
                    <span className="mono" style={{ flexGrow: 1, fontSize: 16 }}>{it.key}</span>
                    <span className="tiny muted">{it.responseType} · exact match</span>
                  </div>
                )}
              </div>
              {it.witnesses.length > 0 && (
                <p className="small muted">
                  Catalog: {it.witnesses.length} witness row{it.witnesses.length === 1 ? "" : "s"} on this item from{" "}
                  {[...new Set(it.witnesses.map((w) => w.programId))].join(", ")}.
                </p>
              )}
              <div className="row tiny muted" style={{ marginTop: "auto", borderTop: "1px solid var(--line-soft)", paddingTop: 12 }}>
                <span>Source: {host(it.sourceUrl)}{it.percentCorrect != null ? ` · percent correct ${it.percentCorrect}` : ""}</span>
                {it.sourceUrl && <a className="push" href={it.sourceUrl} target="_blank" rel="noreferrer" style={{ textDecoration: "underline" }}>Released form</a>}
              </div>
            </>
          )}
        </div>

        <div className="stack">
          <div className="row">
            <h2 style={{ fontSize: 24 }}>A priori rules</h2>
            <span className="small muted">{results.length || 15} programs · no fitted parameters · key withheld</span>
            <button className="btn push" onClick={doRun} disabled={running}>{running ? "Running…" : "Run again"}</button>
          </div>

          {runError && <div className="error">Run failed: {runError}</div>}

          {!run ? (
            <div className="verdict pending">
              <div className="eyebrow">Running</div>
              <div className="headline">Scoring every applicable program against the item…</div>
            </div>
          ) : hits.length > 0 ? (
            <div className="verdict found">
              <div className="eyebrow">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5" /></svg>
                Witness found
              </div>
              <div className="headline">
                A pass on this item does not require {lacked.length > 0 ? lacked.map((l, i) => <span key={l}>{i > 0 ? ", " : ""}<em>{l}</em></span>) : "the tagged operation"}. {hits.length === 1 ? "One program" : `${hits.length} programs`} without {lacked.length === 1 ? "it" : "them"} returned the key.
              </div>
              <div className="note">Refutes the tag for this item only. It says nothing about what students did.</div>
            </div>
          ) : (
            <div className="verdict none">
              <div className="eyebrow">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M8 12h8" /></svg>
                No witness
              </div>
              <div className="headline">None of the searched programs returned the key.</div>
              <div className="note">This proves nothing beyond the programs we tried. The tag is not certified, and it is not refuted.</div>
            </div>
          )}

          <div className="card">
            <table>
              <thead>
                <tr><th>Program</th><th>Channel</th><th>Lacks</th><th>Answer</th><th>Result</th></tr>
              </thead>
              <tbody>
                {shown.map((r) => (
                  <tr key={r.ruleId} className={r.correct ? "sel" : ""}>
                    <td>
                      <span className="mono">{r.ruleId}</span>
                      {r.trace.length > 0 && <div className="trace">{r.trace.join(" · ")}</div>}
                      {r.skipped && r.skipReason && <div className="trace">{r.skipReason}</div>}
                    </td>
                    <td>{r.channel}</td>
                    <td><LacksPills lacks={r.lacks} /></td>
                    <td className="mono">{r.answer ?? "—"}</td>
                    <td>{resultPill(r)}</td>
                  </tr>
                ))}
                {notApplicable > 0 && (
                  <tr>
                    <td className="mono muted">{notApplicable} not applicable to {it?.responseType ?? "this"} response</td>
                    <td className="muted">—</td><td></td><td className="mono muted">—</td><td><Pill kind="none">Skip</Pill></td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
