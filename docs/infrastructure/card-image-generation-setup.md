---
title: "Card Image Generation Infrastructure Setup"
description: "Setup guide for Playwright headless browsers and S3 caching for social sharing card images"
audience: [developers, devops]
tags: [infrastructure, playwright, s3, docker, card-images]
created: 2025-11-19
updated: 2025-11-19
category: "configuration-deployment"
status: published
related:
  - /docs/architecture/card-image-generation.md
---

# Card Image Generation Infrastructure Setup

This guide covers the infrastructure setup for Phase 2b card image generation, which enables social sharing features with dynamically generated Open Graph images.

## Overview

The card image generation system consists of two main components:

1. **Playwright Headless Browser**: Renders HTML/CSS card templates to PNG images
2. **S3 Storage**: Caches generated images with automatic lifecycle management

## Architecture

```
┌─────────────────┐
│  API Request    │
│  /og-image/123  │
└────────┬────────┘
         │
         v
┌─────────────────────────────────┐
│  Card Image Service             │
│  1. Check S3 cache              │
│  2. Generate if missing         │
│  3. Upload to S3                │
│  4. Return image URL            │
└────────┬────────────────────────┘
         │
    ┌────┴────┐
    │         │
    v         v
┌────────┐ ┌────────────┐
│ S3     │ │ Playwright │
│ Cache  │ │ Browser    │
└────────┘ └────────────┘
```

## Component 1: Playwright Setup

### Docker Configuration

Playwright requires specific system dependencies and browser binaries. These are installed in the API container.

**File**: `/home/user/deal-brain/infra/api/Dockerfile`

The Dockerfile includes:
- System libraries for Chromium (libnss3, libgtk-3-0, etc.)
- Playwright browser installation (`playwright install chromium`)
- Only Chromium is installed to minimize image size (~200MB vs ~600MB for all browsers)

### Python Dependencies

**File**: `/home/user/deal-brain/pyproject.toml`

```toml
[tool.poetry.dependencies]
playwright = "^1.41.2"
pillow = "^10.2.0"
```

### Configuration Settings

**File**: `/home/user/deal-brain/apps/api/dealbrain_api/settings.py`

```python
class PlaywrightSettings(BaseModel):
    enabled: bool = True
    max_concurrent_browsers: int = 2  # Limit memory usage
    browser_timeout_ms: int = 30000   # 30 second timeout
    headless: bool = True              # Required for Docker
```

### Environment Variables

**File**: `/home/user/deal-brain/.env.example`

```bash
# Playwright Configuration
PLAYWRIGHT__ENABLED=true
PLAYWRIGHT__MAX_CONCURRENT_BROWSERS=2
PLAYWRIGHT__BROWSER_TIMEOUT_MS=30000
PLAYWRIGHT__HEADLESS=true
```

### Testing Playwright Setup

After deployment, test Playwright availability:

```bash
# Via Celery task
docker-compose exec api python -c "from dealbrain_api.tasks.card_images import test_playwright; print(test_playwright())"

# Expected output:
# {'status': 'success', 'success': True, 'browser': 'chromium', 'version': '120.0.6099.28', 'headless': True}
```

### Performance Considerations

**Memory Usage**:
- Each Chromium instance: ~100-150MB
- With `max_concurrent_browsers=2`: ~300MB total
- Recommendation: Ensure API container has at least 1GB RAM

**Startup Time**:
- First browser launch: ~1-2 seconds
- Subsequent launches: ~500ms (browser pool maintained)

**Browser Pool**:
- Browsers are launched on-demand
- Maximum 2 concurrent instances (configurable)
- Automatic cleanup after timeout

## Component 2: S3 Storage Setup

### AWS S3 Bucket Creation

**REQUIRES MANUAL AWS SETUP**

#### Step 1: Create S3 Bucket

```bash
# Using AWS CLI
aws s3 mb s3://dealbrain-card-images --region us-east-1

# Or via AWS Console:
# 1. Go to S3 Console
# 2. Click "Create bucket"
# 3. Bucket name: dealbrain-card-images
# 4. Region: us-east-1 (or your preferred region)
# 5. Block all public access: NO (we need public read for og:image URLs)
# 6. Enable versioning: Optional
# 7. Create bucket
```

#### Step 2: Configure CORS Policy

Card images need to be accessible from any domain for social sharing:

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedOrigins": ["*"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3600
  }
]
```

Apply via AWS CLI:

```bash
aws s3api put-bucket-cors \
  --bucket dealbrain-card-images \
  --cors-configuration file://cors-config.json
