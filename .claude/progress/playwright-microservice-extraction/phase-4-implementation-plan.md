---
title: "Phase 4 - Production Deployment & Monitoring Implementation Plan"
description: "Detailed task breakdown for production deployment with zero downtime and comprehensive monitoring"
status: "draft"
created: 2025-11-20
---

# Phase 4: Production Deployment & Monitoring

**Duration**: 1-2 days | **Effort**: ~23 hours | **Team Size**: 4 engineers

## Phase Objective

Deploy Playwright microservices to production with zero downtime, establish comprehensive monitoring and alerting, and decommission embedded Playwright code from API/Worker.

## Success Criteria

- [x] Both services deployed and healthy in production
- [x] Monitoring and alerting active and validated
- [x] Zero-downtime deployment completed successfully
- [x] All metrics show expected values
- [x] No regressions in production metrics
- [x] Runbooks and playbooks documented
- [x] Team trained on operational procedures

---

## Task Breakdown

### Task 4.1: Set up Prometheus Monitoring for Ingestion Service

**Owner**: DevOps/SRE Engineer
**Model**: Sonnet
**Duration**: 2 hours
**Status**: Not Started
**Depends On**: Phase 3 Complete

**Description**:
Configure Prometheus to scrape metrics from the Playwright Ingestion Service and create dashboards for monitoring.

**Acceptance Criteria**:
- [ ] Prometheus configuration updated to scrape Ingestion Service
- [ ] Scrape interval: 15s
- [ ] Scrape timeout: 5s
- [ ] Relabel configs for service identification
- [ ] Metrics collected:
  - [ ] Request latency histogram
  - [ ] Success/failure counters
  - [ ] Timeout counters
  - [ ] Browser pool metrics
  - [ ] Page pool availability
  - [ ] Up/down status
- [ ] Grafana dashboard created:
  - [ ] Request rate (req/s)
  - [ ] Latency percentiles (p50, p95, p99)
  - [ ] Success rate percentage
  - [ ] Error rate percentage
  - [ ] Browser pool status
  - [ ] Page pool availability
- [ ] Dashboard auto-refreshes (30s interval)
- [ ] Dashboard linked in Grafana main page
- [ ] Historical data retention: 15 days minimum

**Prometheus Configuration**:

```yaml
# prometheus.yml

scrape_configs:
  - job_name: 'playwright-ingestion'
    static_configs:
      - targets: ['playwright-ingestion:8000']
    scrape_interval: 15s
    scrape_timeout: 5s
    metrics_path: '/metrics'
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
      - source_labels: [__scheme__]
        target_label: scheme
```

**Grafana Dashboard**:
```json
{
  "title": "Playwright Ingestion Service",
  "panels": [
    {
      "title": "Request Rate (req/s)",
      "targets": [
        {
          "expr": "rate(playwright_requests_success_total[1m])"
        }
      ]
    },
    {
      "title": "Latency p95 (ms)",
      "targets": [
        {
          "expr": "histogram_quantile(0.95, playwright_request_latency_ms)"
        }
      ]
    },
    {
      "title": "Success Rate %",
      "targets": [
        {
          "expr": "rate(playwright_requests_success_total[5m]) / (rate(playwright_requests_success_total[5m]) + rate(playwright_requests_failure_total[5m])) * 100"
        }
      ]
    }
  ]
}
```

**Dependencies**:
- Phase 3 complete (metrics implemented)
- Prometheus running in Docker Compose

---

### Task 4.2: Set up Prometheus Monitoring for Image Service

**Owner**: DevOps/SRE Engineer
**Model**: Sonnet
**Duration**: 2 hours
**Status**: Not Started
**Depends On**: Phase 3 Complete

**Description**:
Configure Prometheus monitoring for the Playwright Image Service with similar dashboard and metrics.

**Acceptance Criteria**:
- [ ] Prometheus configuration updated for Image Service
- [ ] Scrape interval: 15s
- [ ] Metrics collected:
  - [ ] Request latency histogram
  - [ ] Success/failure counters
  - [ ] Timeout counters
  - [ ] Browser pool metrics
  - [ ] Image generation time
