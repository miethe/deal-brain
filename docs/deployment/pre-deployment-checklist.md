---
title: "Pre-Deployment Checklist"
description: "Comprehensive checklist of security, performance, and operational requirements before deploying Deal Brain to production"
audience: [developers, devops, pm, qa]
tags: [deployment, security, checklist, production-readiness]
created: 2025-11-20
updated: 2025-11-20
category: "configuration-deployment"
status: published
related:
  - /docs/deployment/DEPLOYMENT_STRATEGY.md
  - /docs/deployment/environment-configuration.md
---

# Pre-Deployment Checklist

This checklist ensures Deal Brain is production-ready before public deployment. Complete all sections before going live.

---

## Security Hardening

### Application Security

- [ ] **Secret Scanning**
  - No credentials found in git history
  ```bash
  trufflehog filesystem . --json | jq
  ```
  - All secrets moved to environment variables
  - .env files in .gitignore

- [ ] **Dependency Vulnerabilities**
  - Python dependencies scanned with Safety
  ```bash
  poetry run safety check
  ```
  - JavaScript dependencies scanned with npm audit
  ```bash
  pnpm audit --audit-level=moderate
  ```
  - No high/critical vulnerabilities without mitigation plan

- [ ] **OWASP Top 10 Review**
  - [ ] Broken Authentication: Authentication/authorization implemented
  - [ ] Sensitive Data Exposure: HTTPS enforced, data encrypted at rest
  - [ ] Injection: Input validation on all endpoints, parameterized queries
  - [ ] Broken Access Control: Role-based access control (if applicable)
  - [ ] Security Misconfiguration: Production config reviewed, debug off
  - [ ] XSS Protection: React escapes user input, CSP headers set
  - [ ] CSRF Protection: CSRF tokens on state-changing requests
  - [ ] Insecure Deserialization: No pickle/eval on untrusted data
  - [ ] Broken API: API authentication required, rate limiting set
  - [ ] Insufficient Logging: Security events logged and monitored

- [ ] **Security Headers**
  - [ ] Content-Security-Policy header set
  - [ ] X-Frame-Options: DENY or SAMEORIGIN
  - [ ] X-Content-Type-Options: nosniff
  - [ ] Strict-Transport-Security: max-age >= 31536000
  - [ ] X-XSS-Protection header set
  - [ ] Referrer-Policy header set

- [ ] **API Security**
  - [ ] API endpoints require authentication
  - [ ] Rate limiting configured (e.g., 100 requests/minute per IP)
  - [ ] Request validation on all endpoints
  - [ ] Error messages don't leak sensitive info
  - [ ] CORS properly configured

- [ ] **Database Security**
  - [ ] Database user has minimal required permissions
  - [ ] Connection requires strong password
  - [ ] SSL/TLS enabled for database connections
  - [ ] Database backups encrypted
  - [ ] No default credentials used

### Infrastructure Security

- [ ] **Container Security**
  - [ ] Dockerfile runs as non-root user
  ```dockerfile
  USER 1000
  ```
  - [ ] No secrets in container images
  - [ ] No development tools in production image
  - [ ] Images scanned with Trivy
  ```bash
  trivy image ghcr.io/username/deal-brain-api:latest
  ```
  - [ ] No critical vulnerabilities

- [ ] **Network Security**
  - [ ] HTTPS enforced (HTTP redirects to HTTPS)
  - [ ] TLS 1.2+ required
  - [ ] Strong cipher suites configured
  - [ ] Database not accessible from internet
  - [ ] Redis requires authentication
  - [ ] Internal services isolated

- [ ] **Access Control**
  - [ ] GitHub branch protection enabled on main
  - [ ] Require pull request reviews before merge
  - [ ] Require status checks to pass before merge
  - [ ] Dismiss stale pull request approvals
  - [ ] Production deployment requires manual approval
  - [ ] Deployment logs auditable

- [ ] **Secrets Rotation**
  - [ ] Plan for rotating secrets every 90 days
  - [ ] SECRET_KEY changed from development default
  - [ ] Database password is strong and unique
  - [ ] API keys for external services are production keys
  - [ ] Credentials not shared between environments

---

## Performance Optimization

### Backend Performance

- [ ] **Database Performance**
  - [ ] Database indexes on frequently queried columns
  - [ ] EXPLAIN ANALYZE run on slow queries
  - [ ] Connection pooling configured
  - [ ] Query timeouts set (prevent runaway queries)
  - [ ] Statistics analyzed

