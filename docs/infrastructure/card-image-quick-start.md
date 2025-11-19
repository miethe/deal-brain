---
title: "Card Image Generation - Quick Start"
description: "Quick reference for setting up card image generation infrastructure"
audience: [developers]
tags: [quick-start, infrastructure, playwright, s3]
created: 2025-11-19
updated: 2025-11-19
category: "configuration-deployment"
status: published
related:
  - /docs/infrastructure/card-image-generation-setup.md
---

# Card Image Generation - Quick Start

This is a condensed quick-start guide for developers. For comprehensive documentation, see [card-image-generation-setup.md](./card-image-generation-setup.md).

## Local Development (No AWS)

**Fastest setup - uses Playwright only, no caching:**

```bash
# 1. Update .env
cat >> .env << EOF
PLAYWRIGHT__ENABLED=true
PLAYWRIGHT__MAX_CONCURRENT_BROWSERS=2
S3__ENABLED=false
EOF

# 2. Install dependencies
poetry install

# 3. Rebuild Docker containers
docker-compose build api worker

# 4. Start services
docker-compose up -d

# 5. Test Playwright
docker-compose exec api python -c "
from dealbrain_api.tasks.card_images import test_playwright
print(test_playwright())
"
```

**Expected output:**
```json
{
  "status": "success",
  "success": true,
  "browser": "chromium",
  "version": "120.0.6099.28",
  "headless": true
}
```

## Local Development with LocalStack (S3 Emulator)

**Full feature parity without AWS account:**

```bash
# 1. Add LocalStack to docker-compose.yml
cat >> docker-compose.yml << EOF

  localstack:
    image: localstack/localstack:3.0
    ports:
      - "4566:4566"
    environment:
      SERVICES: s3
      DEFAULT_REGION: us-east-1
    volumes:
      - localstack_data:/tmp/localstack
EOF

# Add volume to volumes section
# volumes:
#   localstack_data:

# 2. Update .env
cat >> .env << EOF
PLAYWRIGHT__ENABLED=true
S3__ENABLED=true
AWS_S3_BUCKET_NAME=dealbrain-card-images
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
S3__ENDPOINT_URL=http://localstack:4566
EOF

# 3. Rebuild and start
docker-compose build api worker
docker-compose up -d

# 4. Create S3 bucket in LocalStack
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
print('✓ LocalStack S3 bucket created')
"

# 5. Test S3 upload
docker-compose exec api python -c "
import boto3
from dealbrain_api.settings import get_settings
settings = get_settings()
s3 = boto3.client(
    's3',
    endpoint_url=settings.s3.endpoint_url,
    region_name=settings.s3.region
)
s3.put_object(
    Bucket=settings.s3.bucket_name,
    Key='card-images/test.png',
    Body=b'test',
    ContentType='image/png'
)
print('✓ S3 upload successful')
"
```

## Production Setup (AWS S3)

**Requires AWS account and manual bucket setup:**

### Step 1: Create S3 Bucket (AWS Console or CLI)

```bash
# Using AWS CLI
aws s3 mb s3://dealbrain-card-images --region us-east-1
```

### Step 2: Configure Bucket

Apply these configurations via AWS Console or CLI:

**CORS Policy** (S3 Console → Permissions → CORS):
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

**Lifecycle Policy** (S3 Console → Management → Lifecycle):
- Rule name: "DeleteOldCardImages"
- Scope: Prefix "card-images/"
- Expiration: 30 days

**Bucket Policy** (S3 Console → Permissions → Bucket policy):
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

### Step 3: IAM Permissions

**Option A: IAM Role (Recommended)**

Attach this policy to your ECS task role or EC2 instance role:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
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

**Option B: IAM User (Development)**

Create IAM user and save access keys:
```bash
aws iam create-user --user-name dealbrain-card-images
# ... attach policy, create access keys
```

### Step 4: Configure Application

```bash
# Update .env (production)
PLAYWRIGHT__ENABLED=true
PLAYWRIGHT__MAX_CONCURRENT_BROWSERS=2
S3__ENABLED=true
AWS_S3_BUCKET_NAME=dealbrain-card-images
AWS_REGION=us-east-1

# Option A: IAM Role (leave empty, role is attached to container)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

# Option B: IAM User (set credentials from Step 3)
# AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
# AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

### Step 5: Deploy and Test

```bash
# Rebuild containers
docker-compose build api worker

# Start services
docker-compose up -d

# Test S3 connectivity
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
print('✓ S3 upload successful')

