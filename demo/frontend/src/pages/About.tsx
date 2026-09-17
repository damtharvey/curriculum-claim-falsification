export function About() {
  return (
    <>
      <h2 style={{ marginBottom: "1rem" }}>
        About This Demo
      </h2>

      <div className="card">
        <h3>Curriculum Claim Falsification</h3>
        <p style={{ fontSize: "0.9rem", lineHeight: 1.7 }}>
          An assessment item carries a published tag: a standard code, or a cognitive domain
          such as <em>reasoning</em>. A passing score is then read as evidence of that competency.
        </p>
        <p style={{ fontSize: "0.9rem", lineHeight: 1.7, marginTop: "0.5rem" }}>
          This project searches for <strong>programs that lack the tagged operation</strong> and
          still pass under the published key. Each such program is a{" "}
          <strong>witness</strong> that the tag overstates what a pass shows.
        </p>
      </div>

      <div className="card">
        <h3>One-Sided Semantics</h3>
        <ul style={{ fontSize: "0.85rem", paddingLeft: "1.25rem", lineHeight: 1.8 }}>
          <li>A program that <strong>passes</strong> refutes the claim that passing requires the tagged operation.</li>
          <li>A program that <strong>fails</strong> proves nothing beyond the programs we tried.</li>
          <li>We never say students did not learn the skill.</li>
        </ul>
      </div>

      <div className="card">
        <h3>Channels</h3>
        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "0.5rem" }}>
          Each channel fixes the information and instruction set available to a program,
          defining which operations it lacks.
        </p>
        <table className="data-table">
          <thead>
            <tr>
              <th>Channel</th>
              <th>Available</th>
              <th>Operations Lacked</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><span className="badge badge-yellow">item-cues</span></td>
              <td style={{ fontSize: "0.8rem" }}>Option strings only (length, absolute terms, numeric values)</td>
              <td style={{ fontSize: "0.8rem" }}>All content operations</td>
            </tr>
            <tr>
              <td><span className="badge badge-yellow">partial-input</span></td>
              <td style={{ fontSize: "0.8rem" }}>Stem tokens, n-grams, choices, stem–option overlap</td>
              <td style={{ fontSize: "0.8rem" }}>Bind, distinguish, explain</td>
            </tr>
            <tr>
              <td><span className="badge badge-yellow">unbound-exec</span></td>
              <td style={{ fontSize: "0.8rem" }}>Stem, choices, numbers — formula catalog without situation binding</td>
              <td style={{ fontSize: "0.8rem" }}>Bind, explain</td>
            </tr>
            <tr>
              <td><span className="badge badge-yellow">instruction-only</span></td>
              <td style={{ fontSize: "0.8rem" }}>Worked examples with number substitution</td>
              <td style={{ fontSize: "0.8rem" }}>Bind, distinguish, transfer</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3>Interactive Runner</h3>
        <p style={{ fontSize: "0.85rem", lineHeight: 1.7 }}>
          The <strong>Run Rules</strong> page lets you pick any item from the 2,405-item census
          and execute all 15 a priori programs against it in real time. Each program operates
          on a restricted view (no access to the answer key) and reports its answer, whether
          it matched the key, and a trace of the computation.
        </p>
        <p style={{ fontSize: "0.85rem", lineHeight: 1.7, marginTop: "0.5rem" }}>
          A correct answer from a program that lacks a tagged operation is a witness.
        </p>
      </div>

      <div className="card">
        <h3>Architecture</h3>
        <ul style={{ fontSize: "0.85rem", paddingLeft: "1.25rem", lineHeight: 1.8 }}>
          <li><strong>Frontend:</strong> React + Vite, served from S3 via CloudFront</li>
          <li><strong>API:</strong> AWS Lambda (Node.js) behind API Gateway, executing a priori rules</li>
          <li><strong>Data:</strong> Pre-computed JSON exports in S3 (witnesses, cell tables, comparisons)</li>
          <li><strong>Infrastructure:</strong> AWS CDK (TypeScript)</li>
        </ul>
      </div>

      <div className="card" style={{ borderLeft: "3px solid var(--text-muted)" }}>
        <h3>CHAT Hackathon – Minds and Machines, September 2026</h3>
        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
          This demo was built for the CHAT: Minds and Machines event (September 15–17, 2026).
          Resources are provided by AWS and will be automatically deleted after the hackathon.
        </p>
      </div>
    </>
  );
}
