#!/usr/bin/env bash
# Safe Stargate Railway rollback script.
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
    echo "Production rollback requested for ${SERVICE_NAME} to ${GIT_REF}"
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
RESOLVED_SHA="$(git -C "${TMP_DIR}" rev-parse HEAD)"
BUILD_TIME="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

echo "Setting deployment provenance for ${ENVIRONMENT}"
railway variable set \
    --service "${SERVICE_NAME}" \
    --environment "${ENVIRONMENT}" \
    --skip-deploys \
    "STARGATE_BUILD_SHA=${RESOLVED_SHA}" \
    "STARGATE_BUILD_TIME=${BUILD_TIME}" \
    "STARGATE_DEPLOYMENT_ID=manual-rollback" \
    "STARGATE_ENVIRONMENT=${ENVIRONMENT}" \
    "ENVIRONMENT=${ENVIRONMENT}"

echo "Deploying ref '${GIT_REF}' (${RESOLVED_SHA}) to ${ENVIRONMENT} (${SERVICE_NAME})"
railway deployment up "${TMP_DIR}" \
    --path-as-root \
    --ci \
    --service "${SERVICE_NAME}" \
    --environment "${ENVIRONMENT}" \
    --message "rollback ${ENVIRONMENT} ${RESOLVED_SHA}"

echo "Rollback deployment submitted successfully"
