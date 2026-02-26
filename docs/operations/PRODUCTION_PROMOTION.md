# Stargate Production Promotion Runbook

This runbook is the canonical process for promoting `stargate-lite` from staging to production.

## One-time GitHub configuration

Set these repository secrets:

- `RAILWAY_TOKEN_STAGING`
- `RAILWAY_TOKEN_PRODUCTION`
- `STAGING_API_KEY`
- `PRODUCTION_API_KEY`

Set these repository variables:

- `STAGING_URL` (example: `https://stargate-lite-staging.up.railway.app`)
- `PRODUCTION_URL` (example: `https://stargate-lite-production.up.railway.app`)
- `RAILWAY_SERVICE_NAME` (default expected by workflows: `stargate-lite`)
- `RAILWAY_STAGING_ENVIRONMENT` (default: `staging`)
- `RAILWAY_PRODUCTION_ENVIRONMENT` (default: `production`)
- `STAGING_MIN_CAPABILITIES` (optional, default: `100`)

## Promotion workflow

Trigger GitHub Actions workflow: `Deploy to Production`.

Inputs:

- `git_ref`: ref to deploy (default `main`)
- `confirm`: must equal `deploy-production`
- `min_capabilities`: minimum capability count expected after deploy

The workflow enforces:

1. Target ref must be on `main`
2. Staging Railway env readiness check
3. Production Railway env readiness check
4. Staging API health + smoke verification
5. Current production health check
6. Deploy to production
7. Post-deploy production health + smoke verification (with retries)

## Readiness checks used by workflow

- `scripts/check_railway_readiness.py`
  - validates required runtime vars
  - validates key-gated vars for all enabled services
  - validates `ENVIRONMENT` value when requested

- `scripts/verify_remote_api.py`
  - `/health` must return `status=healthy`
  - `/api/v1/capabilities` must meet `min_capabilities`
  - `/api/v1/execute` smoke test using `calc.npv`

## Rollback process

Use the rollback script with a known-good SHA/tag:

```bash
./scripts/rollback.sh production <git-ref> stargate-lite
```

This rollback path is safe for local working trees because it deploys from a temporary git worktree.

## Manual local preflight (optional)

```bash
python scripts/check_railway_readiness.py \
  --environment staging \
  --service stargate-lite \
  --expect-env-value staging

python scripts/check_railway_readiness.py \
  --environment production \
  --service stargate-lite \
  --expect-env-value production
```
