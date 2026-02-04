# MAP Observability & Health Monitoring Plan

## Overview

MAP needs comprehensive observability to ensure reliability across all external integrations. This covers credential health, platform connectivity, bot provisioning status, schema mapping effectiveness, and real-time diagnostics.

---

## What Gets Monitored

### Layer 1: Platform Connectors

**Credential Health:**
- Valid credentials per platform per org
- Token expiry status (expired, expiring soon <24hrs, healthy)
- Last successful OAuth refresh
- Authentication failure count
- Credential mode distribution (impersonation vs bot_user)

**API Connectivity:**
- Last successful API call timestamp per platform
- API error rate (24hr rolling window)
- Response time percentiles (p50, p95, p99)
- Rate limit status (current usage vs limit)
- Platform-specific outages detected

**Coverage:**
- Configured platforms (credentials exist)
- Active platforms (used in last 7 days)
- Dormant platforms (configured but unused)

### Layer 2: Schema Mapping

**Translation Success:**
- Successful mappings per platform (24hr count)
- Failed mappings (unmapped fields logged)
- Universal field → platform field coverage matrix

**Field Support Matrix:**
```
| Universal Field | ClickUp | Linear | Monday | Asana | Jira | Trello |
|-----------------|---------|--------|--------|-------|------|--------|
| priority        | ✅      | ✅     | ✅     | ✅    | ✅   | ❌     |
| status          | ✅      | ✅     | ✅     | ✅    | ✅   | ⚠️*   |
| assignee        | ✅      | ✅     | ✅     | ✅    | ✅   | ✅     |
| due_date        | ✅      | ✅     | ✅     | ✅    | ✅   | ✅     |

* = Partial support (Trello status = column position)
```

**Routing Health:**
- Workspace → platform routing success rate
- Ambiguous routing failures
- Missing workspace mapping errors

### Layer 3: Identity Polyfill

**Mode Distribution:**
- Orgs using impersonation mode vs bot_user mode
- Per-platform mode breakdown
- Mode preference trends

