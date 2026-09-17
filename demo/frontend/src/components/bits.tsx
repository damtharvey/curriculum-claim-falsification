/** Small presentational pieces shared across pages. */

export function Pill({ kind, children }: { kind: "wit" | "none" | "tag" | "op" | "lack" | "tag strong"; children: React.ReactNode }) {
  return <span className={`pill ${kind}`}>{children}</span>;
}

export function Stat({ label, value, dark }: { label: string; value: React.ReactNode; dark?: boolean }) {
  return (
    <div className={`stat${dark ? " dark" : ""}`}>
      <div className="label">{label}</div>
      <div className="value">{value}</div>
    </div>
  );
}

export function LacksPills({ lacks, max = 2 }: { lacks: string[]; max?: number }) {
  const shown = lacks.slice(0, max);
  const rest = lacks.length - shown.length;
  return (
    <span className="row" style={{ gap: 4, display: "inline-flex", flexWrap: "wrap" }}>
      {shown.map((l) => <Pill key={l} kind="lack">{l}</Pill>)}
      {rest > 0 && <span className="tiny muted">+{rest}</span>}
    </span>
  );
}

export function fmtBytes(n: number): string {
  if (n >= 1024 * 1024) return `${(n / 1024 / 1024).toFixed(1)} MiB`;
  if (n >= 1024) return `${(n / 1024).toFixed(0)} KiB`;
  return `${n} B`;
}

export const ONE_SIDED =
  "A pass refutes the tag for that item. A fail proves nothing beyond the programs tried.";
