---
title: "Playwright Microservice Extraction - Implementation Plan"
description: "Comprehensive implementation plan for extracting Playwright into two dedicated microservices with detailed task breakdown"
audience: [ai-agents, developers, pm, devops]
tags: [playwright, microservices, implementation-plan, infrastructure]
created: 2025-11-20
status: draft
category: "product-planning"
---

# Playwright Microservice Extraction - Implementation Plan

**Based on PRD**: `/docs/project_plans/PRDs/enhancements/playwright-microservice-extraction-v1.md`

**Project Duration**: 8-12 days across 4 phases
**Complexity Level**: Large (L)
**Track**: Full Track (Comprehensive planning required)

---

## Executive Summary

This implementation plan decomposes the Playwright microservice extraction PRD into four phases over 8-12 days, removing 1.1GB of Playwright dependencies from API and Worker containers while maintaining 100% functional parity.

### Key Outcomes

- **70% Image Size Reduction**: API/Worker containers shrink from 1.71GB to <500MB
- **50% Build Time Reduction**: Build time decreases from 5-6 minutes to <3 minutes
- **Independent Scaling**: Playwright services can scale independently from core API
- **Zero Regressions**: 100% functional parity maintained throughout
- **Production Ready**: Comprehensive monitoring, testing, and deployment procedures

### Implementation Approach

**Phase-Based Strategy**:
1. **Phase 1** (3-4 days): Build standalone Playwright services
2. **Phase 2** (2-3 days): Refactor API/Worker to use services
3. **Phase 3** (2-3 days): Comprehensive testing and validation
4. **Phase 4** (1-2 days): Production deployment with monitoring

### Success Metrics

| Metric | Target | Validation |
|--------|--------|-----------|
| API image size | <500MB | Docker images output |
| Build time | <3 minutes | CI/CD metrics |
| Ingestion latency (p95) | <10s | Prometheus |
| Image rendering latency (p95) | <15s | Prometheus |
| Functional parity | 100% | Integration tests |
| Test coverage | >80% | Coverage report |

---

## Phase Overview & Timeline

### Phase 1: Microservice Foundation (3-4 days)

**Objective**: Build standalone Playwright services with baseline functionality

**Duration**: 3-4 days
**Team Composition**: Backend Engineers (2), DevOps Engineer (1), Test Automation Engineer (1)
**Key Deliverable**: Two functioning FastAPI services deployable in Docker Compose

**Major Tasks**:
- Create Dockerfiles for both services
- Implement REST API endpoints (`/v1/extract`, `/v1/render`)
- Add observability (OpenTelemetry, Prometheus, structured logging)
- Comprehensive unit testing (>80% coverage)
- Integration testing with API communication
- Documentation (API specs, Docker procedures)

**Acceptance Criteria**:
- Both services build successfully and start in Docker Compose
- Health check endpoints return valid responses
- Metrics endpoints return Prometheus format
- Unit tests pass with >80% coverage
- Integration tests verify API ↔ service communication

**Detailed Task Breakdown**: See `phase-1-implementation-plan.md`

---

### Phase 2: API/Worker Refactoring (2-3 days)

**Objective**: Refactor API and Worker to use Playwright services

**Duration**: 2-3 days
**Team Composition**: Backend Engineers (2), DevOps Engineer (1)
**Key Deliverable**: API/Worker using external services instead of embedded Playwright

**Major Tasks**:
- Create HTTP client wrappers for both services
- Update AdapterRouter and ImageGenerationService
- Remove Playwright from API/Worker Dockerfiles
- Add environment variable configuration
- Implement circuit breaker and timeout handling
- Comprehensive integration testing
- Verify zero Playwright imports in API/Worker code

**Acceptance Criteria**:
- API container builds without Playwright (<500MB, <3 min)
- Worker container builds without Playwright (<500MB, <3 min)
- All integration tests pass
- All end-to-end tests pass
- Zero regressions in extraction or rendering quality

**Detailed Task Breakdown**: See `phase-2-implementation-plan.md`

