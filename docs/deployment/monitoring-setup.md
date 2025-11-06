# Monitoring & Observability Setup

Comprehensive guide for setting up monitoring, metrics, and alerting for Deal Brain.

## Overview

Deal Brain includes built-in observability components:

- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **OpenTelemetry**: Trace and metric collection
- **Application Metrics**: FastAPI /metrics endpoint
- **Health Checks**: Service health verification

## Architecture

```
┌─────────────────────────────────────────────┐
│         Deal Brain Services                 │
│  ┌──────────────────────────────────────┐  │
│  │  API, Web, Worker (emit metrics)    │  │
│  └──────────────┬───────────────────────┘  │
└─────────────────┼────────────────────────────┘
                  │
        ┌─────────┴──────────┐
        │                    │
   ┌────▼──────┐      ┌──────▼──────┐
   │Prometheus │      │   OpenTel   │
   │:9090      │      │  Collector  │
   └────┬──────┘      └─────────────┘
        │
   ┌────▼──────────────┐
   │    Grafana        │
   │ Dashboards & UI   │
   │    :3000          │
   └───────────────────┘
```

## Prometheus Setup

### Configuration

Prometheus is configured via `/infra/prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "dealbrain-api"
    metrics_path: /metrics
    static_configs:
      - targets: ["api:8000"]
  - job_name: "otel-collector"
    static_configs:
      - targets: ["otel-collector:9464"]
```

### Verify Prometheus is Running

```bash
# Check if container is running
docker-compose ps prometheus

# Access Prometheus UI
# http://your-server:9090
# or https://yourdomain.com/prometheus

# Check metrics endpoint directly
curl http://localhost:8000/metrics | head -20
```

### Prometheus Queries

Common metrics queries:

```promql
# Request rate (requests per second)
rate(http_requests_total[5m])

# Request latency (95th percentile)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# Container memory usage
container_memory_usage_bytes

# Database connection pool usage
pg_pool_active_connections

# Redis memory usage
redis_memory_used_bytes

# Worker queue size
celery_queue_size

# Active requests
http_requests_in_progress
```

### Update Prometheus Configuration

To add more monitoring targets:

```bash
# Edit prometheus configuration
nano /infra/prometheus/prometheus.yml

# Add new scrape config
scrape_configs:
  - job_name: "custom-service"
    static_configs:
      - targets: ["service-host:port"]

# Reload Prometheus (no restart needed)
curl -X POST http://localhost:9090/-/reload
```

## Grafana Setup

### Initial Access

1. Open browser: `http://your-server:3000`
2. Default credentials: `admin` / `admin`
3. Change password immediately (Settings → User Profile)

### Configure Prometheus Data Source

1. Navigate to Configuration → Data Sources
2. Click "Add data source"
3. Select Prometheus
4. Set URL to `http://prometheus:9090` (Docker) or `http://localhost:9090`
5. Click "Save & Test"

### Create Dashboards

#### Dashboard 1: Application Overview

Create a new dashboard with these panels:

**Panel 1: Requests Per Second**
```promql
rate(http_requests_total[1m])
```

**Panel 2: Error Rate**
```promql
rate(http_requests_total{status=~"5.."}[1m])
```

**Panel 3: Request Latency (p95)**
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

**Panel 4: CPU Usage**
```promql
rate(container_cpu_usage_seconds_total[5m]) * 100
```

**Panel 5: Memory Usage**
```promql
container_memory_usage_bytes / 1024 / 1024
```

#### Dashboard 2: Database Performance

**Panel 1: Active Connections**
```promql
pg_stat_activity_count
```

**Panel 2: Queries Per Second**
```promql
rate(pg_stat_statements_calls[1m])
```

**Panel 3: Query Duration (avg)**
```promql
pg_stat_statements_mean_exec_time
```

**Panel 4: Cache Hit Ratio**
```promql
(rate(pg_stat_database_blks_hit[5m]) / (rate(pg_stat_database_blks_hit[5m]) + rate(pg_stat_database_blks_read[5m])))
```

#### Dashboard 3: Application Health

**Panel 1: Services Status**
- Create a status indicator for each service
- Check health endpoints

**Panel 2: Database Size**
```promql
pg_database_size_bytes
```

**Panel 3: Disk Space Available**
```promql
node_filesystem_avail_bytes{mountpoint="/"}
```

