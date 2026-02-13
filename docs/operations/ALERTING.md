# Degradation Alerting

Stargate Lite emits fire-and-forget UDP metrics to the DataDog agent via `app/observability.py`.

## Metrics Emitted

| Metric | Tags | Emitted From |
|--------|------|-------------|
| `stargate_lite.execution.success` | `service` | `execute_handler()` on successful handler completion |
| `stargate_lite.execution.error` | `service`, `error_code` | `handle_stargate_error()` and `handle_unexpected_error()` |

## Recommended DataDog Monitors

### 1. Per-Service Error Rate

Trigger when a service accumulates errors beyond normal levels.

```
Monitor Type: Metric Alert
Query: sum(last_5m):sum:stargate_lite.execution.error{*} by {service}.as_count() > 10
Name: "[Stargate] High error rate for {{service.name}}"
Priority: P2
```

**Thresholds:**
- Warning: > 5 errors / 5 min
- Critical: > 10 errors / 5 min

### 2. Circuit Breaker Opened

Any circuit breaker opening indicates a service outage worth investigating.

```
Monitor Type: Log Alert
Query: logs("service:stargate-lite log_event:circuit_opened").index("*").rollup("count").last("5m") > 0
Name: "[Stargate] Circuit breaker opened for service"
Priority: P1
```

### 3. Health Check Degraded

Health endpoint returning "degraded" means Redis or DB is unreachable.

```
Monitor Type: HTTP Check
URL: https://stargate-lite.up.railway.app/health
Check: Response body contains "healthy"
Frequency: 60s
Name: "[Stargate] Health check degraded"
Priority: P1
```

### 4. Credential Error Spike

High rate of credential errors may indicate a token refresh regression or provider OAuth outage.

```
Monitor Type: Metric Alert
Query: sum(last_5m):sum:stargate_lite.execution.error{error_code:CREDENTIALS_INVALID OR error_code:CREDENTIALS_MISSING}.as_count() > 5
Name: "[Stargate] Credential error spike"
Priority: P2
```

## Error Codes Reference

| Error Code | Retry Strategy | Typical Cause |
|-----------|---------------|---------------|
| `NETWORK_ERROR` | `backoff` | Service down, timeout, circuit breaker open |
| `RATE_LIMIT` | `backoff` | Provider rate limit hit |
| `CREDENTIALS_MISSING` | `human_intervention` | User hasn't connected service |
| `CREDENTIALS_INVALID` | `human_intervention` | Token revoked or refresh failed |
| `CREDENTIALS_INSUFFICIENT` | `human_intervention` | Missing required scopes |
| `EXECUTION_ERROR` | `backoff` | Provider returned unexpected error |
| `VALIDATION_ERROR` | `none` | Bad request args |
| `CAPABILITY_NOT_FOUND` | `none` | Unknown capability key |
| `QUOTA_EXCEEDED` | `human_intervention` | Account quota exceeded |
| `PERMISSION_DENIED` | `human_intervention` | Insufficient permissions |
