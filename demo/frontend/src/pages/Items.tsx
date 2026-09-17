import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { getItems, getStats } from "../api";
import { Pill, Stat, ONE_SIDED } from "../components/bits";
import { useAsync } from "../components/useAsync";

const PAGE_SIZE = 25;

export function Items() {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const stats = useAsync(getStats, []);

  const page = Number(params.get("page")) || 1;
  const authority = params.get("authority") ?? "";
  const claim = params.get("claim") ?? "";
  const channel = params.get("channel") ?? "";
  const search = params.get("search") ?? "";
  // Default on: the explorer opens on the witnessed rows, as in the design.
  const witnessed = params.get("witnessed") !== "0";
  const [draft, setDraft] = useState(search);
  useEffect(() => setDraft(search), [search]);

  const list = useAsync(
    () =>
      getItems({
        page: String(page),
        pageSize: String(PAGE_SIZE),
        ...(authority && { authority }),
        ...(claim && { claim }),
        ...(channel && { channel }),
        ...(search && { search }),
        ...(witnessed && { witnessed: "1" }),
      }),
    [page, authority, claim, channel, search, witnessed],
  );

  const set = (patch: Record<string, string>) => {
    const next = new URLSearchParams(params);
    for (const [k, v] of Object.entries(patch)) {
      if (v) next.set(k, v);
      else next.delete(k);
    }
    if (!("page" in patch)) next.delete("page");
    setParams(next);
  };

  const claimOptions = useMemo(() => {
    const all = stats.data?.claims ?? [];
    const rows = authority ? all.filter((c) => c.authority === authority) : all;
    return [...new Set(rows.map((c) => c.claim))];
  }, [stats.data, authority]);

  const total = list.data?.total ?? 0;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1 style={{ fontSize: 36 }}>Items</h1>
          <p className="lede">
            A witness is a program that lacks the tagged operation and still passes under the published key. {ONE_SIDED}
          </p>
        </div>
        <div className="row push">
          <Stat label="Items" value={stats.data?.totalItems.toLocaleString() ?? "…"} />
          <Stat label="Selected" value={stats.data?.responseTypes.selected?.toLocaleString() ?? "…"} />
          <Stat label="Numeric" value={stats.data?.responseTypes.numeric?.toLocaleString() ?? "…"} />
          <Stat label="A priori rules" value={stats.data?.ruleCount ?? "…"} />
          <Stat label="Witness rows" value={stats.data?.totalWitnesses.toLocaleString() ?? "…"} dark />
        </div>
      </div>

      <form
        className="row end wrap"
        onSubmit={(e) => {
          e.preventDefault();
          set({ search: draft });
        }}
      >
        <div className="field" style={{ width: 300 }}>
          <label htmlFor="q">Search</label>
          <input id="q" type="search" placeholder="Item id or stem text" value={draft} onChange={(e) => setDraft(e.target.value)} />
        </div>
        <div className="field" style={{ width: 160 }}>
          <label htmlFor="auth">Authority</label>
          <select id="auth" value={authority} onChange={(e) => set({ authority: e.target.value, claim: "" })}>
            <option value="">All</option>
            {stats.data?.authorities.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
        </div>
        <div className="field" style={{ width: 180 }}>
          <label htmlFor="claim">Claim</label>
          <select id="claim" value={claim} onChange={(e) => set({ claim: e.target.value })}>
            <option value="">All</option>
            {claimOptions.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        <div className="field" style={{ width: 160 }}>
          <label htmlFor="chan">Channel</label>
          <select id="chan" value={channel} onChange={(e) => set({ channel: e.target.value })}>
            <option value="">All</option>
            {stats.data?.channels.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        <label className="check" style={{ padding: "0 4px" }}>
          <input type="checkbox" checked={witnessed} onChange={(e) => set({ witnessed: e.target.checked ? "" : "0" })} /> Witnessed only
        </label>
        <button type="submit" className="btn ghost push">Search</button>
      </form>

      {list.error && <div className="error">Could not load items: {list.error}</div>}

      <div className="card">
        <table>
          <thead>
            <tr>
              <th style={{ width: 300 }}>Item</th>
              <th>Stem</th>
              <th>Authority</th>
              <th>Claim</th>
              <th>Type</th>
              <th>Channel</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {list.loading && !list.data && (
              <tr><td colSpan={7} className="muted">Loading items…</td></tr>
            )}
            {list.data?.items.length === 0 && (
              <tr><td colSpan={7} className="muted">No items match these filters.</td></tr>
            )}
            {list.data?.items.map((it) => (
              <tr key={it.id} className="click" onClick={() => navigate(`/items/${encodeURIComponent(it.id)}`)}>
                <td style={{ whiteSpace: "nowrap" }}><Link className="mono" to={`/items/${encodeURIComponent(it.id)}`}>{it.id}</Link></td>
                <td className="preview">{it.stem}</td>
                <td>{it.authority}</td>
                <td>{it.claim}</td>
                <td>{it.responseType}</td>
                <td>{it.channels.length ? it.channels.join(", ") : "—"}</td>
                <td>
                  {it.witnessCount > 0
                    ? <Pill kind="wit">Witness · {it.witnessPrograms}</Pill>
                    : <Pill kind="none">No witness</Pill>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="table-foot">
          <span>
            {list.data ? `Showing ${list.data.items.length} of ${total.toLocaleString()} ${witnessed ? "witnessed items" : "items"} · page ${page} of ${pages}` : "…"}
          </span>
          <div className="row push" style={{ gap: 8 }}>
            <button className="btn ghost sm" disabled={page <= 1} onClick={() => set({ page: String(page - 1) })}>Prev</button>
            <button className="btn ghost sm" disabled={page >= pages} onClick={() => set({ page: String(page + 1) })}>Next</button>
          </div>
        </div>
      </div>
    </div>
  );
}
