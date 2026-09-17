#!/usr/bin/env bash
set -euo pipefail

# Full deploy: install deps, build, CDK deploy, upload data.
# Usage: bash demo/scripts/deploy.sh

DIR="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$DIR/.." && pwd)"

echo "=== Installing infra dependencies ==="
cd "$DIR/infra"
npm install

echo "=== Installing Lambda dependencies ==="
cd "$DIR/lambda"
npm install

echo "=== Installing frontend dependencies ==="
cd "$DIR/frontend"
npm install

echo "=== Building frontend ==="
npm run build

echo "=== Resolving AWS credentials ==="
# The CDK CLI's bundled SDK cannot read an `aws login` session, so hand it
# the session as plain env vars. Fails loudly here rather than inside CDK.
eval "$(aws configure export-credentials --format env)"
export AWS_REGION="${AWS_REGION:-$(aws configure get region 2>/dev/null || echo us-east-1)}"
export CDK_DEFAULT_REGION="$AWS_REGION"
export CDK_DEFAULT_ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
export JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION=1
echo "account $CDK_DEFAULT_ACCOUNT, region $AWS_REGION"

echo "=== CDK bootstrap (if needed) ==="
cd "$DIR/infra"
npx cdk bootstrap 2>/dev/null || true

echo "=== CDK deploy ==="
npx cdk deploy --all --require-approval never --outputs-file "$DIR/cdk-outputs.json"

echo "=== Extracting bucket name from CDK outputs ==="
DATA_BUCKET=$(python3 -c "
import json
with open('$DIR/cdk-outputs.json') as f:
    out = json.load(f)
stack = out.get('CcfDemoStack', {})
print(stack.get('DataBucketName', ''))
")

if [ -z "$DATA_BUCKET" ]; then
  echo "ERROR: Could not find DataBucketName in CDK outputs."
  echo "Upload data manually: node demo/scripts/upload-data.mjs <bucket-name>"
  exit 1
fi

echo "=== Uploading data to $DATA_BUCKET ==="
cd "$ROOT"
node demo/scripts/upload-data.mjs "$DATA_BUCKET"

echo ""
echo "=== Deploy complete ==="
DIST_URL=$(python3 -c "
import json
with open('$DIR/cdk-outputs.json') as f:
    out = json.load(f)
stack = out.get('CcfDemoStack', {})
print(stack.get('DistributionUrl', ''))
")

echo "CloudFront URL: $DIST_URL"
echo ""
echo "Note: CloudFront may take a few minutes to propagate. The API is available"
echo "immediately at the ApiUrl shown in CDK output."
