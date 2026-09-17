import { useEffect, useState } from "react";
import { getClaims, OPERATIONS, type Claim, type ClaimFile } from "../api";
import { AdminShell } from "../components/AdminShell";
import { Pill } from "../components/bits";
import { downloadJson } from "../components/download";
import { useAsync } from "../components/useAsync";

/** Claims configuration: one file per authority from /api/claims, edited locally and exported. */
export function AdminClaims() {
  const loaded = useAsync(getClaims, []);
  const [files, setFiles] = useState<ClaimFile[]>([]);
  const [selectedFile, setSelectedFile] = useState("");
  const [code, setCode] = useState<string | null>(null);
  const [draft, setDraft] = useState<Claim | null>(null);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    const data = loaded.data;
    if (data) {
      setFiles(data);
      setSelectedFile((cur) => cur || data.find((f) => f.file === "claims/nyregents.json")?.file || data[0]?.file || "");
    }
  }, [loaded.data]);
  const file = files.find((f) => f.file === selectedFile);
  const authority = file?.authority ?? "";
  useEffect(() => { setCode(file?.claims[0]?.code ?? null); }, [selectedFile, file?.claims.length]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { setDraft(file?.claims.find((c) => c.code === code) ?? null); }, [file, code]);

  const patch = (p: Partial<Claim>) => draft && setDraft({ ...draft, ...p });
  const toggleOp = (op: string) =>
    draft && patch({ operations: draft.operations.includes(op) ? draft.operations.filter((o) => o !== op) : [...draft.operations, op] });

  const save = () => {
    if (!draft || !file) return;
    setFiles((fs) => fs.map((f) => (f !== file ? f : { ...f, claims: f.claims.map((c) => (c.code === code ? draft : c)) })));
    setCode(draft.code);
    setDirty(true);
  };
  const addClaim = () => {
    if (!file) return;
    const c: Claim = { authority, code: "new-claim", text: "", operationalization: "", operations: ["bind", "execute"], items: 0 };
    setFiles((fs) => fs.map((f) => (f !== file ? f : { ...f, claims: [...f.claims, c] })));
    setCode(c.code);
    setDirty(true);
  };
  const remove = () => {
    if (!file || !code) return;
    setFiles((fs) => fs.map((f) => (f !== file ? f : { ...f, claims: f.claims.filter((c) => c.code !== code) })));
    setDirty(true);
  };
  const exportFile = () => file && downloadJson(file.file.replace(/^claims\//, ""), {
    authority: file.authority,
    ...(file.note && { note: file.note }),
    claims: file.claims.map(({ items: _n, ...c }) => c),
  });

  return (
    <AdminShell>
      <div className="page-head">
        <div>
          <h1>Claims</h1>
          <p className="lede">One file per authority. Each claim names the tag as published and the operations it asserts a pass requires.</p>
        </div>
        <div className="field push" style={{ width: 220 }}>
          <label htmlFor="cauth">Authority</label>
          <select id="cauth" value={selectedFile} onChange={(e) => setSelectedFile(e.target.value)}>
            {files.map((f) => <option key={f.file} value={f.file}>{f.file.replace(/^claims\/|\.json$/g, "")}</option>)}
          </select>
        </div>
        <button className="btn ghost" onClick={exportFile} disabled={!file}>Export {file ? file.file.replace(/^claims\//, "") : "JSON"}</button>
        <button className="btn" onClick={addClaim} disabled={!file}>New claim</button>
      </div>
      {loaded.error && <div className="error">Could not load claims: {loaded.error}</div>}

      {file && (
        <div className="note-box">
          <div style={{ flexGrow: 1 }}>
            <div className="stat-label tiny muted" style={{ letterSpacing: "0.05em", textTransform: "uppercase", fontSize: 11 }}>Authority note</div>
            <div className="field" style={{ marginTop: 4 }}>
              <textarea aria-label="Authority note" style={{ minHeight: 44 }} value={file.note ?? ""} onChange={(e) => { setFiles((fs) => fs.map((f) => (f !== file ? f : { ...f, note: e.target.value }))); setDirty(true); }} />
            </div>
          </div>
          <span className="mono muted" style={{ fontSize: 12 }}>{file.file}{dirty ? " · edited locally" : ""}</span>
        </div>
      )}

      <div className="two-col">
        <div className="card">
          <table>
            <thead><tr><th>Code</th><th>Claim text</th><th>Operations</th><th>Items</th></tr></thead>
            <tbody>
              {file?.claims.map((c) => (
                <tr key={c.code} className={`click${c.code === code ? " sel" : ""}`} onClick={() => setCode(c.code)}>
                  <td className="mono">{c.code}</td>
                  <td>{c.text || <span className="muted">—</span>}</td>
                  <td className="row" style={{ gap: 4, display: "flex", flexWrap: "wrap" }}>{c.operations.map((o) => <Pill key={o} kind="op">{o}</Pill>)}</td>
                  <td>{c.items}</td>
                </tr>
              ))}
              {!file && <tr><td colSpan={4} className="muted">{loaded.loading ? "Loading claims…" : "No claims files."}</td></tr>}
            </tbody>
          </table>
          <div className="table-foot" style={{ lineHeight: 1.5 }}>
            Operations vocabulary: <span className="mono">{OPERATIONS.join(" · ")}</span>. A rule that lacks any operation a claim requires is witness-eligible on that claim.
          </div>
        </div>

        {draft && (
          <form className="card edit" onSubmit={(e) => { e.preventDefault(); save(); }}>
            <div className="row">
              <h2>Edit claim</h2>
              <Pill kind="tag">{authority} · {draft.code}</Pill>
            </div>
            <div className="two-col" style={{ gap: 16 }}>
              <div className="field"><label htmlFor="ccode">Code</label><input id="ccode" value={draft.code} onChange={(e) => patch({ code: e.target.value })} /></div>
              <div className="field"><label htmlFor="citems">Items tagged</label><input id="citems" readOnly value={draft.items} /></div>
            </div>
            <div className="field"><label htmlFor="ctext">Claim text (as published)</label><input id="ctext" value={draft.text} onChange={(e) => patch({ text: e.target.value })} /></div>
            <div className="field"><label htmlFor="coper">Operationalization</label><textarea id="coper" value={draft.operationalization} onChange={(e) => patch({ operationalization: e.target.value })} /></div>
            <div className="field">
              <span className="label">Operations a pass is claimed to require</span>
              <div className="check-grid">
                {OPERATIONS.map((op) => (
                  <label key={op} className="check"><input type="checkbox" checked={draft.operations.includes(op)} onChange={() => toggleOp(op)} /> {op}</label>
                ))}
              </div>
            </div>
            <div className="field"><label htmlFor="csrc">Source URL</label><input id="csrc" type="url" value={draft.sourceUrl ?? ""} onChange={(e) => patch({ sourceUrl: e.target.value })} /></div>
            <div className="actions">
              <button className="btn" type="submit">Save claim</button>
              <button className="btn danger push" type="button" onClick={remove}>Remove</button>
            </div>
          </form>
        )}
      </div>
    </AdminShell>
  );
}