- [ ] **API Performance**
  - [ ] Response times < 200ms for simple queries (p95)
  - [ ] Response times < 1000ms for complex queries (p95)
  - [ ] No N+1 query problems (use eager loading)
  - [ ] Pagination implemented for large result sets
  - [ ] Caching strategy implemented (Redis)
  - [ ] Database connection pooling: min 5, max 20 connections

- [ ] **Worker/Background Job Performance**
  - [ ] Task timeouts configured
  - [ ] Max concurrent workers set appropriately
  - [ ] Task retry strategy configured
  - [ ] Dead letter queue for failed tasks
  - [ ] Task monitoring via Celery flower or similar

- [ ] **Resource Management**
  - [ ] Memory limits set on containers
  - [ ] CPU limits set if running on Kubernetes
  - [ ] Logging doesn't consume excessive memory
  - [ ] Long-running processes have timeout
  - [ ] Connection pools have max limits

### Frontend Performance

- [ ] **Next.js Build**
  - [ ] Production build tested locally
  - [ ] Bundle size analyzed (target: < 200KB gzipped)
  ```bash
  pnpm --filter web build
  ```
  - [ ] Code splitting working
  - [ ] Static assets optimized
  - [ ] Image optimization enabled

- [ ] **Client-Side Performance**
  - [ ] Core Web Vitals good (LCP < 2.5s, FID < 100ms, CLS < 0.1)
  - [ ] Lighthouse score >= 80
  - [ ] No unnecessary re-renders
  - [ ] Event debouncing/throttling implemented
  - [ ] Lazy loading for below-the-fold content

- [ ] **Caching Strategy**
  - [ ] Browser cache headers set (Cache-Control)
  - [ ] Service worker for offline capability (if applicable)
  - [ ] CDN configured for static assets
  - [ ] API response caching implemented (Redis)

### Playwright Card Generation

- [ ] **Card Generation Performance**
  - [ ] Average generation time < 5 seconds
  - [ ] Concurrent browser instances: 2-4
  - [ ] Memory usage per browser < 500MB
  - [ ] S3 caching enabled for generated cards
  - [ ] Cache TTL: 30 days
  - [ ] Failed generations don't block user flow

---

## Monitoring & Alerting

### Application Monitoring

- [ ] **Metrics Configured**
  - [ ] Request rate (requests/second)
  - [ ] Error rate (errors/minute, by status code)
  - [ ] Response time percentiles (p50, p95, p99)
  - [ ] Database query time
  - [ ] Cache hit rate
  - [ ] Task queue depth
  - [ ] Active database connections

- [ ] **Alerting Rules Set**
  - [ ] Alert: Error rate > 5% for 2+ minutes
  - [ ] Alert: Response time p95 > 3000ms for 3+ minutes
  - [ ] Alert: CPU > 80% for 5+ minutes
  - [ ] Alert: Memory > 85% for 5+ minutes
  - [ ] Alert: Disk usage > 80%
  - [ ] Alert: Database connection pool exhausted
  - [ ] Alert: Task queue depth > 1000 for 5+ minutes

- [ ] **Log Aggregation**
  - [ ] Application logs aggregated in single location
  - [ ] Structured logging (JSON) enabled
  - [ ] Log level appropriate (WARNING in production)
  - [ ] Error stack traces logged
  - [ ] Request IDs for tracing
  - [ ] Log retention: 30 days minimum

- [ ] **Distributed Tracing**
  - [ ] OpenTelemetry instrumented
  - [ ] Request tracing across services
  - [ ] Database query tracing enabled
  - [ ] Slow query tracing (> 1s)

### Infrastructure Monitoring

- [ ] **Deployment Monitoring**
  - [ ] Prometheus scraping configured
  - [ ] Grafana dashboards created
  - [ ] Key metrics displayed in real-time
  - [ ] Historical data available (30+ days)

- [ ] **Health Checks**
  - [ ] API health endpoint responds
  - [ ] Database connectivity verified
  - [ ] Redis connectivity verified
  - [ ] All dependencies healthy before accepting traffic

- [ ] **Deployment Metrics**
  - [ ] Deployment frequency tracked
  - [ ] Lead time for changes tracked
  - [ ] Change failure rate tracked
  - [ ] Mean time to recovery (MTTR) tracked

---

## Operational Excellence

### Backup & Disaster Recovery

- [ ] **Database Backups**
  - [ ] Daily automated backups configured
  - [ ] Backups tested with restore
  - [ ] Backup retention: 30 days minimum
  - [ ] Backups stored in separate region (if cloud)
  - [ ] Recovery time objective (RTO): < 1 hour
  - [ ] Recovery point objective (RPO): < 5 minutes

