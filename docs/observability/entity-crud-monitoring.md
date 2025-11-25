---
title: "Entity CRUD Operations Monitoring"
description: "Comprehensive monitoring guide for catalog entity UPDATE and DELETE operations"
audience: [developers, devops, ai-agents]
tags: [monitoring, grafana, prometheus, crud, catalog, observability]
created: 2025-11-14
updated: 2025-11-14
category: "observability"
status: published
related:
  - /docs/observability/developer-guide.md
  - /docs/observability/logging-design.md
  - /docs/api/catalog-endpoints.md
---

# Entity CRUD Operations Monitoring

This guide provides comprehensive monitoring instructions for catalog entity CRUD operations (UPDATE and DELETE) in the Deal Brain API.

## Overview

The monitoring infrastructure tracks performance, errors, and business metrics for entity management operations across all catalog entities:
- CPU
- GPU
- RAM Spec
- Storage Profile
- Ports Profile
- Profile

## Accessing the Dashboard

### Grafana Dashboard

1. **URL**: `http://localhost:3021` (or your configured Grafana host)
2. **Credentials**: `admin` / `admin` (default)
3. **Dashboard**: Navigate to "Entity CRUD Operations" dashboard

The dashboard auto-refreshes every 30 seconds and shows data from the last hour by default.

### Direct Access

- **Grafana**: http://localhost:3021
- **Prometheus**: http://localhost:9090
- **API Metrics**: http://localhost:8020/metrics

## Metrics Tracked

### 1. Request Rates

**UPDATE Request Rate (PUT/PATCH)**
- **Query**: `sum(rate(http_requests_total{path=~"/api/v1/catalog/.*", method=~"PUT|PATCH"}[5m])) by (method, handler)`
- **Unit**: Requests per second
- **Purpose**: Track volume of entity update operations
- **What to Look For**: Spikes indicating bulk operations or unusual activity

**DELETE Request Rate**
- **Query**: `sum(rate(http_requests_total{path=~"/api/v1/catalog/.*", method="DELETE"}[5m])) by (handler)`
- **Unit**: Requests per second
- **Purpose**: Track volume of entity deletion attempts
- **What to Look For**: Unexpected deletion spikes

### 2. Error Rates

**4xx Client Errors**
- **Query**: `sum(rate(http_requests_total{path=~"/api/v1/catalog/.*", status=~"4.."}[5m])) by (status) / sum(rate(http_requests_total{path=~"/api/v1/catalog/.*"}[5m]))`
- **Unit**: Percentage
- **Common Codes**:
  - `404`: Entity not found
  - `409`: Conflict (entity in use, cannot delete)
  - `422`: Validation error (invalid update data)
- **What to Look For**: High 404 rates may indicate UI/client bugs; 409s are expected for cascade protections

**5xx Server Errors**
- **Query**: `sum(rate(http_requests_total{path=~"/api/v1/catalog/.*", status=~"5.."}[5m])) by (status) / sum(rate(http_requests_total{path=~"/api/v1/catalog/.*"}[5m]))`
- **Unit**: Percentage
- **Target**: < 1%
- **Alert Threshold**: > 5%
- **What to Look For**: Any 5xx errors indicate server-side issues requiring investigation

### 3. Latency Metrics

**UPDATE Latency (PUT/PATCH)**
- **Queries**:
  - P50: `histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket{path=~"/api/v1/catalog/.*", method=~"PUT|PATCH"}[5m])) by (le))`
  - P95: `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{path=~"/api/v1/catalog/.*", method=~"PUT|PATCH"}[5m])) by (le))`
  - P99: `histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{path=~"/api/v1/catalog/.*", method=~"PUT|PATCH"}[5m])) by (le))`
- **Target**: P95 < 500ms
- **Alert Threshold**: P95 > 500ms for 5 minutes
- **What to Look For**: Gradual increases may indicate database performance degradation

