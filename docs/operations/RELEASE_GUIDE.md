# Stargate Release Engineering Guide

## The Golden Rules

1. **Never ship on Friday** - If it breaks, you debug on Saturday
2. **Deploy ≠ Release** - Code on server vs. users see it
3. **Always backward compatible** - Old clients must keep working
4. **Rollback plan first** - Know how to undo before you do

---

## Version Strategy

We use **semantic versioning**: `MAJOR.MINOR.PATCH`

```
v1.4.2
│ │ │
│ │ └─ PATCH: Bug fixes, no API changes
│ └─── MINOR: New capabilities, backward compatible
└───── MAJOR: Breaking changes, clients must update
```

### When to Bump What

| Change | Version Bump | Example |
|--------|--------------|---------|
| Fix a bug | PATCH | Token refresh timing fix |
| Add new capability | MINOR | `vendor.bulk_create` added |
| Add optional parameter | MINOR | `include_metadata` param |
| Remove capability | MAJOR | Delete `legacy.endpoint` |
| Change response format | MAJOR | Rename `error_code` to `code` |
| New required parameter | MAJOR | `session_id` now required |

### Pre-1.0 Versioning

We're currently at **0.9.0** (pre-release). In this phase:
- PATCH bumps (0.9.0 → 0.9.1) for bug fixes
- MINOR bumps (0.9.x → 0.10.0) for new features
- **1.0.0** when: production validated, API stable, docs complete

### Version in Code

The version lives in `app/main.py`:

```python
VERSION = "0.9.0"

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": VERSION,
        "capabilities_count": len(CAPABILITY_REGISTRY),
    }
```

**Always update VERSION when releasing.**

---

## Branching Strategy

We use **trunk-based development**. Keep it simple.

```
main ─────●─────●─────●─────●─────●───▶  (always deployable)
           \   /       \   /
            ●─●         ●─●
         feature/x   fix/y
         (< 2 days)  (< 1 day)
```

### Rules

1. **`main` is always deployable** - Never merge broken code
2. **Feature branches live < 2 days** - Small PRs, fast merges
3. **Every merge triggers staging deploy** - Automatic via Railway
4. **Production deploys are manual** - Human decides when

### Branch Naming

```
feature/add-recurly-connector
fix/token-refresh-race-condition
chore/update-dependencies
docs/add-release-guide
```

---

## Release Types

### Regular Release (Weekly)

Normal feature releases, bug fixes.

```
Monday-Wednesday: Merge PRs to main → auto-deploy staging
Thursday: Staging soak (24h minimum)
Tuesday/Wednesday (next week): Deploy to production
```

**Never rush a regular release.**

### Hotfix Release (Emergency)

Production is broken. Users are affected.

```
1. Create fix on branch from main
2. Minimal testing (does it fix the issue? does health pass?)
3. Merge → deploy to production immediately
4. Full testing AFTER it's live
5. Post-mortem within 48 hours
```

**Hotfixes skip the staging soak. That's the tradeoff.**

### Breaking Release (Coordinated)

API changes that affect Baby MARS.

```
Week 1: Ship Stargate with BOTH old and new API
Week 2: Update Baby MARS to use new API
Week 3: Verify all traffic uses new API
Week 4: Remove old API from Stargate
```

**Never ship breaking changes without coordination.**

---

## Release Checklist

Copy this into your PR or release notes:

```markdown
## Pre-Release

- [ ] All tests pass (`make test`)
- [ ] No new Sentry errors in staging (24h soak)
- [ ] Version bumped in `app/main.py`
- [ ] CHANGELOG.md updated
- [ ] Database migrations tested (if any)
- [ ] Rollback plan documented

## Release (Deploy Order: Stargate → Baby MARS → Aleq)

- [ ] Deploy Stargate
- [ ] Verify: `curl $STARGATE_URL/health` returns new version
- [ ] Verify: `curl -H "X-API-Key: $KEY" $STARGATE_URL/api/v1/capabilities | jq 'keys | length'`
- [ ] Test one capability: `calc.npv` (no external deps)

## Post-Release (30 min monitoring)

- [ ] Sentry: No new errors
- [ ] PostHog: Events flowing normally
- [ ] Railway logs: No unexpected errors
- [ ] Rate limiting: Headers present on responses
- [ ] Close related GitHub issues
```

