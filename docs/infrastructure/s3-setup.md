---
title: "S3 Bucket Setup for Card Image Caching"
description: "Step-by-step guide to configure AWS S3 for card image caching with lifecycle policies and CORS"
audience: [developers, devops]
tags: [s3, aws, infrastructure, card-images, deployment]
created: 2025-11-19
updated: 2025-11-19
category: "configuration-deployment"
status: published
related:
  - /docs/infrastructure/card-image-generation-setup.md
  - /docs/infrastructure/phase-2b-infrastructure-summary.md
---

# S3 Bucket Setup for Card Image Caching

This guide provides step-by-step instructions for configuring an AWS S3 bucket to cache dynamically generated card images with proper lifecycle management, CORS policies, and access controls.

## Prerequisites

- AWS account with appropriate permissions
- AWS CLI installed and configured (optional but recommended)
- Access to AWS Management Console

## Quick Start

For experienced users, here's the complete setup in one command block:

```bash
# Create bucket
aws s3 mb s3://dealbrain-card-images --region us-east-1

# Configure CORS
aws s3api put-bucket-cors --bucket dealbrain-card-images --cors-configuration file://cors.json

# Configure lifecycle policy
aws s3api put-bucket-lifecycle-configuration --bucket dealbrain-card-images --lifecycle-configuration file://lifecycle.json

# Set bucket policy (public read for card-images/* prefix)
aws s3api put-bucket-policy --bucket dealbrain-card-images --policy file://bucket-policy.json

# Enable versioning (optional)
aws s3api put-bucket-versioning --bucket dealbrain-card-images --versioning-configuration Status=Enabled

# Enable logging (optional)
aws s3api put-bucket-logging --bucket dealbrain-card-images --bucket-logging-status file://logging.json
```

Configuration files are provided in the sections below.

## Step 1: Create S3 Bucket

### Via AWS Console

1. Navigate to **S3** service in AWS Console
2. Click **Create bucket**
3. Configure bucket settings:
   - **Bucket name**: `dealbrain-card-images` (must be globally unique)
   - **AWS Region**: `us-east-1` (or your preferred region)
   - **Object Ownership**: ACLs disabled (recommended)
   - **Block Public Access**: Keep all blocked for now (we'll configure specific public access via bucket policy)
   - **Bucket Versioning**: Disabled (optional: enable for image history)
   - **Default encryption**: Server-side encryption with Amazon S3 managed keys (SSE-S3)
4. Click **Create bucket**

### Via AWS CLI

```bash
aws s3 mb s3://dealbrain-card-images --region us-east-1
```

## Step 2: Configure CORS Policy

CORS (Cross-Origin Resource Sharing) allows web browsers to load card images from different domains.

### Via AWS Console

1. Navigate to your bucket → **Permissions** tab
2. Scroll to **Cross-origin resource sharing (CORS)**
3. Click **Edit**
4. Paste the following configuration:

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedOrigins": ["*"],
    "ExposeHeaders": ["ETag", "Content-Length", "Content-Type"],
    "MaxAgeSeconds": 3600
  }
]
```

5. Click **Save changes**

### Via AWS CLI

Create a file named `cors.json`:

```json
{
  "CORSRules": [
    {
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "HEAD"],
      "AllowedOrigins": ["*"],
      "ExposeHeaders": ["ETag", "Content-Length", "Content-Type"],
      "MaxAgeSeconds": 3600
    }
  ]
}
```

Apply the policy:

```bash
aws s3api put-bucket-cors --bucket dealbrain-card-images --cors-configuration file://cors.json
```

### CORS Configuration Explained

- **AllowedMethods**: Only GET and HEAD (read-only public access)
- **AllowedOrigins**: `*` allows any domain (restrict to your domains in production)
- **MaxAgeSeconds**: Browsers cache CORS preflight requests for 1 hour
- **ExposeHeaders**: Allows JavaScript to read response headers

## Step 3: Configure Lifecycle Policy

Lifecycle policies automatically delete old card images after 30 days to manage storage costs.

### Via AWS Console

1. Navigate to your bucket → **Management** tab
2. Scroll to **Lifecycle rules**
3. Click **Create lifecycle rule**
4. Configure the rule:
   - **Rule name**: `expire-card-images-30-days`
   - **Rule scope**: Limit using filter
   - **Prefix**: `card-images/`
   - **Lifecycle rule actions**: Check "Expire current versions of objects"
   - **Days after object creation**: `30`
5. Click **Create rule**

### Via AWS CLI

Create a file named `lifecycle.json`:

```json
{
  "Rules": [
    {
      "Id": "expire-card-images-30-days",
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

Apply the policy:

```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket dealbrain-card-images \
  --lifecycle-configuration file://lifecycle.json
```

### Lifecycle Policy Explained

- **Prefix**: Only applies to objects under `card-images/` (other prefixes unaffected)
- **Days**: 30 days after creation, objects are automatically deleted
- **Cost savings**: Prevents indefinite storage growth
- **Regeneration**: Card images are regenerated on-demand if requested after expiration

## Step 4: Set Bucket Policy (Public Read)

The bucket policy allows public read access to card images while keeping the bucket itself private.

### Via AWS Console

1. Navigate to your bucket → **Permissions** tab
2. Scroll to **Bucket policy**
3. Click **Edit**
4. Paste the following policy (replace `dealbrain-card-images` with your bucket name):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadForCardImages",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::dealbrain-card-images/card-images/*"
    }
  ]
}
```

5. Click **Save changes**

### Via AWS CLI

Create a file named `bucket-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadForCardImages",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::dealbrain-card-images/card-images/*"
    }
  ]
}
```

Apply the policy:

```bash
aws s3api put-bucket-policy \
  --bucket dealbrain-card-images \
  --policy file://bucket-policy.json
