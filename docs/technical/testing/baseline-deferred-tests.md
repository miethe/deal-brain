# Baseline Valuation System - Deferred Test Plan

This document outlines tests that should be implemented in a dedicated testing sprint for the baseline valuation system. These tests are deferred to maintain velocity while ensuring core functionality is working, but should be completed before production deployment.

## Priority Levels

- **P1 (Critical)**: Must be completed before production
- **P2 (Important)**: Should be completed for system reliability
- **P3 (Nice-to-have)**: Can be added for comprehensive coverage

## Integration Tests

### End-to-End Workflows (P1)

1. **Baseline Ingestion → Evaluation → Breakdown**
   - Test loading baseline from JSON file
   - Verify ruleset creation with correct priority (5)
   - Evaluate listings and verify layer attribution
   - Check valuation breakdown contains baseline layer
   - Estimated effort: 2-3 hours

2. **Multi-Ruleset Evaluation with Three Layers**
   - Create baseline ruleset (priority 5)
   - Create basic ruleset (priority 10)
   - Create advanced ruleset (priority 15)
   - Verify cumulative evaluation and telemetry events
   - Estimated effort: 3-4 hours

3. **Override Persistence and Retrieval**
   - Test creating overrides via API
   - Verify override application in evaluation
   - Test override reset functionality
   - Verify audit log entries
   - Estimated effort: 2-3 hours

4. **Diff/Adopt Workflow (P1)**
   - Load initial baseline
   - Create candidate baseline with changes
   - Generate diff and verify change detection
   - Adopt changes and verify database updates
   - Verify audit logging for all operations
   - Estimated effort: 4-5 hours

### API Integration Tests (P2)

5. **Baseline Metadata Endpoint**
   - Test with active baseline
   - Test with no baseline
   - Verify field definitions returned
   - Estimated effort: 1-2 hours

6. **Metrics Endpoints**
   - Test layer influence calculation
   - Test top rules aggregation
   - Test override churn calculation
   - Verify correct percentages and aggregations
   - Estimated effort: 2-3 hours

7. **Health Check Endpoints**
   - Test with healthy baseline
   - Test with stale baseline (>90 days)
   - Test with missing adjustments group
   - Test hash mismatch detection
   - Estimated effort: 1-2 hours

## Frontend Tests (P2)

### Entity Tabs Component

8. **Entity Navigation**
   - Test tab switching between entities
   - Verify state persistence across tabs
   - Test keyboard navigation (arrow keys)
   - Estimated effort: 2-3 hours

9. **Field Rendering**
   - Test scalar field display and editing
   - Test presence field checkbox behavior
   - Test multiplier field validation (0-2 range)
   - Test formula field syntax validation
   - Estimated effort: 3-4 hours

### Override Controls

10. **Override Creation**
    - Test creating override for each field type
    - Verify immediate UI update
    - Test validation errors
    - Estimated effort: 2-3 hours

11. **Override Management**
    - Test resetting individual overrides
    - Test bulk reset functionality
    - Test override persistence across sessions
    - Estimated effort: 2-3 hours

### Preview Impact Panel

12. **Impact Calculation**
    - Test real-time impact calculation
    - Verify affected listings count
    - Test adjustment range display
    - Estimated effort: 2-3 hours

13. **Visual Indicators**
    - Test color coding for value changes
    - Test loading states
    - Test error states
    - Estimated effort: 1-2 hours

### Diff & Adopt Wizard (P1)

14. **Diff Generation**
    - Test diff display with various change types
    - Test filtering by entity/field
    - Test change highlighting
    - Estimated effort: 2-3 hours

15. **Selective Adoption**
    - Test selecting/deselecting changes
    - Test apply button enablement logic
    - Test confirmation dialogs
    - Estimated effort: 2-3 hours

## Performance Tests (P1)

16. **Evaluation Latency**
    - Measure baseline evaluation time
    - Compare with non-baseline evaluation
    - Target: <5% performance degradation
    - Test with 1000+ listings
    - Estimated effort: 2-3 hours

17. **UI Rendering Performance**
    - Test with 50+ fields per entity
    - Measure initial render time
    - Test scroll performance
    - Target: <100ms for field updates
    - Estimated effort: 2-3 hours

18. **Large Baseline Parsing**
    - Test with 1MB+ JSON files
    - Test with 500+ field definitions
    - Verify memory usage stays reasonable
    - Estimated effort: 1-2 hours

## Regression Tests (P2)

19. **Baseline Instantiation Idempotency**
    - Test repeated instantiation with same file
    - Verify no duplicate rulesets created
    - Verify hash-based deduplication works
    - Estimated effort: 1-2 hours

20. **Version Numbering**
    - Test version derivation from payload
    - Test version incrementing on changes
    - Verify version uniqueness
    - Estimated effort: 1-2 hours

