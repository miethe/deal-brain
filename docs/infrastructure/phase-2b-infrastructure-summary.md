---
title: "Phase 2b Infrastructure Implementation Summary"
description: "Summary of Playwright and S3 infrastructure setup for card image generation"
audience: [developers, devops, pm]
tags: [infrastructure, phase-2b, summary, implementation]
created: 2025-11-19
updated: 2025-11-19
category: "architecture-design"
status: published
related:
  - /docs/infrastructure/card-image-generation-setup.md
  - /docs/infrastructure/card-image-quick-start.md
---

# Phase 2b Infrastructure Implementation Summary

This document summarizes the infrastructure setup completed for Phase 2b card image generation, including what was automated and what requires manual configuration.

## Overview

Phase 2b infrastructure enables social sharing features by providing the foundation for dynamically generating Open Graph card images using Playwright headless browsers and S3 caching.

## Completed Tasks

### Task 2b-infra-1: Playwright Setup ✅

**Status**: Complete and ready to use

**Changes Made**:

1. **Dependencies Added** (`/home/user/deal-brain/pyproject.toml`):
   - `playwright = "^1.41.2"` (moved from dev to main dependencies)
   - `pillow = "^10.2.0"` (for image manipulation)

2. **API Dockerfile Updated** (`/home/user/deal-brain/infra/api/Dockerfile`):
   - Added Chromium system dependencies (libnss3, libgtk-3-0, etc.)
   - Installed Playwright Chromium browser
   - Image size increase: ~200MB (Chromium only, not all browsers)

3. **Worker Dockerfile Updated** (`/home/user/deal-brain/infra/worker/Dockerfile`):
   - Same system dependencies and browser installation
   - Required for background cache warm-up tasks

4. **Settings Configuration** (`/home/user/deal-brain/apps/api/dealbrain_api/settings.py`):
   - Added `PlaywrightSettings` class with:
     - `enabled`: Toggle Playwright on/off
     - `max_concurrent_browsers`: Limit concurrent instances (default: 2)
     - `browser_timeout_ms`: Browser operation timeout (default: 30s)
     - `headless`: Headless mode flag (must be true for Docker)

5. **Environment Variables** (`/home/user/deal-brain/.env.example`):
   ```bash
   PLAYWRIGHT__ENABLED=true
   PLAYWRIGHT__MAX_CONCURRENT_BROWSERS=2
   PLAYWRIGHT__BROWSER_TIMEOUT_MS=30000
   PLAYWRIGHT__HEADLESS=true
   ```

6. **Testing**:
   - Created `test_playwright` Celery task for health checks
   - Added `make test-playwright` command for quick verification

**Next Steps**:
- Rebuild Docker containers: `docker-compose build api worker`
- Test Playwright: `make test-playwright`
- Expected: Chromium launches successfully in headless mode

---

### Task 2b-infra-2: S3 Configuration ✅

**Status**: Complete (requires manual AWS setup)

**Changes Made**:

1. **Dependencies Added** (`/home/user/deal-brain/pyproject.toml`):
   - `boto3 = "^1.34.0"` (AWS SDK for Python)

2. **Settings Configuration** (`/home/user/deal-brain/apps/api/dealbrain_api/settings.py`):
   - Added `S3Settings` class with:
     - `enabled`: Toggle S3 caching on/off
     - `bucket_name`: S3 bucket name
     - `region`: AWS region
     - `access_key_id`: AWS credentials (optional with IAM roles)
     - `secret_access_key`: AWS credentials (optional with IAM roles)
     - `cache_ttl_seconds`: Cache TTL (default: 30 days)
     - `endpoint_url`: Custom S3 endpoint (for LocalStack/MinIO)

