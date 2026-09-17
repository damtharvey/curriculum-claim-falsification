import { useEffect, useState, useCallback } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { getItems, type ItemSummary, type PagedItems } from "../api";

export function ItemBrowser() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [data, setData] = useState<PagedItems | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState(searchParams.get("search") ?? "");

  const page = Number(searchParams.get("page")) || 1;
  const corpus = searchParams.get("corpus") ?? "";

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = { page: String(page), pageSize: "25" };
      if (corpus) params.corpus = corpus;
      if (search) params.search = search;
      const res = await getItems(params);
      setData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [page, corpus, search]);

  useEffect(() => { load(); }, [load]);

  const setPage = (p: number) => {
    const next = new URLSearchParams(searchParams);
    next.set("page", String(p));
    setSearchParams(next);
  };

  const doSearch = () => {
    const next = new URLSearchParams(searchParams);
    if (search) next.set("search", search);
    else next.delete("search");
    next.set("page", "1");
    setSearchParams(next);
  };

  return (
    <>
      <h2 style={{ marginBottom: "1rem" }}>Items ({data?.total ?? "…"})</h2>

      <div className="controls-row">
        <input
          type="search"
          placeholder="Search by ID, stem, or claim…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && doSearch()}
          style={{ flex: 1, minWidth: "200px" }}
          aria-label="Search items"
        />
        <button onClick={doSearch}>Search</button>
        {corpus && (
          <span className="badge badge-accent" style={{ alignSelf: "center" }}>
            corpus: {corpus}{" "}
            <span
              style={{ cursor: "pointer", marginLeft: "0.25rem" }}
              onClick={() => {
                const next = new URLSearchParams(searchParams);
                next.delete("corpus");
                setSearchParams(next);
              }}
              role="button"
              tabIndex={0}
              aria-label={`Remove corpus filter ${corpus}`}
            >
              ×
            </span>
          </span>
        )}
      </div>

      {loading ? (
        <div className="loading">Loading items</div>
      ) : data ? (
        <>
          <div className="card" style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Corpus</th>
                  <th>Claim</th>
                  <th>Type</th>
                  <th>Key</th>
                  <th style={{ maxWidth: "400px" }}>Stem (preview)</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <Link to={`/items/${encodeURIComponent(item.id)}`}>
                        <code style={{ fontSize: "0.78rem" }}>{item.id}</code>
                      </Link>
                    </td>
                    <td>
                      <span className="badge badge-accent">{item.corpus}</span>
                    </td>
                    <td style={{ fontSize: "0.8rem" }}>{item.claim}</td>
                    <td>
                      <span className="badge badge-cyan">{item.responseType}</span>
                    </td>
                    <td>
                      <code>{item.key}</code>
                    </td>
                    <td
                      style={{
                        maxWidth: "400px",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                        fontSize: "0.8rem",
                        color: "var(--text-muted)",
                      }}
                    >
                      {item.stem.slice(0, 120)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="pagination">
            <button disabled={page <= 1} onClick={() => setPage(page - 1)}>
              ← Prev
            </button>
            <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
              Page {page} of {Math.ceil(data.total / data.pageSize)}
            </span>
            <button
              disabled={page * data.pageSize >= data.total}
              onClick={() => setPage(page + 1)}
            >
              Next →
            </button>
          </div>
        </>
      ) : null}
    </>
  );
}
