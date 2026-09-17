## CCF conventions — read before building

**No wrapper needed.** Components are plain React and are styled entirely by the stylesheet: link `styles.css` once and every class below resolves. The only exception is `AdminShell`, which renders `NavLink`s and must sit inside a router — `MemoryRouter` from `window.CcfDemo` works (`<MemoryRouter initialEntries={["/admin/rules"]}><AdminShell>…</AdminShell></MemoryRouter>`); without it the shell throws. Set `<html>` to light: the DS is a light-only ivory theme (`color-scheme: light`).

**Styling idiom: CSS class vocabulary + tokens, no utility framework.** Write ordinary HTML/JSX with these classes; reach for `style={{}}` only for one-off gaps and spacing. Never invent new class names — anything not listed here renders unstyled.

| Family | Classes (exact) | Use |
|---|---|---|
| Page chrome | `app-header` (with child `brand`, `tagline`, `nav a`, `nav a.active`), `app-main`, `page`, `page-head` (child `lede`), `crumbs` | header bar, page column (24px gap), title row with muted lede |
| Layout | `row`, `row end`, `wrap`, `stack`, `two-col`, `three-col`, `push` (margin-left auto), `check-grid` | flex row (12px gap) / column (16px) / 2- and 3-column grids |
| Surfaces | `card`, `card pad` (24px padding), `card-head`, `note-box`, `error` | white surface with `--line` border, radius 12 |
| Text | `serif`, `mono`, `muted`, `small`, `tiny`, `stem` (display 22px), `trace` (mono 11px muted) | `h1`/`h2`/`h3` are Fraunces by default; body is Instrument Sans |
| Forms | `field` (wraps a `label`/`.label` + `input`/`select`/`textarea`), `field compact`, `check` (label wrapping a checkbox), `btn`, `btn ghost`, `btn danger`, `btn sm`, `:disabled` | inputs are 44px tall, radius 8; `btn` is solid ink, `ghost` outlined, `danger` oxblood text |
| Status | `pill` + one of `wit` `none` `tag` `tag strong` `op` `lack`; `verdict` + `found` / `none` / `pending` (children `eyebrow`, `headline`, `note`); `stat`, `stat dark` (children `label`, `value`); `status` | pills are the tag/verdict vocabulary; `verdict found` is the oxblood hero block |
| Item page | `choice`, `choice key` (child `letter`), `stem`, `table-foot`, `preview` | answer options with a mono letter; the key option gets the ink border |
| Admin | `admin` > `side` (children `eyebrow`, `a`, `a.active`, `foot`) + `content` | what `AdminShell` renders — use the component rather than rebuilding it |

Tables need no class: `table`, `th`, `td` are styled globally (uppercase 12px headers, 14px cells, `tr.sel td` highlights a selected row).

**Tokens** (defined on `:root` in `styles.css`; use `var(--…)` in any inline style):
`--bg` #f4f1ea ivory ground · `--surface` white · `--surface-soft` · `--ink` #1a1917 · `--muted` #5a554c · `--line` / `--line-soft` borders · `--accent` #8a2f2a oxblood (the one accent — verdicts, danger, links on hover) · `--accent-soft` / `--accent-ink` rose pair for `lack` · `--teal-soft` / `--teal-ink` for `op` · `--font-body` Instrument Sans · `--font-display` Fraunces · `--font-mono` JetBrains Mono (ids, file paths, rule names).

**Where the truth lives.** `styles.css` → `_ds_bundle.css` is the whole stylesheet (614 lines, every selector above); read it before styling anything new. Per-component API and examples: `components/general/<Name>/<Name>.prompt.md` and `<Name>.d.ts`. Below 900px the layout stacks (`two-col`/`three-col` collapse, the admin sidebar becomes a row) — design desktop-first at 1200–1280.

**Idiomatic build snippet** (a configuration page, as the app lays it out):

```jsx
const { AdminShell, Pill, Stat, MemoryRouter } = window.CcfDemo;

<MemoryRouter initialEntries={["/admin/rules"]}>
  <AdminShell>
    <div className="page-head">
      <div>
        <h1>A-priori rules</h1>
        <p className="lede muted">Programs the runner tries on every item.</p>
      </div>
      <button className="btn push">Save</button>
    </div>
    <div className="three-col">
      <Stat label="Rules" value="24" />
      <Stat label="Enabled" value="21" />
      <Stat dark label="Witnesses" value="317" />
    </div>
    <div className="card">
      <table>
        <thead><tr><th>Rule</th><th>Channel</th><th>Enabled</th></tr></thead>
        <tbody>
          <tr><td className="mono">longest-option</td><td>item-cues</td><td><Pill kind="op">on</Pill></td></tr>
        </tbody>
      </table>
    </div>
  </AdminShell>
</MemoryRouter>
```