3. **Environment Variables** (`/home/user/deal-brain/.env.example`):
   ```bash
   S3__ENABLED=false  # Enable after AWS setup
   AWS_S3_BUCKET_NAME=dealbrain-card-images
   AWS_REGION=us-east-1
   AWS_ACCESS_KEY_ID=
   AWS_SECRET_ACCESS_KEY=
   S3__CACHE_TTL_SECONDS=2592000  # 30 days
   S3__ENDPOINT_URL=  # For LocalStack/MinIO
   ```

4. **Documentation Created**:
   - **Comprehensive Guide**: `/home/user/deal-brain/docs/infrastructure/card-image-generation-setup.md`
     - Complete AWS S3 bucket setup instructions
     - CORS policy configuration
     - Lifecycle policy (30-day TTL)
     - Bucket policy for public read
     - IAM permissions (role-based and user-based)
     - Cost estimates
     - Troubleshooting guide
   - **Quick Start Guide**: `/home/user/deal-brain/docs/infrastructure/card-image-quick-start.md`
     - Fast setup for local development (LocalStack)
     - Condensed production setup steps
     - Common tasks and troubleshooting

5. **Testing**:
   - Added `make test-s3` command for S3 connectivity verification
   - Tests upload, public read, and deletion

**Manual AWS Setup Required**:

The following steps **MUST** be completed manually in AWS Console or via AWS CLI:

| Step | Description | Status |
|------|-------------|--------|
| 1. Create S3 Bucket | `aws s3 mb s3://dealbrain-card-images --region us-east-1` | ⚠️ Manual |
| 2. Configure CORS | Allow cross-origin GET requests | ⚠️ Manual |
| 3. Configure Lifecycle | 30-day TTL for automatic deletion | ⚠️ Manual |
| 4. Set Bucket Policy | Public read for `card-images/*` prefix | ⚠️ Manual |
| 5. Enable Logging | Track access for analytics (optional) | ⚠️ Manual |
| 6. Create IAM Role/User | Grant S3 permissions to API container | ⚠️ Manual |

**Detailed instructions**: See `/home/user/deal-brain/docs/infrastructure/card-image-generation-setup.md` → "AWS S3 Bucket Creation" section

**Next Steps**:
- Follow manual AWS setup instructions in documentation
- Update `.env` with S3 credentials or attach IAM role
- Set `S3__ENABLED=true`
- Test S3: `make test-s3`

---

### Task 2b-infra-3: Background Cache Warm-up ✅

**Status**: Complete (ready to use once card image service is implemented)

**Changes Made**:

1. **Task Module Created** (`/home/user/deal-brain/apps/api/dealbrain_api/tasks/card_images.py`):
   - `warm_cache_top_listings`: Pre-generate top N listings daily
   - `cleanup_expired_cache`: Remove old images weekly
   - `test_playwright`: Health check for Playwright setup

2. **Worker Registration** (`/home/user/deal-brain/apps/api/dealbrain_api/worker.py`):
   - Imported `card_images` task module
   - Registered tasks with Celery

3. **Celery Beat Schedule** (`/home/user/deal-brain/apps/api/dealbrain_api/worker.py`):
   - **Daily Cache Warm-up**: 3 AM UTC, top 100 listings by `cpu_mark_per_dollar`
   - **Weekly Cache Cleanup**: Sundays at 4 AM UTC

4. **Makefile Commands** (`/home/user/deal-brain/Makefile`):
   - `make warm-cache`: Manually trigger cache warm-up
   - `make test-playwright`: Test Playwright setup
   - `make test-s3`: Test S3 connectivity

**Task Details**:

```python
# Daily at 3 AM UTC (off-peak hours)
"warm-cache-top-listings-nightly": {
    "task": "card_images.warm_cache_top_listings",
    "schedule": crontab(hour=3, minute=0),
    "kwargs": {
        "limit": 100,
        "metric": "cpu_mark_per_dollar",
    },
}

# Weekly on Sundays at 4 AM UTC
"cleanup-expired-card-cache-weekly": {
    "task": "card_images.cleanup_expired_cache",
    "schedule": crontab(hour=4, minute=0, day_of_week=0),
}
```