**Panel 4: Worker Queue Size**
```promql
celery_queue_size
```

### Import Pre-made Dashboards

Grafana has community dashboards available:

1. Click "+" → Import
2. Enter dashboard ID (e.g., 6417 for Docker metrics)
3. Select Prometheus data source
4. Click Import

Popular dashboards:
- 6417: Docker Containers Overview
- 1860: Node Exporter Full
- 8588: FastAPI Metrics

### Alert Rules

Create alert rules in Grafana:

**Alert 1: High CPU Usage**
```
Condition: container_cpu_usage_seconds_total > 0.8
Duration: 5 minutes
```

**Alert 2: Database Connection Exhaustion**
```
Condition: pg_stat_activity_count > 80
Duration: 2 minutes
```

**Alert 3: Disk Space Low**
```
Condition: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
Duration: 10 minutes
```

**Alert 4: Error Rate High**
```
Condition: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
Duration: 5 minutes
```

## OpenTelemetry Collector Setup

### Configuration

Located at `/infra/otel/config.yaml`:

```yaml
receivers:
  otlp:
    protocols:
      grpc:
      http:

exporters:
  logging:
    loglevel: info
  prometheus:
    endpoint: 0.0.0.0:9464

service:
  pipelines:
    metrics:
      receivers: [otlp]
      exporters: [prometheus, logging]
    traces:
      receivers: [otlp]
      exporters: [logging]
```

### Enable Application Instrumentation

The API is configured to emit metrics via OpenTelemetry. Verify it's enabled:

```bash
# Check environment variable
docker-compose exec api env | grep OTEL_EXPORTER

# Expected: OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

### View OpenTelemetry Metrics

```bash
# Metrics are exported to Prometheus
# Access via Grafana dashboards or Prometheus UI

# Check metrics being collected
curl http://localhost:9464/metrics | grep -i "otel\|metric"
```

## Application Metrics

### Health Check Endpoint

```bash
# Check application health
curl http://localhost:8000/api/health

# Expected response
# {"status": "healthy", "database": "connected", "redis": "connected"}
```

### Metrics Endpoint

```bash
# Get raw Prometheus metrics
curl http://localhost:8000/metrics

# Get specific metric
curl http://localhost:8000/metrics | grep http_requests_total

# Count total requests
curl http://localhost:8000/metrics | grep http_requests_total | wc -l
```

### Custom Application Metrics

To add custom metrics to the API, update the instrumentation in the FastAPI setup.

Current metrics tracked:
- HTTP request count and duration
- Database query performance
- Cache hit/miss rates
- Worker task metrics
- Queue sizes

## Service Health Monitoring

### Docker Compose Health Checks

Docker Compose includes health checks for services:

```bash
# Check service health status
docker-compose ps

# View health check output
docker-compose exec api healthcheck

# Manual health check
docker-compose exec api curl -f http://localhost:8000/api/health || exit 1
```

### Implement Health Check Alerts

```bash
# Create monitoring script
cat > /home/user/check-service-health.sh << 'EOF'
#!/bin/bash

ALERT_EMAIL="admin@yourdomain.com"

# Check each service
services=("api" "web" "db" "redis" "worker")

for service in "${services[@]}"; do
    if ! docker-compose ps "$service" | grep -q "Up"; then
        echo "ALERT: Service $service is down!" | \
            mail -s "Deal Brain Service Alert" "$ALERT_EMAIL"
    fi
done

# Check API health
if ! curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "ALERT: API health check failed!" | \
        mail -s "Deal Brain API Alert" "$ALERT_EMAIL"
fi
EOF

chmod +x /home/user/check-service-health.sh

# Add to crontab (run every 5 minutes)
(crontab -l 2>/dev/null || echo "") | grep -v "check-service-health.sh" | {
    cat
    echo "*/5 * * * * /home/user/check-service-health.sh"
} | crontab -
```

## Logging Setup

### View Application Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api

# Last N lines
docker-compose logs --tail=100 api

# Logs since specific time
docker-compose logs --since 2024-01-01T00:00:00 api

# With timestamps
docker-compose logs -t api
```

### Configure Log Retention

Edit docker-compose.yml or docker-compose.prod.yml:

```yaml
services:
  api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service=api"
```

