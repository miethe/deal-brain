# Database Backup & Recovery Guide

Comprehensive guide for backing up and recovering Deal Brain's PostgreSQL database.

## Backup Strategy Overview

**Recommended Approach:**
- Daily automated backups
- Weekly full backups stored separately
- Monthly backups for long-term retention
- External storage for disaster recovery
- Monthly restore testing

## Backup Methods

### Method 1: Docker Container (Recommended for VPS)

Simple backup using docker-compose without backup tools.

#### One-Time Backup

```bash
# From the deal-brain directory
docker-compose exec -T db pg_dump -U dealbrain dealbrain > backup.sql

# Compress for storage
gzip backup.sql

# Result: backup.sql.gz
```

#### Backup with Timestamp

```bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T db pg_dump -U dealbrain dealbrain > backup_$TIMESTAMP.sql
gzip backup_$TIMESTAMP.sql
echo "Backup created: backup_$TIMESTAMP.sql.gz"
```

### Method 2: Automated Backup Script

Create automatic daily backups using a shell script.

#### Create Backup Script

```bash
# Create script file
cat > /home/user/backup-deal-brain.sh << 'EOF'
#!/bin/bash

# Configuration
BACKUP_DIR="/var/backups/deal-brain"
DOCKER_COMPOSE_DIR="/home/user/deal-brain"
RETENTION_DAYS=30
LOG_FILE="/var/log/deal-brain-backup.log"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Log function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

log "Starting database backup..."

# Create backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/dealbrain_$TIMESTAMP.sql"

cd "$DOCKER_COMPOSE_DIR"

# Perform backup
if docker-compose exec -T db pg_dump -U dealbrain dealbrain > "$BACKUP_FILE"; then
    # Compress backup
    gzip "$BACKUP_FILE"
    BACKUP_FILE="$BACKUP_FILE.gz"

    # Get file size
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

    log "Backup successful: $BACKUP_FILE ($SIZE)"

    # Remove old backups (older than RETENTION_DAYS)
    find "$BACKUP_DIR" -name "dealbrain_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    log "Removed backups older than $RETENTION_DAYS days"
else
    log "Backup failed!"
    exit 1
fi

log "Backup completed successfully"
EOF

chmod +x /home/user/backup-deal-brain.sh
```

#### Schedule Automatic Backups

Add to crontab for daily backups at 2 AM:

```bash
# Edit crontab
crontab -e

# Add this line (or use the automated method below):
# 0 2 * * * /home/user/backup-deal-brain.sh
```

Or use script to add:

```bash
# Add to crontab if not already present
(crontab -l 2>/dev/null || echo "") | grep -v "backup-deal-brain.sh" | {
    cat
    echo "0 2 * * * /home/user/backup-deal-brain.sh"
} | crontab -

# Verify crontab entry
crontab -l | grep backup
```

### Method 3: Cloud Storage Integration

For disaster recovery, backup to cloud storage.

#### AWS S3 Backup Script

```bash
cat > /home/user/backup-to-s3.sh << 'EOF'
#!/bin/bash

# Configuration
BACKUP_DIR="/var/backups/deal-brain"
S3_BUCKET="s3://your-backup-bucket/deal-brain"
AWS_REGION="us-east-1"
RETENTION_DAYS=90
DOCKER_COMPOSE_DIR="/home/user/deal-brain"

# Create backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/dealbrain_$TIMESTAMP.sql"

cd "$DOCKER_COMPOSE_DIR"

if docker-compose exec -T db pg_dump -U dealbrain dealbrain > "$BACKUP_FILE"; then
    gzip "$BACKUP_FILE"
    BACKUP_FILE="$BACKUP_FILE.gz"

    # Upload to S3
    aws s3 cp "$BACKUP_FILE" "$S3_BUCKET/" --region "$AWS_REGION"

    # Remove local backups older than RETENTION_DAYS
    find "$BACKUP_DIR" -name "dealbrain_*.sql.gz" -mtime +$RETENTION_DAYS -delete

    # Keep S3 backups for 1 year (S3 lifecycle policy handles this)
    echo "Backup uploaded to $S3_BUCKET/$BACKUP_FILE"
else
    echo "Backup failed!"
    exit 1
fi
EOF

chmod +x /home/user/backup-to-s3.sh

# Schedule in crontab
(crontab -l 2>/dev/null || echo "") | grep -v "backup-to-s3.sh" | {
    cat
    echo "0 3 * * * /home/user/backup-to-s3.sh"
} | crontab -
```

#### DigitalOcean Spaces Backup Script

```bash
cat > /home/user/backup-to-spaces.sh << 'EOF'
#!/bin/bash

# Configuration
BACKUP_DIR="/var/backups/deal-brain"
SPACES_BUCKET="your-backup-space"
SPACES_REGION="nyc3"
DOCKER_COMPOSE_DIR="/home/user/deal-brain"

# Install doctl if needed
# sudo apt-get install -y doctl

# Create backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/dealbrain_$TIMESTAMP.sql"

cd "$DOCKER_COMPOSE_DIR"

if docker-compose exec -T db pg_dump -U dealbrain dealbrain > "$BACKUP_FILE"; then
    gzip "$BACKUP_FILE"
    BACKUP_FILE="$BACKUP_FILE.gz"

    # Upload using AWS CLI compatible endpoint
    aws s3 cp "$BACKUP_FILE" "s3://$SPACES_BUCKET/" \
        --endpoint-url "https://$SPACES_REGION.digitaloceanspaces.com" \
        --region "$SPACES_REGION"

    echo "Backup uploaded to Spaces"
else
    echo "Backup failed!"
    exit 1
fi
EOF

chmod +x /home/user/backup-to-spaces.sh
```