21. **Override Reset Functionality**
    - Test reset doesn't affect baseline values
    - Test reset audit logging
    - Test reset with concurrent users
    - Estimated effort: 2-3 hours

## Error Handling Tests (P1)

22. **Invalid Baseline JSON**
    - Test malformed JSON
    - Test missing required fields
    - Test invalid field types
    - Verify graceful error messages
    - Estimated effort: 2-3 hours

23. **Concurrent Operations**
    - Test concurrent override updates
    - Test concurrent diff/adopt operations
    - Test race conditions in evaluation
    - Estimated effort: 3-4 hours

24. **Network Failures**
    - Test API timeout handling
    - Test partial data loading
    - Test retry mechanisms
    - Estimated effort: 2-3 hours

## Security Tests (P1)

25. **Authorization**
    - Test baseline admin operations require permission
    - Test override creation permissions
    - Test audit log access control
    - Estimated effort: 2-3 hours

26. **Input Validation**
    - Test SQL injection in field names
    - Test XSS in override values
    - Test path traversal in baseline file paths
    - Estimated effort: 2-3 hours

## Database Tests (P2)

27. **Migration Rollback**
    - Test baseline audit log migration up/down
    - Verify data preservation
    - Test with existing data
    - Estimated effort: 1-2 hours

28. **Constraint Validation**
    - Test foreign key constraints
    - Test unique constraints
    - Test cascade deletes
    - Estimated effort: 1-2 hours

## Telemetry Tests (P3)

29. **Event Emission**
    - Verify layer contribution events
    - Test Prometheus metrics
    - Test event payloads
    - Estimated effort: 2-3 hours

30. **Metric Aggregation**
    - Test aggregation accuracy
    - Test time-window calculations
    - Test edge cases (no data, single listing)
    - Estimated effort: 2-3 hours

## Audit Log Tests (P2)

31. **Operation Logging**
    - Test all operation types logged
    - Verify payload completeness
    - Test error logging
    - Estimated effort: 2-3 hours

32. **Log Querying**
    - Test filtering by operation
    - Test filtering by actor
    - Test pagination
    - Estimated effort: 1-2 hours

## Load Tests (P3)

33. **Bulk Operations**
    - Test with 10,000+ listings
    - Test with 100+ concurrent users
    - Measure system degradation
    - Estimated effort: 3-4 hours

34. **Memory Leaks**
    - Test long-running evaluation sessions
    - Monitor memory usage over time
    - Test cache invalidation
    - Estimated effort: 2-3 hours

## Documentation Tests (P3)

35. **API Documentation**
    - Verify all endpoints documented
    - Test example requests/responses
    - Verify schema accuracy
    - Estimated effort: 1-2 hours

36. **User Guide Accuracy**
    - Test all documented workflows
    - Verify screenshots match current UI
    - Test troubleshooting steps
    - Estimated effort: 1-2 hours

## Backup & Recovery Tests (P2)

37. **Baseline Backup**
    - Test exporting baseline to JSON
    - Test importing from backup
    - Verify data integrity
    - Estimated effort: 2-3 hours

38. **Override Backup**
    - Test exporting overrides
    - Test selective restoration
    - Test conflict resolution
    - Estimated effort: 2-3 hours

## Compatibility Tests (P3)

39. **Browser Compatibility**
    - Test on Chrome, Firefox, Safari, Edge
    - Test mobile responsiveness
    - Test accessibility features
    - Estimated effort: 3-4 hours

40. **API Version Compatibility**
    - Test backward compatibility
    - Test version negotiation
    - Test deprecation warnings
    - Estimated effort: 2-3 hours

## Summary

- **Total Tests**: 40
- **P1 (Critical)**: 12 tests (~35 hours)
- **P2 (Important)**: 20 tests (~45 hours)
- **P3 (Nice-to-have)**: 8 tests (~20 hours)
- **Total Estimated Effort**: ~100 hours (2-3 weeks for one developer)

## Recommended Execution Order

1. **Sprint 1 (Week 1)**: P1 Integration and Performance Tests
2. **Sprint 2 (Week 2)**: P1 Frontend and Security Tests
3. **Sprint 3 (Week 3)**: P2 Tests
4. **Sprint 4 (Optional)**: P3 Tests

## Test Infrastructure Requirements

- Test database with seed data
- Mock baseline JSON files
- Performance monitoring tools
- Load testing framework (e.g., Locust)
- Browser automation (e.g., Playwright)
- API testing framework (e.g., pytest-asyncio)

## Success Criteria

- All P1 tests passing
- 90% of P2 tests passing
- No performance regression > 10%
- Zero security vulnerabilities
- Audit log coverage > 95%