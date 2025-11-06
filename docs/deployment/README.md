# Deployment Guide

Welcome to the Deal Brain deployment documentation. This guide covers everything you need to deploy Deal Brain to production environments.

## Overview

Deal Brain is a full-stack Python/TypeScript application that can be deployed in various ways:

- **Docker Compose**: Recommended for VPS deployments (simplest approach)
- **Kubernetes**: For enterprise/high-scale deployments
- **Cloud Platforms**: AWS, GCP, Azure, DigitalOcean App Platform, Heroku

This documentation focuses on **Docker Compose deployment on a VPS**, which is the most common and cost-effective approach for most teams.

## Deployment Architecture

Deal Brain consists of several services:

```
┌─────────────────────────────────────────────────┐
│           Reverse Proxy (nginx/Caddy)           │
│              (SSL/TLS, Routing)                 │
└────────────────────┬────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
   ┌────▼──────┐          ┌──────▼──────┐
   │  Web App  │          │  FastAPI    │
   │(Next.js)  │          │  API        │
   │ :3000     │          │  :8000      │
   └───────────┘          └──────┬──────┘
                                 │
        ┌────────────────────────┴─────────────────┐
        │                                          │
   ┌────▼──────┐  ┌──────────┐  ┌──────────────┐  │
   │ PostgreSQL │  │  Redis   │  │   Celery    │  │
   │   (Port    │  │  (Port   │  │   Worker    │  │
   │   5432)    │  │  6379)   │  │             │  │
   └───────────┘  └──────────┘  └─────────────┘  │
                                                   │
   ┌──────────────────────────────────────────────┤
   │                                              │
   │  ┌────────────┐  ┌───────────┐             │
   │  │ Prometheus │  │ Grafana   │             │
   │  │ :9090      │  │ :3000     │             │
   │  └────────────┘  └───────────┘             │
   │                                             │
   │  ┌─────────────────────────────────────┐  │
   │  │  OpenTelemetry Collector            │  │
   │  │  (Traces & Metrics)                 │  │
   │  └─────────────────────────────────────┘  │
   └─────────────────────────────────────────────┘
```

## Quick Start

### 1. Choose Your Deployment Path

- **New to deployments?** Start with [Docker Compose on VPS](./docker-compose-vps.md)
- **Need to understand requirements?** Read [Prerequisites](./prerequisites.md)
- **Configuring environment?** See [Environment Variables](./environment-variables.md)
- **Setting up monitoring?** Follow [Monitoring Setup](./monitoring-setup.md)
- **Securing with SSL?** See [SSL/TLS Setup](./ssl-setup.md)
- **Protecting data?** Check [Database Backup](./database-backup.md)

### 2. Pre-Deployment Checklist

Before deploying, ensure you have:

- [ ] A Linux VPS (Ubuntu 20.04+ or similar)
- [ ] SSH access with sudo privileges
- [ ] Domain name pointing to server (for production)
- [ ] Generated a strong `SECRET_KEY` for the application
- [ ] Obtained SSL certificates or Let's Encrypt setup ready
- [ ] Basic understanding of Docker and Docker Compose

### 3. Security Considerations

**Critical items for production:**

1. **Change Default Credentials**
   - Database: Change `dealbrain` password in `.env`
   - Grafana: Change default `admin/admin` credentials
   - API: Set a strong `SECRET_KEY`

2. **Environment Variables**
   - Never commit `.env` file to version control
   - Use strong random values for all secrets
   - Restrict API keys (eBay, etc.) with IP allowlists when possible
   - Enable HTTPS only

3. **Database Security**
   - Use strong, randomly generated passwords
   - Configure PostgreSQL to only accept local connections or restricted IPs
   - Regular backups with encrypted storage
   - Monitor database logs for suspicious activity

4. **Network Security**
   - Use a firewall (ufw, iptables, or cloud provider firewall)
   - Only expose necessary ports (80, 443, 22 for SSH)
   - Use rate limiting on API endpoints
   - Monitor for DDoS attacks

5. **Application Security**
   - Keep Docker images updated (`docker pull` before deployment)
   - Monitor for security advisories
   - Enable audit logging
   - Use RBAC with PostgreSQL roles

## Deployment Steps Overview

### Step 1: Prepare Server

Follow the [Prerequisites](./prerequisites.md) guide to ensure your server has all required software.