- [ ] Grafana dashboard created:
  - [ ] Request rate
  - [ ] Latency percentiles
  - [ ] Success rate
  - [ ] Error rate
  - [ ] Image format breakdown (PNG vs JPEG)
  - [ ] Render time distribution
- [ ] Linked in Grafana

**Dependencies**:
- Task 4.1 (Prometheus setup)

---

### Task 4.3: Set up Alerting Rules - Service Health

**Owner**: DevOps/SRE Engineer
**Model**: Haiku
**Duration**: 2 hours
**Status**: Not Started
**Depends On**: Tasks 4.1-4.2

**Description**:
Create Prometheus alert rules for service health monitoring.

**Acceptance Criteria**:
- [ ] Alert rules created: `/prometheus/rules/playwright-services.yml`
- [ ] Service down alert:
  - [ ] Condition: up{job="playwright-ingestion"} == 0 for 1 minute
  - [ ] Severity: critical
  - [ ] Action: immediate notification
- [ ] Browser pool unhealthy alert:
  - [ ] Condition: browser pool available = 0 for 2 minutes
  - [ ] Severity: warning
  - [ ] Action: notify ops
- [ ] Health check failing alert:
  - [ ] Condition: health check status != "healthy" for 2 minutes
  - [ ] Severity: warning
  - [ ] Action: notify ops
- [ ] Alerts test successfully
- [ ] Notification channels configured (Slack/PagerDuty)

**Alert Rules**:

```yaml
# prometheus/rules/playwright-services.yml

groups:
  - name: playwright-services
    interval: 30s
    rules:
      - alert: PlaywrightIngestionServiceDown
        expr: up{job="playwright-ingestion"} == 0
        for: 1m
        annotations:
          summary: "Playwright Ingestion Service is down"
          severity: "critical"

      - alert: PlaywrightImageServiceDown
        expr: up{job="playwright-image"} == 0
        for: 1m
        annotations:
          summary: "Playwright Image Service is down"
          severity: "critical"

      - alert: PlaywrightHighErrorRate
        expr: |
          (rate(playwright_requests_failure_total[5m]) /
           (rate(playwright_requests_success_total[5m]) + rate(playwright_requests_failure_total[5m]))) > 0.1
        for: 5m
        annotations:
          summary: "Playwright service error rate > 10%"
          severity: "warning"

      - alert: PlaywrightHighLatency
        expr: histogram_quantile(0.95, playwright_request_latency_ms) > 12000
        for: 5m
        annotations:
          summary: "Playwright ingestion latency p95 > 12s"
          severity: "warning"
```

**Dependencies**:
- Tasks 4.1-4.2 (Metrics collection)

---

### Task 4.4: Set up Alerting Rules - Latency

**Owner**: DevOps/SRE Engineer
**Model**: Haiku
**Duration**: 1.5 hours
**Status**: Not Started
**Depends On**: Task 4.3

**Description**:
Create alerts for latency threshold violations.

**Acceptance Criteria**:
- [ ] Ingestion service latency alert:
  - [ ] p95 > 12 seconds (75% of 10s target + buffer)
  - [ ] Alert for 5 minutes sustained
  - [ ] Severity: warning
- [ ] Image service latency alert:
  - [ ] p95 > 18 seconds (75% of 15s target + buffer)
  - [ ] Alert for 5 minutes sustained
  - [ ] Severity: warning
- [ ] Alerts test successfully
- [ ] Alert escalation rules documented

**Dependencies**:
- Task 4.3 (Alert infrastructure)

---

### Task 4.5: Set up Alerting Rules - Error Rate

**Owner**: DevOps/SRE Engineer
**Model**: Haiku
**Duration**: 1.5 hours
**Status**: Not Started
**Depends On**: Task 4.3

**Description**:
Create alerts for error rate threshold violations.

**Acceptance Criteria**:
- [ ] Error rate alert:
  - [ ] Condition: error_rate > 10% for 5 minutes
  - [ ] Severity: warning
- [ ] Timeout rate alert:
  - [ ] Condition: timeout_rate > 5% for 5 minutes
  - [ ] Severity: warning