```

Or via AWS Console:
1. Go to bucket → Permissions → CORS
2. Paste the JSON above
3. Save changes

#### Step 3: Configure Lifecycle Policy (30-day TTL)

Automatically delete old card images to manage storage costs:

```json
{
  "Rules": [
    {
      "Id": "DeleteOldCardImages",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "card-images/"
      },
      "Expiration": {
        "Days": 30
      }
    }
  ]
}
```

Apply via AWS CLI:

```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket dealbrain-card-images \
  --lifecycle-configuration file://lifecycle-policy.json
```

Or via AWS Console:
1. Go to bucket → Management → Lifecycle rules
2. Create rule: "DeleteOldCardImages"
3. Scope: Limit to prefix "card-images/"
4. Expiration: 30 days
5. Create rule

#### Step 4: Enable Public Read Access

Card images must be publicly readable for social media crawlers:

**Bucket Policy**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadCardImages",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::dealbrain-card-images/card-images/*"
    }
  ]
}
```

Apply via AWS CLI:

```bash
aws s3api put-bucket-policy \
  --bucket dealbrain-card-images \
  --policy file://bucket-policy.json
```

Or via AWS Console:
1. Go to bucket → Permissions → Bucket policy
2. Paste the JSON above
3. Save changes

#### Step 5: Enable Access Logging (Optional but Recommended)

Track image access for analytics:

```bash
# Create logging bucket (if not exists)
aws s3 mb s3://dealbrain-logs --region us-east-1

# Enable logging
aws s3api put-bucket-logging \
  --bucket dealbrain-card-images \
  --bucket-logging-status \
    '{"LoggingEnabled": {"TargetBucket": "dealbrain-logs", "TargetPrefix": "s3-access-logs/card-images/"}}'
```

### IAM Permissions

**REQUIRES MANUAL AWS SETUP**

#### Option 1: IAM Role (Recommended for Production)

Create an IAM role for the API container (ECS/EKS):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CardImageStorage",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::dealbrain-card-images",
        "arn:aws:s3:::dealbrain-card-images/card-images/*"
      ]
    }
  ]
}
```

Attach this policy to:
- ECS Task Role (if using ECS)
- Kubernetes Service Account (if using EKS with IRSA)
- EC2 Instance Role (if running on EC2)

#### Option 2: IAM User (Development/Testing)

Create an IAM user with programmatic access:

```bash
# Create user
aws iam create-user --user-name dealbrain-card-images

# Attach policy
aws iam attach-user-policy \
  --user-name dealbrain-card-images \
  --policy-arn arn:aws:iam::aws:policy/custom/DealBrainCardImagesPolicy

# Create access keys
aws iam create-access-key --user-name dealbrain-card-images
```

Save the `AccessKeyId` and `SecretAccessKey` for environment variables.

### Python Dependencies

**File**: `/home/user/deal-brain/pyproject.toml`

```toml
[tool.poetry.dependencies]
boto3 = "^1.34.0"
```

### Configuration Settings

**File**: `/home/user/deal-brain/apps/api/dealbrain_api/settings.py`

```python
class S3Settings(BaseModel):
    enabled: bool = False  # Enable after AWS setup
    bucket_name: str = "dealbrain-card-images"
    region: str = "us-east-1"
    access_key_id: str | None = None  # Prefer IAM roles
    secret_access_key: str | None = None
    cache_ttl_seconds: int = 2592000  # 30 days
    endpoint_url: str | None = None  # For LocalStack/MinIO
```

### Environment Variables

**File**: `/home/user/deal-brain/.env.example`

```bash
# S3 Configuration
S3__ENABLED=false  # Set to true after AWS setup
AWS_S3_BUCKET_NAME=dealbrain-card-images
AWS_REGION=us-east-1

# Option 1: IAM Role (Recommended - leave empty)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

# Option 2: IAM User (Development - set credentials)
# AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
# AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

S3__CACHE_TTL_SECONDS=2592000  # 30 days
S3__ENDPOINT_URL=  # Leave empty for AWS S3
```

### Testing S3 Setup

After deployment, test S3 connectivity:

```bash
# Test upload
docker-compose exec api python -c "
import boto3
from dealbrain_api.settings import get_settings

settings = get_settings()
s3 = boto3.client('s3', region_name=settings.s3.region)
s3.put_object(
    Bucket=settings.s3.bucket_name,
    Key='card-images/test.txt',
    Body=b'Test upload',
    ContentType='text/plain'
)
print('✓ Upload successful')
"

# Test public read
curl https://dealbrain-card-images.s3.us-east-1.amazonaws.com/card-images/test.txt
# Expected: "Test upload"

# Cleanup
docker-compose exec api python -c "
import boto3
from dealbrain_api.settings import get_settings