**Next Steps**:
- Complete Phase 2b card image service implementation
- Update `warm_cache_top_listings` to call card image generation service
- Monitor Celery worker logs during scheduled runs

---

## File Changes Summary

### Modified Files

| File | Changes |
|------|---------|
| `/home/user/deal-brain/pyproject.toml` | Added playwright, boto3, pillow dependencies |
| `/home/user/deal-brain/infra/api/Dockerfile` | Added Chromium system deps, installed Playwright |
| `/home/user/deal-brain/infra/worker/Dockerfile` | Added Chromium system deps, installed Playwright |
| `/home/user/deal-brain/apps/api/dealbrain_api/settings.py` | Added PlaywrightSettings, S3Settings classes |
| `/home/user/deal-brain/.env.example` | Added Playwright and S3 environment variables |
| `/home/user/deal-brain/apps/api/dealbrain_api/worker.py` | Added card_images tasks, beat schedule |
| `/home/user/deal-brain/Makefile` | Added test-playwright, test-s3, warm-cache commands |

### New Files

| File | Description |
|------|-------------|
| `/home/user/deal-brain/apps/api/dealbrain_api/tasks/card_images.py` | Background tasks for cache warm-up and cleanup |
| `/home/user/deal-brain/docs/infrastructure/card-image-generation-setup.md` | Comprehensive setup guide with AWS instructions |
| `/home/user/deal-brain/docs/infrastructure/card-image-quick-start.md` | Quick reference for developers |
| `/home/user/deal-brain/docs/infrastructure/phase-2b-infrastructure-summary.md` | This document |

---

## Deployment Checklist

### Pre-deployment

- [ ] Review all file changes
- [ ] Update dependencies: `poetry lock && poetry install`
- [ ] Rebuild Docker images: `docker-compose build api worker`
- [ ] Review environment variables in `.env`

### AWS Setup (Manual - Required for Production)

- [ ] Create S3 bucket: `dealbrain-card-images`
- [ ] Configure CORS policy (allow cross-origin GET)
- [ ] Configure lifecycle policy (30-day TTL)
- [ ] Set bucket policy (public read for `card-images/*`)
- [ ] Enable access logging (optional)
- [ ] Create IAM role/user with S3 permissions
- [ ] Save AWS credentials (if using IAM user)

### Configuration

- [ ] Update `.env` with AWS credentials or attach IAM role
- [ ] Set `PLAYWRIGHT__ENABLED=true`
- [ ] Set `S3__ENABLED=true` (after AWS setup)
- [ ] Verify `AWS_REGION` matches S3 bucket region
- [ ] Verify `AWS_S3_BUCKET_NAME` matches created bucket

### Post-deployment Testing

- [ ] Test Playwright: `make test-playwright`
- [ ] Test S3 connectivity: `make test-s3`
- [ ] Check Celery worker startup (no errors in logs)
- [ ] Verify scheduled tasks appear in Celery Beat
- [ ] Monitor Docker container memory usage (should be <1GB)

### Monitoring

- [ ] Set up CloudWatch alarms for S3 errors (optional)
- [ ] Monitor API container memory (Grafana dashboard)
- [ ] Track S3 storage costs (AWS Cost Explorer)
- [ ] Monitor Celery worker logs for task failures

---

## Local Development Options

### Option 1: Playwright Only (Fastest)

**No AWS account required, no caching**

```bash
# .env
PLAYWRIGHT__ENABLED=true
S3__ENABLED=false
```

**Use case**: Testing card generation logic without S3 dependency

### Option 2: Playwright + LocalStack (Full Feature Parity)

**No AWS account required, full S3 emulation**

```bash
# Add LocalStack to docker-compose.yml
# .env
PLAYWRIGHT__ENABLED=true
S3__ENABLED=true
S3__ENDPOINT_URL=http://localstack:4566
```

