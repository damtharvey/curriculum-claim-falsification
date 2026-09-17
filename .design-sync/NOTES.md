# design-sync notes — ccf-frontend

Repo-specific facts for re-syncs. Config lives in `config.json`; this file holds what doesn't map to a `cfg.*` field.

## How this repo is shaped
- Not a component library: `demo/frontend` is a Vite app. The DS is its `src/styles.css` (tokens + class vocabulary shared with the `demo/design/*.dc.html` artboards) plus the four presentational pieces in `src/components/`. Route pages under `src/pages/` fetch from `/api` and are deliberately out of scope (`srcDir: src/components`).
- No library build. The converter runs in synth-entry mode: `--entry ./demo/frontend/dist/index.es.js` never exists, which makes it walk up to `demo/frontend/package.json` and synthesize the entry from `src/components/*.tsx`. `[NO_DIST]` on every build is expected, not a failure.
- Because there's no shipped `.d.ts`, every `<Name>Props` body is hand-written in `cfg.dtsPropsFor`. **When a component's props change in `bits.tsx` / `AdminShell.tsx`, update `dtsPropsFor` too** — nothing catches drift automatically.
- `AdminShell` renders `NavLink`s → `cfg.provider` wraps previews in `MemoryRouter` (merged onto the global via `extraEntries: ["react-router-dom"]`, which is why the bundle is ~225 KB and `window.CcfDemo` has 83 exports). The provider is global, so every `.prompt.md` says "wrap in MemoryRouter"; conventions.md clarifies only AdminShell needs it.
- `AdminShell` uses `cardMode: single` at `1200x640`: the default 900px capture viewport is exactly the app's `@media (max-width: 900px)` breakpoint, where the sidebar collapses to a row and hides its foot. That's the DS behaving correctly, not a defect.
- Fonts are Google-hosted via `@import` in `styles.css` → `[FONT_REMOTE]` informational on every validate. Nothing to ship.
- Converter deps in `.ds-sync/` need `npm approve-scripts esbuild` on a fresh clone (npm blocks esbuild's postinstall by default).

## Run recipe
```
node .ds-sync/resync.mjs --config .design-sync/config.json --node-modules ./demo/frontend/node_modules \
  --entry ./demo/frontend/dist/index.es.js --out ./ds-bundle [--remote .design-sync/.cache/remote-sync.json]
```
Known validate warns: `[FONT_REMOTE]` only. Anything else is new.

## Re-sync risks
- `dtsPropsFor` is inlined config: goes stale silently if `bits.tsx` / `AdminShell.tsx` signatures change. Diff them against the config on every re-sync.
- Preview content in `.design-sync/previews/` uses real vocabulary from `rules/apriori.json` (rule ids, channels, the six operations) and `data/items.jsonl` (corpus/claim tags). If those rename, previews still render but stop being realistic.
- `conventions.md` enumerates every class in `styles.css` by hand. A new or renamed class in the stylesheet needs a header edit; the validation grep in the base skill's "Author the conventions header" step catches removals, not additions.
- Build assumed Node 26 / npm 11, esbuild 0.28, playwright chromium-headless-shell 1243. Google Fonts must be reachable for previews to render in the brand fonts.
- The upload merged `react-router-dom` into the bundle. If the app moves off react-router, drop `extraEntries` + `provider` and exclude or rework `AdminShell`.