---

### Phase 3: Testing & Validation (2-3 days)

**Objective**: Comprehensive testing to ensure production readiness

**Duration**: 2-3 days
**Team Composition**: Test Automation Engineer (1), Backend Engineers (1), DevOps Engineer (1)
**Key Deliverable**: Validated system meeting all non-functional requirements

**Major Tasks**:
- Performance testing (latency percentiles, throughput)
- Load testing (concurrent requests, resource usage)
- Stress testing (graceful degradation under load)
- Error scenario testing (timeouts, crashes, invalid inputs)
- Extraction/rendering quality validation
- Image size and build time verification
- Runbook and operational procedure testing

**Acceptance Criteria**:
- All performance targets met
- All error scenarios handled gracefully
- Extraction/rendering quality matches baseline
- Image size targets achieved
- Runbook procedures documented and tested

**Detailed Task Breakdown**: See `phase-3-implementation-plan.md`

---

### Phase 4: Production Deployment (1-2 days)

**Objective**: Deploy to production with zero downtime and comprehensive monitoring

**Duration**: 1-2 days
**Team Composition**: DevOps Engineer (1), Backend Engineer (1), Platform Lead (1)
**Key Deliverable**: Production deployment complete with monitoring active

**Major Tasks**:
- Set up Prometheus monitoring and alerting
- Document blue-green deployment and rollback procedures
- Perform staging validation
- Perform canary deployment to production
- Monitor metrics during rollout
- Decommission embedded Playwright code
- Update documentation and runbooks

**Acceptance Criteria**:
- Both services deployed and healthy in production
- Monitoring and alerting active
- Zero-downtime deployment successful
- All metrics show expected values
- Runbooks and playbooks documented

**Detailed Task Breakdown**: See `phase-4-implementation-plan.md`

---

## Critical Dependencies & Path

### Dependency Chain

```
Phase 1 Completion (Services Built)
        ↓
    GATE: Services functional
        ↓
Phase 2 (API/Worker Refactored)
        ↓
    GATE: Integration tests pass
        ↓
Phase 3 (Testing & Validation)
        ↓
    GATE: All performance tests pass
        ↓
Phase 4 (Production Deployment)
```

### Critical Path Tasks

**Phase 1**:
- T1.3: Ingestion Service endpoint implementation
- T1.4: Image Service endpoint implementation
- T1.9-10: Test coverage validation

**Phase 2**:
- T2.1-2: HTTP client wrapper implementation
- T2.3-4: AdapterRouter/ImageGenerationService refactoring
- T2.7-8: Dockerfile updates for Playwright removal

**Phase 3**:
- T3.1-5: Performance and load testing
- T3.12-13: Baseline quality validation

**Phase 4**:
- T4.1-3: Monitoring and alerting setup
- T4.8-9: Canary deployment and validation

---

## Subagent Assignments by Phase

### Phase 1: Microservice Foundation

**Lead Coordinator**: Backend Architect (Sonnet)

| Task Group | Subagent | Model | Duration | Dependencies |
|-----------|----------|-------|----------|--------------|
| **T1.1-2: Dockerfiles** | DevOps/Infrastructure Engineer | Sonnet | 4 hours | None |
| **T1.3: Ingestion Service API** | Python Backend Engineer | Sonnet | 6 hours | T1.1 |
| **T1.4: Image Service API** | Python Backend Engineer | Sonnet | 6 hours | T1.2 |
| **T1.5-6: Health/Metrics** | Python Backend Engineer | Haiku | 4 hours | T1.3-4 |
| **T1.7: OpenTelemetry** | Backend/Observability Engineer | Sonnet | 4 hours | T1.3-4 |
| **T1.8: Docker Compose** | DevOps Engineer | Haiku | 2 hours | T1.1-2 |
| **T1.9: Unit Tests** | Test Automation Engineer | Sonnet | 6 hours | T1.3-4 |
| **T1.10: Integration Tests** | Test Automation Engineer | Sonnet | 4 hours | T1.9 |
| **T1.11: Documentation** | Documentation Writer | Haiku | 3 hours | T1.3-10 |

