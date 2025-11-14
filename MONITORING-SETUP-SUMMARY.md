# Entity CRUD Monitoring Setup - Phase 9, Task DOC-004

## Summary

Complete Grafana dashboard and alerting setup for monitoring catalog entity UPDATE and DELETE operations.

## Deliverables

### 1. Grafana Infrastructure

**Directory**: `/home/user/deal-brain/infra/grafana/`

#### Dashboard Configuration
- **File**: `dashboards/entity-crud-dashboard.json`
- **Panels**: 10 monitoring panels
- **Refresh**: 30 seconds
- **Features**:
  - Request rate tracking (UPDATE/DELETE)
  - Error rate monitoring (4xx/5xx)
  - Latency percentiles (P50, P95, P99)
  - Business metrics (entities modified, blocked deletes)
  - Status code distribution

#### Provisioning Configurations
- **Data Source**: `provisioning/datasources/datasource.yml`
  - Prometheus connection at `http://prometheus:9090`
- **Dashboard Provisioning**: `provisioning/dashboards/dashboard.yml`
  - Auto-loads dashboards from `/etc/grafana/dashboards`
- **Alert Rules**: `provisioning/alerting/entity-crud-alerts.yml`
  - 3 alert rules with appropriate thresholds

#### README
- **File**: `README.md`
- **Contents**: Usage instructions, troubleshooting, development guide

### 2. Alert Rules

**File**: `/home/user/deal-brain/infra/grafana/provisioning/alerting/entity-crud-alerts.yml`

#### Configured Alerts
1. **High Error Rate** (Critical)
   - Threshold: 5xx errors > 5% for 5 minutes
   - Action Required: Investigate API errors immediately

2. **Slow DELETE Operations** (Warning)
   - Threshold: P95 latency > 2s for 5 minutes
   - Action Required: Check cascade query performance

3. **Slow UPDATE Operations** (Warning)
   - Threshold: P95 latency > 500ms for 5 minutes
   - Action Required: Review database query optimization

### 3. Documentation

#### Main Monitoring Guide
**File**: `/home/user/deal-brain/docs/observability/entity-crud-monitoring.md`
**Contents**:
- Overview of monitoring infrastructure
- Access instructions
- Detailed metric descriptions
- Alert rule explanations
- Performance targets
- Troubleshooting guide
- Manual monitoring instructions

#### Setup Verification Guide
**File**: `/home/user/deal-brain/docs/observability/monitoring-setup-verification.md`
**Contents**:
- Step-by-step verification process
- Test data generation instructions
- Troubleshooting common setup issues
- Verification checklist

#### Metrics Reference
**File**: `/home/user/deal-brain/docs/observability/metrics-reference.md`
**Contents**:
- Complete Prometheus query reference
- All tracked metrics with examples
- Calculated metrics formulas
- Business metrics definitions
- Alert threshold queries
- Performance targets table

### 4. Docker Configuration

**File**: `/home/user/deal-brain/docker-compose.yml`

**Changes**: Updated Grafana service to mount configuration directories:
```yaml
grafana:
  volumes:
    - ./infra/grafana/provisioning:/etc/grafana/provisioning:ro
    - ./infra/grafana/dashboards:/etc/grafana/dashboards:ro
```

## Metrics Tracked

### Request Metrics
- UPDATE request rate (PUT/PATCH)
- DELETE request rate
- Request rate by entity type

### Error Metrics
- 4xx client error rate (by status code)
- 5xx server error rate (by status code)
- Current error rate gauge
- Response status code distribution

### Latency Metrics
- UPDATE latency (P50, P95, P99)
- DELETE latency (P50, P95, P99)
- Average request duration

### Business Metrics
- Entities updated (count per hour)
- Entities deleted (count per hour)
- Delete blocked count (409 conflicts)

## Performance Targets

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| UPDATE P95 Latency | < 200ms | > 500ms |
| DELETE P95 Latency | < 500ms | > 2s |
| Error Rate (5xx) | < 0.1% | > 5% |
| Success Rate | > 99% | > 95% |

## Access Information

- **Grafana Dashboard**: http://localhost:3021
  - Username: `admin`
  - Password: `admin`
  - Dashboard: "Entity CRUD Operations"

- **Prometheus**: http://localhost:9090
- **API Metrics**: http://localhost:8020/metrics

## Quick Start

### 1. Start the Stack
```bash
make up
```

### 2. Access Grafana
```bash
open http://localhost:3021
```

### 3. View Dashboard
Navigate to: Dashboards → Entity CRUD Operations

### 4. Generate Test Data
```bash
# Option A: Run tests
make test

# Option B: Make API requests
curl -X PATCH http://localhost:8020/api/v1/catalog/cpu/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Test CPU"}'
```

### 5. Verify Metrics
Check that dashboard panels show data after generating traffic.

## File Paths

All files use absolute paths for clarity:

**Infrastructure**:
- `/home/user/deal-brain/infra/grafana/dashboards/entity-crud-dashboard.json`
- `/home/user/deal-brain/infra/grafana/provisioning/datasources/datasource.yml`
- `/home/user/deal-brain/infra/grafana/provisioning/dashboards/dashboard.yml`
- `/home/user/deal-brain/infra/grafana/provisioning/alerting/entity-crud-alerts.yml`
- `/home/user/deal-brain/infra/grafana/README.md`

**Documentation**:
- `/home/user/deal-brain/docs/observability/entity-crud-monitoring.md`
- `/home/user/deal-brain/docs/observability/monitoring-setup-verification.md`
- `/home/user/deal-brain/docs/observability/metrics-reference.md`

**Configuration**:
- `/home/user/deal-brain/docker-compose.yml` (updated)

## Next Steps

1. **Verify Setup**: Follow `/home/user/deal-brain/docs/observability/monitoring-setup-verification.md`
2. **Customize Alerts**: Add notification channels (email, Slack) in Grafana UI
3. **Review Thresholds**: Adjust alert thresholds based on production traffic patterns
4. **Add Recording Rules**: Consider adding Prometheus recording rules for frequently used queries
5. **Set Up Retention**: Configure Prometheus data retention policies

## Success Criteria

✅ Dashboard configuration file created
✅ Alert rules defined for critical thresholds
✅ Metrics mapped to performance targets
✅ Comprehensive documentation created
✅ Docker configuration updated
✅ All files use absolute paths
✅ Setup verification guide provided

## Support

For troubleshooting assistance, see:
- `/home/user/deal-brain/docs/observability/entity-crud-monitoring.md` (Troubleshooting section)
- `/home/user/deal-brain/docs/observability/monitoring-setup-verification.md` (Common issues)
- `/home/user/deal-brain/infra/grafana/README.md` (Development guide)
