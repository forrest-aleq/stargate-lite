# Stargate Lite Cloud Run Deployment

This is a future migration note, not the active production path. Stargate Lite
currently deploys to Railway. If Cloud Run is revived, use GitHub Actions OIDC
and do not store long-lived GCP JSON service account keys in GitHub.

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
- `ENABLE_CLOUD_RUN_DEPLOY`, set to `true` only after the GCP project,
  Artifact Registry repository, service account, Workload Identity provider,
  Cloud Run service, and Secret Manager mappings exist
- `STAGING_URL` or `PRODUCTION_URL`

`GCP_CLOUD_RUN_SECRETS` is passed directly to `gcloud run deploy --set-secrets`.
Use comma-separated mappings, for example:

```text
API_SECRET_KEY=API_SECRET_KEY:latest,DATABASE_URL=DATABASE_URL:latest,ENABLED_SERVICES=ENABLED_SERVICES:latest,ENCRYPTION_KEY=ENCRYPTION_KEY:latest,REDIS_URL=REDIS_URL:latest
```

## Future Deployment Gates

- `deploy-staging.yml` runs after `staging` CI succeeds.
- `deploy-production.yml` is manually dispatched and requires
  `confirm=deploy-production`.
- Both workflows build and push a commit-tagged Docker image to Artifact
  Registry, deploy that image to Cloud Run, set build provenance env vars, then
  verify `/health`, `/version`, `/api/v1/capabilities`, and a smoke
  `/api/v1/execute`.

Before making Cloud Run active again, update `scripts/verify_release_infra.py`
and the deploy workflows to require the Cloud Run variables above, then run:

```bash
python3 scripts/verify_release_infra.py
```

The active verifier currently checks Railway configuration.
