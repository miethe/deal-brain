# Docker Compose Deployment on VPS

This guide provides step-by-step instructions to deploy Deal Brain using Docker Compose on a Linux VPS.

## Prerequisites

Before starting, ensure you have completed the [Prerequisites](./prerequisites.md) guide:

- [ ] Linux VPS (Ubuntu 20.04+) with sufficient resources
- [ ] Docker and Docker Compose installed
- [ ] Domain name pointing to server IP
- [ ] SSL certificates ready (or plan to obtain with Let's Encrypt)
- [ ] `.env` file configured with production values
- [ ] SSH access to server

## Deployment Steps

### Step 1: Clone the Repository

```bash
# Connect to your server
ssh user@your-server-ip

# Clone the Deal Brain repository
git clone https://github.com/your-org/deal-brain.git
cd deal-brain

# Checkout main branch (or desired version)
git checkout main
git pull origin main
```

### Step 2: Prepare Environment File

```bash
# Copy example env file
cp .env.example .env

# Edit with your production values
nano .env
```

**Key variables to update:**

```bash
# Security - MUST CHANGE
SECRET_KEY=<your-strong-random-key>

# Database - MUST CHANGE PASSWORD
DATABASE_URL=postgresql+asyncpg://dealbrain:<strong-password>@db:5432/dealbrain
SYNC_DATABASE_URL=postgresql+psycopg://dealbrain:<strong-password>@db:5432/dealbrain

# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
WEB_URL=https://yourdomain.com

# API Keys (if applicable)
EBAY_API_KEY=<your-ebay-key-if-enabled>

# Observability
PROMETHEUS_ENABLED=true
```

For complete variable reference, see [Environment Variables Guide](./environment-variables.md).

### Step 3: Create Production Docker Compose Override

Create `docker-compose.prod.yml` for production overrides:

```yaml
version: "3.9"

services:
  api:
    restart: always
    environment:
      # Production settings
      DATABASE_URL: postgresql+asyncpg://dealbrain:${DB_PASSWORD}@db:5432/dealbrain
      SYNC_DATABASE_URL: postgresql+psycopg://dealbrain:${DB_PASSWORD}@db:5432/dealbrain
      LOG_LEVEL: INFO
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  worker:
    restart: always
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  db:
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  redis:
    restart: always
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M

  web:
    restart: always
    environment:
      NEXT_PUBLIC_API_URL: https://yourdomain.com/api
      NODE_ENV: production
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  grafana:
    restart: always
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
```

Use this with:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Step 4: Configure Reverse Proxy (Nginx)

Create `/etc/nginx/sites-available/deal-brain`:

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com;

    location / {
        return 301 https://$server_name$request_uri;
    }

    # Allow Let's Encrypt verification
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com;

    # SSL certificates (update paths)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_types text/plain text/css text/javascript application/javascript application/json;

    # API endpoint
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Web app
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Grafana
    location /grafana/ {
        proxy_pass http://localhost:3021/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Prometheus (restrict to internal use)
    location /prometheus/ {
        # Restrict access (uncomment and adjust)
        # allow 10.0.0.0/8;
        # deny all;

        proxy_pass http://localhost:9090/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/deal-brain /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl restart nginx
```

### Step 5: Build and Start Services

```bash
# Build Docker images
docker-compose build

# Start services in background
docker-compose up -d

# Monitor startup
docker-compose logs -f
```

Wait for all services to be healthy:

```bash
# Check service status
docker-compose ps

# Expected output (all should be "Up"):
# NAME      COMMAND             SERVICE    STATUS      PORTS
# db        postgres           db         Up ...
# redis     redis-server       redis      Up ...
# api       dealbrain-api      api        Up ...
# worker    celery worker      worker     Up ...
# web       pnpm dev           web        Up ...
```

### Step 6: Initialize Database

```bash
# Run database migrations
docker-compose exec api alembic upgrade head

# Seed initial data (optional)
docker-compose exec api python -m dealbrain_api.seeds
```

### Step 7: Verify Deployment

```bash
# Check all containers are healthy
docker-compose ps

# View logs for any errors
docker-compose logs --tail=50

# Test API endpoint
curl -X GET http://localhost:8000/api/health

# Test web app
curl -X GET http://localhost:3000 | head -20
```

### Step 8: Set Up SSL Certificate

For Let's Encrypt (recommended):

```bash
# Install Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot certonly --nginx -d yourdomain.com

# Verify certificate
sudo certbot certificates

# The certificate will be at:
# /etc/letsencrypt/live/yourdomain.com/
```

Update the nginx configuration paths above if needed.

### Step 9: Update Environment Variable

Update `.env` to reflect HTTPS URL:

```bash
WEB_URL=https://yourdomain.com
# In docker-compose.prod.yml or via environment:
NEXT_PUBLIC_API_URL=https://yourdomain.com/api
```

Restart services:

```bash
docker-compose down
docker-compose up -d
```

### Step 10: Test Full Deployment

Access your application:

1. **Web App**: https://yourdomain.com
2. **API**: https://yourdomain.com/api/docs
3. **Grafana**: https://yourdomain.com/grafana (admin/admin)
4. **Prometheus**: https://yourdomain.com/prometheus

Verify functionality:
- [ ] Web app loads and is responsive
- [ ] API endpoints are accessible
- [ ] Login/authentication works
- [ ] Data import functions properly
- [ ] Metrics display in Grafana
- [ ] No errors in logs

## Service Management

### View Service Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 api

# View logs since specific time
docker-compose logs --since 2024-01-01T00:00:00 api
```

### Restart Services

```bash
# All services
docker-compose restart

# Specific service
docker-compose restart api

# Soft reload (without losing state)
docker-compose restart worker
```

### Stop Services

```bash
# Stop all services (data persists in volumes)
docker-compose stop

# Stop and remove containers (volumes persist)
docker-compose down

# Stop and remove everything including volumes (DATA LOSS!)
docker-compose down -v
```

### Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild images
docker-compose build

# Restart with new images
docker-compose up -d

# Run migrations if schema changed
docker-compose exec api alembic upgrade head

# Verify
docker-compose logs -f api
```

## Resource Monitoring

### Check Container Resource Usage

```bash
# Real-time resource usage
docker stats

# Specific container
docker stats deal-brain_api_1

# With CPU/memory limits
docker stats --no-stream
```

### Check Disk Usage

```bash
# Overall disk usage
df -h

# Directory-specific
du -sh /var/lib/docker/volumes/*
du -sh /home/user/deal-brain

# Docker image size
docker images

# Docker system usage
docker system df
```

### Monitor Database Size

```bash
# From host
du -sh /var/lib/docker/volumes/deal-brain_db_data/_data

# From inside container
docker-compose exec db du -sh /var/lib/postgresql/data
```

## Backup Configuration

Configure automated backups (see [Database Backup Guide](./database-backup.md)):

```bash
# Create backup script
cat > /home/user/backup-database.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/deal-brain"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/dealbrain_$TIMESTAMP.sql"

mkdir -p $BACKUP_DIR

docker-compose -f /home/user/deal-brain/docker-compose.yml exec -T db pg_dump -U dealbrain dealbrain > $BACKUP_FILE

gzip $BACKUP_FILE

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE.gz"
EOF

chmod +x /home/user/backup-database.sh

# Add to crontab for daily backups at 2 AM
(crontab -l 2>/dev/null || echo "") | grep -v "backup-database.sh" | {
    cat
    echo "0 2 * * * /home/user/backup-database.sh >> /var/log/deal-brain-backup.log 2>&1"
} | crontab -
```

## Common Issues & Troubleshooting

### Container fails to start

```bash
# Check logs
docker-compose logs api

# Common causes:
# - Port already in use
# - Database connection failed
# - Missing environment variable
# - Out of disk space
```

### Database connection refused

```bash
# Verify database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Verify DATABASE_URL in .env
cat .env | grep DATABASE_URL

# Test connection
docker-compose exec api psql $DATABASE_URL -c "SELECT 1"
```

### Reverse proxy returning 502 Bad Gateway

```bash
# Verify backend services running
docker-compose ps

# Check nginx error logs
sudo tail -f /var/log/nginx/error.log

# Verify nginx can reach docker services
sudo curl http://localhost:8000/api/health
sudo curl http://localhost:3000
```

### Out of disk space

```bash
# Check space
df -h

# Clean up Docker
docker system prune -a --volumes

# Remove old backups
find /var/backups/deal-brain -name "*.gz" -mtime +30 -delete

# Check logs size
du -sh /var/lib/docker/containers/*/*-json.log
```

### High memory usage

```bash
# Check which container is using memory
docker stats

# Adjust resource limits in docker-compose.prod.yml
# Restart services
docker-compose restart

# Check for memory leaks in logs
docker-compose logs api | grep -i "memory\|oom\|killed"
```

## Performance Optimization

### Enable Container Resource Limits

Update `docker-compose.yml`:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### Optimize Database Performance

```bash
# Connect to database
docker-compose exec db psql -U dealbrain -d dealbrain

# Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

# Check index usage
SELECT schemaname, tablename, indexname, pg_size_pretty(pg_relation_size(indexrelid))
FROM pg_indexes
ORDER BY pg_relation_size(indexrelid) DESC;
```

### Enable Caching

Redis is already included in docker-compose.yml. Ensure it's being used:

```bash
# Verify Redis is running
docker-compose ps redis

# Check Redis usage
docker-compose exec redis redis-cli INFO stats
```

## Next Steps

1. **[Set Up SSL/TLS](./ssl-setup.md)** - Secure your deployment with HTTPS
2. **[Configure Monitoring](./monitoring-setup.md)** - Set up observability
3. **[Configure Backups](./database-backup.md)** - Protect your data
4. **[Environment Variables](./environment-variables.md)** - Reference for all variables

## Support Resources

- Check logs: `docker-compose logs -f [service]`
- Docker Compose docs: https://docs.docker.com/compose/
- PostgreSQL docs: https://www.postgresql.org/docs/
- Nginx docs: https://nginx.org/en/docs/

---

**Deployment Complete?** Next: [Set Up SSL/TLS](./ssl-setup.md)
