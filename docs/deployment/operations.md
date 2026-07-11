# Systems Operations & Monitoring Runbook

This document details monitoring standards, trace correlation metrics, and quick diagnostics for the Aether platform.

---

## 1. Key Metrics to Monitor

Monitor the following indicators using systems monitoring agents (such as Prometheus, Grafana, or Datadog):

### HTTP Endpoints Performance
* **Request Latency (p95 / p99)**: API endpoints should respond within 200ms. Latencies over 1000ms indicate connection depletion or database lock contention.
* **HTTP 5xx Error Rate**: Any non-zero count of 500 status codes should trigger alert dispatches to pager channels.

### Worker & Queue Lengths
* **Celery Queue Backlog Size**: A growing number of queued tasks indicates Celery worker stalls or insufficient worker container replicas.
* **Celery Task Failures**: Track task failures to identify credential expiration issues in third-party connectors (Google Calendar/Email/Slack).

### Database Resources
* **Active Connections Pool**: High connection counts indicate unclosed session scopes in HTTP routers or long-running transactions.
* **CPU and Disk Storage**: Standard alerts on PostgreSQL VM CPU utilization > 80% or disk capacity > 85%.

---

## 2. Distributed Tracing & Correlation IDs

Every user-triggered operation generates a unique `correlation_id` (UUIDv4) that is propagated across backend API calls, Celery task broker payloads, database queries, and audit events.

To trace a single user action across multiple logs:
1. Extract the `correlation_id` from the HTTP request headers or the API response.
2. Search files for that `correlation_id`:
   ```bash
   grep -rn "correlation-id-uuid-here" /var/log/aether/
   ```
3. Locate DB audit logs using the `correlation_id` filter:
   ```sql
   SELECT * FROM audit_events WHERE correlation_id = 'correlation-id-uuid-here';
   ```

---

## 3. Quick Diagnostics & Troubleshooting Runbook

### Scenario A: Celery Task Backlog & Workers Stalled
1. Check Celery logs for memory depletion or thread timeouts:
   ```bash
   docker compose logs worker
   ```
2. Restart the Celery worker instances:
   ```bash
   docker compose restart worker
   ```
3. If backlogs persist, scale up workers count (requires Docker Compose scaling):
   ```bash
   docker compose up -d --scale worker=3
   ```

### Scenario B: Database Connection Exhaustion (HTTP 500 / Timeout)
1. Verify active PG connections list:
   ```bash
   docker exec -it aether-db psql -U postgres -d aether -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"
   ```
2. If connections are locked in `idle in transaction`, terminate blocking sessions or restart the API gateway container:
   ```bash
   docker compose restart api
   ```
