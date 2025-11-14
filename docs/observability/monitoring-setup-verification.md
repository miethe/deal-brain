---
title: "Monitoring Setup Verification"
description: "Quick guide to verify Grafana dashboard and alert setup for entity CRUD operations"
audience: [developers, devops]
tags: [monitoring, setup, verification, grafana]
created: 2025-11-14
updated: 2025-11-14
category: "observability"
status: published
related:
  - /docs/observability/entity-crud-monitoring.md
---

# Monitoring Setup Verification

This guide walks through verifying the Grafana dashboard and alerting setup for entity CRUD operations.

## Prerequisites

- Docker and Docker Compose installed
- Deal Brain stack running (`make up`)

## Verification Steps

### 1. Start the Stack

```bash
# From project root
make up
```

Wait for all services to be healthy:
```bash
docker-compose ps
```

Expected output should show all services as "Up" or "healthy".

### 2. Verify Prometheus is Scraping Metrics

**Access Prometheus**: http://localhost:9090

**Check Targets**:
1. Navigate to Status → Targets
2. Verify both targets are "UP":
   - `dealbrain-api` (api:8000)
   - `otel-collector` (otel-collector:9464)

**Test a Query**:
1. Navigate to Graph
2. Enter query: `http_requests_total`
3. Click "Execute"
4. You should see metrics data

### 3. Access Grafana Dashboard

**URL**: http://localhost:3021

**Login**:
- Username: `admin`
- Password: `admin`

**Verify Data Source**:
1. Navigate to Connections → Data sources
2. You should see "Prometheus" configured and working
3. Click "Test" - should show "Data source is working"

**Access Dashboard**:
1. Navigate to Dashboards
2. You should see "Entity CRUD Operations" dashboard
3. Click to open it

**Verify Dashboard Panels**:
The dashboard should have 10 panels:
1. UPDATE Request Rate (PUT/PATCH)
2. DELETE Request Rate
3. Error Rate by Status Code
4. Current Error Rate (5xx) - Gauge
5. UPDATE Latency (P50, P95, P99)
6. DELETE Latency (P50, P95, P99)
7. Delete Blocked (409 Conflicts, Last Hour)
8. Entities Updated (Last Hour)
9. Entities Deleted (Last Hour)
10. Response Status Codes

**If panels show "No data"**: This is normal if no API requests have been made yet. Proceed to step 4.

### 4. Generate Test Data

**Option A: Using the Web UI**

1. Access the web app: http://localhost:3020
2. Navigate to catalog management (CPUs, GPUs, etc.)
3. Perform some operations:
   - Update a CPU entry
   - Try to delete an entity (may get 409 if in use)
   - Create a new entity

**Option B: Using curl**

```bash
# Get a CPU to update
curl http://localhost:8020/api/v1/catalog/cpu | jq '.[0]'

# Update a CPU (replace {id} with actual ID)
curl -X PATCH http://localhost:8020/api/v1/catalog/cpu/{id} \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name"}'

# Try to delete (may get 409)
curl -X DELETE http://localhost:8020/api/v1/catalog/cpu/{id}
```

**Option C: Run the Test Suite**

```bash
make test
```

This will generate API requests that populate metrics.

### 5. Verify Metrics Appear in Dashboard

Return to Grafana dashboard (http://localhost:3021):

1. Refresh the dashboard (or wait for auto-refresh)
2. You should now see data in the panels:
   - Request rates should show activity
   - Latency panels should show response times
   - Status code distribution should appear

### 6. Verify Alert Rules

**Access Alert Rules**:
1. Navigate to Alerting → Alert rules
2. You should see 3 alert rules:
   - High Error Rate (Critical)
   - Slow DELETE Operations (Warning)
   - Slow UPDATE Operations (Warning)

**Check Alert Status**:
- All alerts should be in "Normal" state (green)
- If any are firing, investigate using the monitoring guide

### 7. Test Alert Triggering (Optional)

To verify alerts can fire (be careful in production):

**Trigger High Latency Alert**:
```python
# Add artificial delay to DELETE endpoint for testing
# In apps/api/dealbrain_api/api/catalog.py
import asyncio

@router.delete("/cpu/{cpu_id}")
async def delete_cpu(...):
    await asyncio.sleep(3)  # Artificial 3s delay
    # ... rest of function
```

After adding delay:
1. Restart API: `docker-compose restart api`
2. Make several DELETE requests
3. Wait 5-10 minutes
4. Check Alerting → Alert rules - "Slow DELETE Operations" should fire

**Don't forget to remove the test delay!**

## Troubleshooting

### Dashboard Shows "No data"

**Check**:
1. Prometheus is scraping: http://localhost:9090/targets
2. API is exposing metrics: `curl http://localhost:8020/metrics`
3. Time range in dashboard (top-right) is recent (e.g., "Last 1 hour")

**Fix**:
- Generate some API traffic (see step 4)
- Verify Prometheus data source in Grafana
- Check docker logs: `docker-compose logs grafana prometheus api`

### Data Source Not Found

**Symptoms**: Dashboard shows "Data source prometheus was not found"

**Fix**:
1. Check provisioning config: `/infra/grafana/provisioning/datasources/datasource.yml`
2. Verify Grafana has access to provisioning directory:
   ```bash
   docker-compose exec grafana ls -la /etc/grafana/provisioning/datasources/
   ```
3. Restart Grafana: `docker-compose restart grafana`

### Alerts Not Showing

**Check**:
1. Alert provisioning file exists: `/infra/grafana/provisioning/alerting/entity-crud-alerts.yml`
2. Grafana has read access:
   ```bash
   docker-compose exec grafana ls -la /etc/grafana/provisioning/alerting/
   ```
3. Check Grafana logs for errors:
   ```bash
   docker-compose logs grafana | grep -i alert
   ```

**Fix**:
- Restart Grafana: `docker-compose restart grafana`
- Check file permissions on host
- Verify YAML syntax in alert rules file

### High Error Rates

**Symptoms**: Error rate panels show high values

**Investigation**:
1. Check API logs: `docker-compose logs api`
2. Check specific error responses:
   ```bash
   curl http://localhost:8020/metrics | grep http_requests_total | grep 'status="5'
   ```
3. Review recent code changes
4. Check database connectivity: `docker-compose logs db`

## Verification Checklist

- [ ] Prometheus is scraping API metrics
- [ ] Grafana dashboard loads without errors
- [ ] Prometheus data source is connected
- [ ] All 10 dashboard panels are visible
- [ ] Dashboard shows data after generating API traffic
- [ ] 3 alert rules are provisioned
- [ ] Alerts are in "Normal" state
- [ ] Time range and refresh settings are appropriate

## Next Steps

Once verified:
1. Review the full monitoring guide: `/docs/observability/entity-crud-monitoring.md`
2. Set up alert notification channels (email, Slack, etc.)
3. Customize dashboard for your specific needs
4. Establish monitoring runbooks for your team

## Maintenance

**Regular Tasks**:
- Review alert thresholds quarterly
- Update dashboard panels as new metrics are added
- Archive old metrics data (Prometheus retention settings)
- Test alert firing mechanisms periodically

**When to Update**:
- After adding new catalog entity types
- After API performance optimizations
- After database schema changes
- After modifying endpoint paths
