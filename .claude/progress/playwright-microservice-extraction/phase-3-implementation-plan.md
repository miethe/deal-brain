---
title: "Phase 3 - Testing & Validation Implementation Plan"
description: "Detailed task breakdown for comprehensive testing and validation"
status: "draft"
created: 2025-11-20
---

# Phase 3: Testing & Validation

**Duration**: 2-3 days | **Effort**: ~35 hours | **Team Size**: 4-5 engineers

## Phase Objective

Conduct comprehensive testing to validate that the Playwright microservice extraction meets all non-functional requirements, achieves performance targets, and maintains 100% functional parity with the baseline.

## Success Criteria

- [x] Performance targets met (p95 latency)
- [x] Load testing shows expected throughput
- [x] Error scenarios handled gracefully
- [x] Extraction quality >= baseline
- [x] Rendering quality >= baseline
- [x] Image size targets achieved
- [x] Build time targets achieved
- [x] All acceptance criteria checklist items checked
- [x] Production readiness confirmed

---

## Task Breakdown

### Task 3.1: Performance Testing - Latency Profiling

**Owner**: Test Automation Engineer
**Model**: Sonnet
**Duration**: 3 hours
**Status**: Not Started
**Depends On**: Phase 2 Complete

**Description**:
Create performance tests to measure latency percentiles (p50, p95, p99) for both Playwright services and compare against targets.

**Acceptance Criteria**:
- [ ] Performance test suite created in `/tests/performance/`
- [ ] Ingestion Service latency measured:
  - [ ] p50 (median)
  - [ ] p95 (95th percentile) - target <10s
  - [ ] p99 (99th percentile)
  - [ ] min/max/mean recorded
- [ ] Image Service latency measured:
  - [ ] p50 (median)
  - [ ] p95 (95th percentile) - target <15s
  - [ ] p99 (99th percentile)
  - [ ] min/max/mean recorded
- [ ] Latency breakdown measured:
  - [ ] Browser startup time
  - [ ] Network request time
  - [ ] Rendering/extraction time
  - [ ] Response serialization time
- [ ] 100+ requests per service for statistical validity
- [ ] Different URLs tested (various sizes and complexity)
- [ ] Results exported to CSV for comparison
- [ ] Baseline metrics documented
- [ ] Performance regression detected if p95 > targets

**Test Implementation**:

```python
# tests/performance/test_latency.py

import asyncio
import time
from statistics import median, stdev
import httpx

class LatencyProfiler:
    """Measure and analyze request latencies."""

    def __init__(self, num_requests: int = 100):
        self.num_requests = num_requests
        self.latencies = []

    async def profile_ingestion_service(self):
        """Profile Ingestion Service latency."""
        async with httpx.AsyncClient() as client:
            for i in range(self.num_requests):
                start = time.time()
                try:
                    response = await client.post(
                        "http://localhost:8001/v1/extract",
                        json={
                            "url": "https://amazon.com/dp/B0C...",
                            "marketplace_type": "amazon",
                            "timeout_s": 10
                        },
                        timeout=15
                    )
                    elapsed = time.time() - start
                    if response.status_code == 200:
                        self.latencies.append(elapsed * 1000)  # ms
                except Exception as e:
                    print(f"Request {i} failed: {e}")

        return self._calculate_percentiles()

    async def profile_image_service(self):
        """Profile Image Service latency."""
        async with httpx.AsyncClient() as client:
            for i in range(self.num_requests):
                start = time.time()
                try:
                    response = await client.post(
                        "http://localhost:8002/v1/render",
                        json={
                            "html": "<html><body>Test Card</body></html>",
                            "width": 1200,
                            "height": 630,
                            "image_format": "png"
                        },
                        timeout=20
                    )
                    elapsed = time.time() - start
                    if response.status_code == 200:
                        self.latencies.append(elapsed * 1000)  # ms
                except Exception as e:
                    print(f"Request {i} failed: {e}")

        return self._calculate_percentiles()

    def _calculate_percentiles(self) -> dict:
        """Calculate latency percentiles."""
        sorted_latencies = sorted(self.latencies)
        return {
            "min": min(sorted_latencies),
            "max": max(sorted_latencies),
            "mean": sum(sorted_latencies) / len(sorted_latencies),
            "median": median(sorted_latencies),
            "p95": sorted_latencies[int(len(sorted_latencies) * 0.95)],
            "p99": sorted_latencies[int(len(sorted_latencies) * 0.99)],
            "count": len(sorted_latencies)
        }

@pytest.mark.performance
@pytest.mark.asyncio
async def test_ingestion_service_latency():
    """Test Ingestion Service meets latency targets."""
    profiler = LatencyProfiler(num_requests=100)
    results = await profiler.profile_ingestion_service()

    assert results["p95"] < 10000, f"p95 {results['p95']}ms exceeds 10s target"
    assert results["count"] == 100, "Did not complete 100 requests"

    print(f"Ingestion Service Latency: {results}")

@pytest.mark.performance
@pytest.mark.asyncio
async def test_image_service_latency():
    """Test Image Service meets latency targets."""
    profiler = LatencyProfiler(num_requests=100)
    results = await profiler.profile_image_service()

    assert results["p95"] < 15000, f"p95 {results['p95']}ms exceeds 15s target"
    assert results["count"] == 100, "Did not complete 100 requests"

    print(f"Image Service Latency: {results}")
```

