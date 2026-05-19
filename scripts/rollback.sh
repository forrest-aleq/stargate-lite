#!/usr/bin/env bash
# Safe Stargate rollback script
# Usage: ./scripts/rollback.sh <environment> <git-ref> [service]
# Example: ./scripts/rollback.sh production a1b2c3d stargate-lite

set -euo pipefail

ENVIRONMENT="${1:-}"
GIT_REF="${2:-}"
SERVICE_NAME="${3:-${RAILWAY_SERVICE_NAME:-stargate-lite}}"

if [[ -z "${ENVIRONMENT}" || -z "${GIT_REF}" ]]; then
    echo "Usage: $0 <environment> <git-ref> [service]"
    echo "  environment: staging or production"
    echo "  git-ref: commit SHA / tag / branch to deploy"
    echo "  service: optional Railway service name (default: stargate-lite)"
    exit 1
fi

if [[ "${ENVIRONMENT}" != "staging" && "${ENVIRONMENT}" != "production" ]]; then
    echo "Invalid environment '${ENVIRONMENT}'. Expected 'staging' or 'production'."
    exit 1
fi

if [[ "${ENVIRONMENT}" == "production" ]]; then
    echo "Production rollback requested"
    read -r -p "Type 'rollback-production' to continue: " confirm
    if [[ "${confirm}" != "rollback-production" ]]; then
        echo "Aborted"
        exit 1
    fi
fi

TMP_DIR="$(mktemp -d)"
cleanup() {
    git worktree remove --force "${TMP_DIR}" >/dev/null 2>&1 || true
    rm -rf "${TMP_DIR}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "Preparing rollback source at ref '${GIT_REF}'"
git worktree add --detach "${TMP_DIR}" "${GIT_REF}"

echo "Deploying ref '${GIT_REF}' to ${ENVIRONMENT} (${SERVICE_NAME})"
railway deployment up "${TMP_DIR}" \
    --path-as-root \
    --ci \
    --service "${SERVICE_NAME}" \
    --environment "${ENVIRONMENT}"

echo "Rollback deployment submitted successfully"
