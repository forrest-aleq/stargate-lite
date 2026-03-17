# Aleq Production Deployment Guide

For day-2 promotions of Stargate from staging to production, follow
`docs/operations/PRODUCTION_PROMOTION.md`.

## Your System Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Browser   │────▶│    Aleq     │────▶│  Baby MARS  │
│   (User)    │     │  (Vercel)   │     │  (Railway)  │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │  Stargate   │
                                        │  (Railway)  │
                                        └─────────────┘
```

**Data flows ONE direction:** Browser → Aleq → Baby MARS → Stargate

---

## The Mental Model

Think of it like this:
- **Aleq** is the receptionist. It talks to users and passes messages to Baby MARS.
- **Baby MARS** is the brain. It processes requests and calls Stargate when it needs data.
- **Stargate** is the vault. It has the actual financial data.

Each service needs to know the URL of the service it talks to. That's it. That's the whole thing.

---

## Order of Operations

**Deploy bottom-up.** The service that nothing depends on goes first.

```
1. Stargate    (nothing depends on it being up first)
2. Baby MARS   (needs Stargate URL)
3. Aleq        (needs Baby MARS URL)
```

Why this order? Because when Baby MARS starts, it needs to know where Stargate is. When Aleq starts, it needs to know where Baby MARS is. If you deploy top-down, your services will start up pointing at URLs that don't exist yet.

---

## Step 1: Deploy Stargate to Railway

### What you need before starting:
- Railway account
- Stargate code in a GitHub repo
- OAuth credentials for all services you want to enable

### Do this:
1. Go to Railway dashboard → New Project → Deploy from GitHub repo
2. Select your Stargate repo
3. Railway will auto-detect it's Python and set up the build
4. **Add a Redis service** (New → Database → Redis) - required for rate limiting and session caching
5. **Add a PostgreSQL service** (New → Database → PostgreSQL) - or use external DB
6. **Add these environment variables** (Settings → Variables):

```
# ===========================================
# SECURITY (CRITICAL - generate strong values)
# ===========================================
API_SECRET_KEY=<generate-strong-random-string-64-chars>
ENCRYPTION_KEY=<your-fernet-key-from-setup.sh>

# ===========================================
# DATABASE & REDIS
# ===========================================
DATABASE_URL=${{Postgres.DATABASE_URL}}   # Railway reference
REDIS_URL=${{Redis.REDIS_URL}}            # Railway reference

# ===========================================
# ERROR TRACKING & ANALYTICS
# ===========================================
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
SENTRY_ENVIRONMENT=production
POSTHOG_API_KEY=phc_xxx
POSTHOG_HOST=https://us.i.posthog.com

# ===========================================
# RATE LIMITING (optional, defaults shown)
# ===========================================
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60

# ===========================================
# OAUTH SERVICES - Add all you need
# ===========================================
# QuickBooks
QUICKBOOKS_CLIENT_ID=ABxxx
QUICKBOOKS_CLIENT_SECRET=xxx

# HubSpot
HUBSPOT_CLIENT_ID=xxx
HUBSPOT_CLIENT_SECRET=xxx

# Xero
XERO_CLIENT_ID=xxx
XERO_CLIENT_SECRET=xxx

# Google (Gmail, Calendar)
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx

# Slack
SLACK_CLIENT_ID=xxx
SLACK_CLIENT_SECRET=xxx

# Bill.com
BILLCOM_DEV_KEY=xxx
BILLCOM_ENVIRONMENT=production

# Stripe (API key, not OAuth)
STRIPE_SECRET_KEY=sk_live_xxx

# NetSuite (Token-based auth)
NETSUITE_ACCOUNT_ID=xxx
NETSUITE_CONSUMER_KEY=xxx
NETSUITE_CONSUMER_SECRET=xxx

# Sage Intacct
SAGE_INTACCT_SENDER_ID=xxx
SAGE_INTACCT_SENDER_PASSWORD=xxx

# Gusto
GUSTO_CLIENT_ID=xxx
GUSTO_CLIENT_SECRET=xxx
GUSTO_USE_DEMO=false

# Shopify
SHOPIFY_CLIENT_ID=xxx
SHOPIFY_CLIENT_SECRET=xxx

# Square
SQUARE_APPLICATION_ID=xxx
SQUARE_APPLICATION_SECRET=xxx
SQUARE_USE_SANDBOX=false

# DocuSign
DOCUSIGN_INTEGRATION_KEY=xxx
DOCUSIGN_SECRET_KEY=xxx
DOCUSIGN_USE_DEMO=false

# Airtable
AIRTABLE_CLIENT_ID=xxx
AIRTABLE_CLIENT_SECRET=xxx

