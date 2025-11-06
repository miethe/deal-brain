# SSL/TLS Setup Guide

Complete guide for setting up HTTPS with SSL/TLS certificates for Deal Brain.

## Overview

Production Deal Brain deployments require HTTPS for security. This guide covers:

- Let's Encrypt (free, automated renewals)
- Manual certificate installation
- Reverse proxy configuration (nginx, Caddy)
- Certificate renewal and monitoring
- SSL testing and validation

## Let's Encrypt Setup (Recommended)

Let's Encrypt provides free, automated SSL/TLS certificates.

### Prerequisites

- Domain name pointing to your server
- Port 80 accessible (for certificate verification)
- Nginx installed on server

### Step 1: Install Certbot

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# Verify installation
certbot --version
```

### Step 2: Obtain Certificate

```bash
# Get certificate for your domain
sudo certbot certonly --nginx -d yourdomain.com

# For multiple domains
sudo certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com

# Verify certificate creation
sudo ls -la /etc/letsencrypt/live/yourdomain.com/
```

Expected files:
- `cert.pem` - Your certificate
- `chain.pem` - Intermediate certificates
- `fullchain.pem` - Certificate + chain (use this)
- `privkey.pem` - Private key

### Step 3: Update Nginx Configuration

Edit `/etc/nginx/sites-available/deal-brain`:

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com;

    # Allow Let's Encrypt verification
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com;

    # SSL certificate paths
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Recommended SSL configuration
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
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_types text/plain text/css text/javascript application/javascript application/json;

    # API proxy
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Web app proxy
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Step 4: Test and Enable Nginx Configuration

```bash
# Test configuration
sudo nginx -t
# Expected: "syntax is ok"

# Reload nginx
sudo systemctl restart nginx

# Verify nginx is running
sudo systemctl status nginx
```

### Step 5: Configure Automatic Renewal

Let's Encrypt certificates expire in 90 days. Certbot provides automatic renewal:

```bash
# Enable Certbot timer
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# Check timer status
sudo systemctl status certbot.timer

# Test renewal (dry-run, doesn't actually renew)
sudo certbot renew --dry-run

# View renewal logs
sudo journalctl -u certbot.timer -f
```

### Step 6: Update Deal Brain Environment

Update `.env` and docker-compose configuration to use HTTPS:

```bash
# Edit .env
WEB_URL=https://yourdomain.com

# In docker-compose.yml or docker-compose.prod.yml
environment:
  NEXT_PUBLIC_API_URL: https://yourdomain.com/api
```

Restart services:

```bash
docker-compose down
docker-compose up -d
```

## Caddy Setup (Alternative - Simpler)

Caddy automatically handles Let's Encrypt certificates with zero configuration.

### Prerequisites

- Domain name pointing to your server
- Port 80 and 443 accessible

### Step 1: Install Caddy

```bash
# Ubuntu/Debian
sudo apt-get install -y caddy