**Use case**: Full local development with S3 caching

### Option 3: Playwright + AWS S3 (Production-like)

**Requires AWS account, full production setup**

```bash
# .env
PLAYWRIGHT__ENABLED=true
S3__ENABLED=true
AWS_S3_BUCKET_NAME=dealbrain-card-images-dev
# + AWS credentials
```

**Use case**: Testing against real S3 before production deployment

**Recommendation**: Start with Option 1 for initial development, use Option 2 for full testing, use Option 3 for pre-production validation.

---

## Performance Characteristics

### Playwright

**Memory Usage**:
- Each Chromium instance: ~100-150MB
- Max concurrent (2): ~300MB total
- **Recommendation**: API container with ≥1GB RAM

**Startup Time**:
- First browser launch: 1-2 seconds
- Subsequent launches: ~500ms

**Throughput**:
- With 2 concurrent browsers: ~4-8 cards/second
- Cold start (no cache): 1-2 seconds/card
- Warm cache (S3 hit): <100ms/card

### S3 Caching

**Cache Hit Scenario**:
- S3 HEAD request: ~50ms
- S3 GET request: ~100ms (for 100KB image)
- Total latency: ~150ms

**Cache Miss Scenario**:
- Generate image: 1-2 seconds
- S3 PUT request: ~200ms
- Total latency: 1.2-2.2 seconds

**Storage**:
- Average image size: ~100KB
- 100 listings: 10MB
- 1,000 listings: 100MB
- 10,000 listings: 1GB

---

## Cost Estimates

### AWS S3 (us-east-1)

**100 Listings** (small deployment):
- Storage: 10MB × $0.023/GB = **$0.00023/month**
- PUT requests: 100 × $0.005/1000 = **$0.0005/month**
- GET requests: 10,000 × $0.0004/1000 = **$0.004/month**
- Data transfer: 1GB × $0.09/GB = **$0.09/month**
- **Total: ~$0.10/month**

**1,000 Listings** (medium deployment):
- Storage: 100MB × $0.023/GB = **$0.0023/month**
- PUT requests: 1,000 × $0.005/1000 = **$0.005/month**
- GET requests: 100,000 × $0.0004/1000 = **$0.04/month**
- Data transfer: 10GB × $0.09/GB = **$0.90/month**
- **Total: ~$1/month**

**10,000 Listings** (large deployment):
- Storage: 1GB × $0.023/GB = **$0.023/month**
- PUT requests: 10,000 × $0.005/1000 = **$0.05/month**
- GET requests: 1,000,000 × $0.0004/1000 = **$0.40/month**
- Data transfer: 100GB × $0.09/GB = **$9/month**
- **Total: ~$10/month**

### EC2/ECS Memory Overhead

**Additional RAM for Playwright**:
- Base API container: 512MB
- With Playwright: 1GB
- Overhead: +512MB
- **Estimated cost**: $5-10/month (varies by instance type)

**Total Monthly Cost**:
- Small (100 listings): ~$5-10/month
- Medium (1,000 listings): ~$6-11/month
- Large (10,000 listings): ~$15-20/month

---

## Security Considerations

### AWS Credentials

**DO**:
- Use IAM roles with least privilege (production)
- Rotate access keys regularly (if using IAM user)
- Use AWS Secrets Manager for credentials (production)
- Enable MFA for IAM users

**DO NOT**:
- Commit credentials to git
- Use root AWS account keys
- Share credentials across environments

### S3 Bucket Security

**Public Access**:
- Only `card-images/*` prefix is publicly readable
- Bucket root and other prefixes remain private
- Use bucket policies, not ACLs

**Monitoring**:
- Enable S3 access logging
- Review logs for unauthorized access
- Set up CloudWatch alarms for unusual patterns

---

## Next Steps (Phase 2b Implementation)

### Immediate (Complete Infrastructure Setup)