This keeps only 3 files of 10MB each (30MB total).

### Centralized Logging (Optional)

For advanced log management, use ELK Stack or similar:

```bash
# Example: Logstash configuration to send to Elasticsearch
# Requires additional setup beyond scope of this guide
```

## Alerts & Notifications

### Email Alerts (via Grafana)

1. Navigate to Alerting → Notification channels
2. Click "New channel"
3. Select "Email"
4. Configure:
   - Email address
   - SMTP server details (if needed)
5. Create alert rules that use this channel

### Slack Alerts (via Grafana)

1. Create Slack webhook: https://api.slack.com/messaging/webhooks
2. In Grafana → Notification channels → New channel
3. Select "Slack"
4. Paste webhook URL
5. Create alert rules

### PagerDuty Integration

1. Get PagerDuty integration key
2. In Grafana → Notification channels → New channel
3. Select "PagerDuty"
4. Enter integration key
5. Create critical alerts

## Performance Optimization

### Prometheus Storage Optimization

```bash
# Check Prometheus data size
du -sh /var/lib/docker/volumes/deal-brain_prometheus_data/_data

# Reduce retention (edit prometheus.yml)
global:
  scrape_interval: 15s
  retention: 7d  # Keep 7 days of metrics

# Restart Prometheus
docker-compose restart prometheus
```

### Grafana Dashboard Performance

- Use time intervals (avoid "all time" queries)
- Limit number of metrics per panel
- Use aggregation functions (sum, avg, max, min)
- Set appropriate refresh intervals

## Monitoring Checklist

### Daily
- [ ] Check application error rate in Grafana
- [ ] Review API latency metrics
- [ ] Verify all services are healthy
- [ ] Monitor disk space usage

### Weekly
- [ ] Review weekly performance trends
- [ ] Check database size growth
- [ ] Verify backup completion
- [ ] Test alert notifications

### Monthly
- [ ] Analyze performance trends
- [ ] Plan capacity upgrades if needed
- [ ] Review and optimize slow queries
- [ ] Test disaster recovery procedures

## Troubleshooting

### Prometheus Not Collecting Metrics

```bash
# Check if API metrics endpoint is accessible
curl http://localhost:8000/metrics

# Check Prometheus configuration
docker-compose logs prometheus | head -20

# Verify target is up in Prometheus UI
# http://localhost:9090/targets
```

### Grafana Can't Connect to Prometheus

```bash
# Verify Prometheus is running
docker-compose ps prometheus

# Test connection from Grafana container
docker-compose exec grafana curl http://prometheus:9090/api/v1/query?query=up

# Check network connectivity
docker network inspect deal-brain_default
```

### Missing Metrics

```bash
# Verify application is emitting metrics
docker-compose exec api curl http://localhost:8000/metrics | grep metric_name

# Check OpenTelemetry configuration
docker-compose logs otel-collector

# Verify OTEL endpoint is configured
docker-compose exec api env | grep OTEL
```

### Alert Not Firing

```bash
# Test alert query in Prometheus
# http://localhost:9090/graph

# Verify alert rules are loaded
curl http://localhost:9090/api/v1/rules

# Check alert status in Grafana
# Alerting → Alert Rules → Check status

# Test notification channel
# Alerting → Notification channels → Edit → Send test notification
```

## Best Practices

1. **Set Meaningful Thresholds**
   - Based on historical data
   - Account for normal variations
   - Adjust over time

2. **Avoid Alert Fatigue**
   - Don't alert on every small change
   - Use composite conditions
   - Aggregate related alerts

3. **Document Dashboards**
   - Add descriptions to panels
   - Document metric meanings
   - Keep runbooks for alerts

4. **Regular Review**
   - Audit unused dashboards
   - Remove obsolete alerts
   - Update thresholds based on data

5. **Test Procedures**
   - Test alert notifications monthly
   - Verify restore procedures
   - Document incident response

## Next Steps

- [Database Backup](./database-backup.md) - Protect your data
- [SSL Setup](./ssl-setup.md) - Secure your deployment
- [Docker Compose Deployment](./docker-compose-vps.md) - Return to deployment

## Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/grafana/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [FastAPI Metrics](https://fastapi.tiangolo.com/tutorial/monitoring/)

---

**Monitoring Configured?** Next: [Database Backup](./database-backup.md)