**Total Phase 1 Effort**: ~39 hours across 4-6 engineers
**Estimated Duration**: 3-4 days with parallel work

### Phase 2: API/Worker Refactoring

**Lead Coordinator**: Backend Architect (Sonnet)

| Task Group | Subagent | Model | Duration | Dependencies |
|-----------|----------|-------|----------|--------------|
| **T2.1-2: HTTP Clients** | Python Backend Engineer | Sonnet | 4 hours | Phase 1 Complete |
| **T2.3: AdapterRouter** | Backend Engineer | Sonnet | 4 hours | T2.1 |
| **T2.4: ImageGenerationService** | Backend Engineer | Sonnet | 4 hours | T2.2 |
| **T2.5-6: Code Cleanup** | Python Backend Engineer | Haiku | 3 hours | T2.3-4 |
| **T2.7-8: Dockerfiles** | DevOps Engineer | Haiku | 2 hours | T2.5-6 |
| **T2.9: Configuration** | Backend Engineer | Haiku | 2 hours | T2.1-4 |
| **T2.10: Circuit Breaker** | Backend/Platform Engineer | Sonnet | 3 hours | T2.1-2 |
| **T2.11: Timeout Handling** | Backend Engineer | Haiku | 2 hours | T2.1-2 |
| **T2.12: Integration Tests** | Test Automation Engineer | Sonnet | 6 hours | T2.1-11 |
| **T2.13: E2E Tests** | Test Automation Engineer | Sonnet | 4 hours | T2.12 |

**Total Phase 2 Effort**: ~34 hours across 4-5 engineers
**Estimated Duration**: 2-3 days with parallel work

### Phase 3: Testing & Validation

**Lead Coordinator**: Test Automation Engineer (Sonnet)

| Task Group | Subagent | Model | Duration | Dependencies |
|-----------|----------|-------|----------|--------------|
| **T3.1-2: Performance Tests** | Test Automation Engineer | Sonnet | 6 hours | Phase 2 Complete |
| **T3.3-4: Load Tests** | Test Automation Engineer | Sonnet | 6 hours | Phase 2 Complete |
| **T3.5-9: Error/Stress Tests** | Test Automation Engineer | Sonnet | 8 hours | T3.1-4 |
| **T3.10: Degradation Tests** | Backend Engineer | Haiku | 3 hours | T3.5-9 |
| **T3.11: Resource Tests** | DevOps Engineer | Sonnet | 4 hours | T3.1-10 |
| **T3.12-13: Quality Validation** | Backend Engineer | Sonnet | 4 hours | T3.1-11 |
| **T3.14-15: Verification** | DevOps Engineer | Haiku | 2 hours | T3.12-13 |
| **T3.16: Runbook Testing** | DevOps/SRE Engineer | Haiku | 2 hours | T3.1-15 |

**Total Phase 3 Effort**: ~35 hours across 4-5 engineers
**Estimated Duration**: 2-3 days with parallel work

### Phase 4: Production Deployment

**Lead Coordinator**: DevOps Architect (Sonnet)

| Task Group | Subagent | Model | Duration | Dependencies |
|-----------|----------|-------|----------|--------------|
| **T4.1-3: Monitoring Setup** | DevOps/SRE Engineer | Sonnet | 4 hours | Phase 3 Complete |
| **T4.4-5: Alerting** | DevOps/SRE Engineer | Haiku | 3 hours | T4.1-3 |
| **T4.6-7: Procedures** | DevOps/SRE Engineer | Haiku | 3 hours | T4.1-5 |
| **T4.8: Staging Deployment** | DevOps Engineer | Sonnet | 2 hours | T4.1-7 |
| **T4.9: Canary Deployment** | DevOps Engineer | Sonnet | 2 hours | T4.8 |
| **T4.10: Monitoring Validation** | DevOps/SRE Engineer | Haiku | 2 hours | T4.9 |
| **T4.11: Traffic Gradual Increase** | DevOps Engineer | Haiku | 2 hours | T4.10 |
| **T4.12: Code Decommission** | Backend Engineer | Haiku | 2 hours | T4.11 |
| **T4.13: Documentation** | Documentation Writer | Haiku | 3 hours | T4.1-12 |