**Convention Detection:**
- @mention detection count (webhooks processed)
- Assignment detection via tags (#aleq)
- Signature injection success rate
- False positive rate (non-Aleq items detected as Aleq)

**Polyfill Effectiveness:**
- Correctly identified Aleq assignments
- Missed assignments (false negatives)
- User satisfaction indicator (manual override rate)

### Layer 4: Bot Provisioning

**Provisioning Status:**
- Total orgs with bot identity created
- Bot email per org
- Provisioning completion percentage per org
- Platforms linked per bot identity

**Setup Progress Tracking:**
```
Org: dockwa (aleq@dockwa.com)
├─ ✅ Gmail setup complete
├─ ✅ ClickUp linked (bot user created)
├─ ✅ Linear linked (actor=app)
├─ ⏳ Monday pending (invitation sent)
├─ ❌ Slack not started
└─ 60% complete (3/5 platforms)
```

**Bot User Health:**
- Bot credentials still valid
- Bot user still exists in platform (not deleted)
- Bot user permissions intact (can create tasks, send emails, etc.)
- Last successful action as bot user

### Cross-Layer System Health

**End-to-End Success:**
- MIND request → Stargate execution success rate
- Average latency per domain (task, email, calendar, etc.)
- Error distribution by layer (Layer 1 vs 2 vs 3 vs 4)

**Integration Reliability Score:**
```
Overall: 98.5% (Healthy)
├─ ClickUp: 99.2% ✅
├─ Linear: 99.8% ✅
├─ Monday: 97.1% ✅
├─ Gmail: 99.9% ✅
├─ Sheets: 95.3% ⚠️ (degraded)
└─ QuickBooks: 89.2% 🔴 (critical - auth issues)
```

---

## Health Endpoints

### 1. Overall MAP Health
**`GET /health/map`**

Returns summary of all MAP layers with overall health score.

**Response:**
```json
{
  "status": "healthy",
  "health_score": 98.5,
  "layers": {
    "connectors": {
      "status": "healthy",
      "platforms_total": 13,
      "platforms_healthy": 12,
      "platforms_degraded": 1,
      "platforms_down": 0
    },
    "schema_mapping": {
      "status": "healthy",
      "mapping_success_rate": 99.1,
      "unsupported_fields_24h": 23
    },
    "identity_polyfill": {
      "status": "healthy",
      "orgs_using_polyfill": 45,
      "orgs_using_bot_mode": 12,
      "detection_accuracy": 97.8
    },
    "bot_provisioning": {
      "status": "healthy",
      "total_bots": 12,
      "fully_provisioned": 8,
      "partially_provisioned": 4
    }
  },
  "critical_issues": [],
  "warnings": [
    {
      "type": "credential_expiring",
      "platform": "quickbooks",
      "org_id": "org_456",
      "expires_in_hours": 18
    }
  ]
}
```

### 2. Platform Health
**`GET /health/map/platforms`**

Lists all platforms with health status.

**Response:**
```json
{
  "platforms": [
    {
      "name": "clickup",
      "status": "healthy",
      "credentials_count": 23,
      "credentials_valid": 23,
      "last_successful_call": "2025-11-22T10:45:23Z",
      "error_rate_24h": 0.012,
      "avg_latency_ms": 245,
      "rate_limit_status": {
        "current": 1234,
        "limit": 10000,
        "reset_at": "2025-11-23T00:00:00Z"
      }
    },
    {
      "name": "quickbooks",
      "status": "degraded",
      "credentials_count": 15,
      "credentials_valid": 12,
      "credentials_expired": 3,
      "last_successful_call": "2025-11-22T09:15:00Z",
      "error_rate_24h": 0.089,
      "avg_latency_ms": 1850
    }
  ]
}
```

**`GET /health/map/platforms/{platform}`**

Detailed health for specific platform.

**Response:**
```json
{
  "platform": "clickup",
  "status": "healthy",
  "credentials": {
    "total": 23,
    "valid": 23,
    "expired": 0,
    "expiring_soon": 1,
    "mode_distribution": {
      "impersonation": 18,
      "bot_user": 5
    }
  },
  "api_health": {
    "last_successful_call": "2025-11-22T10:45:23Z",
    "uptime_24h": 99.98,
    "error_rate_24h": 0.012,
    "total_calls_24h": 8234,
    "failed_calls_24h": 99,
    "avg_latency_ms": 245,
    "p95_latency_ms": 420,
    "p99_latency_ms": 680
  },
  "rate_limits": {
    "current": 1234,
    "limit": 10000,
    "percentage_used": 12.34,
    "reset_at": "2025-11-23T00:00:00Z"
  },
  "recent_errors": [
    {
      "timestamp": "2025-11-22T10:30:15Z",
      "error_type": "rate_limit",
      "org_id": "org_123",
      "resolved": true
    }
  ]
}
```

### 3. Credential Health
**`GET /health/map/credentials`**

All credentials across all orgs and platforms.

**Query Params:**
- `status=expired|expiring|valid` - Filter by status
- `platform=clickup` - Filter by platform
- `org_id=org_123` - Filter by org

**Response:**
```json
{
  "total_credentials": 245,
  "valid": 238,
  "expired": 2,
  "expiring_soon": 5,
  "credentials": [
    {
      "org_id": "org_123",
      "user_id": "user_456",
      "platform": "clickup",
      "credential_type": "customer",
      "credential_mode": "impersonation",
      "status": "valid",
      "expires_at": "2025-12-15T14:30:00Z",
      "last_refreshed": "2025-11-15T14:30:00Z",
      "last_used": "2025-11-22T10:30:00Z"
    },
    {
      "org_id": "org_456",
      "user_id": "ALEQ_AGENT",
      "platform": "linear",
      "credential_type": "agent",
      "credential_mode": "bot_user",
      "bot_email": "aleq@dockwa.com",
      "status": "expiring_soon",
      "expires_at": "2025-11-23T08:00:00Z",
      "hours_until_expiry": 18
    }
  ]
}
```

**`GET /health/map/credentials/{org_id}`**

Org-specific credential health.

### 4. Bot Provisioning Status
**`GET /health/map/bot-provisioning`**

All orgs with bot setup status.

**Response:**
```json
{
  "total_orgs": 57,
  "orgs_with_bot": 12,
  "bots": [
    {
      "org_id": "org_dockwa",
      "bot_email": "aleq@dockwa.com",
      "bot_name": "Aleq AI",
      "provisioning_started": "2025-11-20T14:00:00Z",
      "provisioning_completed": "2025-11-20T16:30:00Z",
      "completion_percentage": 80,
      "platforms_linked": [
        {
          "platform": "gmail",
          "status": "complete",
          "linked_at": "2025-11-20T14:15:00Z",
          "credential_valid": true
        },
        {
          "platform": "clickup",
          "status": "complete",
          "linked_at": "2025-11-20T15:00:00Z",
          "credential_valid": true
        },
        {
          "platform": "linear",
          "status": "complete",
          "linked_at": "2025-11-20T15:30:00Z",
          "credential_valid": true
        },
        {
          "platform": "monday",
          "status": "complete",
          "linked_at": "2025-11-20T16:00:00Z",
          "credential_valid": true
        }
      ],
      "platforms_pending": [
        {
          "platform": "slack",
          "status": "not_started",
          "next_step": "Invite aleq@dockwa.com to Slack workspace"
        }
      ]
    }
  ]
}
```

**`GET /health/map/bot-provisioning/{org_id}`**

Specific org bot status with setup instructions.

**Response:**
```json
{
  "org_id": "org_dockwa",
  "bot_email": "aleq@dockwa.com",
  "bot_name": "Aleq AI",
  "completion_percentage": 80,
  "platforms_linked": ["gmail", "clickup", "linear", "monday"],
  "platforms_pending": ["slack"],
  "next_steps": [
    {
      "platform": "slack",
      "instructions": [
        "1. Go to Slack workspace settings",
        "2. Invite aleq@dockwa.com",
        "3. Bot will accept via Gmail inbox",
        "4. Generate Slack API token",
        "5. Paste token in Stargate"
      ],
      "estimated_time_minutes": 5
    }
  ],
  "health_check": {
    "all_platforms_healthy": false,
    "issues": []
  }
}
```

### 5. Schema Mapping Metrics
**`GET /health/map/schema`**

Field coverage matrix and mapping stats.

**Response:**
```json
{
  "universal_fields": {
    "task": {
      "title": {
        "supported_platforms": ["clickup", "linear", "monday", "asana", "jira", "trello"],
        "unsupported_platforms": [],
        "coverage_percentage": 100
      },
      "priority": {
        "supported_platforms": ["clickup", "linear", "monday", "asana", "jira"],
        "unsupported_platforms": ["trello", "github"],
        "coverage_percentage": 71.4,
        "notes": "Trello has no native priority field"
      },
      "status": {
        "supported_platforms": ["clickup", "linear", "monday", "asana", "jira"],
        "partial_support": ["trello"],
        "coverage_percentage": 85.7,
        "notes": "Trello status mapped to column position"
      }
    }
  },
  "mapping_stats_24h": {
    "total_mappings": 12453,
    "successful": 12342,
    "failed": 111,
    "success_rate": 99.11,
    "unmapped_fields": [
      {
        "universal_field": "sprint",
        "platform": "monday",
        "count": 45,
        "note": "Monday doesn't have native sprint concept"
      }
    ]
  }
}
```

### 6. Layer 3 Polyfill Metrics
**`GET /health/map/polyfill`**

Identity polyfill usage and effectiveness.

**Response:**
```json
{
  "mode_distribution": {
    "total_orgs": 57,
    "impersonation_mode": 45,
    "bot_user_mode": 12,
    "percentage_using_polyfill": 78.9
  },
  "per_platform": {
    "clickup": {
      "impersonation": 18,
      "bot_user": 5,
      "polyfill_usage_percentage": 78.3
    },
    "linear": {
      "impersonation": 0,
      "bot_user": 12,
      "polyfill_usage_percentage": 0,
      "note": "Linear has native agent support"
    }
  },
  "convention_detection_24h": {
    "mentions_detected": 234,
    "assignments_detected": 156,
    "false_positives": 8,
    "false_negatives": 12,
    "detection_accuracy": 96.7
  },
  "signature_injection": {
    "tasks_created_24h": 445,
    "signatures_injected": 356,
    "injection_rate": 80.0,
    "note": "20% created in bot_user mode (no injection needed)"
  }
}
```

### 7. Real-Time Live Check
**`GET /health/map/live`**

Performs live connectivity test to all configured platforms.

**Query Params:**
- `org_id=org_123` - Test specific org's credentials
- `platform=clickup` - Test specific platform only

**Response:**
```json
{
  "test_timestamp": "2025-11-22T10:50:00Z",
  "org_id": "org_123",
  "results": [
    {
      "platform": "clickup",
      "status": "success",
      "latency_ms": 234,
      "credential_valid": true,
      "api_reachable": true
    },
    {
      "platform": "quickbooks",
      "status": "failed",
      "error": "Token expired",
      "credential_valid": false,
      "api_reachable": true,
      "recommended_action": "Refresh OAuth token"
    }
  ]
}
```

### 8. Historical Metrics
**`GET /metrics/map`**

Time-series data for dashboards.

**Query Params:**
- `timerange=24h|7d|30d` - Time window
- `platform=clickup` - Filter by platform
- `metric=success_rate|latency|error_rate` - Specific metric

**Response:**
```json
{
  "timerange": "24h",
  "granularity": "1h",
  "metrics": {
    "success_rate": [
      {"timestamp": "2025-11-22T00:00:00Z", "value": 98.5},
      {"timestamp": "2025-11-22T01:00:00Z", "value": 98.7},
      {"timestamp": "2025-11-22T02:00:00Z", "value": 97.2}
    ],
    "avg_latency_ms": [
      {"timestamp": "2025-11-22T00:00:00Z", "value": 245},
      {"timestamp": "2025-11-22T01:00:00Z", "value": 250}
    ],
    "total_requests": [
      {"timestamp": "2025-11-22T00:00:00Z", "value": 523},
      {"timestamp": "2025-11-22T01:00:00Z", "value": 412}
    ]
  }
}
```

---

## Alerting & Notifications

### Critical Alerts (Immediate Action Required)

**Trigger Conditions:**
- Credential expired for active platform
- Platform API completely unreachable (>5 consecutive failures)
- Bot user deleted/disabled in platform
- Authentication failures (>10 in 1 hour)
- Error rate >25% for any platform

**Alert Channels:**
- Slack webhook to #aleq-alerts
- Email to oncall engineer
- PagerDuty incident (for production)

**Alert Format:**
```json
{
  "severity": "critical",
  "alert_type": "credential_expired",
  "platform": "quickbooks",
  "org_id": "org_456",
  "message": "QuickBooks credential expired for org_456",
  "impact": "QuickBooks capabilities unavailable for 3 users",
  "recommended_action": "Re-authorize QuickBooks OAuth",
  "reauth_link": "https://stargate.aleq.com/oauth/quickbooks/authorize?org_id=org_456"
}
```

### Warning Alerts (Action Needed Soon)

**Trigger Conditions:**
- Credential expiring within 24 hours
- Error rate >5% but <25%
- API latency >2s (p95)
- Rate limit >80% consumed
- Bot provisioning stalled (>48hrs incomplete)

**Alert Channels:**
- Slack to #aleq-monitoring
- Email digest (daily summary)

### Info Notifications

**Trigger Conditions:**
- New platform connected
- Bot provisioning completed
- Credential refreshed successfully
- Platform recovered from degraded state

---

## Diagnostic Tools

### 1. Schema Mapping Debugger
**`POST /debug/map/schema`**

Test universal → platform translation without executing.

**Request:**
```json
{
  "platform": "clickup",
  "universal_schema": {
    "domain": "task",
    "action": "create",
    "data": {
      "workspace": "engineering",
      "title": "Fix login bug",
      "priority": "high",
      "status": "in_progress"
    }
  }
}
```

**Response:**
```json
{
  "translation_result": {
    "list_id": "123456",
    "name": "Fix login bug",
    "priority": 2,
    "status": "in progress"
  },
  "mappings_applied": [
    {"universal": "workspace:engineering", "platform": "list_id:123456"},
    {"universal": "title", "platform": "name"},
    {"universal": "priority:high", "platform": "priority:2"},
    {"universal": "status:in_progress", "platform": "status:'in progress'"}
  ],
  "unsupported_fields": [],
  "warnings": []
}
```

### 2. Credential Tester
**`POST /debug/map/credentials/{org_id}/{platform}`**

Test if credential is valid without making real API call.

**Response:**
```json
{
  "credential_status": "valid",
  "expires_at": "2025-12-15T14:30:00Z",
  "hours_until_expiry": 552,
  "refresh_token_available": true,
  "test_api_call": {
    "success": true,
    "latency_ms": 234,
    "response": "OK"
  }
}
```

### 3. Bot Provisioning Checker
**`POST /debug/map/bot-provisioning/{org_id}/verify`**

Verify bot user still exists and has permissions on all linked platforms.

**Response:**
```json
{
  "bot_email": "aleq@dockwa.com",
  "verification_results": [
    {
      "platform": "clickup",
      "bot_user_exists": true,
      "bot_user_id": "user_789",
      "permissions_intact": true,
      "can_create_tasks": true,
      "last_successful_action": "2025-11-22T09:30:00Z"
    },
    {
      "platform": "monday",
      "bot_user_exists": false,
      "issue": "Bot user removed from workspace",
      "recommended_action": "Re-invite aleq@dockwa.com to Monday workspace"
    }
  ]
}
```

### 4. Platform Connectivity Tester
**`POST /debug/map/platforms/{platform}/ping`**

Test raw API connectivity.

**Response:**
```json
{
  "platform": "clickup",
  "reachable": true,
  "latency_ms": 245,
  "api_version": "v2",
  "rate_limit_remaining": 8766,
  "server_timestamp": "2025-11-22T10:50:00Z"
}
```

---

## Data Storage

### Health Metrics Database

**New Tables:**

```sql
-- Platform health snapshots (hourly)
CREATE TABLE platform_health_snapshots (
    id UUID PRIMARY KEY,
    platform VARCHAR NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    status VARCHAR NOT NULL, -- healthy, degraded, down
    error_rate FLOAT,
    avg_latency_ms INT,
    total_calls INT,
    failed_calls INT,
    credentials_valid INT,
    credentials_total INT,
    INDEX idx_platform_timestamp (platform, timestamp)
);

-- Bot provisioning tracking
CREATE TABLE bot_provisioning_status (
    org_id VARCHAR PRIMARY KEY,
    bot_email VARCHAR NOT NULL,
    bot_name VARCHAR,
    provisioning_started TIMESTAMP,
    provisioning_completed TIMESTAMP,
    completion_percentage INT,
    platforms_linked JSON, -- ["gmail", "clickup", "linear"]
    platforms_pending JSON, -- ["monday", "slack"]
    last_updated TIMESTAMP
);

-- Schema mapping stats (daily aggregates)
CREATE TABLE schema_mapping_stats (
    id UUID PRIMARY KEY,
    date DATE NOT NULL,
    universal_field VARCHAR NOT NULL,
    platform VARCHAR NOT NULL,
    total_mappings INT,
    successful_mappings INT,
    failed_mappings INT,
    success_rate FLOAT,
    INDEX idx_date_field_platform (date, universal_field, platform)
);

-- Alert history
CREATE TABLE alert_history (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    severity VARCHAR NOT NULL, -- critical, warning, info
    alert_type VARCHAR NOT NULL,
    platform VARCHAR,
    org_id VARCHAR,
    message TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_severity_resolved (severity, resolved)
);
```

### Caching Strategy

**Redis for Real-Time Status:**
- Platform health (5min TTL)
- Credential expiry cache (1hr TTL)
- Rate limit tracking (15min TTL)
- Live connectivity results (1min TTL)

**Postgres for Historical:**
- Hourly snapshots (retained 90 days)
- Daily aggregates (retained 1 year)
- Alert history (retained indefinitely)

---

## Implementation Phases

### Phase 1: Core Health (Week 1)
**Goal:** Basic platform and credential health monitoring

**Deliverables:**
- `GET /health/map`
- `GET /health/map/platforms`
- `GET /health/map/credentials`
- Platform health snapshots (hourly background job)
- Critical alerts for expired credentials

**Database:**
- `platform_health_snapshots` table
- Redis cache for real-time status

### Phase 2: Bot Provisioning Tracking (Week 2)
**Goal:** Track bot setup progress and status

**Deliverables:**
- `GET /health/map/bot-provisioning`
- `GET /health/map/bot-provisioning/{org_id}`
- `POST /debug/map/bot-provisioning/{org_id}/verify`
- Bot setup completion tracking

**Database:**
- `bot_provisioning_status` table

### Phase 3: Schema Metrics (Week 3)
**Goal:** Schema mapping effectiveness and coverage

**Deliverables:**
- `GET /health/map/schema`
- `POST /debug/map/schema` (translation debugger)
- Field coverage matrix
- Mapping success/failure tracking

**Database:**
- `schema_mapping_stats` table

### Phase 4: Advanced Diagnostics (Week 4)
**Goal:** Real-time testing and debugging tools

**Deliverables:**
- `GET /health/map/live`
- `POST /debug/map/credentials/{org_id}/{platform}`
- `POST /debug/map/platforms/{platform}/ping`
- Live connectivity dashboard

### Phase 5: Datadog Integration & Dashboards (Week 5)
**Goal:** Time-series data and Datadog integration

**Deliverables:**
- `GET /metrics/map`
- Datadog custom metrics integration
- Datadog APM tracing for all MAP layers
- Pre-built Datadog dashboards for MAP monitoring
- 24h/7d/30d trend views
- Platform reliability reports

---

## Success Metrics

**Platform Reliability:**
- Target: 99.5% uptime per platform
- Measure: Successful API calls / Total API calls

**Credential Health:**
- Target: <1% expired credentials at any time
- Measure: Valid credentials / Total credentials

**Bot Provisioning:**
- Target: 80% completion rate within 24hrs of starting
- Measure: Fully provisioned bots / Total bots started

**Schema Mapping:**
- Target: 98% mapping success rate
- Measure: Successful mappings / Total mappings

**Alert Accuracy:**
- Target: <5% false positive alert rate
- Measure: False alerts / Total alerts

**Response Time:**
- Target: All health endpoints <500ms
- Measure: p95 latency

---

## Dashboard Views

### Executive View (CEO/Leadership)
- Overall MAP health score (single number)
- Critical issues count
- Platform uptime summary (last 30 days)
- Bot provisioning adoption rate

### Engineering View (Dev Team)
- Platform-specific error rates
- API latency trends
- Schema mapping failures
- Credential expiry timeline

### Operations View (Support/Success)
- Per-org credential status
- Bot provisioning progress per customer
- Recent alerts and resolutions
- Platform-specific issues affecting customers

### Debug View (On-call Engineer)
- Live platform connectivity
- Real-time error logs
- Credential test results
- Bot verification results

---

## Datadog Integration

### Custom Metrics

Send MAP metrics to Datadog using `datadog-api-client`:

```python
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v2.api.metrics_api import MetricsApi
from datadog_api_client.v2.model.metric_payload import MetricPayload
from datadog_api_client.v2.model.metric_point import MetricPoint
from datadog_api_client.v2.model.metric_series import MetricSeries

# Send platform health metrics
def send_platform_health_to_datadog(platform: str, status: str, error_rate: float, latency_ms: int):
    configuration = Configuration()
    with ApiClient(configuration) as api_client:
        api_instance = MetricsApi(api_client)

        body = MetricPayload(
            series=[
                MetricSeries(
                    metric="map.platform.health",
                    type="gauge",
                    points=[MetricPoint(timestamp=int(time.time()), value=1 if status == "healthy" else 0)],
                    tags=[f"platform:{platform}", f"status:{status}"]
                ),
                MetricSeries(
                    metric="map.platform.error_rate",
                    type="gauge",
                    points=[MetricPoint(timestamp=int(time.time()), value=error_rate)],
                    tags=[f"platform:{platform}"]
                ),
                MetricSeries(
                    metric="map.platform.latency_ms",
                    type="gauge",
                    points=[MetricPoint(timestamp=int(time.time()), value=latency_ms)],
                    tags=[f"platform:{platform}"]
                )
            ]
        )
        api_instance.submit_metrics(body=body)
```

**Key Metrics to Send:**
- `map.platform.health` (gauge: 0 or 1) - Tags: platform, status
- `map.platform.error_rate` (gauge: 0-1) - Tags: platform
- `map.platform.latency_ms` (gauge) - Tags: platform
- `map.platform.calls` (count) - Tags: platform, status
- `map.credential.status` (gauge) - Tags: platform, org_id, credential_type, status
- `map.bot.provisioning.completion` (gauge: 0-100) - Tags: org_id
- `map.schema.mapping.success_rate` (gauge: 0-1) - Tags: platform, universal_field
- `map.polyfill.detection.accuracy` (gauge: 0-1) - Tags: platform, detection_type

### APM Tracing

Add Datadog APM traces to track MAP layer execution:

```python
from ddtrace import tracer

@tracer.wrap(service="stargate-map", resource="layer2.schema_mapping")
def translate_universal_to_platform(platform: str, universal_data: dict):
    span = tracer.current_span()
    span.set_tag("platform", platform)
    span.set_tag("domain", universal_data.get("domain"))

    # Translation logic
    result = perform_translation(platform, universal_data)

    span.set_tag("mapping.success", True)
    return result
```

**Key Traces:**
- `layer1.connector.api_call` - Platform API calls
- `layer2.schema_mapping` - Universal → platform translation
- `layer3.identity_polyfill` - Signature injection, convention detection
- `layer4.bot_provisioning` - Bot setup operations

### Datadog Dashboards

**Pre-built Dashboard: MAP Overview**
- Overall MAP health score (SLO widget)
- Platform health status grid
- Error rate by platform (timeseries)
- API latency by platform (heatmap)
- Credential expiry timeline
- Bot provisioning completion funnel

**Pre-built Dashboard: Platform Deep Dive**
- Per-platform metrics
- API call volume
- Error distribution
- Rate limit tracking
- Recent errors log stream

**Pre-built Dashboard: Bot Provisioning**
- Total bots created (count)
- Provisioning completion rate (gauge)
- Platforms linked distribution (pie chart)
- Incomplete provisioning list (table)

### Datadog Monitors & Alerts

**Critical Monitors:**
```
Monitor: Credential Expired
Metric: map.credential.status{status:expired}
Alert: If count > 0 for 5 minutes
Notification: @slack-aleq-alerts @pagerduty-stargate

Monitor: Platform Down
Metric: map.platform.health{status:down}
Alert: If count > 0 for 10 minutes
Notification: @slack-aleq-alerts @pagerduty-stargate

Monitor: High Error Rate
Metric: avg:map.platform.error_rate{*}
Alert: If > 0.25 for 15 minutes
Warning: If > 0.05 for 30 minutes
Notification: @slack-aleq-monitoring
```

**Warning Monitors:**
```
Monitor: Credential Expiring Soon
Metric: map.credential.status{status:expiring_soon}
Alert: If count > 0
Notification: @slack-aleq-monitoring

Monitor: Elevated Latency
Metric: avg:map.platform.latency_ms{*}
Alert: If p95 > 2000ms for 30 minutes
Notification: @slack-aleq-monitoring
```

### Datadog Log Integration

Send MAP logs to Datadog:

```python
import logging
from ddtrace import tracer

logger = logging.getLogger("stargate.map")
logger.setLevel(logging.INFO)

# Log with trace correlation
def log_schema_mapping_failure(platform: str, field: str, error: str):
    logger.error(
        "Schema mapping failed",
        extra={
            "platform": platform,
            "universal_field": field,
            "error": error,
            "dd.trace_id": tracer.current_span().trace_id,
            "dd.span_id": tracer.current_span().span_id
        }
    )
```

**Log Queries:**
- Failed mappings: `service:stargate-map status:error @platform:*`
- Bot provisioning errors: `service:stargate-map @layer:bot_provisioning status:error`
- Credential issues: `service:stargate-map @error_type:credential*`

---

## Open Questions

1. **Metrics Retention:** How long to keep hourly snapshots in Postgres? (90 days proposed, Datadog retains 15 months)
2. **Alert Noise:** Should we batch warnings into daily digest? Or real-time Slack?
3. **Performance Impact:** Background health checks - how often without slowing system?
4. **User-Facing:** Should customers see their own org's health status in Aleq UI?
5. **Datadog Cost:** Custom metrics pricing - estimate ~200 custom metrics, need to validate budget