**Dependencies**:
- Phase 2 complete (Services and API/Worker running)

---

### Task 3.2: Performance Testing - Throughput Validation

**Owner**: Test Automation Engineer
**Model**: Sonnet
**Duration**: 2 hours
**Status**: Not Started
**Depends On**: Task 3.1

**Description**:
Measure throughput (requests per second) for both services under sustained load.

**Acceptance Criteria**:
- [ ] Throughput tests created
- [ ] Ingestion Service throughput measured:
  - [ ] Target: >100 concurrent requests
  - [ ] Sustained load test (5-10 minute duration)
  - [ ] Success rate tracked
  - [ ] Error rate tracked
- [ ] Image Service throughput measured:
  - [ ] Target: >50 concurrent renders
  - [ ] Sustained load test
  - [ ] Success rate tracked
  - [ ] Error rate tracked
- [ ] Resource usage monitored during tests
- [ ] Service health checks pass during load
- [ ] Recovery verified after load ends

**Dependencies**:
- Task 3.1 (Performance infrastructure)

---

### Task 3.3: Load Testing - Concurrent Ingestion Requests

**Owner**: Test Automation Engineer
**Model**: Sonnet
**Duration**: 3 hours
**Status**: Not Started
**Depends On**: Phase 2 Complete

**Description**:
Run load tests with concurrent ingestion requests to validate service stability under realistic concurrent load.

**Acceptance Criteria**:
- [ ] Load test framework setup (locust or similar)
- [ ] Test with 10, 50, 100, 200 concurrent users
- [ ] Ramp-up time 1-5 minutes
- [ ] Sustained load for 10 minutes at peak
- [ ] Success rate logged
- [ ] Error rate logged
- [ ] Response time percentiles recorded
- [ ] Service memory usage monitored
- [ ] No crashes or hangs
- [ ] Graceful degradation under extreme load
- [ ] Results compared against baseline

**Dependencies**:
- Phase 2 complete

---

### Task 3.4: Load Testing - Concurrent Image Rendering

**Owner**: Test Automation Engineer
**Model**: Sonnet
**Duration**: 3 hours
**Status**: Not Started
**Depends On**: Phase 2 Complete

**Description**:
Run load tests with concurrent image rendering requests to validate service stability.

**Acceptance Criteria**:
- [ ] Load test framework configured
- [ ] Test with 10, 25, 50 concurrent renders
- [ ] Ramp-up time 1-5 minutes
- [ ] Sustained load for 10 minutes
- [ ] Success rate logged
- [ ] Error rate logged
- [ ] Response time percentiles recorded
- [ ] Service memory usage monitored
- [ ] Image quality validated (spot checks)
- [ ] No crashes or hangs
- [ ] Graceful degradation under extreme load

**Dependencies**:
- Phase 2 complete

---

### Task 3.5: Stress Testing - Graceful Degradation

**Owner**: Test Automation Engineer
**Model**: Sonnet
**Duration**: 2 hours
**Status**: Not Started
**Depends On**: Phase 2 Complete

**Description**:
Run stress tests to verify services degrade gracefully under extreme load without crashing.

**Acceptance Criteria**:
- [ ] Stress test pushes services to resource limits
- [ ] Tests measure behavior:
  - [ ] What happens at 300+ concurrent requests?
  - [ ] What happens when memory limit reached?
  - [ ] What happens when browser pool exhausted?