**Total Phase 4 Effort**: ~23 hours across 4 engineers
**Estimated Duration**: 1-2 days with parallel work

---

## Detailed Deliverables by Phase

See separate phase implementation plan documents:
- **Phase 1 Details**: `phase-1-implementation-plan.md`
- **Phase 2 Details**: `phase-2-implementation-plan.md`
- **Phase 3 Details**: `phase-3-implementation-plan.md`
- **Phase 4 Details**: `phase-4-implementation-plan.md`

---

## Quality Gates & Checkpoints

### Phase 1 Gate

**Must Pass Before Phase 2**:
- [ ] Both services build successfully in Docker
- [ ] Health endpoints return 200 with valid JSON
- [ ] Metrics endpoints return Prometheus format
- [ ] Unit tests pass with >80% coverage
- [ ] Service communication integration tests pass
- [ ] Performance baseline measured (latency, throughput)

### Phase 2 Gate

**Must Pass Before Phase 3**:
- [ ] API/Worker images build without Playwright errors
- [ ] Image size reduction verified (<500MB)
- [ ] Build time reduction measured (<3 min)
- [ ] All integration tests pass
- [ ] All E2E tests pass with zero regressions
- [ ] Docker Compose deployment validated

### Phase 3 Gate

**Must Pass Before Phase 4**:
- [ ] Performance tests meet latency targets (p95)
- [ ] Load tests show expected throughput
- [ ] Error scenarios handled gracefully
- [ ] Extraction quality >= baseline
- [ ] Rendering quality >= baseline
- [ ] All acceptance criteria checklist items checked

### Phase 4 Gate

**Must Pass Before Production Cut-over**:
- [ ] Staging deployment successful
- [ ] Canary deployment shows no regressions
- [ ] Monitoring and alerting active and valid
- [ ] Runbook procedures tested
- [ ] Team trained on operational procedures
- [ ] Rollback procedure tested and validated

---

## Risk Management

### High-Risk Areas with Mitigations

| Risk | Impact | Likelihood | Mitigation | Owner |
|------|--------|-----------|-----------|-------|
| Playwright service unavailable | High | Medium | Circuit breaker; graceful degradation | Backend Eng |
| Network latency increases response time | Medium | Medium | Timeout config (10s/15s); caching; monitoring | DevOps Eng |
| Browser crash under load | High | Medium | Auto-recovery; monitoring; request queuing | Backend Eng |
| Memory leak in browser pool | High | Low | Memory monitoring; pool limits; periodic restart | DevOps Eng |
| Extraction success rate drops | High | Low | Baseline testing; A/B testing; staged rollout | QA/Test Eng |
| Playwright update breaks functionality | Medium | Low | Version pinning; testing before update | DevOps Eng |
| Monitoring gaps prevent diagnosis | Medium | Medium | Comprehensive logging; metrics; tracing | DevOps Eng |

### Rollback Strategy

**Immediate (within 10 minutes)**:
1. Route requests back to API-embedded Playwright via load balancer reconfig
2. Keep services running for diagnostics
3. Alert team to start root cause analysis

**Short-term (within 1 hour)**:
1. Analyze logs and metrics to identify failure cause
2. Redeploy old API/Worker images if needed
3. Document incident

**Permanent**:
1. Evaluate whether to fix in microservices or return to monolith
2. Plan remediation for next iteration
3. Update runbooks with lessons learned

---

## Resource Requirements

### Team Composition (Recommended)