**DELETE Latency**
- **Queries**:
  - P50: `histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket{path=~"/api/v1/catalog/.*", method="DELETE"}[5m])) by (le))`
  - P95: `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{path=~"/api/v1/catalog/.*", method="DELETE"}[5m])) by (le))`
  - P99: `histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{path=~"/api/v1/catalog/.*", method="DELETE"}[5m])) by (le))`
- **Target**: P95 < 1s
- **Alert Threshold**: P95 > 2s for 5 minutes
- **What to Look For**: DELETE includes cascade checks, so higher latency is expected; sustained high values may indicate inefficient queries

### 4. Business Metrics

**Delete Blocked (409 Conflicts)**
- **Query**: `sum(increase(http_requests_total{path=~"/api/v1/catalog/.*", method="DELETE", status="409"}[1h]))`
- **Unit**: Count per hour
- **Purpose**: Track how often deletions are prevented due to entities being in use
- **What to Look For**: High counts may indicate users attempting to delete referenced entities; expected behavior, not an error

**Entities Updated**
- **Query**: `sum(increase(http_requests_total{path=~"/api/v1/catalog/.*", method=~"PUT|PATCH", status="200"}[1h])) by (handler)`
- **Unit**: Count per hour
- **Purpose**: Track successful entity modifications
- **What to Look For**: Activity patterns, bulk operation impact

**Entities Deleted**
- **Query**: `sum(increase(http_requests_total{path=~"/api/v1/catalog/.*", method="DELETE", status="200"}[1h])) by (handler)`
- **Unit**: Count per hour
- **Purpose**: Track successful entity deletions
- **What to Look For**: Unexpected deletion volumes

**Response Status Codes**
- **Query**: `sum(increase(http_requests_total{path=~"/api/v1/catalog/.*"}[5m])) by (status)`
- **Purpose**: Visual breakdown of all HTTP status codes
- **What to Look For**: Distribution should be mostly 2xx (green), some 4xx (yellow) is normal, 5xx (red) should be rare

## Alert Rules

### 1. High Error Rate (Critical)

**Condition**: 5xx error rate > 5% for 5 minutes
**Severity**: Critical
**What It Means**: The API is experiencing significant server-side errors
**Actions to Take**:
1. Check API logs for error details: `docker logs dealbrain-api`
2. Review Prometheus metrics for affected endpoints
3. Check database connectivity and health
4. Review recent deployments or configuration changes
5. Check resource utilization (CPU, memory, disk)

### 2. Slow DELETE Operations (Warning)

**Condition**: P95 DELETE latency > 2s for 5 minutes
**Severity**: Warning
**What It Means**: Entity deletion operations are taking longer than expected
**Actions to Take**:
1. Check for large cascade checks (entities with many references)
2. Review database query performance
3. Check database connection pool saturation
4. Consider adding indexes on foreign key columns
5. Monitor database CPU/memory usage

### 3. Slow UPDATE Operations (Warning)

**Condition**: P95 UPDATE latency > 500ms for 5 minutes
**Severity**: Warning
**What It Means**: Entity update operations are slower than target
**Actions to Take**:
1. Review database query plans for UPDATE operations
2. Check for lock contention on entity tables
3. Monitor database transaction rates
4. Check for missing indexes on commonly updated fields
5. Review concurrent update patterns

## Performance Targets

| Metric | Target | Threshold | Alert Level |
|--------|--------|-----------|-------------|
| UPDATE Latency (P95) | < 200ms | > 500ms | Warning |
| UPDATE Latency (P99) | < 500ms | > 1s | Warning |
| DELETE Latency (P95) | < 500ms | > 2s | Warning |
| DELETE Latency (P99) | < 1s | > 3s | Warning |
| Error Rate (5xx) | < 0.1% | > 5% | Critical |
| Error Rate (4xx) | < 5% | > 20% | Warning |

## Troubleshooting Guide

### High 404 Rates

**Symptoms**: Many 404 responses on entity endpoints
**Possible Causes**:
- UI caching stale entity IDs
- Race conditions between delete and read operations
- Client-side bugs referencing non-existent entities

**Investigation**:
1. Check API logs for specific entity IDs being requested
2. Review frontend code for entity reference patterns
3. Check for concurrent operations on the same entities