settings = get_settings()
s3 = boto3.client('s3', region_name=settings.s3.region)
s3.delete_object(Bucket=settings.s3.bucket_name, Key='card-images/test.txt')
print('✓ Cleanup successful')
"
```

## Background Jobs (Celery)

### Cache Warm-up Task

Pre-generates card images for top 100 listings daily at 3 AM UTC:

```python
# Celery Beat schedule in worker.py
"warm-cache-top-listings-nightly": {
    "task": "card_images.warm_cache_top_listings",
    "schedule": crontab(hour=3, minute=0),
    "kwargs": {
        "limit": 100,
        "metric": "cpu_mark_per_dollar",
    },
}
```

**Purpose**: Reduces p95 latency for popular listings by pre-generating images during off-peak hours.

**Manual trigger**:

```bash
docker-compose exec api python -c "
from dealbrain_api.tasks.card_images import warm_cache_top_listings
result = warm_cache_top_listings.delay(limit=50)
print(f'Task ID: {result.id}')
"
```

### Cache Cleanup Task

Removes expired images weekly (Sundays at 4 AM UTC):

```python
"cleanup-expired-card-cache-weekly": {
    "task": "card_images.cleanup_expired_cache",
    "schedule": crontab(hour=4, minute=0, day_of_week=0),
}
```

**Note**: S3 lifecycle policy handles most cleanup, but this task provides additional manual cleanup logic if needed.

## Local Development Setup

### Option 1: Using AWS S3 (Requires AWS Account)

1. Create S3 bucket (see manual setup above)
2. Create IAM user with access keys
3. Update `.env`:

```bash
S3__ENABLED=true
AWS_S3_BUCKET_NAME=dealbrain-card-images-dev
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
```

### Option 2: Using LocalStack (No AWS Account)

LocalStack provides a local S3 emulator:

**Add to `docker-compose.yml`**:

```yaml
localstack:
  image: localstack/localstack:3.0
  ports:
    - "4566:4566"
  environment:
    SERVICES: s3
    DEFAULT_REGION: us-east-1
    DATA_DIR: /tmp/localstack/data
  volumes:
    - localstack_data:/tmp/localstack
```

**Update `.env`**:

```bash
S3__ENABLED=true
AWS_S3_BUCKET_NAME=dealbrain-card-images
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test  # LocalStack accepts any value
AWS_SECRET_ACCESS_KEY=test
S3__ENDPOINT_URL=http://localstack:4566
```

**Create bucket in LocalStack**:

```bash
docker-compose exec api python -c "
import boto3

s3 = boto3.client(
    's3',
    endpoint_url='http://localstack:4566',
    aws_access_key_id='test',
    aws_secret_access_key='test',
    region_name='us-east-1'
)
s3.create_bucket(Bucket='dealbrain-card-images')
print('✓ LocalStack bucket created')
"
```

### Option 3: Playwright Only (No S3)

For testing card generation without caching:

```bash
PLAYWRIGHT__ENABLED=true
S3__ENABLED=false
```

Images will be generated on-demand but not cached (slower response times).

## Cost Estimates

### S3 Storage Costs (us-east-1)

**Assumptions**:
- 100 listings with card images
- 1 image per listing
- Average image size: 100KB
- 30-day TTL (automatic deletion)

**Monthly costs**:
- Storage: 100 images × 100KB = 10MB = **$0.00023/month**
- PUT requests: 100 images = **$0.0005**
- GET requests: 10,000 views/month = **$0.004**
- Data transfer: 10,000 views × 100KB = 1GB = **$0.09**

**Total estimated monthly cost: ~$0.10/month** (negligible)

**Scaling**:
- 1,000 listings: ~$1/month
- 10,000 listings: ~$10/month

### EC2/ECS Memory Costs

**Playwright memory overhead**:
- Base API container: 512MB
- With Playwright: 1GB (recommendation)
- Additional cost: ~$5-10/month (depends on instance type)

## Deployment Checklist

### Pre-deployment

- [ ] Update dependencies: `poetry lock && poetry install`
- [ ] Rebuild Docker images: `docker-compose build api worker`
- [ ] Review environment variables in `.env`

### AWS Setup (Manual)

- [ ] Create S3 bucket: `dealbrain-card-images`
- [ ] Configure CORS policy
- [ ] Configure lifecycle policy (30-day TTL)
- [ ] Set bucket policy for public read
- [ ] Enable access logging (optional)
- [ ] Create IAM role/user with appropriate permissions
- [ ] Save access keys (if using IAM user)

### Configuration

- [ ] Update `.env` with S3 credentials/settings
- [ ] Set `S3__ENABLED=true`
- [ ] Set `PLAYWRIGHT__ENABLED=true`
- [ ] Verify `AWS_REGION` matches bucket region

### Post-deployment

- [ ] Test Playwright: `test_playwright` task
- [ ] Test S3 upload/download (see testing section)
- [ ] Monitor Celery worker logs for scheduled tasks
- [ ] Check Grafana dashboards for memory usage
- [ ] Verify cache warm-up task runs successfully

### Monitoring

- [ ] Set up CloudWatch alarms for S3 errors
- [ ] Monitor API container memory usage (should stay under 1GB)
- [ ] Track S3 storage costs in AWS Cost Explorer
- [ ] Monitor cache hit rate (future implementation)

## Troubleshooting

### Playwright Issues

**Error**: `playwright._impl._api_types.Error: Executable doesn't exist`