- **Backend Architects** (1-2): Design reviews, integration point decisions
- **Python Backend Engineers** (2-3): Service implementation, refactoring
- **DevOps/Infrastructure Engineers** (1-2): Docker, observability, deployment
- **Test Automation Engineers** (1-2): Testing strategy, test implementation
- **Documentation Writer** (1): API docs, runbooks, deployment guides
- **Platform/DevOps Lead** (1): Overall coordination, production deployment

### Tools & Infrastructure

- **Docker**: Container building and orchestration
- **Python 3.11+**: Application runtime
- **FastAPI**: Web framework (already in use)
- **Playwright 1.41+**: Browser automation
- **PostgreSQL**: Database (shared with API)
- **Redis**: Caching and message queue (shared)
- **OpenTelemetry**: Observability
- **Prometheus**: Metrics and alerting
- **Docker Compose**: Development environment

### Estimated Effort

**Total Effort**: ~130 hours across 4-6 engineers
**Calendar Time**: 8-12 days with parallel work
**Cost Estimate**: ~$3,000-4,500 (assuming $500/day blended rate)

---

## Technical Architecture Summary

### Service Topology

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Network                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐          ┌──────────────────┐        │
│  │ API Container    │◄────────►│ Ingestion Svc    │        │
│  │ (<500MB)         │ HTTP     │ (with Playwright)│        │
│  │ • FastAPI        │ /extract │ • FastAPI server │        │
│  │ • SQLAlchemy     │          │ • Browser pool   │        │
│  │ • (NO Playwright)│          │ • Chromium       │        │
│  └──────────────────┘          └──────────────────┘        │
│         │                                                    │
│         │                                                    │
│         ├──────────────────┐                               │
│         │                  │                               │
│         ▼                  ▼                               │
│  ┌──────────────────┐  ┌──────────────────┐             │
│  │ Worker Container │  │ Image Svc        │             │
│  │ (<500MB)         │  │ (with Playwright)│             │
│  │ • Celery         │  │ • FastAPI server │             │
│  │ • Redis client   │  │ • Browser pool   │             │
│  │ • (NO Playwright)│  │ • Chromium       │             │
│  └──────────────────┘  └──────────────────┘             │
│                                                            │
│  ┌──────────────────┐  ┌──────────────────┐             │
│  │ PostgreSQL       │  │ Redis            │             │
│  │ Database         │  │ Cache/Queue      │             │
│  └──────────────────┘  └──────────────────┘             │
│                                                            │
└─────────────────────────────────────────────────────────────┘
```

### Key Integration Points

1. **AdapterRouter → Ingestion Service**: HTTP POST `/v1/extract`
2. **ImageGenerationService → Image Service**: HTTP POST `/v1/render`
3. **Observability**: OpenTelemetry spans, Prometheus metrics, structured logging
4. **Configuration**: Environment variables for service endpoints

### Data Flow Patterns

**URL Extraction Flow**:
```
User Request → API.import_from_url() → AdapterRouter.extract()
  → HTTP POST to Ingestion Service
  → Ingestion Service handles extraction
  → Return to API → Update database → Response
```

**Card Generation Flow**:
```
User Action → Celery Task → ImageGenerationService.generate()
  → HTTP POST to Image Service
  → Image Service handles rendering
  → Return bytes → Cache to S3 → Update metadata → Complete
```

---

## Configuration & Deployment

### Environment Variables

**For API/Worker**:
```
PLAYWRIGHT_INGESTION_URL=http://playwright-ingestion:8000
PLAYWRIGHT_IMAGE_URL=http://playwright-image:8000
PLAYWRIGHT_TIMEOUT_INGESTION_S=10
PLAYWRIGHT_TIMEOUT_IMAGE_S=15
```

**For Services**:
```
PLAYWRIGHT_BROWSER_POOL_SIZE=3
PLAYWRIGHT_PAGE_POOL_SIZE=5
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
PROMETHEUS_PORT=9090
```

### Docker Compose Configuration

New services added to `docker-compose.yml`:
```yaml
playwright-ingestion:
  build: ./infra/ingestion
  environment:
    OTEL_EXPORTER_OTLP_ENDPOINT: http://otel-collector:4317
  ports:
    - "8001:8000"
  healthcheck:
    test: curl http://localhost:8000/health

