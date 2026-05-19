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
- `scripts/verify_release_infra.py` checks GitHub environment secrets/variables,
  branch protection, and Railway runtime variables without printing secret
  values:

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
- required conversation resolution enabled

## Required Deployment Configuration

The `staging` GitHub environment must contain:

- secrets: `RAILWAY_TOKEN_STAGING`, `STAGING_API_KEY`
- variables: `RAILWAY_SERVICE_NAME`, `RAILWAY_STAGING_ENVIRONMENT`,
  `STAGING_MIN_CAPABILITIES`, `STAGING_URL`

The `production` GitHub environment must contain:

- secrets: `RAILWAY_TOKEN_PRODUCTION`, `PRODUCTION_API_KEY`
- variables: `PRODUCTION_URL`, `RAILWAY_PRODUCTION_ENVIRONMENT`,
  `RAILWAY_SERVICE_NAME`

Railway `staging` and `production` must both contain core runtime variables:
`API_SECRET_KEY`, `DATABASE_URL`, `ENABLED_SERVICES`, `ENCRYPTION_KEY`,
`ENVIRONMENT`, and `REDIS_URL`.