- [ ] **Data Recovery Plan**
  - [ ] Documented procedure for restoring from backup
  - [ ] Restore tested on staging environment
  - [ ] Estimated recovery time validated
  - [ ] Team trained on recovery procedure

- [ ] **Disaster Recovery Plan**
  - [ ] Plan for service outage < 5 hours documented
  - [ ] Plan for data loss < 5 minutes documented
  - [ ] Communication plan defined (status page, notifications)
  - [ ] Runbook created for common failure scenarios

### Documentation

- [ ] **Operational Documentation**
  - [ ] Deployment procedure documented
  - [ ] Rollback procedure documented
  - [ ] Monitoring/alerting setup documented
  - [ ] Common issues and solutions documented
  - [ ] Troubleshooting runbook created
  - [ ] Architecture diagram created
  - [ ] Database schema documented

- [ ] **Runbooks Created**
  - [ ] Deployment runbook
  - [ ] Rollback runbook
  - [ ] Database migration runbook
  - [ ] Incident response runbook
  - [ ] Performance troubleshooting runbook
  - [ ] High load handling runbook

- [ ] **Team Training**
  - [ ] Team trained on deployment process
  - [ ] Team knows how to monitor application
  - [ ] Team knows how to interpret alerts
  - [ ] Team knows rollback procedure
  - [ ] Team knows incident response process

### Scaling & Capacity Planning

- [ ] **Load Testing Completed**
  - [ ] Target traffic simulated
  - [ ] Application performs under load
  - [ ] Database can handle expected queries
  - [ ] Redis can handle expected load
  - [ ] Bottlenecks identified and addressed
  - [ ] Load test results documented

- [ ] **Capacity Planning**
  - [ ] Projected growth 6-12 months planned
  - [ ] Horizontal scaling tested
  - [ ] Vertical scaling options identified
  - [ ] Cost estimated for projected scale

- [ ] **Auto-Scaling** (if applicable)
  - [ ] Auto-scaling configured
  - [ ] Scale-up threshold: CPU > 70%
  - [ ] Scale-down threshold: CPU < 30%
  - [ ] Minimum 2 instances (high availability)
  - [ ] Maximum instances: cost-acceptable level

---

## Quality Assurance

### Testing Coverage

- [ ] **Unit Tests**
  - [ ] Backend unit test coverage > 70%
  - [ ] All unit tests passing
  - [ ] Critical paths have > 80% coverage

- [ ] **Integration Tests**
  - [ ] Database integration tested
  - [ ] API endpoint integration tested
  - [ ] External service integrations tested
  - [ ] All integration tests passing

- [ ] **E2E Tests**
  - [ ] Critical user flows tested
  - [ ] Mobile flows tested
  - [ ] All E2E tests passing
  - [ ] Test data realistic

- [ ] **Manual QA**
  - [ ] Critical features tested on staging
  - [ ] Mobile/tablet tested
  - [ ] Cross-browser tested (Chrome, Firefox, Safari, Edge)
  - [ ] Accessibility tested (screen reader, keyboard nav)
  - [ ] No regression from previous version

### Code Quality

- [ ] **Code Review**
  - [ ] Code review process defined
  - [ ] At least one approval required
  - [ ] No direct commits to main
  - [ ] All PRs merged with review

- [ ] **Linting & Formatting**
  - [ ] All linting issues fixed
  - [ ] Code formatted consistently
  - [ ] Type checking passing (mypy)
  - [ ] No unused imports or variables

- [ ] **Security Code Review**
  - [ ] Security-sensitive code reviewed
  - [ ] No hardcoded credentials
  - [ ] Input validation reviewed
  - [ ] Authentication/authorization reviewed

---

## Compliance & Legal

### Regulatory Compliance

- [ ] **Data Protection**
  - [ ] GDPR compliance verified (if applicable)
  - [ ] Data retention policy documented
  - [ ] Data deletion procedure implemented
  - [ ] User consent collected where needed

- [ ] **Security Standards**
  - [ ] OWASP compliance verified
  - [ ] PCI-DSS compliance (if processing payments)
  - [ ] HIPAA compliance (if handling health data)
  - [ ] SOX compliance (if publicly traded)

### Terms & Licenses

- [ ] **Licensing**
  - [ ] All dependencies have compatible licenses
  - [ ] SBOM (Software Bill of Materials) generated
  - [ ] No GPL violations if proprietary
  - [ ] License headers in source files (if required)

