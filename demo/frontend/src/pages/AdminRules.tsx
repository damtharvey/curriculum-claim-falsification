import { useEffect, useMemo, useState } from "react";
import { getRules, OPERATIONS, runRules, type RuleDefinition } from "../api";
import { AdminShell } from "../components/AdminShell";
import { Pill } from "../components/bits";
import { downloadJson } from "../components/download";
import { useAsync } from "../components/useAsync";

type Rule = RuleDefinition & { enabled: boolean };

const CHANNELS = ["item-cues", "partial-input", "unbound-exec", "instruction-only"];
const RESPONSE_SETS: Record<string, string[]> = {
  "selected only": ["selected"],
  "numeric only": ["numeric"],
  "selected and numeric": ["selected", "numeric"],
};
const responseLabel = (r: string[]) =>
  Object.entries(RESPONSE_SETS).find(([, v]) => v.length === r.length && v.every((x) => r.includes(x)))?.[0] ?? "selected and numeric";

/** Rules configuration: the list from /api/rules, edited locally and exported as rules/apriori.json. */
export function AdminRules() {
  const loaded = useAsync(getRules, []);
  const [rules, setRules] = useState<Rule[]>([]);
  const [filter, setFilter] = useState("");
  const [channel, setChannel] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [draft, setDraft] = useState<Rule | null>(null);
  const [dirty, setDirty] = useState(false);
  const [dryRun, setDryRun] = useState<string | null>(null);

  useEffect(() => {
    if (loaded.data) {
      const rs = loaded.data.map((r) => ({ ...r, enabled: true }));
      setRules(rs);
      setSelectedId((id) => id ?? rs[0]?.id ?? null);
    }
  }, [loaded.data]);
  useEffect(() => {
    setDraft(rules.find((r) => r.id === selectedId) ?? null);
  }, [selectedId, rules]);

  const visible = useMemo(
    () => rules.filter((r) => (!channel || r.channel === channel) && (!filter || r.id.includes(filter) || r.description.toLowerCase().includes(filter.toLowerCase()))),
    [rules, filter, channel],
  );

  const patch = (p: Partial<Rule>) => draft && setDraft({ ...draft, ...p });
  const toggleLack = (op: string) =>
    draft && patch({ lacks: draft.lacks.includes(op) ? draft.lacks.filter((l) => l !== op) : [...draft.lacks, op] });

  const save = () => {
    if (!draft) return;
    setRules((rs) => rs.map((r) => (r.id === selectedId ? draft : r)));
    setSelectedId(draft.id);
    setDirty(true);
  };
  const exportFile = () =>
    downloadJson("apriori.json", {
      rules: rules.filter((r) => r.enabled).map(({ enabled: _e, ...r }) => r),
    });

  // Dry run: score the rule on the first witnessed items the list gives us.
  const doDryRun = async () => {
    if (!draft) return;
    setDryRun("Running…");
    const sample = ["staar-2019-5-q7", "nyregents-geometry-2025-jan-q6", "staar-2019-6-q8", "timss2011-8-M032064"];
    const rows = await Promise.all(sample.map((id) => runRules(id).catch(() => null)));
    const lines = rows.map((r, i) => {
      const hit = r?.results.find((x) => x.ruleId === draft.id);
      return `${sample[i]}: ${hit ? (hit.skipped ? "abstain" : `${hit.answer} ${hit.correct ? "✓" : "✗"}`) : "n/a"}`;
    });
    setDryRun(lines.join("\n"));
  };

  return (
    <AdminShell>
      <div className="page-head">
        <div>
          <h1>Rules</h1>
          <p className="lede">A priori programs. No fitted parameters; scored on every applicable item. Each declares the operations it lacks.</p>
        </div>
        <div className="row push">
          {dirty && <span className="small muted">Edited locally · export to apply</span>}
          <button className="btn ghost" onClick={exportFile} disabled={!rules.length}>Export apriori.json</button>
        </div>
      </div>
      {loaded.error && <div className="error">Could not load rules: {loaded.error}</div>}

      <div className="two-col">
        <div className="card" style={{ display: "flex", flexDirection: "column" }}>
          <div className="row" style={{ padding: 12, borderBottom: "1px solid var(--line-soft)", gap: 8 }}>
            <div className="field compact" style={{ flexGrow: 1 }}>
              <input type="search" placeholder="Filter rules" aria-label="Filter rules" value={filter} onChange={(e) => setFilter(e.target.value)} />
            </div>
            <div className="field compact" style={{ width: 160 }}>
              <select aria-label="Channel" value={channel} onChange={(e) => setChannel(e.target.value)}>
                <option value="">All channels</option>
                {CHANNELS.map((c) => <option key={c}>{c}</option>)}
              </select>
            </div>
          </div>
          <table>
            <thead><tr><th>Rule</th><th>Channel</th><th>Lacks</th><th>On</th></tr></thead>
            <tbody>
              {visible.map((r) => (
                <tr key={r.id} className={`click${r.id === selectedId ? " sel" : ""}`} onClick={() => setSelectedId(r.id)}>
                  <td className="mono">{r.id}</td>
                  <td>{r.channel}</td>
                  <td>{r.lacks.length}</td>
                  <td>{r.enabled ? <Pill kind="op">on</Pill> : <Pill kind="none">off</Pill>}</td>
                </tr>
              ))}
              {!visible.length && <tr><td colSpan={4} className="muted">{loaded.loading ? "Loading rules…" : "No rules match."}</td></tr>}
            </tbody>
          </table>
        </div>

        {draft && (
          <form className="card edit" onSubmit={(e) => { e.preventDefault(); save(); }}>
            <div className="row">
              <h2>Edit rule</h2>
              <span className="mono muted" style={{ fontSize: 12 }}>rules/apriori.json</span>
              <Pill kind="tag">applies to {draft.appliesTo.join(" + ")}</Pill>
            </div>
            <div className="two-col" style={{ gap: 16 }}>
              <div className="field"><label htmlFor="rid">Id</label><input id="rid" value={draft.id} onChange={(e) => patch({ id: e.target.value })} /></div>
              <div className="field"><label htmlFor="rch">Channel</label>
                <select id="rch" value={draft.channel} onChange={(e) => patch({ channel: e.target.value })}>{CHANNELS.map((c) => <option key={c}>{c}</option>)}</select>
              </div>
            </div>
            <div className="field"><label htmlFor="rdesc">Description</label><textarea id="rdesc" value={draft.description} onChange={(e) => patch({ description: e.target.value })} /></div>
            <div className="field">
              <span className="label">Lacks (operations the program never performs)</span>
              <div className="check-grid">
                {OPERATIONS.map((op) => (
                  <label key={op} className="check"><input type="checkbox" checked={draft.lacks.includes(op)} onChange={() => toggleLack(op)} /> {op}</label>
                ))}
              </div>
            </div>
            <div className="field"><label htmlFor="rcite">Citation</label><input id="rcite" value={draft.citation} onChange={(e) => patch({ citation: e.target.value })} /></div>
            <div className="two-col" style={{ gap: 16 }}>
              <div className="field"><label htmlFor="rresp">Response types</label>
                <select id="rresp" value={responseLabel(draft.appliesTo)} onChange={(e) => patch({ appliesTo: RESPONSE_SETS[e.target.value] })}>
                  {Object.keys(RESPONSE_SETS).map((k) => <option key={k}>{k}</option>)}
                </select>
              </div>
              <div className="field"><label htmlFor="ron">Status</label>
                <select id="ron" value={draft.enabled ? "on" : "off"} onChange={(e) => patch({ enabled: e.target.value === "on" })}>
                  <option value="on">Enabled</option><option value="off">Disabled (left out of export)</option>
                </select>
              </div>
            </div>
            {dryRun && <pre className="trace" style={{ margin: 0, fontSize: 12 }}>{dryRun}</pre>}
            <div className="actions">
              <button className="btn" type="submit">Save rule</button>
              <button className="btn ghost" type="button" onClick={doDryRun}>Dry-run on 4 items</button>
              <button className="btn danger push" type="button" onClick={() => { patch({ enabled: !draft.enabled }); }}>{draft.enabled ? "Disable" : "Enable"}</button>
            </div>
          </form>
        )}
      </div>
    </AdminShell>
  );
}
