# Release Controls

Stargate Lite production releases must come through staging. The release gate in
`scripts/release_gate.py` enforces that rule in source control.

## Individual Service Gate

Promotion mode is used before opening or updating a staging-to-main PR:

```bash
python3 scripts/release_gate.py --mode promotion --target-ref origin/staging
```

The gate requires:

- `origin/main` is an ancestor of `origin/staging`
- the target commit is contained in `origin/staging`

Production mode is used before deploying:

```bash
python3 scripts/release_gate.py --mode production --target-ref origin/main
```

The gate requires:

- the target commit is contained in `origin/main`
- the target commit is contained in `origin/staging`, or its Git tree exactly
  matches the staged tree if GitHub created a merge or squash commit on `main`

That prevents a production deploy from a direct branch, local SHA, tag, or hotfix
whose content was not first present on staging.

## Coordinated Stack Gate

When Stargate Lite is released together with Baby MARS, the product repo owns a
stack lock file. Run the Stargate gate with the lock:

```bash
python3 scripts/release_gate.py \
  --mode production \
  --target-ref origin/main \
  --stack-lock ../Aleq/release/stack-lock.json
```

The locked SHA must match the Stargate Lite target exactly. This gives auditors
and operators one artifact that says which M1 and S1 commits were released as a
tested unit.

## CI Enforcement

- `.github/workflows/promote-staging.yml` runs the promotion gate before creating
  the staging-to-main PR.
- `.github/workflows/deploy-production.yml` runs the production gate, then runs
  staging preflight under the `staging` GitHub environment and production
  preflight/deploy under the `production` GitHub environment. This is required
  because deploy secrets and variables are environment-scoped.
- `.github/workflows/ci.yml` runs PR checks for both `main` and `staging`, so
  both protected branches can require the same CI contexts.
- `scripts/verify_release_infra.py` checks GitHub environment secrets/variables
  and branch protection without printing secret values. Runtime secrets live in
  GCP Secret Manager and are attached through `GCP_CLOUD_RUN_SECRETS`:

```bash
python3 scripts/verify_release_infra.py
```

## Required Branch Controls

`staging` and `main` must be protected in GitHub:

- force pushes disabled
- branch deletion disabled
- admins included
- PRs required before merge
- zero required approving reviews
- stale approvals dismissed
- required checks enabled: `Lint & Type Check`, `Tests`, `Security Scan`, and
  `Build Check`
- required linear history enabled
- required conversation resolution disabled

## Required Deployment Configuration

The `staging` GitHub environment must contain:

- secrets: `STAGING_API_KEY`
- variables: `GCP_PROJECT_ID`, `GCP_REGION`, `GCP_WORKLOAD_IDENTITY_PROVIDER`,
  `GCP_SERVICE_ACCOUNT`, `GCP_ARTIFACT_REGISTRY_LOCATION`,
  `GCP_ARTIFACT_REGISTRY_REPOSITORY`, `GCP_CLOUD_RUN_SERVICE`,
  `GCP_CLOUD_RUN_SECRETS`, `STAGING_MIN_CAPABILITIES`, `STAGING_URL`

The `production` GitHub environment must contain:

- secrets: `PRODUCTION_API_KEY`
- variables: `GCP_PROJECT_ID`, `GCP_REGION`, `GCP_WORKLOAD_IDENTITY_PROVIDER`,
  `GCP_SERVICE_ACCOUNT`, `GCP_ARTIFACT_REGISTRY_LOCATION`,
  `GCP_ARTIFACT_REGISTRY_REPOSITORY`, `GCP_CLOUD_RUN_SERVICE`,
  `GCP_CLOUD_RUN_SECRETS`, `PRODUCTION_URL`

`GCP_CLOUD_RUN_SECRETS` is passed to `gcloud run deploy --set-secrets`; it must
include the runtime values Stargate needs, including `API_SECRET_KEY`,
`DATABASE_URL`, `ENABLED_SERVICES`, `ENCRYPTION_KEY`, and `REDIS_URL`.