# Cognitive Utilities
ANTHROPIC_API_KEY=sk-ant-xxx
TAVILY_API_KEY=tvly-xxx
```

7. Deploy. Wait for green checkmark.
8. **Copy the Railway URL** - it looks like: `https://stargate-production-xxxx.up.railway.app`
9. **Save your API_SECRET_KEY** - Baby MARS needs this exact value

### Verify it works:
```bash
# Health check (no auth required)
curl https://stargate-production-xxxx.up.railway.app/health
# Should return {"status": "healthy", "version": "..."}

# Verify capabilities loaded (requires auth)
curl -H "X-API-Key: YOUR_API_SECRET_KEY" \
  https://stargate-production-xxxx.up.railway.app/api/v1/capabilities | jq 'keys | length'
# Should return: 614 (or similar)

# Test a capability (no external API needed)
curl -X POST https://stargate-production-xxxx.up.railway.app/api/v1/execute \
  -H "X-API-Key: YOUR_API_SECRET_KEY" \
  -H "Content-Type: application/json" \
  -d '{"capability_key": "calc.npv", "org_id": "test", "user_id": "test", "turn_id": "deploy-test-1", "args": {"rate": 0.1, "cash_flows": [-1000, 300, 300, 300, 300]}}'
# Should return NPV calculation result
```

**Don't move on until all three checks pass.**

---

## Step 2: Deploy Baby MARS to Railway

### What you need:
- Baby MARS code in GitHub repo
- Stargate URL from Step 1
- **Stargate API_SECRET_KEY from Step 1** (CRITICAL)

### Do this:
1. Railway dashboard → New Project → Deploy from GitHub repo
2. Select Baby MARS repo
3. **Add these environment variables**:

```
# ===========================================
# STARGATE CONNECTION (CRITICAL)
# ===========================================
STARGATE_URL=https://stargate-production-xxxx.up.railway.app
STARGATE_API_KEY=<same-API_SECRET_KEY-from-Stargate>

# ===========================================
# DATABASE
# ===========================================
DATABASE_URL=postgresql://user:pass@host:5432/dbname
# If using Supabase, set DATABASE_URL to the project's Postgres connection string.

# ===========================================
# AI PROVIDER
# ===========================================
ANTHROPIC_API_KEY=sk-ant-...
# OR
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_KEY=...

# ===========================================
# ANALYTICS (for session correlation)
# ===========================================
POSTHOG_API_KEY=phc_xxx
POSTHOG_HOST=https://us.i.posthog.com

# ===========================================
# ENVIRONMENT
# ===========================================
ENVIRONMENT=staging
LOG_LEVEL=info
```

4. Deploy. Wait for green.
5. **Copy the Railway URL**: `https://baby-mars-production-xxxx.up.railway.app`

### How Baby MARS calls Stargate:
Baby MARS must send the API key in the `X-API-Key` header:
```python
response = httpx.post(
    f"{STARGATE_URL}/api/v1/execute",
    headers={
        "X-API-Key": STARGATE_API_KEY,      # Required for auth
        "X-Session-ID": session_id,          # For PostHog correlation
        "Content-Type": "application/json",
    },
    json={
        "capability_key": "vendor.create",
        "org_id": org_id,
        "user_id": user_id,
        "turn_id": turn_id,
        "args": {...}
    }
)
```

### Verify it works:
```bash
# Health check
curl https://baby-mars-production-xxxx.up.railway.app/health

# Test birth endpoint (should work without auth for health check)
curl -X POST https://baby-mars-production-xxxx.up.railway.app/birth \
  -H "Content-Type: application/json" \
  -d '{"person_id":"test","name":"Test","email":"test@test.com","org_id":"test-org","org_name":"Test"}'
```

**Don't move on until this works.**

---

## Step 3: Deploy Aleq to Vercel

### What you need:
- Aleq code in GitHub repo
- Baby MARS URL from Step 2
- Supabase project (for auth)

### Do this:
1. Go to vercel.com → Add New Project → Import your Aleq repo
2. Vercel auto-detects Next.js
3. **Add these environment variables** (Settings → Environment Variables):

```
# Baby MARS connection (the URL you copied in Step 2)
BABY_MARS_URL=https://baby-mars-production-xxxx.up.railway.app

# Supabase Auth
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# AI SDK (for any direct AI calls from frontend API routes)
AZURE_FOUNDRY_RESOURCE_NAME=your-resource
AZURE_FOUNDRY_API_KEY=...
AZURE_FOUNDRY_DEPLOYMENT_NAME=claude-sonnet

# Optional: Analytics
NEXT_PUBLIC_POSTHOG_KEY=phc_...
NEXT_PUBLIC_POSTHOG_HOST=https://app.posthog.com

# Rate Limiting (Upstash)
UPSTASH_REDIS_REST_URL=https://...
UPSTASH_REDIS_REST_TOKEN=...
```

