#!/usr/bin/env bash
# Push to GitHub and deploy the static site to Netlify production.
set -euo pipefail

echo "Pushing to GitHub..."
git push

set -a && source "$(dirname "$0")/../.env" && set +a
echo "Deploying to Netlify..."
npx netlify deploy --prod --dir=products/website/output