### Step 2: Configure Environment

Use the [Environment Variables](./environment-variables.md) guide to set up your `.env` file with production values.

### Step 3: Deploy with Docker Compose

Follow the [Docker Compose VPS](./docker-compose-vps.md) guide for step-by-step deployment instructions.

### Step 4: Set Up SSL/TLS

Use the [SSL Setup](./ssl-setup.md) guide to secure your application with HTTPS.

### Step 5: Configure Monitoring

Follow the [Monitoring Setup](./monitoring-setup.md) guide to set up observability.

### Step 6: Configure Backups

Use the [Database Backup](./database-backup.md) guide to protect your data.

## Support & Troubleshooting

### Common Issues

**"Connection refused" when accessing the app**
- Check if all services are running: `docker-compose ps`
- Verify firewall settings: `sudo ufw status`
- Check reverse proxy configuration
- Review container logs: `docker-compose logs api`

**"Database connection failed"**
- Verify `DATABASE_URL` in `.env` matches running container
- Check PostgreSQL service health: `docker-compose ps db`
- Ensure database credentials match configuration
- Check database logs: `docker-compose logs db`

**"High CPU/Memory usage"**
- Check if a worker process is stuck: `docker-compose logs worker`
- Review Prometheus metrics via Grafana dashboard
- Scale services horizontally if needed
- Adjust resource limits in docker-compose.yml

**"SSL certificate expired"**
- Renew certificates immediately: `certbot renew`
- Check renewal logs: `journalctl -u certbot.timer`
- Verify auto-renewal is enabled and running

### Getting Help

1. Check relevant documentation file for your issue
2. Review container logs: `docker-compose logs [service-name]`
3. Check system resources: `docker stats`
4. Review error messages in application logs
5. Check GitHub issues or create a new one

## Maintenance

### Regular Tasks

- **Daily**: Monitor disk space and application health
- **Weekly**: Review error logs and performance metrics
- **Monthly**: Update Docker images and dependencies
- **Quarterly**: Test backup and restore procedures
- **As needed**: Scale services based on load

### Monitoring Health

Check service status:
```bash
docker-compose ps
```

View logs:
```bash
docker-compose logs -f [service-name]
```

Monitor resources:
```bash
docker stats
```

Check metrics in Grafana:
- Open browser: `https://your-domain/grafana`
- Login with admin credentials
- View pre-configured dashboards

## Environment Specifics

### Development
- Use local docker-compose without reverse proxy
- Enable debug logging
- Use self-signed certificates or skip HTTPS
- Disable production security measures

### Staging
- Use Docker Compose with SSL
- Enable production logging
- Test all workflows before production release
- Monitor for issues but allow some experimentation

### Production
- Use Docker Compose with strong SSL/TLS
- Enable audit logging
- Restrict access, enable rate limiting
- Monitor continuously with alerts
- Regular backup and disaster recovery drills

## Scale & Performance

### Capacity Planning

For a typical deployment:
- **Database**: 10GB minimum, 50GB recommended for 100K listings
- **Memory**: 4GB minimum, 8GB for 10K concurrent users
- **CPU**: 2 cores minimum, 4+ cores recommended
- **Storage**: 100GB for 1M listings with full history

### Scaling Strategies

**Vertical Scaling** (single VPS):
1. Increase VPS CPU/RAM
2. Adjust resource limits in docker-compose.yml
3. Optimize database queries

**Horizontal Scaling** (multiple servers):
1. Deploy multiple API containers on different VPS
2. Use load balancer (nginx, HAProxy)
3. Use shared PostgreSQL instance or managed database
4. Use shared Redis for caching

## Version & Upgrade Path

Deal Brain follows semantic versioning. Check for updates:

```bash
git fetch origin
git log --oneline origin/main -20
```

To upgrade:

1. Pull latest code: `git pull origin main`
2. Run migrations: `make migrate`
3. Rebuild images: `docker-compose up --build -d`
4. Verify health: `docker-compose ps`
5. Check logs for errors: `docker-compose logs`

## Further Reading

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Backup & Restore](https://www.postgresql.org/docs/current/backup.html)
- [Prometheus Monitoring](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/grafana/)
- [Let's Encrypt HTTPS](https://letsencrypt.org/docs/)

---

**Next Steps**: Start with the [Prerequisites](./prerequisites.md) guide to prepare your deployment environment.
