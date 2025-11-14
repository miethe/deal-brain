# Deployment Prerequisites

Complete this checklist before deploying Deal Brain to ensure a successful deployment.

## Server Requirements

### Hardware Specifications

| Resource | Minimum | Recommended | Large Scale |
|----------|---------|-------------|------------|
| CPU | 2 cores | 4 cores | 8+ cores |
| RAM | 4 GB | 8 GB | 16+ GB |
| Disk | 50 GB | 100 GB | 500+ GB |
| Disk Type | HDD | SSD | SSD |
| Network | 1 Gbps | 1 Gbps | 10 Gbps |

### Server Specifications by Tier

**Small (< 10K listings):**
- CPU: 2 cores
- RAM: 4 GB
- Disk: 50 GB SSD
- Example: DigitalOcean $12/month, Linode 4GB, AWS t3.medium

**Medium (10K-100K listings):**
- CPU: 4 cores
- RAM: 8 GB
- Disk: 100 GB SSD
- Example: DigitalOcean $24/month, Linode 8GB, AWS t3.large

**Large (100K+ listings):**
- CPU: 8+ cores
- RAM: 16+ GB
- Disk: 500+ GB SSD
- Example: DigitalOcean $48/month (or larger), Dedicated server

### Storage Considerations

**PostgreSQL Data:**
- Base installation: 1 GB
- Per 10K listings: 100-200 MB
- With indices and history: 2x base size

**Application Files:**
- Deal Brain application: 500 MB
- Docker images: 2-3 GB (can be pruned)
- Logs: 10-100 GB/month (rotate aggressively)

**Backup Storage:**
- Full database backup: 10-50% of database size
- Weekly backups: Keep 4 weeks (4-5 copies)
- Monthly backups: Keep 12 months
- External storage: Recommended (cloud object storage)

## Software Requirements

### Required

