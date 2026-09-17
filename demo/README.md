# CCF Live Demo

Interactive demo for **Curriculum Claim Falsification** — Does the Assessment Require the Skill?

Built for the CHAT: Minds and Machines hackathon, September 15–17, 2026. Deployed on AWS infrastructure provided by the hackathon (auto-deleted after the event).

**Live:** [https://d2nqjgx9lqdrd.cloudfront.net](https://d2nqjgx9lqdrd.cloudfront.net)

## Architecture

```
CloudFront (d2nqjgx9lqdrd.cloudfront.net)
├── /              → S3 frontend bucket (React SPA)
├── /data/*        → S3 data bucket (pre-computed JSON exports)
└── /api/*         → API Gateway → Lambda (a priori rule runner)
```

| Component | Stack | Notes |
|-----------|-------|-------|
| Frontend | React 18 + Vite, served from S3 via CloudFront | ~196 KB JS, ~8 KB CSS |
| API | Lambda (Node.js 20) behind HTTP API Gateway | 15 KB bundled, 512 MB memory, 15 s timeout |
| Data | S3 bucket with pre-computed exports | 2,405 items, witnesses, cell tables, GPU results |
| Infra | AWS CDK (TypeScript), single stack | All resources set to auto-delete on teardown |

## Pages

| Route | What it does |
|-------|-------------|
| `/items` | Item explorer with stats strip, filters (authority, claim, channel, witnessed-only, search), and paged table |
| `/items/:id` | Item detail showing stem, choices, and key. Runs all 15 a priori rules on load and shows witness-found or no-witness verdict |
| `/admin/rules` | Browse the a priori rule definitions — channel, lacks, applies-to, description, and citation |
| `/admin/claims` | Per-authority claim files with expandable tables of claim codes, operations, and item counts |
| `/admin/data` | Runtime info (region, memory, Node version), API route table, and S3 data file inventory |

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/stats` | Counts for the header strip (items, witnesses, rules, corpora) |
| `GET` | `/api/items` | Paged list; filter by `authority`, `claim`, `channel`, `witnessed`, `search`, `page`, `pageSize` |
| `GET` | `/api/items/{itemId}` | Item with choices, key, and associated witness rows |
| `GET` | `/api/rules` | A priori rule definitions |
| `GET` | `/api/claims` | Claims per authority with item counts |
| `GET` | `/api/config` | Bucket contents, routes, runtime |
| `POST` | `/api/run-rules` | `{ "itemId": "..." }` → score one item against every rule |

Direct API base: `https://4bbskj3on9.execute-api.us-east-1.amazonaws.com`

## Deploying

### One-command deploy

```bash
bash demo/scripts/deploy.sh
```

Installs deps → builds frontend → CDK bootstrap → CDK deploy → uploads data → prints URL.

### Manual deploy

```bash
# 1. Install
cd demo/infra    && npm install
cd demo/lambda   && npm install
cd demo/frontend && npm install

# 2. Build frontend
cd demo/frontend && npm run build

# 3. CDK
cd demo/infra
npx cdk bootstrap                                               # first time only
npx cdk deploy --all --require-approval never --outputs-file ../cdk-outputs.json

# 4. Upload data (bucket name from CDK output)
node demo/scripts/upload-data.mjs <DataBucketName>
```

### Prerequisites

- Node.js 20+
- AWS CLI configured with credentials (`aws sts get-caller-identity` to verify)
- Python 3 (used by the deploy script to parse CDK outputs)

## Local Development

No AWS needed — the Lambda has a dev server that reads directly from the repo checkout.

```bash
# Terminal 1: build and serve the API on :3001
cd demo/lambda
npm run build
node dev-server.mjs

# Terminal 2: Vite dev server on :5173 with proxy to :3001
cd demo/frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). The Vite proxy forwards `/api/*` to the local Lambda dev server, which reads `data/items.jsonl`, `rules/apriori.json`, `claims/*.json`, and `exports/*.json` from the repo root.

## Data Uploaded to S3

The upload script (`demo/scripts/upload-data.mjs`) sends these files:

| Local path | S3 key | Purpose |
|------------|--------|---------|
| `data/items.jsonl` | `data/items.jsonl` | 2,405 keyed items |
| `rules/apriori.json` | `data/apriori.json` | 15 a priori rule definitions |
| `claims/*.json` | `data/claims/*.json` | Claim files per authority |
| `exports/witnesses.json` | `data/witnesses.json` | All witness records |
| `exports/rule-chance.json` | `data/rule-chance.json` | Per-rule per-claim pass rates and CI |
| `exports/apriori-cell-table.json` | `data/apriori-cell-table.json` | Family-wise correction table |
| `exports/comparisons.json` | `data/comparisons.json` | Comparison rows with power analysis |
| `exports/addendum-gpu/*.json` | `data/gpu/*.json` | Masked-stem LM results (7B, 14B, Phi-4, Mistral) |
| `exports/addendum/*.json` | `data/addendum/*.json` | Witness dependence, cue attribution, power |

## Teardown

```bash
cd demo/infra && npx cdk destroy --all --force
```

All resources have `RemovalPolicy.DESTROY` and `autoDeleteObjects: true`. Nothing survives teardown.

## Directory Structure

```
demo/
├── frontend/          React + Vite SPA
│   └── src/
│       ├── pages/     Items, ItemPage, AdminRules, AdminClaims, AdminData
│       ├── components/ Pill, Stat, LacksPills, AdminShell, useAsync
│       ├── api.ts     API client
│       └── styles.css Design system (ivory ground, oxblood accent, Fraunces/Instrument Sans)
├── lambda/            Node.js Lambda function
│   ├── src/
│   │   ├── handler.ts Route dispatcher
│   │   ├── programs.ts 15 a priori programs (ported from runner/)
│   │   ├── channels.ts View constructors and surface features
│   │   ├── data.ts    S3 / local file loading with caching
│   │   └── types.ts   Shared types
│   └── dev-server.mjs Local HTTP wrapper for development
├── infra/             AWS CDK stack
│   ├── lib/ccf-demo-stack.ts  S3, CloudFront, Lambda, API Gateway
│   └── bin/app.ts
├── design/            HTML artboards (design reference)
├── scripts/
│   ├── deploy.sh      One-command deploy
│   └── upload-data.mjs S3 data uploader
└── cdk-outputs.json   Deployment outputs (generated)
```