- [ ] Browser crash rate alert:
  - [ ] Condition: crash_rate > 2% for 5 minutes
  - [ ] Severity: warning
- [ ] Alerts test successfully
- [ ] Runbook links included in alert annotations

**Dependencies**:
- Task 4.3 (Alert infrastructure)

---

### Task 4.6: Document Blue-Green Deployment Procedure

**Owner**: DevOps/SRE Engineer
**Model**: Haiku
**Duration**: 2 hours
**Status**: Not Started
**Depends On**: Phase 3 Complete

**Description**:
Document the procedure for blue-green deployment of new API/Worker versions without downtime.

**Acceptance Criteria**:
- [ ] Deployment guide created: `/docs/deployment/playwright-zero-downtime-deployment.md`
- [ ] Blue-green deployment strategy documented:
  - [ ] Deploy new services in parallel (blue env)
  - [ ] Run health checks
  - [ ] Run smoke tests
  - [ ] Switch traffic (load balancer)
  - [ ] Monitor for regressions (5-10 minutes)
  - [ ] Decommission old services (green env) or keep as backup
- [ ] Prerequisites listed:
  - [ ] Load balancer configured
  - [ ] Health check endpoints working
  - [ ] Monitoring active
- [ ] Step-by-step deployment procedures
- [ ] Validation steps
- [ ] Estimated deployment time
- [ ] Rollback procedures

**Deployment Document Template**:

```markdown
# Playwright Zero-Downtime Deployment

## Strategy
Blue-Green deployment allows zero-downtime updates:
- Blue: Current production environment
- Green: New environment with updated code
- Switch traffic after validation

## Prerequisites
- Docker Compose or orchestration platform
- Load balancer configured with health checks
- Monitoring and alerting active
- Team notified of deployment window

## Deployment Steps

### 1. Prepare Green Environment
```bash
# Build new images
docker build -t dealbrain-api:new -f infra/api/Dockerfile .
docker build -t dealbrain-worker:new -f infra/worker/Dockerfile .

# Start green environment in parallel
docker-compose -p green up -d api worker
```

### 2. Health Check
```bash
# Verify services are healthy
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health

# Run smoke tests
pytest tests/smoke/ -v
```

### 3. Validation
- [ ] API responds to requests
- [ ] Worker processes tasks
- [ ] Ingestion service working
- [ ] Image service working
- [ ] Database connectivity OK
- [ ] Redis connectivity OK

### 4. Traffic Switch
```bash
# Update load balancer config
# Route traffic to green environment

# Monitor for errors (5-10 minutes)
watch curl http://localhost:8000/metrics
```

### 5. Decommission Blue
```bash
# After validation period, stop blue environment
docker-compose -p blue down

# Keep containers for quick rollback (optional)
```

## Rollback Procedure
```bash
# If issues detected, switch traffic back to blue
# Takes <1 minute

# Restart blue environment
docker-compose -p blue up -d
```

## Estimated Time
- Preparation: 2-3 minutes
- Deployment: 2-3 minutes
- Validation: 5-10 minutes
- **Total: 10-15 minutes**

## Team Notification
- Notify #devops on Slack before deployment
- Post deployment status updates
- Post completion and validation results
```

**Dependencies**:
- Phase 3 complete

---

### Task 4.7: Document Rollback Procedure

**Owner**: DevOps/SRE Engineer
**Model**: Haiku
**Duration**: 1.5 hours
**Status**: Not Started
**Depends On**: Task 4.6

**Description**:
Document detailed rollback procedures for emergency situations.

**Acceptance Criteria**:
- [ ] Rollback guide created: `/docs/operations/playwright-rollback-procedure.md`
- [ ] Rollback scenarios documented:
  - [ ] Uncontrolled error rate (>20%)
  - [ ] Service unavailability
  - [ ] Data corruption detected
  - [ ] Performance degradation (p95 > 30s)
- [ ] Quick rollback steps (<5 minutes):
  - [ ] Load balancer config revert
  - [ ] Service restart
  - [ ] Health check verification
  - [ ] Monitoring validation
- [ ] Recovery steps after rollback:
  - [ ] Root cause analysis
  - [ ] Log collection
  - [ ] Incident debrief
  - [ ] Decision: fix and re-deploy or keep old version

