import { useState } from "react";
import { getConfig, getStats } from "../api";
import { AdminShell } from "../components/AdminShell";
import { Pill, Stat, fmtBytes } from "../components/bits";
import { downloadJson } from "../components/download";
import { useAsync } from "../components/useAsync";

/** Files the upload script sends; anything else in the bucket is listed after them. */
const EXPECTED = ["data/items.jsonl", "data/apriori.json", "data/witnesses.json", "data/rule-chance.json", "data/apriori-cell-table.json"];
const OPTIONAL = [
  { key: "exports/matrix.json", note: "33 MiB · recreated by the census run" },
  { key: "exports/trials.jsonl", note: "126 MiB · optional log" },
];

interface Settings {
  population: string;
  alpha: string;
  minCell: number;
  chance: string;
  withholdKey: boolean;
  oneSided: boolean;
  fitted: boolean;
}
const DEFAULTS: Settings = { population: "print-faithful only", alpha: "0.05", minCell: 10, chance: "per-item 1 / options", withholdKey: true, oneSided: true, fitted: false };

function Sub({ children }: { children: React.ReactNode }) {
  return <div className="muted" style={{ fontSize: 12, fontFamily: "var(--font-mono)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{children}</div>;
}

/** Data & deploy: what the bucket holds, the routes, and runner settings kept in this browser. */
export function AdminData() {
  const config = useAsync(getConfig, []);
  const stats = useAsync(getStats, []);
  const [settings, setSettings] = useState<Settings>(() => {
    try { return { ...DEFAULTS, ...JSON.parse(localStorage.getItem("ccf.settings") ?? "{}") }; } catch { return DEFAULTS; }
  });
  const [saved, setSaved] = useState(false);
  const set = (p: Partial<Settings>) => { setSettings((s) => ({ ...s, ...p })); setSaved(false); };
  const save = () => {
    try { localStorage.setItem("ccf.settings", JSON.stringify(settings)); } catch { /* private window */ }
    setSaved(true);
  };

  const cfg = config.data;
  const files = cfg?.dataFiles ?? [];
  const byKey = new Map(files.map((f) => [f.key, f]));
  const extra = files.filter((f) => !EXPECTED.includes(f.key));
  const claimsFiles = extra.filter((f) => f.key.startsWith("data/claims/"));
  const others = extra.filter((f) => !f.key.startsWith("data/claims/"));
  const local = Boolean(cfg?.localDataRoot);
  const items = byKey.get("data/items.jsonl");

  return (
    <AdminShell>
      <div className="page-head">
        <div>
          <h1>Data &amp; deploy</h1>
          <p className="lede">Frozen item set, exported artifacts served from the data bucket, and the runner endpoint behind CloudFront.</p>
        </div>
        <button className="btn ghost push" onClick={() => cfg && downloadJson("ccf-config.json", cfg)} disabled={!cfg}>Export config</button>
      </div>
      {config.error && <div className="error">Could not load config: {config.error}</div>}

      <div className="three-col">
        <Stat label="Item set" value={<>{stats.data ? `${stats.data.totalItems.toLocaleString()} frozen` : "…"}<Sub>data/items.jsonl · {items ? fmtBytes(items.size) : "—"}</Sub></>} />
        <Stat label="Runner" value={<>{local ? "Local · " : "Lambda · "}Node {cfg?.nodeVersion.replace(/^v/, "").split(".")[0] ?? "…"}<Sub>{cfg?.memoryMb ? `${cfg.memoryMb} MB` : local ? "dev-server.mjs" : "—"}{cfg?.functionName ? ` · ${cfg.functionName}` : ""}</Sub></>} />
        <Stat label="Data source" value={<>{local ? "Repo checkout" : cfg?.dataBucket ? "S3 bucket" : "…"}<Sub>{cfg?.localDataRoot ?? cfg?.dataBucket ?? "—"}{cfg?.region ? ` · ${cfg.region}` : ""}</Sub></>} />
      </div>

      <div className="two-col">
        <div className="stack">
          <div className="card">
            <div className="card-head">Exports in data bucket <span className="mono muted" style={{ fontSize: 12 }}>/data/*</span></div>
            <table>
              <thead><tr><th>File</th><th>Size</th><th>Status</th></tr></thead>
              <tbody>
                {EXPECTED.map((k) => {
                  const f = byKey.get(k);
                  return (
                    <tr key={k}>
                      <td className="mono">{k.replace(/^data\//, "")}</td>
                      <td>{f ? fmtBytes(f.size) : "—"}</td>
                      <td>{f ? <Pill kind="op">synced</Pill> : <Pill kind="none">{config.loading ? "…" : "missing"}</Pill>}</td>
                    </tr>
                  );
                })}
                {claimsFiles.length > 0 && (
                  <tr>
                    <td className="mono">claims/ <span className="muted">({claimsFiles.length} files)</span></td>
                    <td>{fmtBytes(claimsFiles.reduce((n, f) => n + f.size, 0))}</td>
                    <td><Pill kind="op">synced</Pill></td>
                  </tr>
                )}
                {others.map((f) => (
                  <tr key={f.key}><td className="mono">{f.key.replace(/^data\//, "")}</td><td>{fmtBytes(f.size)}</td><td><Pill kind="op">synced</Pill></td></tr>
                ))}
                {OPTIONAL.map((o) => (
                  <tr key={o.key}><td className="mono">{o.key.replace(/^exports\//, "")}<div className="trace">{o.note}</div></td><td>—</td><td><Pill kind="none">not uploaded</Pill></td></tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="card">
            <div className="card-head">API routes</div>
            <table>
              <tbody>
                {(cfg?.routes ?? []).map((r) => (
                  <tr key={r.method + r.path}><td className="mono" style={{ width: 70 }}>{r.method}</td><td className="mono">{r.path}</td><td className="muted">{r.note}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <form className="card edit" onSubmit={(e) => { e.preventDefault(); save(); }}>
          <h2>Runtime settings</h2>
          <p className="small muted">Held in this browser only. The deployed runner reads its bucket and region from the stack; the claim population and thresholds below describe the paper's analysis and are not yet wired into <span className="mono">/api/run-rules</span>.</p>
          <div className="two-col" style={{ gap: 16 }}>
            <div className="field"><label htmlFor="bkt">Data bucket</label><input id="bkt" readOnly value={cfg?.dataBucket ?? (local ? "(local checkout)" : "")} /></div>
            <div className="field"><label htmlFor="reg">Region</label><input id="reg" readOnly value={cfg?.region ?? (local ? "(local)" : "")} /></div>
          </div>
          <div className="field"><label htmlFor="dist">Served from</label><input id="dist" readOnly value={window.location.origin} /></div>
          <div className="two-col" style={{ gap: 16 }}>
            <div className="field"><label htmlFor="pop">Claim population</label>
              <select id="pop" value={settings.population} onChange={(e) => set({ population: e.target.value })}>
                <option>print-faithful only</option><option>text layer (reference)</option><option>all keyed items</option>
              </select>
            </div>
            <div className="field"><label htmlFor="alpha">Holm family alpha</label><input id="alpha" value={settings.alpha} onChange={(e) => set({ alpha: e.target.value })} /></div>
          </div>
          <div className="two-col" style={{ gap: 16 }}>
            <div className="field"><label htmlFor="mincell">Min cell n</label><input id="mincell" type="number" value={settings.minCell} onChange={(e) => set({ minCell: Number(e.target.value) })} /></div>
            <div className="field"><label htmlFor="chance">Chance rule</label>
              <select id="chance" value={settings.chance} onChange={(e) => set({ chance: e.target.value })}>
                <option>per-item 1 / options</option><option>modal key rate</option>
              </select>
            </div>
          </div>
          <div className="field">
            <span className="label">Interactive runner</span>
            <label className="check"><input type="checkbox" checked={settings.withholdKey} onChange={(e) => set({ withholdKey: e.target.checked })} /> Withhold the key from every program</label>
            <label className="check"><input type="checkbox" checked={settings.oneSided} onChange={(e) => set({ oneSided: e.target.checked })} /> Show one-sided wording on every result</label>
            <label className="check"><input type="checkbox" checked={settings.fitted} onChange={(e) => set({ fitted: e.target.checked })} /> Allow fitted held-out programs in the demo</label>
          </div>
          <div className="actions">
            <button className="btn" type="submit">Save settings</button>
            <button className="btn ghost" type="button" onClick={() => downloadJson("ccf-settings.json", settings)}>Export</button>
            {saved && <span className="small muted" style={{ alignSelf: "center" }}>Saved in this browser</span>}
          </div>
        </form>
      </div>
    </AdminShell>
  );
}