**Solution**: Playwright browsers not installed in Docker image

```bash
# Rebuild API image
docker-compose build api

# Verify installation
docker-compose run --rm api playwright install --dry-run chromium
```

**Error**: `TimeoutError: Timeout 30000ms exceeded`

**Solution**: Increase browser timeout or check system resources

```bash
# Update .env
PLAYWRIGHT__BROWSER_TIMEOUT_MS=60000  # 60 seconds

# Verify container has enough memory
docker stats
```

### S3 Issues

**Error**: `botocore.exceptions.NoCredentialsError: Unable to locate credentials`

**Solution**: Configure AWS credentials or IAM role

```bash
# Option 1: Set environment variables
export AWS_ACCESS_KEY_ID=your-key-id
export AWS_SECRET_ACCESS_KEY=your-secret-key

# Option 2: Use IAM role (ECS/EKS)
# Attach role to task/service

# Verify credentials
aws sts get-caller-identity
```

**Error**: `botocore.exceptions.ClientError: An error occurred (AccessDenied)`

**Solution**: Check IAM permissions and bucket policy

```bash
# Verify bucket policy allows public read
aws s3api get-bucket-policy --bucket dealbrain-card-images

# Verify IAM user/role has required permissions
aws iam get-user-policy --user-name dealbrain-card-images --policy-name CardImageStoragePolicy
```

### Performance Issues

**Issue**: High memory usage (>2GB)

**Solution**: Reduce concurrent browsers or optimize image size

```bash
# Update .env
PLAYWRIGHT__MAX_CONCURRENT_BROWSERS=1

# Restart API container
docker-compose restart api
```

**Issue**: Slow card generation (>5 seconds)

**Solution**: Optimize HTML/CSS template or increase browser timeout

```bash
# Check browser startup time
docker-compose exec api python -c "
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    start = time.time()
    browser = p.chromium.launch(headless=True)
    print(f'Browser startup: {time.time() - start:.2f}s')
    browser.close()
"
```

## Security Considerations

### Secrets Management

**DO NOT**:
- Commit AWS credentials to git
- Store credentials in `.env` (except for development)
- Use root AWS account access keys

**DO**:
- Use IAM roles with least privilege (production)
- Rotate access keys regularly (if using IAM user)
- Use AWS Secrets Manager or environment variables (production)
- Enable MFA for IAM users

### S3 Security

**Public Access**:
- Only `card-images/*` prefix should be publicly readable
- Block public access to bucket root and other prefixes
- Use bucket policies, not ACLs

**Access Logging**:
- Enable S3 access logging to monitor suspicious activity
- Review logs regularly for unauthorized access
- Set up CloudWatch alarms for unusual access patterns

### Network Security

**CORS**:
- Restrict `AllowedOrigins` to known domains (optional)
- Current configuration allows all origins for maximum compatibility

**API Security**:
- Rate limit card generation endpoints
- Implement request signing for cache invalidation
- Monitor for abuse (excessive image generation)

## Future Enhancements

### Planned Improvements

- [ ] CDN integration (CloudFront) for faster global delivery
- [ ] Image optimization (WebP format, compression)
- [ ] Cache hit rate metrics and dashboarding
- [ ] Automatic cache invalidation on listing updates
- [ ] A/B testing for card designs
- [ ] Custom domain for image URLs (images.dealbrain.com)

### Infrastructure as Code

Consider using Terraform to automate AWS setup:

```hcl
# Future: infrastructure/terraform/s3-card-images.tf
resource "aws_s3_bucket" "card_images" {
  bucket = "dealbrain-card-images"
  # ... lifecycle, CORS, etc.
}
```

## References

- [Playwright Python Documentation](https://playwright.dev/python/docs/intro)
- [AWS S3 Lifecycle Policies](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)
- [Boto3 S3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
- [Celery Beat Scheduling](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html)

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review Celery worker logs: `docker-compose logs worker`
3. Review API logs: `docker-compose logs api`
4. File a GitHub issue with logs and environment details