**Rollback Document**:

```markdown
# Playwright Rollback Procedure

## Quick Rollback (<5 minutes)

### Detect Issue
- Prometheus alert fires
- Error rate spike
- Latency spike
- Service unavailability

### Execute Rollback
```bash
# 1. Switch load balancer to previous version
# (Edit load balancer config or use DNS switch)

# 2. Verify services are responding
curl http://localhost:8000/health

# 3. Monitor metrics (5 minutes)
# Check error rate returns to normal
# Check latency returns to baseline
```

### Recovery Steps
1. Collect logs from failed deployment
2. Investigate root cause
3. Fix issue or mark as regression
4. Update deployment procedures if needed

## Detailed Rollback Steps

### For Blue-Green Setup
```bash
# If deployment to green failed:
# 1. Stop green environment
docker-compose -p green down

# 2. Ensure blue is running
docker-compose -p blue status

# 3. Update load balancer to point to blue
# (Configuration-dependent)

# 4. Verify traffic is flowing
tail -f logs/api.log | grep request_count
```

### Manual Rollback
```bash
# If orchestration failed:
# 1. Kill new containers
docker-compose down

# 2. Restore previous version
git checkout previous-tag
docker-compose build

# 3. Start services
docker-compose up -d

# 4. Verify health
curl http://localhost:8000/health
```

## Rollback Time Target
- Detection: 1 minute (alert fires)
- Execution: 2-3 minutes (config switch)
- Verification: 1-2 minutes (health checks)
- **Total: <5 minutes**

## After Rollback
- [ ] Create incident report
- [ ] Analyze logs
- [ ] Identify root cause
- [ ] Update procedures
- [ ] Schedule post-mortem
```

**Dependencies**:
- Task 4.6 (Deployment procedures)

---

### Task 4.8: Perform Staging Deployment

**Owner**: DevOps Engineer
**Model**: Sonnet
**Duration**: 2 hours
**Status**: Not Started
**Depends On**: Tasks 4.6-4.7

**Description**:
Execute full deployment procedure on staging environment to validate all steps before production.

**Acceptance Criteria**:
- [ ] Staging environment mirrors production
- [ ] Full deployment executed using documented procedures
- [ ] All validation steps pass:
  - [ ] Services start successfully
  - [ ] Health checks pass
  - [ ] Smoke tests pass
  - [ ] Monitoring active
  - [ ] Alerting triggered for test failures
- [ ] Blue-green deployment tested
- [ ] Rollback procedure tested
- [ ] Estimated deployment time measured
- [ ] Issues identified and resolved
- [ ] Procedure documentation updated based on findings

**Staging Deployment Checklist**:

```markdown
## Pre-Deployment
- [ ] Code changes merged to main
- [ ] All tests passing in CI
- [ ] Docker images built
- [ ] Staging environment ready
- [ ] Team notified

## Deployment
- [ ] Build new images
- [ ] Deploy to blue environment
- [ ] Verify services started
- [ ] Run health checks
- [ ] Run smoke tests
- [ ] Switch traffic
- [ ] Monitor metrics (10 minutes)
- [ ] Run integration tests
- [ ] Run E2E tests

## Validation
- [ ] No error rate spike
- [ ] No latency increase
- [ ] No memory leak
- [ ] Logs show normal operation
- [ ] Database transactions OK
- [ ] Cache working

## Rollback Test
- [ ] Trigger rollback
- [ ] Verify traffic switched back
- [ ] Verify old version working
- [ ] Document rollback time

## Sign-off
- [ ] DevOps lead approves
- [ ] Team lead approves
- [ ] Ready for production
```

**Dependencies**:
- Tasks 4.6-4.7 (Procedures documented)
- Staging environment configured

---

### Task 4.9: Perform Canary Deployment to Production

**Owner**: DevOps Engineer
**Model**: Sonnet
**Duration**: 2 hours
**Status**: Not Started
**Depends On**: Task 4.8

**Description**:
Execute canary deployment to production, gradually shifting traffic to new services while monitoring for issues.

