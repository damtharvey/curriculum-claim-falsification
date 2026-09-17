# CCF Live Demo — AWS Hybrid Deployment

Interactive demo for the Curriculum Claim Falsification project.
Built for the CHAT: Minds and Machines hackathon (September 2026).

## Architecture

```
CloudFront
├── /              → S3 (React frontend)
├── /data/*        → S3 (pre-computed JSON exports)
└── /api/*         → API Gateway → Lambda (interactive rule runner)
```

- **Frontend:** React + Vite SPA with five pages — dashboard, item browser, witness browser, interactive rule runner, and about.
- **API Lambda:** Runs all 15 a priori programs against any item in real time. Reads items and rules from S3.
- **Data:** Pre-computed exports (witnesses, cell tables, comparisons, GPU results) served as static JSON from S3.
- **Infrastructure:** AWS CDK (TypeScript) — single stack with auto-delete on teardown.

## Prerequisites

- Node.js 20+
- AWS CLI configured with credentials
- AWS CDK (`npm install -g aws-cdk` or use `npx`)

## Quick Deploy

```bash
bash demo/scripts/deploy.sh
```

This will:
1. Install all dependencies (infra, lambda, frontend)
2. Build the frontend
3. CDK bootstrap + deploy the stack
4. Upload pre-computed data to S3
5. Print the CloudFront URL

## Manual Steps

### 1. Install dependencies

```bash
cd demo/infra    && npm install
cd demo/lambda   && npm install
cd demo/frontend && npm install
```

### 2. Build the frontend

```bash
cd demo/frontend && npm run build
```

### 3. Deploy infrastructure

```bash
cd demo/infra
npx cdk bootstrap           # first time only
npx cdk deploy --all --require-approval never --outputs-file ../cdk-outputs.json
```

### 4. Upload data

```bash
# Get the bucket name from CDK outputs
node demo/scripts/upload-data.mjs <DataBucketName>
```

### 5. Access the demo

The CloudFront URL is printed in the CDK output (`DistributionUrl`).
CloudFront propagation takes a few minutes; the API Gateway URL works immediately.

## Local Development

### Frontend only (with API proxy)

```bash
cd demo/frontend
npm run dev
```

This starts Vite on `http://localhost:5173` with a proxy to `http://localhost:3001` for `/api/*`.

### Teardown

```bash
cd demo/infra
npx cdk destroy --all --force
```

All resources have `RemovalPolicy.DESTROY` and `autoDeleteObjects: true` — nothing survives teardown. AWS also auto-deletes hackathon resources.

## What's Served

| Route | Source | Description |
|-------|--------|-------------|
| `/` | Frontend | Dashboard with stats |
| `/items` | Frontend + API | Paginated item browser with search/filter |
| `/items/:id` | Frontend + API | Item detail with witnesses and run-rules |
| `/witnesses` | Frontend + S3 | Browse all witnesses with filters |
| `/runner` | Frontend + API | Interactive: pick any item, run all 15 rules live |
| `/about` | Frontend | Project explanation and channel descriptions |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/stats` | Summary stats (item count, witness count, corpora) |
| `GET` | `/api/items?page=1&corpus=staar&search=...` | Paginated item list |
| `GET` | `/api/items/{itemId}` | Single item with associated witnesses |
| `GET` | `/api/rules` | List all a priori rule definitions |
| `POST` | `/api/run-rules` | `{ "itemId": "..." }` → run all rules on item |

## Data Files Uploaded

The upload script sends these from the repo's existing exports:

- `data/items.jsonl` — 2,405 keyed items
- `rules/apriori.json` — 15+ a priori rule definitions
- `exports/witnesses.json` — all witness records
- `exports/rule-chance.json` — per-rule per-claim pass rates
- `exports/apriori-cell-table.json` — family-wise correction table
- `exports/comparisons.json` — comparison rows with power analysis
- `exports/addendum-gpu/*.json` — masked-stem LM results
- `exports/addendum/*.json` — witness dependence, cue attribution