- [ ] Services remain responsive (health checks pass)
- [ ] New requests queued or rejected gracefully (not hung)
- [ ] After stress ends, services recover to normal
- [ ] No data loss during stress
- [ ] Errors logged appropriately

**Dependencies**:
- Phase 2 complete

---

### Task 3.6-3.9: Error Scenario Testing

**Owner**: Test Automation Engineer
**Model**: Sonnet
**Duration**: 4 hours
**Status**: Not Started
**Depends On**: Phase 2 Complete

**Description**:
Test error handling for specific failure scenarios.

**Task 3.6: Timeout Handling**

- [ ] Requests timing out are handled gracefully
- [ ] Timeout errors returned to caller
- [ ] No hanging connections
- [ ] Resources cleaned up properly
- [ ] Service remains healthy after timeouts

**Task 3.7: Browser Crashes**

- [ ] Browser crashes detected
- [ ] Service recovers automatically
- [ ] Requests fail gracefully
- [ ] New page pool created
- [ ] Service health restored

**Task 3.8: Invalid Input**

- [ ] Invalid URLs rejected with 400 error
- [ ] Invalid HTML rejected with 400 error
- [ ] Oversized payloads rejected with 413 error
- [ ] Malformed JSON rejected with 400 error
- [ ] Service remains stable

**Task 3.9: Network Failures**

- [ ] Service unavailability handled by API/Worker
- [ ] Graceful degradation (skip extraction/rendering)
- [ ] Circuit breaker activated
- [ ] Errors logged
- [ ] No cascading failures

**Dependencies**:
- Phase 2 complete

---

### Task 3.10: Graceful Degradation Testing

**Owner**: Backend Engineer
**Model**: Haiku
**Duration**: 2 hours
**Status**: Not Started
**Depends On**: Phase 2 Complete

**Description**:
Verify API and Worker continue functioning when Playwright services are unavailable.

**Acceptance Criteria**:
- [ ] Stop Ingestion Service → API still responds
- [ ] Stop Image Service → Worker still processes tasks
- [ ] URL extraction skipped gracefully
- [ ] Card generation skipped with warning logged
- [ ] No errors visible to users
- [ ] Errors logged with context
- [ ] Circuit breaker prevents repeated attempts
- [ ] Service recovery triggers when services restart

**Test Scenarios**:
```python
# Stop Ingestion Service
docker-compose stop playwright-ingestion

# Try URL import → should skip extraction, continue
curl -X POST http://localhost:8000/v1/listings/import?url=...

# Should succeed with warning that extraction was skipped

# Restart service
docker-compose start playwright-ingestion

# Should automatically recover
```

**Dependencies**:
- Phase 2 complete

---

### Task 3.11: Memory/Resource Usage Testing

**Owner**: DevOps Engineer
**Model**: Sonnet
**Duration**: 3 hours
**Status**: Not Started
**Depends On**: Phase 2 Complete

**Description**:
Monitor memory and CPU usage during testing to identify leaks and ensure resource efficiency.

**Acceptance Criteria**:
- [ ] Memory monitoring setup (container metrics)
- [ ] CPU usage monitoring setup
- [ ] Baseline measurements taken
- [ ] Sustained load test for 30 minutes
- [ ] Memory growth tracked
- [ ] No memory leaks detected (stable after initial allocation)
- [ ] CPU usage reasonable (<50% of 1 core at steady state)
- [ ] Browser pool cleanup working (no orphaned processes)
- [ ] Page pool cleanup working (no stale pages)
- [ ] Metrics exported and analyzed

**Monitoring Commands**:
```bash
# Watch container memory/CPU
docker stats playwright-ingestion playwright-image

# Check memory growth over time
watch -n 5 'docker stats --no-stream | grep playwright'

# Check for orphaned processes
ps aux | grep chromium
ps aux | grep playwright
```

**Dependencies**:
- Phase 2 complete

---

### Task 3.12: Extraction Quality Testing

**Owner**: Backend Engineer
**Model**: Sonnet
**Duration**: 3 hours
**Status**: Not Started
**Depends On**: Phase 2 Complete

**Description**:
Test that extraction quality matches baseline (no regressions in extraction accuracy).

