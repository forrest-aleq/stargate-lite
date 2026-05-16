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

The gate requires everything from promotion mode, plus:

- the target commit is contained in `origin/main`

That prevents a production deploy from a direct branch, local SHA, tag, or hotfix
that was not first present on staging.

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
- `.github/workflows/deploy-production.yml` runs the production gate before
  Railway readiness checks and deployment.