---

## Database Migrations

**The cardinal rule: Migrations must be reversible.**

### Safe Migration Pattern

```
Phase 1: ADD new column (nullable)
         Deploy code that WRITES to both old and new

Phase 2: BACKFILL old data to new column
         Deploy code that READS from new

Phase 3: REMOVE old column (separate release)
         Clean up code
```

### Example: Renaming a Column

**WRONG (breaks production):**
```sql
ALTER TABLE credentials RENAME COLUMN token TO access_token;
-- Everything breaks instantly
```

**RIGHT (safe rollout):**
```sql
-- Migration 1: Add new column
ALTER TABLE credentials ADD COLUMN access_token TEXT;

-- Code release 1: Write to both
# In Python
cred.access_token = value
cred.token = value  # Keep old column working

-- Migration 2: Backfill (can be slow, no lock)
UPDATE credentials SET access_token = token WHERE access_token IS NULL;

-- Code release 2: Read from new, stop writing old
# Now only use access_token

-- Migration 3: Drop old (weeks later)
ALTER TABLE credentials DROP COLUMN token;
```

### Migration Commands

```bash
# Create migration
alembic revision --autogenerate -m "Add access_token column"

# Run migrations (staging)
alembic upgrade head

# Rollback one step
alembic downgrade -1

# See current state
alembic current
```

**Always test migrations on a copy of production data first.**

---

## Feature Flags

Decouple deployment from release. Ship code hidden, release when ready.

### Simple Implementation

```python
# app/feature_flags.py
import os

FEATURES = {
    "new_billing_engine": os.getenv("FF_NEW_BILLING", "false").lower() == "true",
    "beta_capabilities": os.getenv("FF_BETA_CAPS", "").split(","),
    "rate_limit_v2": os.getenv("FF_RATE_LIMIT_V2", "false").lower() == "true",
}

def is_enabled(feature: str) -> bool:
    return FEATURES.get(feature, False)

def is_capability_beta(capability_key: str) -> bool:
    return capability_key in FEATURES.get("beta_capabilities", [])
```

### Usage

```python
from app.feature_flags import is_enabled

if is_enabled("new_billing_engine"):
    return new_billing_flow(request)
else:
    return legacy_billing_flow(request)
```

### Why This Matters

- **Deploy Friday** (code is hidden behind flag)
- **Release Monday** (flip the flag in Railway env vars)
- **Something breaks?** Flip it back. No redeploy needed.

---

## Multi-Service Coordination

```
Aleq depends on → Baby MARS API
Baby MARS depends on → Stargate API
```

### The Backward Compatibility Rule

**Never ship a breaking change without a transition period.**

```
BAD:
1. Ship Baby MARS that requires Stargate v2 API
2. Stargate is still on v1
3. Everything breaks

GOOD:
1. Ship Stargate that supports BOTH v1 and v2
2. Ship Baby MARS that uses v2
3. Wait 2 weeks, verify no v1 traffic
4. Remove v1 from Stargate
```

### API Versioning

```python
# Stargate endpoints
@router.post("/api/v1/execute")  # Old, deprecated, still works
async def execute_v1(...): ...

@router.post("/api/v2/execute")  # New, Baby MARS uses this
async def execute_v2(...): ...
```

### Deploy Order

When releasing changes that span services:

```
1. Stargate (backend, no dependencies)
2. Baby MARS (depends on Stargate)
3. Aleq (depends on Baby MARS)
```

**Never deploy in reverse order.**

---

## Rollback Procedures

Know these BEFORE you need them.

### Stargate (Railway)

```bash
# Option 1: Railway Dashboard
Railway → Stargate service → Deployments → Click previous → Rollback

# Option 2: Git revert + redeploy
git revert HEAD
git push origin main
# Railway auto-deploys
```

### Database Rollback

```bash
# Rollback last migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade abc123
```

**If migration deleted data, you need backups. This is why migrations should be additive.**

### Emergency Contacts

```
Railway Status: status.railway.app
Sentry Status: status.sentry.io
PostHog Status: status.posthog.com

Internal Escalation:
1. Check #stargate-alerts Slack
2. Page on-call (if configured)
3. Rollback first, debug second
```

---

## Changelog Discipline

Every release updates `CHANGELOG.md`:

```markdown
# Changelog

All notable changes to Stargate are documented here.

## [Unreleased]
### Added
- (next features go here)

## [1.5.0] - 2025-01-28
### Added
- `vendor.bulk_create` capability for batch operations
- Rate limiting headers on all responses (X-RateLimit-*)
- PostHog analytics integration

### Fixed
- Token refresh race condition in QuickBooks connector (#142)
- Bill.com session cache now uses Redis for horizontal scaling

### Changed
- Default request timeout increased to 30s
- Disabled high-risk services: ibkr, schwab, blandai, twilio, hyperbrowser

## [1.4.2] - 2025-01-21
### Fixed
- Sentry error context missing org_id

## [1.4.0] - 2025-01-15
### Added
- FCI (Financial Command Interface) aggregation layer
- 12 Recurly capabilities for subscription billing

### BREAKING
- Removed deprecated `/api/v1/legacy` endpoint
```

### Changelog Rules

1. **Update with every PR** - Don't batch at release time
2. **Group by type** - Added, Fixed, Changed, Removed, BREAKING
3. **Link to issues** - `(#142)` makes debugging easier
4. **Date every release** - `[1.5.0] - 2025-01-28`

---

## Release Cadence

### Weekly Schedule

| Day | Activity |
|-----|----------|
| Monday | Merge PRs, staging auto-deploys |
| Tuesday | Continue merging, staging soaks |
| Wednesday | **Release day** (if staging is healthy) |
| Thursday | Monitor production, address issues |
| Friday | **No deploys.** Documentation, planning only. |

### Monthly Review

First Monday of each month:

- [ ] Review Sentry error trends
- [ ] Clean up stale feature flags
- [ ] Deprecate old API versions (if safe)
- [ ] Update dependencies (`pip-audit`, `safety check`)
- [ ] Review and rotate secrets (if needed)

---

## Incident Response

When production breaks:

```
1. ACKNOWLEDGE - "I'm looking at this"
2. ASSESS - Is it affecting users? How many?
3. MITIGATE - Rollback, feature flag off, or hotfix
4. COMMUNICATE - Update #stargate-alerts
5. RESOLVE - Fix the root cause
6. POSTMORTEM - Document what happened (within 48h)
```

### Severity Levels

| Level | Definition | Response Time |
|-------|------------|---------------|
| SEV1 | All users affected, data loss possible | Immediate, all hands |
| SEV2 | Major feature broken, workaround exists | < 1 hour |
| SEV3 | Minor feature broken, low impact | < 24 hours |
| SEV4 | Cosmetic, no user impact | Next sprint |

---

## Quick Reference

### Commands

```bash
# Run tests
make test

# Check current version
curl $STARGATE_URL/health | jq .version

# Deploy to staging (automatic on merge)
git push origin main

# Deploy to production (Railway)
# Manual: Railway dashboard → Deploy

# Rollback
# Railway dashboard → Deployments → Previous → Rollback

# Check capabilities count
curl -H "X-API-Key: $KEY" $STARGATE_URL/api/v1/capabilities | jq 'keys | length'
```

### Files to Update on Release

```
app/main.py          # VERSION constant
CHANGELOG.md         # What changed
docs/operations/RELEASE_GUIDE.md  # If process changed
```

### Don't Forget

- [ ] Bump VERSION in `app/main.py`
- [ ] Update CHANGELOG.md
- [ ] Verify staging health (24h soak)
- [ ] Post-release monitoring (30 min)
- [ ] Never ship on Friday

---

## Maturity Ladder

Where we are → Where we're going:

```
Level 1: "We can deploy"
         ✓ Done

Level 2: "We have a release process"  ← YOU ARE HERE (v0.9.0)
         Changelogs, version numbers, checklists

Level 3: "We can release without fear" → TARGET FOR v1.0
         Feature flags, staged rollouts, instant rollback

Level 4: "Releases are boring"
         Ship 10x/day, monitoring catches everything
```

### Path to v1.0.0

- [ ] Production deployment validated (real traffic)
- [ ] All connectors tested end-to-end with real credentials
- [ ] Sentry + PostHog verified in production
- [ ] Rate limiting tuned based on actual usage
- [ ] API stable (no breaking changes planned)
- [ ] Documentation complete

---

*Last updated: January 2025*