**Acceptance Criteria**:
- [ ] Canary deployment strategy:
  - [ ] Deploy new services (green env)
  - [ ] Start with 10% traffic
  - [ ] Monitor metrics
  - [ ] Gradual increase: 10% → 25% → 50% → 100%
  - [ ] Hold at each stage for 10 minutes
  - [ ] Check metrics at each stage
- [ ] Metrics monitored during canary:
  - [ ] Error rate
  - [ ] Latency (p50, p95, p99)
  - [ ] Success rate
  - [ ] Resource usage
  - [ ] Browser pool health
- [ ] Automated rollback if:
  - [ ] Error rate increases >5% above baseline
  - [ ] Latency p95 > 20 seconds
  - [ ] Service unavailable
- [ ] Manual canary control:
  - [ ] Can pause at any stage
  - [ ] Can rollback at any time
  - [ ] Can skip to 100% if metrics good
- [ ] Deployment completed successfully

**Canary Deployment Script**:

```bash
#!/bin/bash

set -e

# Configuration
STAGES=(10 25 50 100)  # Traffic percentage at each stage
HOLD_TIME=600  # 10 minutes per stage
BASELINE_ERROR_RATE=0.02  # 2%
BASELINE_LATENCY=10000  # 10 seconds

# Deploy new services
echo "Deploying new services..."
docker-compose -p green up -d api worker

# Verify services healthy
echo "Verifying services..."
curl http://localhost:8000/health || exit 1

# Start canary
for stage in "${STAGES[@]}"; do
    echo "Canary stage: $stage% traffic"

    # Update load balancer to route $stage% to green
    update_traffic_percentage $stage

    # Monitor for HOLD_TIME
    echo "Monitoring for ${HOLD_TIME}s..."
    start_time=$(date +%s)

    while true; do
        current_time=$(date +%s)
        elapsed=$((current_time - start_time))

        if [ $elapsed -gt $HOLD_TIME ]; then
            break
        fi

        # Check metrics
        error_rate=$(get_error_rate)
        latency_p95=$(get_latency_p95)

        echo "Error rate: $error_rate, Latency p95: $latency_p95"

        # Check for issues
        if (( $(echo "$error_rate > 0.07" | bc -l) )); then
            echo "ERROR RATE TOO HIGH! Rolling back..."
            rollback
            exit 1
        fi

        if (( $(echo "$latency_p95 > 20000" | bc -l) )); then
            echo "LATENCY TOO HIGH! Rolling back..."
            rollback
            exit 1
        fi

        sleep 30
    done

    echo "Stage $stage% passed!"
done

echo "Canary deployment successful!"
```

**Dependencies**:
- Task 4.8 (Staging validated)
- Load balancer with canary support

---

### Task 4.10: Monitor Metrics During Canary Phase

**Owner**: DevOps/SRE Engineer
**Model**: Haiku
**Duration**: 1.5 hours
**Status**: Not Started
**Depends On**: Task 4.9

**Description**:
Active monitoring during canary deployment to quickly identify and respond to issues.

**Acceptance Criteria**:
- [ ] Monitoring dashboard displayed during canary
- [ ] Key metrics tracked:
  - [ ] Error rate comparison (old vs new)
  - [ ] Latency comparison
  - [ ] Success rate
  - [ ] Browser pool health
  - [ ] Resource usage
- [ ] Metrics checked at each canary stage
- [ ] Issues identified and documented
- [ ] Automatic alerts configured and tested
- [ ] Manual escalation path clear
- [ ] Post-canary metrics summary generated

**Monitoring Checklist**:

```markdown
## Pre-Canary
- [ ] Prometheus up and running
- [ ] Grafana dashboards loaded
- [ ] Alert rules active
- [ ] Notification channels configured
- [ ] Team members on standby

## During Each Stage
- [ ] Error rate stable or decreasing
- [ ] Latency stable or decreasing
- [ ] Success rate stable or increasing
- [ ] No alerts firing
- [ ] No unusual logs
- [ ] Resource usage normal

## Issues Found
- [ ] Document issue with timestamp
- [ ] Collect logs and metrics
- [ ] Make rollback decision
- [ ] If rolling back:
  - [ ] Execute rollback
  - [ ] Verify old version working
  - [ ] Schedule analysis

## Post-Canary
- [ ] Generate metrics summary
- [ ] Compare old vs new
- [ ] Document performance impact
- [ ] Approve full rollout or investigate issues
```

