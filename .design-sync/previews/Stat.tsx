import { Stat } from 'ccf-frontend';

/** Three stats in the data page's row: a count, a runtime, and a source. */
export const Row = () => (
  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
    <Stat label="Item set" value="6,032 frozen" />
    <Stat label="Runner" value="Lambda · Node 20" />
    <Stat label="Data source" value="S3 bucket" />
  </div>
);

/** A value with a small sub-line, as the data page composes it. */
export const WithSubline = () => (
  <Stat
    label="Item set"
    value={
      <>
        6,032 frozen
        <div style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--muted)', marginTop: 4 }}>
          data/items.jsonl · 4.8 MiB
        </div>
      </>
    }
  />
);

/** The inverted variant for the headline number. */
export const Dark = () => (
  <div style={{ display: 'flex', gap: 12 }}>
    <Stat dark label="Witnesses" value="317" />
    <Stat label="Items tried" value="6,032" />
  </div>
);