- [ ] **Terms of Service**
  - [ ] Terms of Service reviewed by legal
  - [ ] Privacy Policy reviewed by legal
  - [ ] Cookies policy documented
  - [ ] Third-party services terms reviewed

---

## Communication & Launch Preparation

### User Communication

- [ ] **Announcement Prepared**
  - [ ] Launch announcement drafted
  - [ ] FAQ prepared
  - [ ] Help documentation prepared
  - [ ] Support channels ready

- [ ] **Status Page**
  - [ ] Status page deployed
  - [ ] Incident notification process defined
  - [ ] Team knows how to update status

### Team Preparation

- [ ] **Escalation Plan**
  - [ ] Escalation contacts defined
  - [ ] On-call rotation established
  - [ ] Incident response team identified
  - [ ] Communication channels established

- [ ] **Post-Launch Support**
  - [ ] Support team trained
  - [ ] Monitoring dashboards shared with team
  - [ ] Alert notification channels working
  - [ ] Incident response plan ready

---

## Final Sign-Off

### Pre-Launch Review Meeting

- [ ] Technical Lead: Code quality and architecture approved
- [ ] DevOps Lead: Infrastructure and deployment approved
- [ ] QA Lead: Testing and quality approved
- [ ] Product Manager: Feature completeness approved
- [ ] Security Lead: Security hardening approved
- [ ] Operations Lead: Monitoring and runbooks approved

### Deployment Day Checklist

**2 hours before launch:**
- [ ] All team members notified and on standby
- [ ] Monitoring dashboards open
- [ ] Incident response team ready
- [ ] Rollback plan reviewed
- [ ] Status page test notification sent

**1 hour before launch:**
- [ ] Final backup of production database
- [ ] Database migration tested on staging clone
- [ ] Deployment script tested
- [ ] Health check endpoints verified

**At launch:**
- [ ] Deploy to staging first
- [ ] Verify staging deployment
- [ ] Approval from tech lead
- [ ] Deploy to production
- [ ] Monitor error rates for 30+ minutes
- [ ] Monitor response times
- [ ] Monitor CPU/memory usage

**30+ minutes post-launch:**
- [ ] No error rate spike
- [ ] Performance metrics normal
- [ ] Health checks passing
- [ ] User reports normal
- [ ] Green light for full operational mode

### Documentation Sign-Off

- [ ] Deployment documentation complete and accurate
- [ ] Runbooks reviewed and tested
- [ ] Team trained on procedures
- [ ] Escalation contacts documented
- [ ] Incident response plan documented

---

## Go/No-Go Decision Framework

### GO Conditions (All must be true)
- Unit tests: 100% passing
- Integration tests: 100% passing
- E2E tests: 100% passing
- Security scan: No unmitigated high/critical vulnerabilities
- Load test: Passes expected load with safety margin
- Staging: Fully functional and tested
- Monitoring: All systems green
- Team: All stakeholders ready and trained
- Documentation: Complete and accurate

### NO-GO Conditions (Any is true)
- Unit/integration/E2E test failure
- Unmitigated security vulnerability found
- Load test failure or poor performance
- Team not trained or unavailable
- Monitoring not fully configured
- Runbooks not completed
- Critical bug found in staging

---

## Template: Pre-Launch Checklist Status

```markdown
# Pre-Launch Checklist Status - [Date]

## Security Hardening
- [ ] Application Security: IN PROGRESS
- [ ] Infrastructure Security: COMPLETE
- [ ] Access Control: COMPLETE

## Performance Optimization
- [ ] Backend Performance: COMPLETE
- [ ] Frontend Performance: COMPLETE
- [ ] Load Testing: PENDING

## Monitoring & Alerting
- [ ] Application Monitoring: COMPLETE
- [ ] Infrastructure Monitoring: IN PROGRESS
- [ ] Alerting Rules: PENDING

## Operational Excellence
- [ ] Backup & Disaster Recovery: COMPLETE
- [ ] Documentation: IN PROGRESS
- [ ] Team Training: PENDING

## Quality Assurance
- [ ] Testing Coverage: COMPLETE
- [ ] Code Quality: COMPLETE
- [ ] Security Code Review: IN PROGRESS

## Overall Status
**Status**: 75% READY
**Target Launch**: [Date]
**Blockers**: Load testing incomplete, alerting pending setup
**ETA to GO**: [Date]
```

---

## Additional Resources

- [Deployment Strategy](/docs/deployment/DEPLOYMENT_STRATEGY.md)
- [Environment Configuration](/docs/deployment/environment-configuration.md)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [Cloud Security Best Practices](https://cloud.google.com/docs/enterprise)