**Dependencies**:
- Task 4.9 (Canary in progress)
- Tasks 4.1-5 (Monitoring configured)

---

### Task 4.11: Gradually Increase Production Traffic

**Owner**: DevOps Engineer
**Model**: Haiku
**Duration**: 1 hour
**Status**: Not Started
**Depends On**: Task 4.10

**Description**:
After canary validation, gradually increase traffic to 100% in production.

**Acceptance Criteria**:
- [ ] Traffic increased in stages (if canary not at 100%)
  - [ ] 50% → 75% → 100%
  - [ ] 10 minutes between stages
  - [ ] Metrics monitored at each stage
- [ ] Final traffic at 100% on green services
- [ ] Monitoring continues for 1 hour post-deployment
- [ ] All metrics show expected values
- [ ] No errors or issues
- [ ] Production deployment considered complete
- [ ] Blue environment decommissioned or kept as backup

**Final Rollout Steps**:

```bash
#!/bin/bash

# If canary stopped at <100%, complete the rollout
update_traffic_percentage 100

# Monitor for 1 hour
for i in {1..120}; do
    echo "Post-deployment monitoring: $((i*30))s"
    check_metrics
    sleep 30
done

# Decommission blue environment
docker-compose -p blue down

# Archive blue images (optional)
docker save dealbrain-api:old -o dealbrain-api-backup.tar

echo "Production deployment complete!"
```

**Dependencies**:
- Task 4.10 (Canary monitoring complete)

---

### Task 4.12: Decommission Embedded Playwright Code

**Owner**: Backend Engineer
**Model**: Haiku
**Duration**: 1 hour
**Status**: Not Started
**Depends On**: Task 4.11

**Description**:
After successful production deployment, remove embedded Playwright code from API/Worker codebase.

**Acceptance Criteria**:
- [ ] Verify production deployment successful (1+ hour of metrics)
- [ ] Remove deprecated files:
  - [ ] `apps/api/dealbrain_api/adapters/playwright.py`
  - [ ] `apps/api/dealbrain_api/adapters/browser_pool.py`
  - [ ] Any other Playwright-specific code
- [ ] Remove from `__init__.py` exports
- [ ] Update pyproject.toml:
  - [ ] Remove playwright dependency (if not used elsewhere)
  - [ ] Remove from dev dependencies (if not used elsewhere)
- [ ] Run code cleanup:
  - [ ] `git clean -fd` (remove unused files)
  - [ ] Remove unused imports
- [ ] Final code review
- [ ] Commit and merge:
  - [ ] Commit message: "chore: remove embedded Playwright code after microservice extraction"
- [ ] Verify no broken imports

**Dependencies**:
- Task 4.11 (Production deployment confirmed successful)

---

### Task 4.13: Update Documentation & Runbooks

**Owner**: Documentation Writer
**Model**: Haiku
**Duration**: 2 hours
**Status**: Not Started
**Depends On**: Task 4.12

**Description**:
Update all documentation to reflect the new microservice architecture and operational procedures.

**Acceptance Criteria**:
- [ ] Architecture documentation updated:
  - [ ] `/docs/architecture/playwright-microservice-architecture.md` (new)
  - [ ] Architecture diagram updated
  - [ ] Integration points documented
  - [ ] Data flows documented
- [ ] Deployment documentation:
  - [ ] `/docs/deployment/playwright-zero-downtime-deployment.md` (verified)
  - [ ] `/docs/operations/playwright-rollback-procedure.md` (verified)
  - [ ] `/docs/deployment/playwright-services-deployment.md` (new)
- [ ] Monitoring documentation:
  - [ ] `/docs/operations/playwright-services-monitoring.md` (new)
  - [ ] Alert definitions documented
  - [ ] Metrics reference created
  - [ ] Dashboard links provided
