#!/bin/bash
# Stargate Rollback Script
# Usage: ./scripts/rollback.sh <environment> <commit-sha>
# Example: ./scripts/rollback.sh production abc123

set -e

ENV=${1:-staging}
COMMIT=${2}

if [ -z "$COMMIT" ]; then
    echo "Usage: $0 <environment> <commit-sha>"
    echo "  environment: staging or production"
    echo "  commit-sha: git commit to rollback to"
    exit 1
fi

echo "🔄 Rolling back $ENV to commit $COMMIT"

# Checkout the specific commit
git checkout $COMMIT

# Deploy based on environment
if [ "$ENV" == "production" ]; then
    echo "⚠️  PRODUCTION ROLLBACK"
    read -p "Type 'rollback' to confirm: " confirm
    if [ "$confirm" != "rollback" ]; then
        echo "Aborted"
        exit 1
    fi
    railway up --service stargate
else
    railway up --service stargate-staging
fi

# Return to main branch
git checkout main

echo "✅ Rollback complete"
echo "Run health check: curl https://$ENV.stargate.up.railway.app/health"
