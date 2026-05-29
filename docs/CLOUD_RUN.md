# Stargate Lite Cloud Run Deployment

Stargate Lite deploys to Cloud Run through GitHub Actions OIDC. Do not store
long-lived GCP JSON service account keys in GitHub.

## GitHub Environment Variables

Configure these in both `staging` and `production` GitHub environments:

- `GCP_PROJECT_ID`
- `GCP_REGION`
- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_SERVICE_ACCOUNT`
- `GCP_ARTIFACT_REGISTRY_LOCATION`
- `GCP_ARTIFACT_REGISTRY_REPOSITORY`
- `GCP_CLOUD_RUN_SERVICE`
- `GCP_CLOUD_RUN_SECRETS`
- `GCP_CLOUD_RUN_ENV_VARS` optional
- `STAGING_URL` or `PRODUCTION_URL`

`GCP_CLOUD_RUN_SECRETS` is passed directly to `gcloud run deploy --set-secrets`.
Use comma-separated mappings, for example:

```text
API_SECRET_KEY=API_SECRET_KEY:latest,DATABASE_URL=DATABASE_URL:latest,ENABLED_SERVICES=ENABLED_SERVICES:latest,ENCRYPTION_KEY=ENCRYPTION_KEY:latest,REDIS_URL=REDIS_URL:latest
```

## Deployment Gates

- `deploy-staging.yml` runs after `staging` CI succeeds.
- `deploy-production.yml` is manually dispatched and requires
  `confirm=deploy-production`.
- Both workflows build and push a commit-tagged Docker image to Artifact
  Registry, deploy that image to Cloud Run, set build provenance env vars, then
  verify `/health`, `/version`, `/api/v1/capabilities`, and a smoke
  `/api/v1/execute`.

Run the infra verifier before cutover:

```bash
python3 scripts/verify_release_infra.py
```
