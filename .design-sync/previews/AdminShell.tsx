import { AdminShell } from 'ccf-frontend';

/** Sidebar plus a configuration page's head and a card, as the Rules page lays out. */
export const RulesPage = () => (
  <AdminShell>
    <div className="page-head">
      <div>
        <div className="eyebrow">Rules</div>
        <h1>A-priori rules</h1>
        <p className="lede muted">Programs the runner tries on every item. A pass refutes the tag for that item.</p>
      </div>
    </div>
    <div className="card">
      <table>
        <thead>
          <tr><th>Rule</th><th>Channel</th><th>Lacks</th><th>Enabled</th></tr>
        </thead>
        <tbody>
          <tr><td className="mono">longest-option</td><td>item-cues</td><td>6</td><td><span className="pill op">on</span></td></tr>
          <tr><td className="mono">stem-option-overlap</td><td>partial-input</td><td>3</td><td><span className="pill op">on</span></td></tr>
          <tr><td className="mono">avoid-absolute-terms</td><td>item-cues</td><td>3</td><td><span className="pill none">off</span></td></tr>
        </tbody>
      </table>
    </div>
  </AdminShell>
);
