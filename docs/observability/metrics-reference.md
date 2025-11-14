---
title: "Entity CRUD Metrics Reference"
description: "Quick reference for all metrics tracked for catalog entity operations"
audience: [developers, devops, ai-agents]
tags: [metrics, prometheus, monitoring, reference]
created: 2025-11-14
updated: 2025-11-14
category: "observability"
status: published
related:
  - /docs/observability/entity-crud-monitoring.md
  - /docs/observability/monitoring-setup-verification.md
---

# Entity CRUD Metrics Reference

Quick reference for all Prometheus metrics tracked for catalog entity CRUD operations.

## HTTP Request Metrics

These metrics are automatically collected by `prometheus-fastapi-instrumentator`.

### http_requests_total

**Type**: Counter
**Description**: Total count of HTTP requests
**Labels**:
- `method`: HTTP method (GET, POST, PUT, PATCH, DELETE)
- `handler`: Endpoint handler name
- `path`: Request path pattern
- `status`: HTTP status code

**Example Queries**:

```promql
# Total requests to catalog endpoints
http_requests_total{path=~"/api/v1/catalog/.*"}

# UPDATE requests (PUT/PATCH)
http_requests_total{path=~"/api/v1/catalog/.*", method=~"PUT|PATCH"}

# DELETE requests
http_requests_total{path=~"/api/v1/catalog/.*", method="DELETE"}

# 4xx errors
http_requests_total{path=~"/api/v1/catalog/.*", status=~"4.."}

# 5xx errors
http_requests_total{path=~"/api/v1/catalog/.*", status=~"5.."}

# 409 Conflict (blocked deletes)
http_requests_total{path=~"/api/v1/catalog/.*", method="DELETE", status="409"}
```

### http_request_duration_seconds

**Type**: Histogram
**Description**: HTTP request latency distribution
**Labels**:
- `method`: HTTP method
- `handler`: Endpoint handler name
- `path`: Request path pattern
**Buckets**: Standard duration buckets (configurable)

**Example Queries**:

```promql
# P50 UPDATE latency
histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket{
  path=~"/api/v1/catalog/.*",
  method=~"PUT|PATCH"
}[5m])) by (le))

# P95 UPDATE latency
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{
  path=~"/api/v1/catalog/.*",
  method=~"PUT|PATCH"
}[5m])) by (le))

# P99 DELETE latency
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{
  path=~"/api/v1/catalog/.*",
  method="DELETE"
}[5m])) by (le))

# Average request duration
rate(http_request_duration_seconds_sum{path=~"/api/v1/catalog/.*"}[5m])
/
rate(http_request_duration_seconds_count{path=~"/api/v1/catalog/.*"}[5m])
```

## Calculated Metrics

These metrics are derived from the base HTTP metrics.

### Request Rate

**Description**: Requests per second
**Calculation**: `rate(http_requests_total[5m])`

**Queries**:

```promql
# UPDATE request rate
sum(rate(http_requests_total{
  path=~"/api/v1/catalog/.*",
  method=~"PUT|PATCH"
}[5m])) by (handler)

# DELETE request rate
sum(rate(http_requests_total{
  path=~"/api/v1/catalog/.*",
  method="DELETE"
}[5m])) by (handler)

# Total catalog endpoint request rate
sum(rate(http_requests_total{path=~"/api/v1/catalog/.*"}[5m]))
```

### Error Rate

**Description**: Percentage of failed requests
**Calculation**: `(errors / total_requests) * 100`

**Queries**:

```promql
# 5xx error rate
sum(rate(http_requests_total{
  path=~"/api/v1/catalog/.*",
  status=~"5.."
}[5m]))
/
sum(rate(http_requests_total{path=~"/api/v1/catalog/.*"}[5m]))

# 4xx error rate
sum(rate(http_requests_total{
  path=~"/api/v1/catalog/.*",
  status=~"4.."
}[5m]))
/
sum(rate(http_requests_total{path=~"/api/v1/catalog/.*"}[5m]))

# Combined error rate
sum(rate(http_requests_total{
  path=~"/api/v1/catalog/.*",
  status=~"[45].."
}[5m]))
/
sum(rate(http_requests_total{path=~"/api/v1/catalog/.*"}[5m]))
```

### Success Rate

**Description**: Percentage of successful requests (2xx)
**Calculation**: `(successful_requests / total_requests) * 100`

**Query**:

```promql
sum(rate(http_requests_total{
  path=~"/api/v1/catalog/.*",
  status=~"2.."
}[5m]))
/
sum(rate(http_requests_total{path=~"/api/v1/catalog/.*"}[5m]))
```

## Business Metrics

Application-specific metrics for monitoring business operations.

### Entities Updated

**Description**: Count of successful entity updates
**Source**: `http_requests_total{method=~"PUT|PATCH", status="200"}`

**Queries**:

```promql
# Updates in last hour
sum(increase(http_requests_total{
  path=~"/api/v1/catalog/.*",
  method=~"PUT|PATCH",
  status="200"
}[1h])) by (handler)

# Update rate per minute
sum(rate(http_requests_total{
  path=~"/api/v1/catalog/.*",
  method=~"PUT|PATCH",
  status="200"
}[5m])) * 60
```

### Entities Deleted

**Description**: Count of successful entity deletions
**Source**: `http_requests_total{method="DELETE", status="200"}`

**Queries**:

```promql
# Deletions in last hour
sum(increase(http_requests_total{
  path=~"/api/v1/catalog/.*",
  method="DELETE",
  status="200"
}[1h])) by (handler)

# Deletion rate per minute
sum(rate(http_requests_total{
  path=~"/api/v1/catalog/.*",
  method="DELETE",
  status="200"
}[5m])) * 60
```

### Blocked Deletes (409 Conflicts)

**Description**: Count of delete attempts blocked due to entity being in use
**Source**: `http_requests_total{method="DELETE", status="409"}`

**Queries**:

```promql
# Blocked deletes in last hour
sum(increase(http_requests_total{
  path=~"/api/v1/catalog/.*",
  method="DELETE",
  status="409"
}[1h]))

# Blocked delete rate
sum(rate(http_requests_total{
  path=~"/api/v1/catalog/.*",
  method="DELETE",
  status="409"
}[5m]))

# Block rate as percentage of total delete attempts
sum(rate(http_requests_total{
  path=~"/api/v1/catalog/.*",
  method="DELETE",
  status="409"
}[5m]))
/
sum(rate(http_requests_total{
  path=~"/api/v1/catalog/.*",
  method="DELETE"
}[5m]))
```

### Not Found Errors (404)

**Description**: Requests for non-existent entities
**Source**: `http_requests_total{status="404"}`

**Queries**:

```promql
# 404 errors in last hour
sum(increase(http_requests_total{
  path=~"/api/v1/catalog/.*",
  status="404"
}[1h]))

# 404 rate
sum(rate(http_requests_total{
  path=~"/api/v1/catalog/.*",
  status="404"
}[5m]))
```

## Entity-Specific Metrics

Metrics broken down by entity type.

### By Entity Type

Use the `handler` label to filter by entity:

```promql
# CPU updates
http_requests_total{
  handler=~".*cpu.*",
  method=~"PUT|PATCH"
}

# GPU deletes
http_requests_total{
  handler=~".*gpu.*",
  method="DELETE"
}

# Profile updates
http_requests_total{
  handler=~".*profile.*",
  method=~"PUT|PATCH"
}
```

### Entity Type Request Distribution

```promql
# Request count by entity type
sum(increase(http_requests_total{path=~"/api/v1/catalog/.*"}[1h])) by (handler)
```

## Alert Threshold Queries

Queries used in Grafana alert rules.

### High Error Rate Alert

**Condition**: 5xx errors > 5% for 5 minutes

```promql
sum(rate(http_requests_total{
  path=~"/api/v1/catalog/.*",
  status=~"5.."
}[5m]))
/
sum(rate(http_requests_total{path=~"/api/v1/catalog/.*"}[5m]))
> 0.05
```

### Slow DELETE Alert

**Condition**: P95 DELETE latency > 2s for 5 minutes

```promql
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{
  path=~"/api/v1/catalog/.*",
  method="DELETE"
}[5m])) by (le))
> 2
```

### Slow UPDATE Alert

**Condition**: P95 UPDATE latency > 500ms for 5 minutes

```promql
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{
  path=~"/api/v1/catalog/.*",
  method=~"PUT|PATCH"
}[5m])) by (le))
> 0.5
```

## Performance Targets

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| UPDATE P95 Latency | < 200ms | > 500ms |
| UPDATE P99 Latency | < 500ms | > 1s |
| DELETE P95 Latency | < 500ms | > 2s |
| DELETE P99 Latency | < 1s | > 3s |
| Error Rate (5xx) | < 0.1% | > 5% |
| Error Rate (4xx) | < 5% | > 20% |
| Success Rate | > 99% | < 95% |

## Recording Rules (Optional)

For frequently used queries, consider adding recording rules to Prometheus.

**Example** (`/infra/prometheus/rules.yml`):

```yaml
groups:
  - name: entity_crud_rules
    interval: 30s
    rules:
      - record: entity_crud:update_latency_p95
        expr: |
          histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{
            path=~"/api/v1/catalog/.*",
            method=~"PUT|PATCH"
          }[5m])) by (le))

      - record: entity_crud:delete_latency_p95
        expr: |
          histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{
            path=~"/api/v1/catalog/.*",
            method="DELETE"
          }[5m])) by (le))

      - record: entity_crud:error_rate
        expr: |
          sum(rate(http_requests_total{
            path=~"/api/v1/catalog/.*",
            status=~"5.."
          }[5m]))
          /
          sum(rate(http_requests_total{path=~"/api/v1/catalog/.*"}[5m]))
```

## Useful Dashboard Queries

### Top 10 Slowest Endpoints

```promql
topk(10,
  rate(http_request_duration_seconds_sum{path=~"/api/v1/catalog/.*"}[5m])
  /
  rate(http_request_duration_seconds_count{path=~"/api/v1/catalog/.*"}[5m])
)
```

### Request Rate Heatmap

```promql
sum(rate(http_requests_total{path=~"/api/v1/catalog/.*"}[5m])) by (method, status)
```

### Latency by Percentile

```promql
# Multiple percentiles
histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) or
histogram_quantile(0.90, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) or
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) or
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
```

## Resources

- [Prometheus Query Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [PromQL Functions](https://prometheus.io/docs/prometheus/latest/querying/functions/)
- [Histogram Quantiles](https://prometheus.io/docs/practices/histograms/)
- [Rate vs iRate](https://prometheus.io/docs/prometheus/latest/querying/functions/#rate)