- **Operating System**: Ubuntu 20.04+, Debian 11+, CentOS 8+, or equivalent
- **Docker**: 20.10+ ([Install Docker](https://docs.docker.com/engine/install/))
- **Docker Compose**: 2.0+ ([Install Docker Compose](https://docs.docker.com/compose/install/))
- **Git**: 2.30+ (for cloning and version management)
- **curl/wget**: For testing endpoints

### Optional but Recommended

- **ufw**: For firewall management (usually pre-installed)
- **htop**: For process monitoring
- **du/df**: For disk usage monitoring (usually pre-installed)
- **nginx**: For reverse proxy (installed via package manager)
- **Caddy**: Alternative reverse proxy (simpler SSL handling)
- **fail2ban**: For brute-force protection

## Installation Steps

### 1. Update System Packages

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### 2. Install Docker

```bash
# Install Docker repository
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add current user to docker group (optional, requires re-login)
sudo usermod -aG docker $USER
newgrp docker

# Verify Docker installation
docker --version
docker run hello-world
```

### 3. Install Docker Compose

```bash
# Install Docker Compose v2 (recommended)
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

### 4. Install Git

```bash
sudo apt-get install -y git
git --version
```

### 5. Install Monitoring Tools (Optional)

```bash
# Install htop for monitoring
sudo apt-get install -y htop

# Install other useful tools
sudo apt-get install -y curl wget jq
```

## Domain & DNS Setup

### Prerequisites

- Registered domain name (or subdomain)
- Access to DNS provider (Route53, Cloudflare, etc.)

### Step 1: Point Domain to Server IP

1. Get your server's IP address:
   ```bash
   curl -s https://checkip.amazonaws.com
   ```
   Or from cloud provider dashboard

2. Update DNS A record:
   - Hostname: `yourdomain.com` or `app.yourdomain.com`
   - Type: `A`
   - Value: Your server's IP address
   - TTL: 300 (5 minutes for testing)

3. Verify DNS resolution:
   ```bash
   # Wait a few minutes for DNS propagation
   dig yourdomain.com
   nslookup yourdomain.com
   ```

### Step 2: Verify DNS (Before SSL Setup)

```bash
# Check DNS propagation (use multiple tools)
ping yourdomain.com

# Verify A record
dig yourdomain.com +short

# Detailed DNS info
nslookup -type=A yourdomain.com
```

DNS typically propagates in 5-30 minutes, but can take up to 48 hours.

## Firewall Configuration

### Enable UFW Firewall

```bash
# Enable firewall
sudo ufw enable

# Allow SSH (CRITICAL - do this first!)
sudo ufw allow 22/tcp

# Allow HTTP
sudo ufw allow 80/tcp

# Allow HTTPS
sudo ufw allow 443/tcp

# Optionally allow Docker ports (for debugging only)
sudo ufw allow 5432/tcp   # PostgreSQL (restrict to localhost recommended)
sudo ufw allow 6379/tcp   # Redis (restrict to localhost recommended)
sudo ufw allow 8000/tcp   # API (for debugging)
sudo ufw allow 3000/tcp   # Web (for debugging)
sudo ufw allow 9090/tcp   # Prometheus (for debugging)

# Allow all outbound traffic (default)
sudo ufw default allow outgoing

# Restrict incoming to established connections
sudo ufw default deny incoming

# View firewall status
sudo ufw status verbose
```

### Cloud Provider Firewall

If using cloud provider (AWS, DigitalOcean, etc.), also configure their security groups:

**Inbound Rules:**
- Port 22 (SSH): Restrict to your IP if possible
- Port 80 (HTTP): Allow from anywhere (0.0.0.0/0)
- Port 443 (HTTPS): Allow from anywhere (0.0.0.0/0)

**Outbound Rules:**
- Allow all traffic to anywhere (0.0.0.0/0)

## SSL Certificate Preparation

### Option 1: Let's Encrypt (Recommended & Free)

```bash
# Install Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Install nginx (required for Certbot)
sudo apt-get install -y nginx

# Get certificate (before deployment)
sudo certbot certonly --standalone -d yourdomain.com

# Certificates located in:
# /etc/letsencrypt/live/yourdomain.com/
```

### Option 2: Caddy (Auto SSL, Easiest)

Caddy automatically handles Let's Encrypt certificates. See [SSL Setup Guide](./ssl-setup.md).

### Option 3: Bring Your Own Certificates

If you have existing certificates:

1. Copy certificates to server:
   ```bash
   scp /local/path/fullchain.pem user@server:/tmp/
   scp /local/path/privkey.pem user@server:/tmp/
   ```

2. Create certificate directory:
   ```bash
   sudo mkdir -p /etc/ssl/deal-brain
   sudo mv /tmp/fullchain.pem /etc/ssl/deal-brain/
   sudo mv /tmp/privkey.pem /etc/ssl/deal-brain/
   sudo chmod 600 /etc/ssl/deal-brain/privkey.pem
   sudo chmod 644 /etc/ssl/deal-brain/fullchain.pem
   ```

## Database Planning

### PostgreSQL Version

- **Minimum**: PostgreSQL 12
- **Recommended**: PostgreSQL 15+
- **Docker Image**: `postgres:15-alpine` (default in docker-compose.yml)

### Database Backup Location

Choose backup storage strategy:

**Local Backup:**
```bash
# Create backup directory
mkdir -p /var/backups/deal-brain
chmod 700 /var/backups/deal-brain
```

**Cloud Storage:**
- AWS S3 bucket (recommended)
- DigitalOcean Spaces
- Google Cloud Storage
- Azure Blob Storage

For details, see [Database Backup Guide](./database-backup.md).

## Environment Variables

Create a production-ready `.env` file. Start from `.env.example`:

```bash
cp .env.example .env
nano .env  # Edit with your values
```

**Critical variables to change:**

```bash
# Security
SECRET_KEY=<generate-a-strong-random-key>

# Database
DATABASE_URL=postgresql+asyncpg://dealbrain:<strong-password>@db:5432/dealbrain
SYNC_DATABASE_URL=postgresql+psycopg://dealbrain:<strong-password>@db:5432/dealbrain

# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
WEB_URL=https://yourdomain.com

# API Keys (if using integrations)
EBAY_API_KEY=<your-key-if-enabled>
```

See [Environment Variables Guide](./environment-variables.md) for all options.

## Generate Strong Secrets

### Secret Key Generation

```bash
# Generate a 32-character random secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Or using openssl
openssl rand -base64 32

# Or using Python
python3 -c "import random, string; print(''.join(random.choices(string.ascii_letters + string.digits, k=32)))"
```

### Database Password Generation

```bash
# Generate a strong password
openssl rand -base64 16
```

Store these securely (password manager, secrets vault, etc.).

## SSH Key Setup (Recommended)

For enhanced security, set up SSH key-based authentication:

```bash
# On your local machine
ssh-keygen -t ed25519 -C "deploy@yourdomain.com"

# Copy public key to server
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@server-ip

# Disable password authentication (optional, after testing)
# Edit /etc/ssh/sshd_config and set:
# PasswordAuthentication no
# Then restart SSH
sudo systemctl restart sshd
```

## Pre-Deployment Checklist

Review and check off each item:

### Infrastructure
- [ ] Server is running and accessible via SSH
- [ ] Server meets minimum hardware requirements
- [ ] Operating system is up to date
- [ ] Firewall is configured (ports 22, 80, 443 open)

### Software
- [ ] Docker is installed and running
- [ ] Docker Compose 2.0+ is installed
- [ ] Git is installed
- [ ] UFW (or equivalent) firewall is configured

### Domain & SSL
- [ ] Domain name is registered and pointed to server IP
- [ ] DNS resolves correctly (`dig yourdomain.com`)
- [ ] SSL certificates obtained or ready
- [ ] Certificate paths available on server

### Configuration
- [ ] `.env` file created with production values
- [ ] `SECRET_KEY` is strong and random
- [ ] Database password is strong and random
- [ ] API keys configured (if applicable)
- [ ] `NEXT_PUBLIC_API_URL` points to correct host

### Backup & Monitoring
- [ ] Backup storage location decided and created
- [ ] Monitoring/observability plan in place
- [ ] Disk space available for logs and backups
- [ ] Backup retention policy documented

### Security
- [ ] All default credentials changed
- [ ] Firewall rules configured
- [ ] SSH key authentication set up (optional but recommended)
- [ ] Secrets stored securely (not in git)

## System Configuration Optimization

### Kernel Parameters (Optional)

For high-traffic deployments, optimize Linux kernel:

```bash
# Edit /etc/sysctl.conf
sudo nano /etc/sysctl.conf

# Add these lines (adjust for your needs):
# Increase file descriptors
fs.file-max = 2097152

# Increase network connections
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535

# Apply changes
sudo sysctl -p
```

### Docker Daemon Configuration (Optional)

Create `/etc/docker/daemon.json`:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "insecure-registries": []
}
```

Then restart Docker:
```bash
sudo systemctl restart docker
```

## Next Steps

Once you've completed all prerequisites:

1. **[Configure Environment Variables](./environment-variables.md)** - Set up your production configuration
2. **[Deploy with Docker Compose](./docker-compose-vps.md)** - Deploy the application
3. **[Set Up SSL/TLS](./ssl-setup.md)** - Secure your application
4. **[Configure Monitoring](./monitoring-setup.md)** - Set up observability
5. **[Set Up Backups](./database-backup.md)** - Protect your data

---

**Prerequisites Complete?** Next: [Configure Environment Variables](./environment-variables.md)