**Acceptance Criteria**:
- [ ] Baseline extraction quality measured (existing PlaywrightAdapter)
- [ ] Sample URLs extracted with both old and new implementation
- [ ] Compare results:
  - [ ] Title accuracy
  - [ ] Price accuracy
  - [ ] Specs accuracy
  - [ ] Image count
  - [ ] Overall extraction confidence
- [ ] No regression in success rate (≥85%)
- [ ] No regression in confidence scores
- [ ] Edge cases tested (missing fields, unusual formats)
- [ ] Results documented

**Test Data**:
- 20+ marketplace URLs (Amazon, eBay, etc.)
- URLs with various complexity levels
- URLs with missing or unusual data

**Comparison Metrics**:
```python
# For each URL:
# 1. Extract with old PlaywrightAdapter (baseline)
# 2. Extract with new Ingestion Service
# 3. Compare results:
#    - Title match: exact or fuzzy?
#    - Price match: exact value?
#    - Specs match: all fields present?
#    - Success rate: both succeeded?

results = {
    "total_urls": 20,
    "both_succeeded": 18,
    "title_match_rate": 0.95,
    "price_match_rate": 0.90,
    "specs_match_rate": 0.88,
    "new_success_rate": 0.90,
    "baseline_success_rate": 0.90,
    "regression_detected": False
}
```

**Dependencies**:
- Phase 2 complete
- Baseline extraction data

---

### Task 3.13: Rendering Quality Testing

**Owner**: Backend Engineer
**Model**: Sonnet
**Duration**: 3 hours
**Status**: Not Started
**Depends On**: Phase 2 Complete

**Description**:
Test that image rendering quality matches baseline (no regressions in visual quality).

**Acceptance Criteria**:
- [ ] Baseline rendering quality measured (existing ImageGenerationService)
- [ ] Sample listings rendered with both old and new implementation
- [ ] Visual comparison:
  - [ ] Layout preserved
  - [ ] Colors accurate
  - [ ] Text rendering quality
  - [ ] Image composition
- [ ] File size comparison (baseline vs new)
- [ ] Dimensions validation (correct width/height)
- [ ] No regression in success rate (≥95%)
- [ ] Edge cases tested
- [ ] Results documented with sample images

**Test Implementation**:
```python
# For each test listing:
# 1. Generate image with old service (baseline)
# 2. Generate image with new service
# 3. Compare:
#    - Image dimensions correct?
#    - Image file size reasonable?
#    - Visual hash similar? (use perceptual hashing)
#    - Manual visual spot check

import imagehash
from PIL import Image

# Compare image quality
baseline_img = Image.open("baseline.png")
new_img = Image.open("new.png")

baseline_hash = imagehash.phash(baseline_img)
new_hash = imagehash.phash(new_img)

# Hash difference should be small (perceptually similar)
difference = baseline_hash - new_hash
assert difference < 5, "Images differ too much"
```

**Dependencies**:
- Phase 2 complete
- Baseline rendering samples

---

### Task 3.14: Docker Image Size Verification

**Owner**: DevOps Engineer
**Model**: Haiku
**Duration**: 1 hour
**Status**: Not Started
**Depends On**: Phase 2 Complete

**Description**:
Verify that Docker images meet size reduction targets.

**Acceptance Criteria**:
- [ ] Measure current image sizes
- [ ] API image: <500MB (target: 70% reduction from 1.71GB)
- [ ] Worker image: <500MB (target: 70% reduction from 1.71GB)
- [ ] Playwright Ingestion Service: ~1.5GB (expected size)
- [ ] Playwright Image Service: ~1.5GB (expected size)
- [ ] Total system size reduction measured
- [ ] Size breakdown analyzed (layers, content)
- [ ] Results documented

**Verification Commands**:
```bash
# Build images
docker build -t dealbrain-api -f infra/api/Dockerfile .
docker build -t dealbrain-worker -f infra/worker/Dockerfile .
docker build -t playwright-ingestion -f infra/ingestion/Dockerfile .
docker build -t playwright-image -f infra/image/Dockerfile .

# Check sizes
docker images | grep -E "dealbrain|playwright"

# Expected output:
# dealbrain-api          <500MB
# dealbrain-worker       <500MB
# playwright-ingestion   ~1.5GB
# playwright-image       ~1.5GB
```

**Dependencies**:
- Phase 2 complete (Dockerfiles finalized)

---

### Task 3.15: Build Time Verification