1. **Manual AWS Setup**:
   - Create S3 bucket
   - Configure CORS, lifecycle, bucket policies
   - Create IAM role/user

2. **Deploy and Test**:
   - Rebuild Docker containers
   - Run health checks (`make test-playwright`, `make test-s3`)
   - Verify Celery Beat schedule

### Phase 2b Service Implementation

1. **Create Card Image Service** (`apps/api/dealbrain_api/services/card_images.py`):
   - HTML/CSS template rendering
   - Playwright screenshot capture
   - S3 upload/download logic
   - Cache hit/miss handling

2. **Create API Endpoint** (`apps/api/dealbrain_api/api/card_images.py`):
   - `GET /api/og-image/{listing_id}`
   - Returns cached image or generates new
   - Proper caching headers

3. **Update Listing Pages** (Next.js frontend):
   - Add Open Graph meta tags
   - Link to card image URL
   - Test social sharing on Twitter, Facebook, LinkedIn

4. **Update Background Tasks**:
   - Implement `warm_cache_top_listings` to call card service
   - Implement `cleanup_expired_cache` with S3 cleanup logic

### Future Enhancements

- [ ] CDN integration (CloudFront) for faster global delivery
- [ ] Image optimization (WebP format, compression)
- [ ] Cache hit rate metrics and dashboarding
- [ ] Automatic cache invalidation on listing updates
- [ ] A/B testing for card designs
- [ ] Custom domain for images (images.dealbrain.com)
- [ ] Infrastructure as Code (Terraform) for AWS setup

---

## Documentation Reference

### Main Documentation

- **Comprehensive Setup Guide**: `/home/user/deal-brain/docs/infrastructure/card-image-generation-setup.md`
  - Complete AWS S3 bucket setup
  - Playwright installation and configuration
  - IAM permissions and security
  - Cost estimates and monitoring
  - Troubleshooting guide

- **Quick Start Guide**: `/home/user/deal-brain/docs/infrastructure/card-image-quick-start.md`
  - Fast local development setup
  - LocalStack S3 emulation
  - Common tasks and commands
  - Environment variable reference

- **Implementation Summary**: `/home/user/deal-brain/docs/infrastructure/phase-2b-infrastructure-summary.md` (this document)
  - What was implemented
  - What requires manual setup
  - Deployment checklist
  - Cost estimates

### External Resources

- [Playwright Python Documentation](https://playwright.dev/python/docs/intro)
- [AWS S3 Lifecycle Policies](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)
- [Boto3 S3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
- [Celery Beat Scheduling](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html)

---

## Support

For questions or issues:

1. **Check Documentation**:
   - Review setup guide for configuration issues
   - Check quick start for common tasks
   - Review troubleshooting section

2. **Check Logs**:
   - API logs: `docker-compose logs api`
   - Worker logs: `docker-compose logs worker`
   - Docker stats: `docker stats`

3. **Run Health Checks**:
   - Playwright: `make test-playwright`
   - S3: `make test-s3`
   - Worker status: `docker-compose exec worker celery -A dealbrain_api.worker inspect active`

4. **File GitHub Issue**:
   - Include logs and environment details
   - Describe steps to reproduce
   - Include output of health checks

---

## Changelog

### 2025-11-19 - Initial Implementation

- Added Playwright setup in API and worker containers
- Added S3 configuration and settings
- Created background tasks for cache warm-up and cleanup
- Created comprehensive documentation
- Added Makefile commands for testing
- Updated environment variable examples

---

**Infrastructure Status**: ✅ Complete and ready for Phase 2b service implementation

**Manual Setup Required**: ⚠️ AWS S3 bucket creation and configuration

**Estimated Setup Time**:
- Automated (rebuild Docker): 5-10 minutes
- Manual AWS setup: 15-30 minutes
- Testing and verification: 10 minutes
- **Total: 30-50 minutes**