```

### Bucket Policy Explained

- **Principal**: `*` allows anyone (public access)
- **Action**: `s3:GetObject` (read-only, no write/delete permissions)
- **Resource**: Only applies to `card-images/*` prefix
- **Security**: Bucket root and other prefixes remain private

**Important**: Update "Block Public Access" settings if needed:

```bash
aws s3api put-public-access-block \
  --bucket dealbrain-card-images \
  --public-access-block-configuration \
    BlockPublicAcls=true,\
    IgnorePublicAcls=true,\
    BlockPublicPolicy=false,\
    RestrictPublicBuckets=false
```

## Step 5: Create IAM Permissions

The API application needs permissions to upload, read, and delete card images from S3.

### Option A: IAM Role (Recommended for Production)

**Use case**: EC2, ECS, Lambda, or EKS deployments

1. Navigate to **IAM** → **Roles** → **Create role**
2. Select trusted entity:
   - **EC2** (for EC2 instances)
   - **Elastic Container Service** (for ECS/Fargate)
   - **Lambda** (for Lambda functions)
3. Attach the following inline policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CardImageS3Access",
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

4. Name the role: `dealbrain-api-card-images-role`
5. Attach role to your EC2 instance, ECS task definition, or Lambda function

**Environment Configuration**:

```bash
# .env (no credentials needed with IAM role)
S3__ENABLED=true
AWS_S3_BUCKET_NAME=dealbrain-card-images
AWS_REGION=us-east-1
```

### Option B: IAM User (For Development/Testing)

**Use case**: Local development, testing, or non-AWS deployments

1. Navigate to **IAM** → **Users** → **Add users**
2. User name: `dealbrain-api-card-images`
3. Select **Programmatic access** (generates access key)
4. Attach the following inline policy (same as above)
5. Save the **Access Key ID** and **Secret Access Key** (shown only once!)

**Environment Configuration**:

```bash
# .env (requires credentials)
S3__ENABLED=true
AWS_S3_BUCKET_NAME=dealbrain-card-images
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
```

**Security Best Practices**:

- Rotate access keys every 90 days
- Never commit credentials to source control
- Use AWS Secrets Manager for production credentials
- Enable MFA for IAM users

## Step 6: Enable Access Logging (Optional)

Access logs help track usage patterns, troubleshoot issues, and detect unauthorized access.

### Create Logging Bucket

```bash
# Create a separate bucket for logs
aws s3 mb s3://dealbrain-card-images-logs --region us-east-1

# Grant S3 log delivery permissions
aws s3api put-bucket-acl \
  --bucket dealbrain-card-images-logs \
  --grant-write URI=http://acs.amazonaws.com/groups/s3/LogDelivery \
  --grant-read-acp URI=http://acs.amazonaws.com/groups/s3/LogDelivery
```

### Enable Logging

Create `logging.json`:

```json
{
  "LoggingEnabled": {
    "TargetBucket": "dealbrain-card-images-logs",
    "TargetPrefix": "card-images-access-logs/"
  }
}
```

Apply configuration:

```bash
aws s3api put-bucket-logging \
  --bucket dealbrain-card-images \
  --bucket-logging-status file://logging.json
```

### Log Analysis

Logs are stored in the logging bucket and can be analyzed using:

- AWS Athena (SQL queries on logs)
- CloudWatch Insights
- Third-party log analysis tools

## Step 7: Test S3 Configuration

### Test via AWS CLI

```bash
# Upload test file
echo "test" > test.txt
aws s3 cp test.txt s3://dealbrain-card-images/card-images/test.txt

# Test public read access (no credentials needed)
curl https://dealbrain-card-images.s3.amazonaws.com/card-images/test.txt

# Expected output: "test"

# Delete test file
aws s3 rm s3://dealbrain-card-images/card-images/test.txt
```

### Test via Application

```bash
# Rebuild Docker containers with updated environment
docker-compose build api worker

# Start services
docker-compose up -d

# Test S3 connectivity via Makefile command
make test-s3
```

Expected output:

```
Testing S3 connectivity...
✓ Upload successful
✓ Cleanup successful
```

## Environment Variable Reference

### Development (LocalStack/MinIO)

```bash
# .env.example (local development)
S3__ENABLED=true
AWS_S3_BUCKET_NAME=dealbrain-card-images
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
S3__ENDPOINT_URL=http://localstack:4566  # LocalStack
# S3__ENDPOINT_URL=http://minio:9000      # MinIO alternative
S3__CACHE_TTL_SECONDS=2592000  # 30 days
```

### Production (AWS)

```bash
# .env.example (production with IAM role)
S3__ENABLED=true
AWS_S3_BUCKET_NAME=dealbrain-card-images
AWS_REGION=us-east-1
# AWS_ACCESS_KEY_ID=  # Omit if using IAM role
# AWS_SECRET_ACCESS_KEY=  # Omit if using IAM role
S3__CACHE_TTL_SECONDS=2592000  # 30 days
```

### Settings in Code

The application settings are defined in `/home/user/deal-brain/apps/api/dealbrain_api/settings.py`:

```python
class S3Settings(BaseModel):
    enabled: bool = False  # Enable after AWS setup
    bucket_name: str = "dealbrain-card-images"
    region: str = "us-east-1"
    access_key_id: str | None = None  # Optional with IAM role
    secret_access_key: str | None = None  # Optional with IAM role
    cache_ttl_seconds: int = 2592000  # 30 days
    endpoint_url: str | None = None  # For LocalStack/MinIO
```

## Cost Estimates

### Storage Costs (S3 Standard - us-east-1)

| Listings | Storage | Cost/Month |
|----------|---------|------------|
| 100      | 10 MB   | $0.00023   |
| 1,000    | 100 MB  | $0.0023    |
| 10,000   | 1 GB    | $0.023     |

### Request Costs

| Operation | Price | Example Usage | Cost/Month |
|-----------|-------|---------------|------------|
| PUT (upload) | $0.005/1,000 | 1,000 new images | $0.005 |
| GET (download) | $0.0004/1,000 | 100,000 views | $0.04 |

### Data Transfer Costs

| Traffic | Price | Example Usage | Cost/Month |
|---------|-------|---------------|------------|
| Data out | $0.09/GB | 10 GB transferred | $0.90 |

### Total Monthly Cost Examples

- **Small (100 listings, 10K views)**: ~$0.10/month
- **Medium (1,000 listings, 100K views)**: ~$1/month
- **Large (10,000 listings, 1M views)**: ~$10/month

## Troubleshooting

### Issue: "Access Denied" when uploading

**Symptoms**: API logs show S3 access denied errors

**Solutions**:

1. Verify IAM permissions include `s3:PutObject`
2. Check bucket policy doesn't block write access
3. Verify AWS credentials are correctly set in `.env`
4. Test credentials: `aws s3 ls s3://dealbrain-card-images`

### Issue: "NoSuchBucket" error

**Symptoms**: Application can't find S3 bucket

**Solutions**:

1. Verify bucket exists: `aws s3 ls s3://dealbrain-card-images`
2. Check bucket name in `.env` matches actual bucket name
3. Verify region is correct (bucket is region-specific)

### Issue: CORS errors in browser

**Symptoms**: Browser console shows CORS errors when loading images

**Solutions**:

1. Verify CORS policy is configured correctly
2. Check `AllowedOrigins` includes your domain (or `*`)
3. Test with curl: `curl -H "Origin: https://example.com" -I https://dealbrain-card-images.s3.amazonaws.com/card-images/test.png`
4. Expected response includes `Access-Control-Allow-Origin` header

### Issue: Public access blocked

**Symptoms**: Public users can't view card images

**Solutions**:

1. Verify bucket policy grants public read access
2. Check "Block Public Access" settings:
   - `BlockPublicPolicy`: Must be **disabled**
   - `RestrictPublicBuckets`: Must be **disabled**
3. Test public access without credentials:
   ```bash
   curl https://dealbrain-card-images.s3.amazonaws.com/card-images/test.png
   ```

### Issue: High storage costs

**Symptoms**: AWS bill shows unexpected S3 charges

**Solutions**:

1. Verify lifecycle policy is enabled and working
2. Check number of objects: `aws s3 ls s3://dealbrain-card-images/card-images/ --recursive | wc -l`
3. Review S3 Storage Lens for detailed usage metrics
4. Consider reducing cache TTL from 30 days to 7 days

## Security Best Practices

### 1. Least Privilege Access

- Grant only necessary permissions (PutObject, GetObject, DeleteObject)
- Restrict IAM policies to `card-images/*` prefix only
- Don't grant `s3:*` wildcard permissions

### 2. Credential Management

- **Production**: Use IAM roles (EC2, ECS, Lambda)
- **Development**: Use IAM users with programmatic access
- Never commit credentials to git
- Rotate access keys every 90 days
- Enable MFA for IAM users

### 3. Encryption

- Enable server-side encryption (SSE-S3 or SSE-KMS)
- Consider encryption in transit (HTTPS only)
- For sensitive data, use bucket key encryption

### 4. Monitoring

- Enable S3 access logging
- Set up CloudWatch alarms for unusual activity
- Review AWS CloudTrail logs for API calls
- Monitor Storage Lens for usage patterns

### 5. Network Security

- Consider VPC endpoints for private S3 access
- Use bucket policies to restrict access by IP
- Enable AWS PrivateLink for enhanced security

## Next Steps

1. **Verify Configuration**:
   ```bash
   make test-s3
   ```

2. **Update Environment**:
   - Set `S3__ENABLED=true` in `.env`
   - Add AWS credentials (if using IAM user)
   - Restart API and worker containers

3. **Monitor Usage**:
   - Check S3 Storage Lens after 24 hours
   - Review access logs weekly
   - Set up CloudWatch billing alarms

4. **Production Optimization**:
   - Consider CloudFront CDN for global delivery
   - Enable S3 Transfer Acceleration if needed
   - Implement cache invalidation on listing updates
   - Set up automated backups if required

## Additional Resources

- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [Boto3 S3 Reference](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
- [S3 CORS Configuration](https://docs.aws.amazon.com/AmazonS3/latest/userguide/cors.html)
- [S3 Lifecycle Policies](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)

## Support

For questions or issues:

1. Check this guide's troubleshooting section
2. Review API/worker logs: `docker-compose logs api worker`
3. Test S3 connectivity: `make test-s3`
4. Review comprehensive setup guide: `/docs/infrastructure/card-image-generation-setup.md`
5. File a GitHub issue with logs and environment details

---

**Document Status**: Complete and production-ready

**Last Updated**: 2025-11-19

**Estimated Setup Time**: 15-30 minutes