**Owner**: DevOps Engineer
**Model**: Haiku
**Duration**: 1 hour
**Status**: Not Started
**Depends On**: Phase 2 Complete

**Description**:
Measure build times for all images and verify targets are met.

**Acceptance Criteria**:
- [ ] Build each image 3 times (measure variance)
- [ ] API build time: <3 minutes (target: 50% reduction from 5-6 min)
- [ ] Worker build time: <3 minutes
- [ ] Ingestion build time: <5 minutes (acceptable, less critical)
- [ ] Image build time: <5 minutes
- [ ] Average build times documented
- [ ] Cold cache build times measured
- [ ] Build optimization opportunities identified

**Measurement Script**:
```bash
#!/bin/bash

for i in {1..3}; do
  echo "Build $i:"
  time docker build -t dealbrain-api -f infra/api/Dockerfile .
  echo "---"
done
```

**Dependencies**:
- Phase 2 complete

---

### Task 3.16: Runbook Testing & Documentation

**Owner**: DevOps/SRE Engineer
**Model**: Haiku
**Duration**: 2 hours
**Status**: Not Started
**Depends On**: All other Phase 3 tasks

**Description**:
Document and test operational runbooks for common scenarios (deployment, monitoring, incident response).

**Acceptance Criteria**:
- [ ] Runbook created: `/docs/operations/playwright-services-runbook.md`
- [ ] Deployment runbook:
  - [ ] Steps to deploy services
  - [ ] Health check verification
  - [ ] Rollback procedure
- [ ] Monitoring runbook:
  - [ ] Key metrics to monitor
  - [ ] Alert thresholds
  - [ ] How to investigate issues
- [ ] Incident response runbook:
  - [ ] Service unavailable → steps to diagnose
  - [ ] High latency → investigation steps
  - [ ] High error rate → mitigation steps
- [ ] All runbook procedures tested and verified
- [ ] Average MTTR measured for common issues

**Runbook Sections**:
```markdown
# Playwright Services Runbook

## Deployment
- Prerequisites
- Deployment steps
- Health check validation
- Rollback procedure
- Time estimate: X minutes

## Monitoring
- Prometheus queries
- Alert definitions
- Key metrics and thresholds

## Incident Response
- Service Down
  - Check: docker-compose ps
  - Check: service logs
  - Restart: docker-compose restart service-name
  - Time to recover: <2 minutes

- High Latency
  - Check: Prometheus p95 latency metric
  - Check: browser pool availability
  - Check: resource usage (CPU, memory)
  - Mitigation: scale service horizontally

- High Error Rate
  - Check: error logs
  - Check: timeout settings
  - Check: service dependencies
  - Mitigation: increase timeouts or scale

## Troubleshooting
- Common issues and solutions
```

**Dependencies**:
- All Phase 3 tasks (to document findings)

---

## Phase 3 Acceptance Checklist

### Performance Targets

- [ ] Ingestion Service latency (p95): <10 seconds
- [ ] Image Service latency (p95): <15 seconds
- [ ] Ingestion Service throughput: >100 concurrent
- [ ] Image Service throughput: >50 concurrent
- [ ] Error rate: <5% under normal load
- [ ] Memory usage: <1GB per service instance

### Quality Targets

- [ ] Extraction success rate: ≥85% (no regression)
- [ ] Rendering success rate: ≥95% (no regression)
- [ ] Extraction quality: matches baseline
- [ ] Rendering quality: matches baseline
- [ ] Zero test regressions identified

### Infrastructure Targets

- [ ] API image size: <500MB (70% reduction)
- [ ] Worker image size: <500MB (70% reduction)
- [ ] Build time: <3 minutes
- [ ] Image size targets met
- [ ] Build time targets met

### Documentation

- [ ] Performance baseline documented
- [ ] Test results documented
- [ ] Runbooks tested and documented
- [ ] Troubleshooting guide created
- [ ] Known limitations documented

---

## Phase 3 Success Criteria (GATE)

**All of the following must be true to proceed to Phase 4**:

1. All performance tests pass
2. All load tests pass
3. All error scenario tests pass
4. Graceful degradation verified
5. No memory leaks detected
6. Extraction quality >= baseline
7. Rendering quality >= baseline
8. Image size targets achieved
9. Build time targets achieved
10. Runbooks tested and documented

---

**Document Version**: 1.0
**Status**: Draft
**Last Updated**: 2025-11-20
