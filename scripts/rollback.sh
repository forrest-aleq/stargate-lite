#!/usr/bin/env bash
# Roll Stargate Lite Cloud Run traffic back to an existing revision.
# Usage: ./scripts/rollback.sh <environment> <revision> [service]
# Example: ./scripts/rollback.sh production stargate-lite-00042-ab3 stargate-lite

set -euo pipefail

ENVIRONMENT="${1:-}"
REVISION="${2:-}"
SERVICE_NAME="${3:-${GCP_CLOUD_RUN_SERVICE:-stargate-lite}}"
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-}"

if [[ -z "${ENVIRONMENT}" || -z "${REVISION}" ]]; then
    echo "Usage: $0 <environment> <revision> [service]"
    echo "  environment: staging or production"
    echo "  revision: existing Cloud Run revision name"
    echo "  service: optional Cloud Run service name (default: GCP_CLOUD_RUN_SERVICE or stargate-lite)"
    exit 1
fi

if [[ "${ENVIRONMENT}" != "staging" && "${ENVIRONMENT}" != "production" ]]; then
    echo "Invalid environment '${ENVIRONMENT}'. Expected 'staging' or 'production'."
    exit 1
fi

if [[ -z "${PROJECT_ID}" || -z "${REGION}" ]]; then
    echo "GCP_PROJECT_ID and GCP_REGION must be exported before rollback."
    exit 1
fi

if [[ "${ENVIRONMENT}" == "production" ]]; then
    echo "Production rollback requested for ${SERVICE_NAME} to revision ${REVISION}"
    read -r -p "Type 'rollback-production' to continue: " confirm
    if [[ "${confirm}" != "rollback-production" ]]; then
        echo "Aborted"
        exit 1
    fi
fi

echo "Sending 100% ${ENVIRONMENT} traffic for ${SERVICE_NAME} to ${REVISION}"
gcloud run services update-traffic "${SERVICE_NAME}" \
    --project "${PROJECT_ID}" \
    --region "${REGION}" \
    --to-revisions "${REVISION}=100"

if [[ "${ENVIRONMENT}" == "production" ]]; then
    HEALTH_URL="${PRODUCTION_URL:-}"
else
    HEALTH_URL="${STAGING_URL:-}"
fi

if [[ -n "${HEALTH_URL}" ]]; then
    echo "Checking ${HEALTH_URL%/}/health"
    curl -fsS "${HEALTH_URL%/}/health" >/dev/null
fi

echo "Rollback traffic update completed"