# Test public read
url = f'https://{settings.s3.bucket_name}.s3.{settings.s3.region}.amazonaws.com/card-images/test.txt'
print(f'✓ Test file URL: {url}')

# Cleanup
s3.delete_object(Bucket=settings.s3.bucket_name, Key='card-images/test.txt')
print('✓ Cleanup successful')
"
```

## Environment Variables Reference

### Playwright Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `PLAYWRIGHT__ENABLED` | `true` | Enable/disable Playwright |
| `PLAYWRIGHT__MAX_CONCURRENT_BROWSERS` | `2` | Max concurrent browser instances (1-10) |
| `PLAYWRIGHT__BROWSER_TIMEOUT_MS` | `30000` | Browser timeout in milliseconds |
| `PLAYWRIGHT__HEADLESS` | `true` | Headless mode (must be true for Docker) |

### S3 Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `S3__ENABLED` | `false` | Enable/disable S3 caching |
| `AWS_S3_BUCKET_NAME` | `dealbrain-card-images` | S3 bucket name |
| `AWS_REGION` | `us-east-1` | AWS region |
| `AWS_ACCESS_KEY_ID` | - | AWS access key (optional with IAM role) |
| `AWS_SECRET_ACCESS_KEY` | - | AWS secret key (optional with IAM role) |
| `S3__CACHE_TTL_SECONDS` | `2592000` | Cache TTL (30 days) |
| `S3__ENDPOINT_URL` | - | Custom S3 endpoint (LocalStack/MinIO) |

## Common Tasks

### Test Playwright

```bash
docker-compose exec api python -c "
from dealbrain_api.tasks.card_images import test_playwright
print(test_playwright())
"
```

### Manually Trigger Cache Warm-up

```bash
docker-compose exec api python -c "
from dealbrain_api.tasks.card_images import warm_cache_top_listings
result = warm_cache_top_listings(limit=50, metric='cpu_mark_per_dollar')
print(result)
"
```

### Check Celery Beat Schedule

```bash
docker-compose exec worker celery -A dealbrain_api.worker inspect scheduled
```

### Monitor Background Tasks

```bash
# View worker logs
docker-compose logs -f worker

# View API logs
docker-compose logs -f api
```

## Troubleshooting

### Playwright Not Working

```bash
# Check if Playwright is installed
docker-compose exec api python -c "import playwright; print(playwright.__version__)"

# Rebuild API container
docker-compose build api

# Check system dependencies
docker-compose exec api dpkg -l | grep -E "libnss3|libgtk-3-0"
```

### S3 Connection Issues

```bash
# Verify credentials
docker-compose exec api python -c "
from dealbrain_api.settings import get_settings
s = get_settings()
print(f'S3 Enabled: {s.s3.enabled}')
print(f'Bucket: {s.s3.bucket_name}')
print(f'Region: {s.s3.region}')
print(f'Endpoint: {s.s3.endpoint_url}')
"

# Test AWS credentials
aws sts get-caller-identity

# List bucket contents
aws s3 ls s3://dealbrain-card-images/card-images/
```

### High Memory Usage

```bash
# Check container memory
docker stats

# Reduce concurrent browsers
# Update .env:
PLAYWRIGHT__MAX_CONCURRENT_BROWSERS=1

# Restart API
docker-compose restart api
```

## Cost Estimates

### Development (LocalStack)
- **Cost**: $0/month (runs locally)

### Production (AWS S3)
- **100 listings**: ~$0.10/month
- **1,000 listings**: ~$1/month
- **10,000 listings**: ~$10/month

**Includes**: Storage, PUT/GET requests, data transfer

**Additional cost**: EC2/ECS memory overhead (~$5-10/month for 1GB RAM)

## Next Steps

After infrastructure setup:

1. **Implement card image service** (Phase 2b)
   - HTML/CSS template rendering
   - Playwright screenshot capture
   - S3 upload/download logic

2. **Create API endpoint** (Phase 2b)
   - `/api/og-image/{listing_id}`
   - Returns cached or generates new image

3. **Update listing pages** (Phase 2b)
   - Add Open Graph meta tags
   - Link to card image URL

4. **Monitor and optimize**
   - Track cache hit rates
   - Monitor S3 costs
   - Optimize image sizes

## Documentation

- **Comprehensive Guide**: [card-image-generation-setup.md](./card-image-generation-setup.md)
- **Playwright Docs**: https://playwright.dev/python/docs/intro
- **AWS S3 Docs**: https://docs.aws.amazon.com/s3/
- **Boto3 Docs**: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html
