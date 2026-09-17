import { LacksPills } from 'ccf-frontend';

/** A rule that lacks two operations, shown in full. */
export const TwoLacks = () => <LacksPills lacks={['bind', 'distinguish']} />;

/** Beyond the default cap of two, the rest collapses to a +N count. */
export const Overflow = () => (
  <LacksPills lacks={['retrieve', 'execute', 'bind', 'distinguish', 'explain', 'transfer']} />
);

/** Raise `max` to show every operation. */
export const ShowAll = () => (
  <LacksPills max={6} lacks={['retrieve', 'execute', 'bind', 'distinguish', 'explain', 'transfer']} />
);