4. Deploy. Wait for green.
5. Your URL is: `https://aleq-xxx.vercel.app` (or your custom domain)

### Verify it works:
1. Open the URL in browser
2. You should see the login page
3. Login with Google/Microsoft
4. You should see the dashboard with the terminal
5. Type "hello" - you should get a response from Baby MARS

---

## Common Fuckups and How to Avoid Them

### 1. "Connection refused" or "ECONNREFUSED"
**Cause:** Service A is trying to talk to Service B, but the URL is wrong or Service B isn't running.

**Fix:**
- Check the URL in your env vars. Is it exactly right? No trailing slash?
- Is the target service actually deployed and running?
- Check Railway/Vercel logs for the actual error.

### 2. "CORS error" in browser console
**Cause:** Baby MARS isn't allowing requests from your Aleq domain.

**Fix:** Add CORS configuration to Baby MARS:
```python
# In Baby MARS, allow your Aleq domain
ALLOWED_ORIGINS = [
    "https://aleq-xxx.vercel.app",
    "https://yourdomain.com",
    "http://localhost:3000",  # for local dev
]
```

### 3. "Unauthorized" or 401 errors
**Cause:** Auth tokens aren't being passed correctly between services.

**Fix:** Check that:
- Supabase keys are correct (not swapped)
- Service role key is used for server-side operations
- Anon key is used for client-side

### 4. Environment variables not updating
**Cause:** You changed env vars but the old values are cached.

**Fix:**
- Vercel: Redeploy after changing env vars
- Railway: Should auto-redeploy, but you can trigger manual redeploy

### 5. "Module not found" or build errors
**Cause:** Dependencies missing or wrong Node/Python version.

**Fix:**
- Check that `package.json` / `requirements.txt` has all deps
- Set explicit runtime versions in Railway/Vercel settings

---

## The Staging → Production Flow

### Staging Environment
Use this for testing. Safe to break.

```
Stargate Staging:  https://stargate-staging-xxx.up.railway.app
Baby MARS Staging: https://baby-mars-staging-xxx.up.railway.app
Aleq Staging:      https://aleq-staging.vercel.app
```

### Production Environment
This is what customers use. Don't break.

```
Stargate Prod:  https://stargate-prod-xxx.up.railway.app
Baby MARS Prod: https://baby-mars-prod-xxx.up.railway.app
Aleq Prod:      https://app.aleq.ai (your domain)
```

### How to set up both:

**Railway:** Create two separate projects, or use Railway's environment feature.

**Vercel:**
- Use Preview deployments for staging (every PR gets a preview URL)
- Production deployment is whichever branch Vercel is configured to treat as Production
- Set different env vars per environment (Settings → Environment Variables → select "Production" or "Preview")

---

## Pre-Launch Checklist

### 1. Security
- [ ] All API keys are in env vars, not in code
- [ ] HTTPS everywhere (Railway and Vercel do this automatically)
- [ ] CORS configured to only allow your domains
- [ ] Rate limiting enabled (Stargate has built-in rate limiting)
- [ ] Supabase RLS policies are set up
- [ ] Stargate `API_SECRET_KEY` is strong (64+ chars)
- [ ] Stargate `ENCRYPTION_KEY` is set (Fernet key)
- [ ] Baby MARS `STARGATE_API_KEY` matches Stargate's `API_SECRET_KEY`

### 2. Monitoring
- [ ] Sentry configured for all three services (Aleq, Baby MARS, Stargate)
- [ ] PostHog configured for session correlation across stack
- [ ] Can you see logs? (Railway logs, Vercel logs)
- [ ] Health check endpoints work for all services
- [ ] Stargate capabilities count is correct (~614)

### 3. Database & Redis
- [ ] Database backups enabled
- [ ] Migrations have been run
- [ ] Redis provisioned for Stargate (rate limiting, sessions)
- [ ] Test user can sign up and use the app

### 4. DNS/Domain (if using custom domain)
- [ ] Domain DNS points to Vercel
- [ ] SSL certificate is active (Vercel handles this)
- [ ] Supabase redirect URLs include your custom domain
- [ ] OAuth redirect URIs updated for all services (QuickBooks, HubSpot, etc.)

---

## Debugging Workflow

When something doesn't work:

```
1. Check the browser console (F12)
   → Network tab shows failed requests
   → Console tab shows JS errors

2. Check Vercel logs (Vercel dashboard → your project → Logs)
   → Shows API route errors
   → Shows server-side rendering errors

3. Check Railway logs (Railway dashboard → your service → Logs)
   → Shows Baby MARS / Stargate errors
   → Shows startup failures

4. Test the chain manually:
   curl Stargate health → works?
   curl Baby MARS health → works?
   curl Baby MARS birth → works?
   Browser loads Aleq → works?
   Browser login → works?
   Browser send message → works?
```

Find where the chain breaks. Fix that link. Move on.

---

## How Services Authenticate

Understanding this is CRITICAL. If you get it wrong, you'll get 401 errors.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        API KEY FLOW                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Baby MARS                              Stargate                           │
│   ┌─────────────────┐                   ┌─────────────────┐                │
│   │ STARGATE_API_KEY│ ═══════════════▶  │ API_SECRET_KEY  │                │
│   │ = "abc123..."   │   X-API-Key:      │ = "abc123..."   │                │
│   └─────────────────┘   "abc123..."     └─────────────────┘                │
│                                                                             │
│   THESE MUST BE THE SAME VALUE                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

1. **You generate ONE secret** (64+ characters, random)
2. **Put it in Stargate** as `API_SECRET_KEY`
3. **Put the SAME value in Baby MARS** as `STARGATE_API_KEY`
4. **Baby MARS sends it** in the `X-API-Key` header on every request

That's it. If they don't match, you get 401.

---

## Post-Deploy Monitoring

### Sentry (Error Tracking)
1. Go to sentry.io → Your Stargate Project → Issues
2. Filter by `environment:production`
3. After deploy, you should see 0 new errors
4. Set up alerts: Settings → Alerts → "When a new issue is seen"

**What to watch for:**
- `CredentialMissingError` - Customer hasn't connected OAuth yet (expected)
- `CredentialInvalidError` - Token expired, needs re-auth
- `ExternalAPIError` - Third-party API issue
- `RateLimitError` - Customer hitting rate limits

### PostHog (Analytics)
1. Go to PostHog → Events
2. Filter by `$lib = stargate-lite`
3. You'll see events: `capability_called`, `connector_error`, `token_refreshed`, `fci_aggregation`
4. Session correlation: Filter by `session_id` to see full request flow across Baby MARS → Stargate

### Railway Logs
1. Railway dashboard → Stargate service → Logs
2. Logs are structured JSON (easy to filter)
3. Key `log_event` values to search:
   - `execute_start` / `execute_success` - normal request flow
   - `token_refresh_success` / `token_refresh_error` - OAuth issues
   - `rate_limit_rejected` - abuse detection
   - `session_create_success` - Bill.com session creation

### Rate Limit Headers
Every response from Stargate includes:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 97
X-RateLimit-Reset: 1706123456
```

If a request is rate limited, it returns 429 with `Retry-After` header.

---

## Quick Reference: All Environment Variables

### Aleq (Vercel)
```
BABY_MARS_URL=https://baby-mars-xxx.up.railway.app
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
AZURE_FOUNDRY_RESOURCE_NAME=...
AZURE_FOUNDRY_API_KEY=...
AZURE_FOUNDRY_DEPLOYMENT_NAME=...
UPSTASH_REDIS_REST_URL=...
UPSTASH_REDIS_REST_TOKEN=...
NEXT_PUBLIC_POSTHOG_KEY=...
SENTRY_DSN=...
```

### Baby MARS (Railway)
```
STARGATE_URL=https://stargate-xxx.up.railway.app
STARGATE_API_KEY=<same-as-Stargate-API_SECRET_KEY>  # CRITICAL
DATABASE_URL=<postgres connection string>  # Use the Supabase Postgres URL if Supabase backs this service
ANTHROPIC_API_KEY=... or AZURE_* keys
POSTHOG_API_KEY=...
ENVIRONMENT=staging|production
LOG_LEVEL=info
```

### Stargate (Railway)
```
# Security
API_SECRET_KEY=<strong-64-char-secret>
ENCRYPTION_KEY=<fernet-key>

# Database & Redis
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}

# Monitoring
SENTRY_DSN=https://xxx@sentry.io/xxx
SENTRY_ENVIRONMENT=production
POSTHOG_API_KEY=phc_xxx

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60

# OAuth Services (all that you need)
QUICKBOOKS_CLIENT_ID=...
QUICKBOOKS_CLIENT_SECRET=...
HUBSPOT_CLIENT_ID=...
HUBSPOT_CLIENT_SECRET=...
# ... (see Step 1 for full list)
```

---

## You Got This

The whole thing is just:
1. Deploy services in order (bottom-up)
2. Give each service the URL of the service it talks to
3. Verify each step before moving on
4. When something breaks, find which link in the chain failed

That's it. Everything else is details.