- [ ] Troubleshooting documentation:
  - [ ] `/docs/troubleshooting/playwright-services-troubleshooting.md` (verified)
  - [ ] Common issues and solutions
  - [ ] Diagnostic procedures
  - [ ] Escalation paths
- [ ] Operational runbooks:
  - [ ] `/docs/operations/playwright-services-runbook.md` (final)
  - [ ] Reviewed by operations team
  - [ ] Links updated
- [ ] API documentation:
  - [ ] `/docs/api/playwright-services.md` (final)
  - [ ] OpenAPI specs current
  - [ ] Examples updated
- [ ] Configuration documentation:
  - [ ] `/docs/configuration/playwright-services-config.md` (final)
  - [ ] All env vars documented
  - [ ] Default values current
- [ ] CHANGELOG updated:
  - [ ] Major architectural change noted
  - [ ] Migration guide for operations
  - [ ] Known limitations documented
  - [ ] Performance improvements documented

**Documentation Checklist**:

```markdown
## Architecture
- [ ] System diagram
- [ ] Service relationships
- [ ] Integration points
- [ ] Data flows

## Deployment
- [ ] Prerequisites
- [ ] Step-by-step procedures
- [ ] Estimated time
- [ ] Validation steps
- [ ] Rollback steps

## Operations
- [ ] Monitoring setup
- [ ] Alert configuration
- [ ] Incident response
- [ ] Common issues

## Troubleshooting
- [ ] Issue: Service down
- [ ] Issue: High latency
- [ ] Issue: High error rate
- [ ] Issue: Memory leak

## Configuration
- [ ] All env vars
- [ ] Default values
- [ ] How to change config
- [ ] How to validate config

## API
- [ ] Endpoint reference
- [ ] Request/response examples
- [ ] Error codes
- [ ] Rate limits
```

**Dependencies**:
- Task 4.12 (All changes complete)

---

## Phase 4 Acceptance Checklist

### Deployment

- [ ] Blue-green deployment executed successfully
- [ ] Canary deployment completed with monitoring
- [ ] Zero downtime achieved
- [ ] Traffic gradually shifted to 100%
- [ ] Blue environment decommissioned or archived
- [ ] Embedded Playwright code removed

### Monitoring & Alerting

- [ ] Prometheus metrics collection active
- [ ] Grafana dashboards created and functional
- [ ] Alert rules configured and tested
- [ ] Notification channels working
- [ ] On-call procedures defined
- [ ] Metrics baseline established

### Production Validation

- [ ] All services healthy and responding
- [ ] No error rate spike
- [ ] Latency within targets
- [ ] Memory usage normal
- [ ] Database connectivity OK
- [ ] Cache functioning correctly
- [ ] 1+ hour of clean metrics post-deployment

### Documentation

- [ ] Architecture documentation updated
- [ ] Deployment guide finalized
- [ ] Rollback procedures documented and tested
- [ ] Monitoring guide created
- [ ] Troubleshooting guide created
- [ ] Configuration documentation created
- [ ] API documentation final
- [ ] CHANGELOG updated
- [ ] Team trained on new procedures

---

## Phase 4 Success Criteria (GATE)

**All of the following must be true for completion**:

1. Both services deployed successfully to production
2. Zero-downtime deployment achieved
3. Canary monitoring showed no regressions
4. All metrics within expected ranges
5. Monitoring and alerting active
6. Runbooks tested and team trained
7. Embedded Playwright code removed
8. Documentation complete and reviewed
9. Production deployment stable for 1+ hours
10. Team confident in operational procedures

---

## Post-Deployment (Not In Scope But Important)

### Monitoring (Ongoing)

- Daily metric reviews for first week
- Weekly reviews for first month
- Monthly reviews thereafter
- Trend analysis for capacity planning

### Optimization (Future Phases)

- Browser pool tuning (size, timeout)
- Caching optimization (Redis for URL extractions)
- Performance optimization (reduce latency)
- Cost optimization (resource right-sizing)

### Enhancement (Future Phases)

- GraphQL API support
- gRPC protocol replacement
- Kubernetes deployment
- Multi-tenancy support
- Rate limiting and quotas

---

**Document Version**: 1.0
**Status**: Draft
**Last Updated**: 2025-11-20