### High 409 Conflicts

**Symptoms**: Many 409 responses on DELETE operations
**Possible Causes**:
- Users attempting to delete entities referenced by listings or other entities
- Incorrect cascade check logic
- UI not displaying entity usage information

**Investigation**:
1. Review which entities are being blocked: Check logs for cascade check details
2. Verify entity usage is displayed in UI before deletion
3. Consider adding "force delete" option with cascade warnings

### High DELETE Latency

**Symptoms**: P95 DELETE latency > 2s
**Possible Causes**:
- Complex cascade checks with many relationships
- Missing indexes on foreign key columns
- Database connection pool saturation

**Investigation**:
```sql
-- Check for missing indexes on foreign keys
SELECT * FROM pg_indexes WHERE tablename IN (
  'listings', 'listing_components', 'valuation_rules', 'profiles'
);

-- Check for slow DELETE queries
SELECT * FROM pg_stat_statements
WHERE query LIKE '%DELETE%'
ORDER BY mean_exec_time DESC
LIMIT 10;
```

**Solutions**:
1. Add indexes: `CREATE INDEX idx_listing_components_cpu_id ON listing_components(cpu_id);`
2. Optimize cascade check queries
3. Increase database connection pool size
4. Consider caching entity usage counts

### High UPDATE Latency

**Symptoms**: P95 UPDATE latency > 500ms
**Possible Causes**:
- Lock contention on entity tables
- Inefficient validation logic
- Missing indexes on updated columns

**Investigation**:
```sql
-- Check for lock contention
SELECT * FROM pg_locks WHERE NOT granted;

-- Check UPDATE query performance
SELECT * FROM pg_stat_statements
WHERE query LIKE '%UPDATE%'
ORDER BY mean_exec_time DESC
LIMIT 10;
```

**Solutions**:
1. Review and optimize validation logic
2. Use optimistic locking to reduce lock contention
3. Batch updates when possible
4. Add indexes on commonly updated fields

## Manual Monitoring

If you prefer manual queries over the Grafana dashboard:

### Prometheus Queries

Access Prometheus at http://localhost:9090 and use these queries:

**Current Error Rate**:
```promql
sum(rate(http_requests_total{path=~"/api/v1/catalog/.*", status=~"5.."}[5m]))
/
sum(rate(http_requests_total{path=~"/api/v1/catalog/.*"}[5m]))
```

**P95 UPDATE Latency**:
```promql
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{path=~"/api/v1/catalog/.*", method=~"PUT|PATCH"}[5m])) by (le))
```

**P95 DELETE Latency**:
```promql
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{path=~"/api/v1/catalog/.*", method="DELETE"}[5m])) by (le))
```

**Blocked Deletes (Last Hour)**:
```promql
sum(increase(http_requests_total{path=~"/api/v1/catalog/.*", method="DELETE", status="409"}[1h]))
```

### Direct API Metrics

The FastAPI application exposes Prometheus metrics at `/metrics`:

```bash
curl http://localhost:8020/metrics | grep http_request
```

## Setting Up Alerts

The alert rules are automatically provisioned from `/infra/grafana/provisioning/alerting/entity-crud-alerts.yml`.

To modify alerts:
1. Edit the alert rule file
2. Restart Grafana: `docker-compose restart grafana`
3. Verify alerts in Grafana UI: Alerting → Alert Rules

## Dashboard Customization

The dashboard is provisioned from `/infra/grafana/dashboards/entity-crud-dashboard.json`.

To customize:
1. Make changes in the Grafana UI
2. Export the dashboard JSON: Dashboard Settings → JSON Model
3. Update `/infra/grafana/dashboards/entity-crud-dashboard.json`
4. Commit changes to version control

**Note**: The dashboard config in Git will override local changes on next Grafana restart.

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [FastAPI Instrumentator](https://github.com/trallnag/prometheus-fastapi-instrumentator)
- [Deal Brain Observability Guide](/docs/observability/developer-guide.md)
- [Catalog API Documentation](/docs/api/catalog-endpoints.md)
