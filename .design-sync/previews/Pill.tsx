import { Pill } from 'ccf-frontend';

/** Every kind side by side - the verdict/tag vocabulary used across the app. */
export const Kinds = () => (
  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center' }}>
    <Pill kind="wit">Witness</Pill>
    <Pill kind="none">Miss</Pill>
    <Pill kind="tag">timss2011 · grade 8 · Number</Pill>
    <Pill kind="tag strong">Key</Pill>
    <Pill kind="op">execute</Pill>
    <Pill kind="lack">explain</Pill>
  </div>
);

/** The item-page header: authority + claim, corpus, and response-type tags in a row. */
export const ItemTags = () => (
  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
    <Pill kind="tag">timss · applying</Pill>
    <Pill kind="tag">timss2011 · grade 8 · Number</Pill>
    <Pill kind="tag">numeric</Pill>
  </div>
);

/** Rule-run verdicts as they appear in the trace table, plus the on/off state pills. */
export const Verdicts = () => (
  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
    <Pill kind="wit">Witness</Pill>
    <Pill kind="none">Miss</Pill>
    <Pill kind="none">Abstain</Pill>
    <Pill kind="none">N/A</Pill>
    <Pill kind="op">on</Pill>
    <Pill kind="none">off</Pill>
  </div>
);