## Restore Procedures

### Full Database Restore

#### From Local Backup

```bash
# Stop the application (optional but recommended)
docker-compose down

# Extract backup if compressed
gunzip backup.sql.gz

# Restore database
docker-compose exec -T db psql -U dealbrain dealbrain < backup.sql

# Restart services
docker-compose up -d

# Verify restore
docker-compose exec api curl http://localhost:8000/api/health
```

#### From Compressed Backup

```bash
# Restore directly from .gz file
gunzip -c backup.sql.gz | docker-compose exec -T db psql -U dealbrain dealbrain
```

### Point-in-Time Recovery (PITR)

For production deployments, enable WAL archiving for PITR:

```bash
# Edit postgresql.conf inside container
docker-compose exec db bash

# Inside container:
echo "wal_level = replica" >> /var/lib/postgresql/data/postgresql.conf
echo "archive_mode = on" >> /var/lib/postgresql/data/postgresql.conf
echo "archive_command = 'cp %p /var/lib/postgresql/archive/%f'" >> /var/lib/postgresql/data/postgresql.conf

# Create archive directory
mkdir -p /var/lib/postgresql/archive

# Restart PostgreSQL
docker-compose restart db
```

### Selective Table Restore

```bash
# List tables in backup
gunzip -c backup.sql.gz | grep "^CREATE TABLE"

# Restore specific table
gunzip -c backup.sql.gz | grep -A 100 "CREATE TABLE your_table" | \
    docker-compose exec -T db psql -U dealbrain dealbrain
```

## Backup Verification

### List Available Backups

```bash
# List local backups
ls -lh /var/backups/deal-brain/

# List backups in S3
aws s3 ls s3://your-backup-bucket/deal-brain/ --recursive

# List backups in DigitalOcean Spaces
aws s3 ls s3://your-backup-space/deal-brain/ \
    --endpoint-url https://nyc3.digitaloceanspaces.com \
    --recursive
```

### Test Backup Integrity

```bash
# Check backup file is valid
gunzip -t backup.sql.gz
# Output: backup.sql.gz: OK

# Verify backup can be restored (test on separate database)
# Create test database
docker-compose exec db createdb -U dealbrain dealbrain_test

# Restore to test database
gunzip -c backup.sql.gz | \
    docker-compose exec -T db psql -U dealbrain dealbrain_test

# Verify data
docker-compose exec db psql -U dealbrain dealbrain_test -c "SELECT COUNT(*) FROM listing;"

# Drop test database
docker-compose exec db dropdb -U dealbrain dealbrain_test
```

### Monitor Backup Health

```bash
# Create monitoring script
cat > /home/user/check-backup-health.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/var/backups/deal-brain"
LOG_FILE="/var/log/deal-brain-backup.log"

echo "=== Recent Backups ==="
ls -lh $BACKUP_DIR/dealbrain_*.sql.gz | tail -5

echo ""
echo "=== Backup Directory Size ==="
du -sh $BACKUP_DIR

echo ""
echo "=== Available Disk Space ==="
df -h $BACKUP_DIR

echo ""
echo "=== Recent Backup Log ==="
tail -10 $LOG_FILE
EOF

chmod +x /home/user/check-backup-health.sh

# Run periodically
/home/user/check-backup-health.sh
```

## Backup Retention Policy

### Recommended Retention Schedule

| Backup Type | Frequency | Retention | Storage |
|------------|-----------|-----------|---------|
| Hourly | Every hour | 24 hours | Local |
| Daily | Every day | 7 days | Local |
| Weekly | Every Sunday | 4 weeks | Local or Cloud |
| Monthly | 1st of month | 12 months | Cloud |

### Implement Retention Policy

```bash
# Keep daily backups for 7 days
find /var/backups/deal-brain -name "dealbrain_*.sql.gz" -mtime +7 -delete

# Keep weekly backups for 4 weeks (separate script)
# Keep monthly backups in cloud indefinitely
```

## Disaster Recovery Planning

### Recovery Time Objective (RTO) & Recovery Point Objective (RPO)

- **RTO**: Time to restore and be operational
  - Target: < 1 hour
  - Current setup: 30 minutes (restore from local backup)

- **RPO**: Maximum data loss acceptable
  - Target: < 1 day
  - Current setup: 24 hours (daily backups)

### Disaster Recovery Checklist

**Preparation:**
- [ ] Document backup locations and credentials
- [ ] Test restore procedures monthly
- [ ] Maintain up-to-date documentation
- [ ] Store recovery procedure playbook securely