playwright-image:
  build: ./infra/image
  environment:
    OTEL_EXPORTER_OTLP_ENDPOINT: http://otel-collector:4317
  ports:
    - "8002:8000"
  healthcheck:
    test: curl http://localhost:8000/health
```

---

## Success Metrics & Acceptance

### Functional Acceptance

- [ ] URL extraction works end-to-end without regressions
- [ ] Card image generation works end-to-end without regressions
- [ ] Both services have complete API documentation
- [ ] All endpoints documented with examples

### Technical Acceptance

- [ ] API image size: <500MB (70% reduction)
- [ ] Worker image size: <500MB (70% reduction)
- [ ] Build times: <3 minutes (50% reduction)
- [ ] Ingestion latency (p95): <10 seconds
- [ ] Image rendering latency (p95): <15 seconds
- [ ] Test coverage: >80% for new services
- [ ] Zero Playwright imports in API/Worker
- [ ] OpenTelemetry instrumentation complete
- [ ] Prometheus metrics exposed correctly

### Operational Acceptance

- [ ] Both services deployable in Docker Compose
- [ ] Zero-downtime deployment procedure documented
- [ ] Monitoring and alerting configured
- [ ] Health check endpoints validated
- [ ] Runbooks and incident response documented
- [ ] Team trained on operations

---

## Timeline & Milestones

### Proposed Schedule (8-12 days)

| Phase | Start | End | Duration | Milestone |
|-------|-------|-----|----------|-----------|
| 1 | Day 1 | Day 3-4 | 3-4 days | Services Foundation Complete |
| 2 | Day 4-5 | Day 6-7 | 2-3 days | Refactoring Complete |
| 3 | Day 7-8 | Day 9-10 | 2-3 days | Testing Complete |
| 4 | Day 10-11 | Day 11-12 | 1-2 days | Production Deployment |

### Key Milestones

- **Day 3-4**: Both services functional, Docker builds working
- **Day 6-7**: API/Worker using services, zero regressions
- **Day 9-10**: Full test suite passing, performance targets met
- **Day 11-12**: Production deployment complete, monitoring active

---

## Approval & Sign-off

This implementation plan is based on the approved PRD:
- **PRD**: `/docs/project_plans/PRDs/enhancements/playwright-microservice-extraction-v1.md`
- **PRD Status**: Draft (Ready for Review)
- **PRD Date**: 2025-11-20

**Plan Status**: Draft - Ready for Technical Review

**Approvals Required**:
- [ ] Technical Lead / Backend Architect
- [ ] DevOps / Infrastructure Lead
- [ ] Product Manager
- [ ] QA / Testing Lead

---

## References & Related Documents

### Architecture & Design
- `/docs/architecture/playwright-optimization-analysis.md` - Phase 1 analysis
- `/docs/development/docker-optimization.md` - Docker optimization strategies
- `/docs/project_plans/playwright-infrastructure/playwright-infrastructure-v1.md` - Phase 1 infrastructure

### Implementation Details
- `phase-1-implementation-plan.md` - Phase 1 detailed tasks
- `phase-2-implementation-plan.md` - Phase 2 detailed tasks
- `phase-3-implementation-plan.md` - Phase 3 detailed tasks
- `phase-4-implementation-plan.md` - Phase 4 detailed tasks

### Code References
- `apps/api/dealbrain_api/services/image_generation.py` - Current implementation
- `apps/api/dealbrain_api/adapters/playwright.py` - PlaywrightAdapter
- `apps/api/dealbrain_api/adapters/browser_pool.py` - Browser pool management
- `infra/api/Dockerfile` - Current API Docker build
- `infra/worker/Dockerfile` - Current Worker Docker build

---

**Document Version**: 1.0
**Status**: Draft - Ready for Review
**Last Updated**: 2025-11-20
**Next Review**: Upon Technical Lead Review