# Verify installation
caddy version
```

### Step 2: Create Caddyfile Configuration

Create `/etc/caddy/Caddyfile`:

```caddy
yourdomain.com {
    # API reverse proxy
    handle /api/* {
        reverse_proxy localhost:8000 {
            header_uri X-Forwarded-Proto https
            header_uri X-Forwarded-For {http.request.remote}
        }
    }

    # Web app reverse proxy
    reverse_proxy localhost:3000 {
        header_uri X-Forwarded-Proto https
        header_uri X-Forwarded-For {http.request.remote}
    }

    # Security headers
    header / {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "SAMEORIGIN"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "no-referrer-when-downgrade"
    }

    # Enable compression
    encode gzip

    # Enable HTTP/2 Server Push (optional)
    push /
}
```

### Step 3: Start Caddy

```bash
# Reload configuration
sudo systemctl reload caddy

# Check status
sudo systemctl status caddy

# View logs
sudo journalctl -u caddy -f
```

Caddy automatically obtains and renews Let's Encrypt certificates.

## Manual Certificate Installation

If you have existing certificates from another provider:

### Step 1: Prepare Certificates

Obtain your certificate files:
- `fullchain.pem` or `certificate.crt` (certificate + chain)
- `privkey.pem` or `key.pem` (private key)

### Step 2: Copy to Server

```bash
# From your local machine
scp /path/to/fullchain.pem user@server:/tmp/
scp /path/to/privkey.pem user@server:/tmp/
```

### Step 3: Install Certificates

```bash
# Create certificate directory
sudo mkdir -p /etc/ssl/deal-brain

# Copy certificates
sudo mv /tmp/fullchain.pem /etc/ssl/deal-brain/
sudo mv /tmp/privkey.pem /etc/ssl/deal-brain/

# Set permissions
sudo chmod 600 /etc/ssl/deal-brain/privkey.pem
sudo chmod 644 /etc/ssl/deal-brain/fullchain.pem

# Verify
sudo ls -la /etc/ssl/deal-brain/
```

### Step 4: Update Nginx Configuration

Edit `/etc/nginx/sites-available/deal-brain`:

```nginx
ssl_certificate /etc/ssl/deal-brain/fullchain.pem;
ssl_certificate_key /etc/ssl/deal-brain/privkey.pem;
```

### Step 5: Manual Renewal

When certificate expires (usually annually), repeat the process:

```bash
# Copy new certificates
scp /path/to/new-fullchain.pem user@server:/tmp/
sudo mv /tmp/new-fullchain.pem /etc/ssl/deal-brain/fullchain.pem

# Reload nginx
sudo nginx -t
sudo systemctl reload nginx

# Verify
openssl x509 -in /etc/ssl/deal-brain/fullchain.pem -text -noout | grep "Not After"
```

## Certificate Management

### Check Certificate Expiration

```bash
# Using openssl
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/fullchain.pem -text -noout | grep "Not After"

# Using certbot
sudo certbot certificates

# Check expiration date only
sudo certbot certificates | grep "Expiration Date"
```

### Monitor Certificate Expiration

```bash
# Create monitoring script
cat > /home/user/check-cert-expiry.sh << 'EOF'
#!/bin/bash

CERT_FILE="/etc/letsencrypt/live/yourdomain.com/fullchain.pem"
ALERT_EMAIL="admin@yourdomain.com"
WARN_DAYS=30

if [ ! -f "$CERT_FILE" ]; then
    echo "Certificate file not found: $CERT_FILE"
    exit 1
fi

# Get expiry date and convert to seconds since epoch
EXPIRY_DATE=$(openssl x509 -in "$CERT_FILE" -noout -dates | grep "notAfter" | cut -d= -f2)
EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s)
NOW_EPOCH=$(date +%s)
DAYS_LEFT=$(( ($EXPIRY_EPOCH - $NOW_EPOCH) / 86400 ))

echo "Certificate expires in $DAYS_LEFT days"

# Alert if expiring soon
if [ $DAYS_LEFT -lt $WARN_DAYS ]; then
    echo "WARNING: Certificate expires in $DAYS_LEFT days!" | \
        mail -s "SSL Certificate Expiration Alert" "$ALERT_EMAIL"
fi
EOF

chmod +x /home/user/check-cert-expiry.sh

# Run weekly
(crontab -l 2>/dev/null || echo "") | grep -v "check-cert-expiry.sh" | {
    cat
    echo "0 9 * * 0 /home/user/check-cert-expiry.sh"
} | crontab -
```

## SSL/TLS Testing

### Test SSL Configuration

```bash
# Test with openssl
openssl s_client -connect yourdomain.com:443 -tls1_2

# Test with curl
curl -v https://yourdomain.com

# Test specific cipher
openssl s_client -connect yourdomain.com:443 -cipher 'HIGH'
```

### Check SSL Certificate Details

```bash
# Full certificate details
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/fullchain.pem -text -noout

# Quick summary
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/fullchain.pem -noout -subject -issuer -dates

# Check certificate chain
openssl s_client -connect yourdomain.com:443 -showcerts < /dev/null
```

### Online SSL Testing

Use online tools to verify SSL configuration:

- **SSL Labs**: https://www.ssllabs.com/ssltest/ (detailed report, grade A-F)
- **Mozilla Observatory**: https://observatory.mozilla.org/ (security configuration)
- **Qualys**: https://www.ssllabs.com/ssltest/analyze.html (same as SSL Labs)

Expected grade: A or A+ for proper configuration

## Common SSL Issues

### Certificate Verification Failed

```bash
# Usually means certificate chain is incomplete

# Verify full chain is installed
openssl s_client -connect yourdomain.com:443 -showcerts

# Should show three certificates: end entity, intermediate, root

# Fix: Ensure using fullchain.pem, not just cert.pem
```

### Mixed Content Warning

```
Mixed Content: The page at 'https://...' was loaded over a secure connection,
but contains a resource that was loaded over insecure connection.
```

**Fix**: Ensure all resources use HTTPS, not HTTP.

1. Update `.env`: `WEB_URL=https://yourdomain.com`
2. Check nginx configuration for all proxies using HTTPS
3. Restart services and clear browser cache

### Certificate Not Trusted

```bash
# Usually means certificate chain is wrong

# Verify certificate issuer
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/fullchain.pem -noout -issuer

# Should show: issuer=C = US, O = Let's Encrypt, CN = R3
```

### Renewal Failure

```bash
# Check renewal logs
sudo journalctl -u certbot.timer -n 50

# Manual renewal
sudo certbot renew -v

# Common causes:
# - Port 80 not accessible
# - DNS not pointing to server
# - Rate limit exceeded (wait 7 days)

# Force renewal (bypass rate limit)
sudo certbot renew --force-renewal
```

## Security Best Practices

### 1. Use Strong SSL Configuration

```nginx
# Modern browsers only
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5:!RSA;
ssl_prefer_server_ciphers on;
```

### 2. Enable HSTS

```nginx
# Forces HTTPS for one year (including subdomains)
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### 3. Minimize Certificate Exposure

```bash
# Restrict certificate file permissions
sudo chmod 600 /etc/letsencrypt/live/*/privkey.pem
sudo chmod 644 /etc/letsencrypt/live/*/fullchain.pem
```

### 4. Monitor Certificate Issuance

Let's Encrypt sends notifications to your email when certificates are issued/renewed.

### 5. Regular Updates

```bash
# Keep certbot updated
sudo apt-get update && apt-get install --only-upgrade certbot

# Keep nginx updated
sudo apt-get install --only-upgrade nginx
```

## Disaster Recovery

### Backup Certificates

```bash
# Backup Let's Encrypt certificates
sudo tar czf /var/backups/letsencrypt-backup.tar.gz /etc/letsencrypt/

# Backup manual certificates
sudo tar czf /var/backups/ssl-certs-backup.tar.gz /etc/ssl/deal-brain/

# Store in secure location
# scp /var/backups/letsencrypt-backup.tar.gz backup-server:/backups/
```

### Restore Certificates

```bash
# Restore Let's Encrypt certificates
sudo tar xzf /var/backups/letsencrypt-backup.tar.gz -C /

# Restore manual certificates
sudo tar xzf /var/backups/ssl-certs-backup.tar.gz -C /

# Reload nginx
sudo systemctl reload nginx
```

## Troubleshooting

### Certbot Can't Access Port 80

```bash
# Verify port 80 is accessible
sudo netstat -tulpn | grep :80

# Check firewall
sudo ufw status
sudo ufw allow 80/tcp

# Check if nginx is running
sudo systemctl status nginx
```

### Nginx Configuration Has Errors

```bash
# Test nginx configuration
sudo nginx -t

# Fix syntax errors, then reload
sudo systemctl reload nginx

# Check logs
sudo tail -f /var/log/nginx/error.log
```

### Certificate Still Shows as Untrusted

```bash
# Clear browser cache
# Hard refresh: Ctrl+Shift+R (Cmd+Shift+R on Mac)

# Verify certificate is valid
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Check certificate chain
curl -v https://yourdomain.com 2>&1 | grep -i "certificate"
```

## Next Steps

- [Docker Compose Deployment](./docker-compose-vps.md) - Return to deployment
- [Monitoring Setup](./monitoring-setup.md) - Monitor your deployment
- [Database Backup](./database-backup.md) - Protect your data

## Resources

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Certbot Documentation](https://certbot.eff.org/docs/)
- [Caddy Documentation](https://caddyserver.com/docs/)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [OWASP SSL Best Practices](https://owasp.org/www-community/attacks/SSL-TLS_Vulnerability)

---

**SSL Setup Complete?** Next: [Monitoring Setup](./monitoring-setup.md)