**Incident Response:**
- [ ] Confirm data corruption/loss (don't panic)
- [ ] Choose restore point based on requirements
- [ ] Execute restore procedures
- [ ] Verify data integrity
- [ ] Resume normal operations

### Emergency Restore Procedure

```bash
#!/bin/bash

# Steps to restore from backup in emergency

echo "=== Deal Brain Emergency Recovery ==="

# 1. Choose backup file
BACKUP_FILE="$1"
if [ -z "$BACKUP_FILE" ]; then
    echo "Available backups:"
    ls -lh /var/backups/deal-brain/
    echo ""
    echo "Usage: $0 /var/backups/deal-brain/backup_file.sql.gz"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found: $BACKUP_FILE"
    exit 1
fi

# 2. Stop application
echo "Stopping services..."
docker-compose down

# 3. Drop existing database
echo "Dropping existing database..."
docker-compose up -d db
sleep 5
docker-compose exec -T db dropdb -U dealbrain dealbrain 2>/dev/null
docker-compose exec -T db createdb -U dealbrain dealbrain

# 4. Restore backup
echo "Restoring backup from: $BACKUP_FILE"
gunzip -c "$BACKUP_FILE" | docker-compose exec -T db psql -U dealbrain dealbrain

# 5. Restart all services
echo "Starting services..."
docker-compose up -d

# 6. Verify restore
echo "Verifying restore..."
sleep 5
docker-compose exec api curl http://localhost:8000/api/health

echo "=== Recovery Complete ==="
```

## Monitoring & Alerts

### Backup Success Monitoring

```bash
# Monitor backup logs
tail -f /var/log/deal-brain-backup.log

# Alert if backup is missing
cat > /home/user/check-backup-exists.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/var/backups/deal-brain"
ALERT_EMAIL="admin@yourdomain.com"

# Check if backup from today exists
TODAY=$(date +%Y%m%d)
if [ ! -f "$BACKUP_DIR/dealbrain_${TODAY}_*.sql.gz" ]; then
    echo "ALERT: No backup for today ($TODAY)" | \
        mail -s "Deal Brain Backup Alert" "$ALERT_EMAIL"
fi
EOF

# Run daily via cron
0 3 * * * /home/user/check-backup-exists.sh
```

### Disk Space Monitoring

```bash
# Alert if backup directory is low on disk
cat > /home/user/check-disk-space.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/var/backups/deal-brain"
THRESHOLD=80
ALERT_EMAIL="admin@yourdomain.com"

USAGE=$(df "$BACKUP_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')

if [ "$USAGE" -gt "$THRESHOLD" ]; then
    echo "ALERT: Disk usage is ${USAGE}% on $BACKUP_DIR" | \
        mail -s "Deal Brain Disk Space Alert" "$ALERT_EMAIL"
fi
EOF

# Run daily via cron
0 4 * * * /home/user/check-disk-space.sh
```

## Backup Storage Best Practices

### Local Storage

- Keep on same server (fast restore)
- Rotate backups to prevent disk full
- Monitor disk space
- Not ideal for disaster recovery (server failure = data loss)

### Cloud Storage (Recommended)

- S3, Azure Blob, Google Cloud Storage
- Better for disaster recovery
- Automatic replication and durability
- Lower cost for long-term retention
- Requires credentials and network access

### Hybrid Approach (Best)

```
Local (7 days) → Cloud (90 days) → Archive (1+ year)
```

1. Keep recent backups locally for fast restore
2. Upload older backups to cloud
3. Archive annual backups offline if needed

## Troubleshooting

### Backup Fails with "Permission Denied"

```bash
# Check backup directory permissions
ls -ld /var/backups/deal-brain

# Fix permissions
sudo chown $USER:$USER /var/backups/deal-brain
chmod 755 /var/backups/deal-brain
```

### Docker Exec Fails with "Container Not Found"

```bash
# Ensure containers are running
docker-compose ps

# Start containers if needed
docker-compose up -d

# Use -T flag to disable pseudo-TTY allocation
docker-compose exec -T db pg_dump -U dealbrain dealbrain > backup.sql
```

### Restore Fails: "Database Already Exists"

```bash
# Drop existing database first
docker-compose exec -T db dropdb -U dealbrain dealbrain

# Create empty database
docker-compose exec -T db createdb -U dealbrain dealbrain

# Then restore
gunzip -c backup.sql.gz | docker-compose exec -T db psql -U dealbrain dealbrain
```

### Backup File Corrupted

```bash
# Test backup integrity
gunzip -t backup.sql.gz

# If corrupted, restore from previous backup
ls -lh /var/backups/deal-brain/ | sort -k6,7r | head -5

# Restore from older backup
gunzip -c /var/backups/deal-brain/older_backup.sql.gz | \
    docker-compose exec -T db psql -U dealbrain dealbrain
```

## Next Steps

- [Docker Compose Deployment](./docker-compose-vps.md) - Complete deployment
- [Monitoring Setup](./monitoring-setup.md) - Monitor backup success
- [SSL Setup](./ssl-setup.md) - Secure your deployment

---

**Backup Strategy Configured?** Next: [Monitoring Setup](./monitoring-setup.md)
