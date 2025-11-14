# Deal Brain Troubleshooting Guide

Comprehensive guide to diagnosing and resolving common issues with Deal Brain development and deployment. For each issue, we provide symptoms, root causes, solutions, and prevention tips.

## Table of Contents

1. [Docker Issues](#docker-issues)
2. [Local Development Issues](#local-development-issues)
3. [Database Setup Problems](#database-setup-problems)
4. [API Connection Issues](#api-connection-issues)
5. [Performance Debugging](#performance-debugging)
6. [Common Code Mistakes](#common-code-mistakes)
7. [Quick Diagnostic Commands](#quick-diagnostic-commands)

---

## Docker Issues

### Container Won't Start

**Symptoms:**
- `docker-compose up` fails with error messages
- Container exits immediately after starting
- No logs visible in container output

**Root Causes:**
- Build failures (missing dependencies, syntax errors)
- Environment variable issues (missing .env file)
- Dependency service not ready (db, redis not healthy)
- Port already in use
- Insufficient disk space or memory

**Solutions:**

1. **Check the build log:**
```bash
docker-compose up --build 2>&1 | head -100
```
Look for specific error messages about which service failed.

2. **Examine container logs:**
```bash
docker-compose logs api      # View API service logs
docker-compose logs web      # View web service logs
docker-compose logs db       # View database logs
docker-compose logs -f api   # Follow logs in real-time
```

3. **Verify environment file exists:**
```bash
ls -la /home/user/deal-brain/.env.example
# Copy to .env if needed for local development
cp /home/user/deal-brain/.env.example /home/user/deal-brain/.env
```

4. **Check dependency health:**
```bash
# View all services and their status
docker-compose ps

# Check if db is healthy
docker-compose logs db | grep -i "health\|ready"
```

5. **Rebuild from scratch:**
```bash
# Remove all containers and volumes
docker-compose down -v

# Rebuild and start fresh
docker-compose up --build
```

**Prevention Tips:**

- Always verify `.env` file exists before starting
- Use `docker-compose logs` frequently during development to catch issues early
- Run `make format` and `make lint` before committing to catch syntax errors
- Check disk space: `df -h /` (should have >5GB free for Docker)
- Monitor Docker memory: `docker stats` (stop if using >80% of available RAM)

---

### Port Conflicts

**Symptoms:**
- Error: "Address already in use" when starting containers
- Unable to connect to services on expected ports
- Ports don't match docker-compose.yml configuration

**Root Causes:**
- Another process already using the port
- Previous Docker containers still running
- Host firewall blocking port access
- Container exposing wrong port internally

**Deal Brain Port Reference:**
- **5442** (PostgreSQL) - Database
- **6399** (Redis) - Cache/Queue
- **8020** (FastAPI) - Backend API
- **3020** (Next.js) - Web frontend
- **9090** (Prometheus) - Metrics collection
- **3021** (Grafana) - Monitoring dashboard

**Solutions:**

1. **Find what's using a port:**
```bash
# Linux/Mac
lsof -i :5442
lsof -i :8020
lsof -i :3020

# Windows (in PowerShell)
Get-NetTCPConnection -LocalPort 5442 | Get-Process
```

2. **Kill process using port:**
```bash
# Linux/Mac - replace PID with actual process ID
kill -9 <PID>

# Or use fuser
fuser -k 5442/tcp
```

3. **Change port in docker-compose.yml:**
```yaml
services:
  api:
    ports:
      - "8021:8000"  # Changed from 8020 to 8021
```
Then restart: `docker-compose down && docker-compose up --build`

4. **Check if containers are still running:**
```bash
# Stop all containers
docker-compose down

# List remaining containers
docker ps -a

# Remove any lingering containers
docker rm <container-id>
```

**Prevention Tips:**

- Always run `docker-compose down` before stopping Docker
- Check available ports before starting: `docker-compose ps`
- Use different port mappings if running multiple instances
- Document any port changes in your local `.env` file

---

### Volume Permission Issues

**Symptoms:**
- "Permission denied" errors when accessing volumes
- Database cannot write to `/var/lib/postgresql/data`
- Cannot read/write files in mounted volumes
- Logs show permission errors (13: Permission denied)

**Root Causes:**
- Docker container running as different user than volume owner
- Mounted directories have restrictive permissions (755, 600)
- Volume ownership mismatch between host and container
- SELinux or AppArmor policies blocking access

**Solutions:**

1. **Check volume permissions:**
```bash
# List volumes
docker volume ls

# Inspect specific volume
docker volume inspect dealbrain_db_data

# Check host directory permissions
ls -la /var/lib/docker/volumes/dealbrain_db_data/_data
```

2. **Fix permissions (if using named volumes):**
```bash
# Stop containers first
docker-compose down

# Remove and recreate volume with proper permissions
docker volume rm dealbrain_db_data
docker volume create dealbrain_db_data

# Restart containers
docker-compose up --build
```

3. **For bind mounts, adjust host permissions:**
```bash
# If volumes are mounted from host directories
sudo chown -R 999:999 /path/to/data  # For Postgres
sudo chown -R 1000:1000 /path/to/redis # For Redis

# Or use broader permissions
chmod 755 /path/to/data
```

4. **Check if using Docker Desktop (different permissions model):**
```bash
# Docker Desktop on Windows/Mac uses VM, different permission model
# Usually auto-handled, but try resetting:
docker reset  # Nuclear option - removes all containers/images
```

**Prevention Tips:**

- Use named volumes (preferred) instead of bind mounts when possible
- If using bind mounts, match container user to host user
- Check volume permissions after pulling latest code
- Document any custom volume configuration in `.env`

---

### Network Connectivity Between Containers

**Symptoms:**
- API cannot connect to database: "Connection refused"
- Web cannot reach API: "ECONNREFUSED"
- Containers can't resolve service names (e.g., `db`, `redis`)
- Worker cannot connect to Redis queue

**Root Causes:**
- Services not on same Docker network
- Service dependency not started yet
- Incorrect connection URLs (localhost vs service name)
- Network isolation or firewall rules
- Service health checks failing

**Solutions:**

1. **Verify network and service connectivity:**
```bash
# Check Docker network
docker network ls
docker network inspect dealbrain_default

# Verify all services are on same network
docker-compose ps -a

# Check service health
docker-compose ps | grep "healthy\|starting\|exited"
```

2. **Test connectivity between containers:**
```bash
# Open shell in API container
docker-compose exec api /bin/sh

# Inside container, test database connection
nc -zv db 5432
psql -h db -U dealbrain -d dealbrain -c "SELECT 1"

# Test Redis connection
redis-cli -h redis ping
```

3. **Verify connection URLs are using service names, not localhost:**

Inside containers, use:
- `postgresql+asyncpg://dealbrain:dealbrain@db:5432/dealbrain` (NOT localhost)
- `redis://redis:6379/0` (NOT localhost)

Check docker-compose.yml environment variables:
```yaml
api:
  environment:
    DATABASE_URL: postgresql+asyncpg://dealbrain:dealbrain@db:5432/dealbrain
    REDIS_URL: redis://redis:6379/0
```

4. **Force restart with health checks:**
```bash
# Remove containers but keep volumes
docker-compose down

# Restart with explicit wait for dependencies
docker-compose up --build -d

# Wait for db to be healthy
sleep 30

# Check status
docker-compose ps
```

5. **Check service startup order:**
```bash
# View docker-compose.yml for depends_on
grep -A 5 "depends_on:" docker-compose.yml

# Verify services start in correct order:
# 1. db (must be healthy first)
# 2. redis
# 3. api
# 4. web, worker (depend on api)
```

**Prevention Tips:**

- Always use service names (db, redis, api) not localhost in container-to-container communication
- Use `depends_on` with `condition: service_healthy` for critical dependencies
- Add health checks to all services
- Test connectivity after pulling new code
- Keep services on same Docker network

---

## Local Development Issues

### Poetry Installation Problems

**Symptoms:**
- `poetry install` fails with dependency resolution errors
- "poetry: command not found"
- Python packages won't install
- Version conflicts between packages

**Root Causes:**
- Python version incompatibility (requires 3.10+)
- Poetry not installed or not in PATH
- Corrupted Poetry cache
- Conflicting dependency versions
- Missing system dependencies (for compiled packages)

**Solutions:**

1. **Verify Python version:**
```bash
python --version       # Should be 3.10, 3.11, or 3.12
python3 --version      # Try python3 if python doesn't work

# If wrong version, install correct one
# macOS: brew install python@3.11
# Ubuntu/Debian: sudo apt install python3.11
# Windows: Download from python.org
```

2. **Install or reinstall Poetry:**
```bash
# Install poetry (recommended method)
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH (if not auto-added)
export PATH="$HOME/.local/bin:$PATH"

# Verify installation
poetry --version
```

3. **Clear Poetry cache and reinstall:**
```bash
# Remove cache
rm -rf ~/Library/Caches/pypoetry     # macOS
rm -rf ~/.cache/pypoetry              # Linux

# Remove lock file
rm poetry.lock

# Reinstall dependencies
poetry install --no-cache
```

4. **Resolve dependency conflicts:**
```bash
# Update lock file to resolve conflicts
poetry lock --no-update

# If that fails, try removing and recreating
poetry env remove 3.11  # Remove existing environment
poetry install          # Create fresh environment

# Check what environment Poetry is using
poetry env info
```

5. **Install missing system dependencies:**
```bash
# For compiled packages (psycopg2, etc.), may need:

# Ubuntu/Debian
sudo apt-get install python3.11-dev libpq-dev

# macOS
brew install postgresql

# Retry poetry install
poetry install
```

**Prevention Tips:**

- Pin Python version in pyproject.toml
- Run `poetry lock` after any dependency changes
- Keep poetry updated: `poetry self update`
- Document Python version requirements in README
- Use `poetry show` to view all installed packages

---

### pnpm Installation Problems

**Symptoms:**
- `pnpm install` fails with network or permission errors
- "pnpm: command not found"
- Node modules lock file conflicts
- Package installation hangs

**Root Causes:**
- Node.js not installed or wrong version
- pnpm not installed
- Corrupted node_modules or lockfile
- Network connectivity issues
- Insufficient disk space

**Solutions:**

1. **Verify Node.js version:**
```bash
node --version   # Should be 18+
npm --version    # Should be 9+
pnpm --version   # Should be 8+

# If wrong version, install nvm (Node Version Manager)
# Then: nvm install 18 && nvm use 18
```

2. **Install or update pnpm:**
```bash
# Using npm
npm install -g pnpm@latest

# Using Homebrew (macOS)
brew install pnpm

# Verify
pnpm --version
```

3. **Clean install:**
```bash
# Remove lock file and node_modules
rm -rf pnpm-lock.yaml
rm -rf node_modules
rm -rf apps/*/node_modules

# Fresh install
pnpm install --frozen-lockfile=false

# If using frozen, update lock file instead
pnpm install --frozen-lockfile false --update-lockfile
```

4. **Fix network issues:**
```bash
# Check npm registry connectivity
npm ping

# Change registry if needed
pnpm config set registry https://registry.npmjs.org

# Set higher timeout for slow connections
pnpm config set fetch-timeout 60000

# Retry with verbose logging
pnpm install --verbose 2>&1 | tee install.log
```

5. **Rebuild native modules:**
```bash
# If packages with native bindings fail
pnpm rebuild

# Or rebuild specific package
pnpm rebuild node-sass
```

**Prevention Tips:**

- Keep Node.js version documented in `.nvmrc`
- Pin pnpm version in package.json or GitHub Actions
- Use `pnpm-lock.yaml` for reproducible installs
- Run `pnpm install` on main branch weekly to keep lock file fresh
- Check disk space before installing: `df -h`

---

### Python Version Mismatches

**Symptoms:**
- Type errors or syntax errors when running code
- "SyntaxError: invalid syntax" for f-strings or walrus operators
- Import errors for new syntax features
- Poetry installs but runtime errors occur

**Root Causes:**
- Using Python <3.10 (project requires 3.10+)
- Multiple Python versions installed, using wrong one
- Poetry using different Python than shell
- Virtual environment not activated

**Solutions:**

1. **Determine which Python is being used:**
```bash
# Find all installed Pythons
which python3
which python

# Check version of each
python3 --version
python --version

# Check Poetry's environment
poetry env info
poetry env list
```

2. **Force Poetry to use specific Python:**
```bash
# Remove current environment
poetry env remove $(poetry env info --path | xargs basename)

# Install with specific Python
poetry env use /usr/bin/python3.11

# Verify
poetry env info
```

3. **Update pyproject.toml with Python version:**
```toml
[tool.poetry.dependencies]
python = "^3.10"  # Requires 3.10 or higher
```

4. **Check which Python shell is using:**
```bash
# Create shell script to verify
python3 -c "import sys; print(sys.version, sys.executable)"

# Compare to Poetry
poetry run python -c "import sys; print(sys.version, sys.executable)"

# They should match if Poetry env is activated
```

5. **Use pyenv for version management:**
```bash
# Install pyenv
brew install pyenv  # macOS
# Or follow https://github.com/pyenv/pyenv for other OS

# Install correct Python
pyenv install 3.11.0

# Set local version
pyenv local 3.11.0

# Verify
python --version
```

**Prevention Tips:**

- Pin Python version in pyproject.toml: `python = "^3.10"`
- Use `.python-version` file for consistency
- Run `poetry run python -c "import sys; print(sys.version)"` in CI/CD
- Document Python version requirement in README

---

### Node Version Mismatches

**Symptoms:**
- Build errors with "Cannot find module" or syntax errors
- TypeScript compilation fails
- ESM vs CommonJS compatibility issues
- Version-specific features don't work

**Root Causes:**
- Node.js version too old (<18)
- Using npm instead of pnpm in Docker
- Multiple Node versions installed
- .nvmrc file not being respected

**Solutions:**

1. **Verify Node version:**
```bash
node --version     # Should be 18+
npm --version      # Should be 9+
pnpm --version     # Should be 8+
```

2. **Install correct Node version:**
```bash
# Using nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Load nvm
source ~/.bashrc

# Install and use correct version
nvm install 18
nvm use 18

# Verify
node --version
```

3. **Check .nvmrc:**
```bash
# Verify file exists
cat /home/user/deal-brain/.nvmrc

# Use nvm to auto-switch
nvm use  # If .nvmrc exists, uses that version
```

4. **Update Node.js:**
```bash
# Using nvm
nvm install node  # Latest
nvm install 18    # Specific version

# Using Homebrew (macOS)
brew upgrade node

# Verify upgrade worked
node --version
```

5. **Clear Node cache and reinstall:**
```bash
# Clear npm cache
npm cache clean --force
pnpm store prune

# Remove lock file
rm pnpm-lock.yaml

# Reinstall
pnpm install
```

**Prevention Tips:**

- Use .nvmrc file with version pinned
- Add Node version check to CI/CD
- Document minimum Node version in README
- Keep Node updated regularly: `nvm install node`

---

## Database Setup Problems

### Connection Refused Errors

**Symptoms:**
- "Connection refused" when connecting to database
- "psycopg2.OperationalError: connection failed"
- Frontend shows "API Error" when loading listings
- Worker cannot connect to Redis

**Root Causes:**
- Database service not running
- Wrong connection string/credentials
- Database port not exposed
- Firewall blocking connection
- Database hasn't finished initializing
- Connection pooling issues

**Solutions:**

1. **Verify database is running:**
```bash
# Check container status
docker-compose ps | grep db

# Check database logs
docker-compose logs db | tail -50

# Try connecting to database
docker-compose exec db psql -U dealbrain -d dealbrain -c "SELECT 1"
```

2. **Verify connection string:**
```bash
# For local development (not Docker)
DATABASE_URL=postgresql+asyncpg://dealbrain:dealbrain@localhost:5442/dealbrain

# For Docker containers
DATABASE_URL=postgresql+asyncpg://dealbrain:dealbrain@db:5432/dealbrain

# Check environment variables
docker-compose config | grep DATABASE_URL
```

3. **Check port mapping:**
```bash
# Verify port is exposed
docker-compose ps
# Should show: 5442->5432/tcp (host port -> container port)

# Verify you can connect to port
nc -zv localhost 5442  # Should show "Connection successful"
```

4. **Restart database service:**
```bash
# Restart just the database
docker-compose restart db

# Or remove and recreate
docker-compose down db
docker-compose up db -d

# Wait for health check
sleep 10
docker-compose ps | grep db
```

5. **Check database exists:**
```bash
# List databases in container
docker-compose exec db psql -U dealbrain -l

# If dealbrain database missing, create it
docker-compose exec db psql -U dealbrain -c "CREATE DATABASE dealbrain"
```

6. **Reset database completely:**
```bash
# Remove database volume
docker-compose down
docker volume rm dealbrain_db_data

# Restart services (new empty database created)
docker-compose up -d db

# Wait for initialization
sleep 10

# Verify database exists
docker-compose exec db psql -U dealbrain -l
```

**Prevention Tips:**

- Always verify database is ready before starting other services
- Use health checks in docker-compose.yml
- Test connection string with simple query before running app
- Keep database initialization scripts in version control
- Monitor database logs during startup

---

### Migration Failures

**Symptoms:**
- Alembic migration fails with error
- "FAILED at init with error: Target database is not up to date"
- Schema mismatch errors
- Migration revision conflicts

**Root Causes:**
- Database not initialized
- Migration files corrupt or conflicting
- Database schema differs from expected
- Migration not backwards-compatible
- Running migrations in wrong order

**Solutions:**

1. **Verify database is accessible:**
```bash
# Test connection
poetry run alembic current

# If fails, database might not be ready
# Wait a moment and retry
sleep 5
poetry run alembic current
```

2. **Check migration status:**
```bash
# See current revision
poetry run alembic current

# See all revisions
poetry run alembic history

# See pending migrations
poetry run alembic heads
```

3. **Upgrade to latest migration:**
```bash
# Apply all pending migrations
poetry run alembic upgrade head

# Check result
poetry run alembic current
```

4. **Rollback if migration fails:**
```bash
# Rollback one revision
poetry run alembic downgrade -1

# Rollback to specific revision
poetry run alembic downgrade <revision-id>

# Verify
poetry run alembic current
```

5. **Reset and re-migrate from scratch:**
```bash
# Stop services
docker-compose down

# Remove database volume (WARNING: deletes data)
docker volume rm dealbrain_db_data

# Start fresh
docker-compose up -d db

# Wait for db
sleep 10

# Run migrations
poetry run alembic upgrade head

# Verify
poetry run alembic current
```

6. **Check migration file syntax:**
```bash
# List migration files
ls -la /home/user/deal-brain/apps/api/alembic/versions/

# Check for conflicts (multiple heads)
poetry run alembic heads

# If multiple heads, need to merge manually
poetry run alembic merge -m "merge heads" $(poetry run alembic heads)
```

**Prevention Tips:**

- Always run migrations on fresh database
- Test migrations in CI/CD before merging
- Keep migration files checked into version control
- Document major schema changes
- Run `poetry run alembic current` after pulling changes
- Never manually edit migration files after running

---

### Schema Conflicts

**Symptoms:**
- "Column already exists" errors
- "Relation does not exist" when querying tables
- Migration creates duplicate columns/tables
- ORM models don't match database schema

**Root Causes:**
- Incomplete or failed migrations
- Database state out of sync with migrations
- Multiple migration branches merged incorrectly
- Manual database edits not in migrations
- Stale Python models

**Solutions:**

1. **Verify schema matches expectations:**
```bash
# Connect to database and inspect schema
docker-compose exec db psql -U dealbrain -d dealbrain

# Inside psql:
\dt                    # List all tables
\d listings            # Describe specific table
\d+ listings           # More detailed description
SELECT * FROM information_schema.columns WHERE table_name = 'listings';
```

2. **Compare models to schema:**
```bash
# Check current revision
poetry run alembic current

# Check SQLAlchemy models
grep -r "class.*Base" /home/user/deal-brain/apps/api/dealbrain_api/models/

# Verify models match tables in alembic/versions files
```

3. **Regenerate migration from models:**
```bash
# Create autogenerated migration (compares models to db)
poetry run alembic revision --autogenerate -m "sync schema"

# Review generated migration
cat /home/user/deal-brain/apps/api/alembic/versions/<new_revision>.py

# Apply if looks correct
poetry run alembic upgrade head
```

4. **Reset schema and reimport:**
```bash
# NUCLEAR OPTION - deletes all data
docker-compose down
docker volume rm dealbrain_db_data

# Start fresh
docker-compose up -d db
sleep 10

# Run all migrations from start
poetry run alembic upgrade head

# Seed initial data
poetry run python -m dealbrain_api.seeds
```

**Prevention Tips:**

- Always generate migrations from model changes: `alembic revision --autogenerate`
- Test migrations on fresh database before committing
- Review generated migrations carefully
- Never manually edit database schema
- Keep models in sync with migrations

---

### Alembic Issues

**Symptoms:**
- "Multiple heads detected"
- "Can't locate revision" errors
- Circular dependency in revisions
- Migration files corrupt

**Root Causes:**
- Multiple migration branches merged
- Migration history corrupted
- Alembic configuration incorrect
- Missing migration files

**Solutions:**

1. **Fix multiple heads:**
```bash
# Detect multiple heads
poetry run alembic heads

# If multiple, need to merge them
# First understand the branches
poetry run alembic history

# Merge the heads
poetry run alembic merge -m "merge conflicting heads" <head1> <head2>

# This creates new migration that merges both branches
# Apply it
poetry run alembic upgrade head
```

2. **Check Alembic configuration:**
```bash
# Verify alembic.ini points to correct database
cat /home/user/deal-brain/alembic.ini | grep sqlalchemy.url

# Verify migrations directory exists
ls -la /home/user/deal-brain/apps/api/alembic/versions/

# Check env.py configuration
cat /home/user/deal-brain/apps/api/alembic/env.py | head -50
```

3. **Verify revision integrity:**
```bash
# Check for orphaned revisions
poetry run alembic history

# Should show linear chain with no gaps
# If broken, may need manual fixes

# Validate all revisions can be found
poetry run alembic current
poetry run alembic heads
```

4. **Reinitialize Alembic (last resort):**
```bash
# Backup current alembic directory
cp -r /home/user/deal-brain/apps/api/alembic /home/user/deal-brain/apps/api/alembic.backup

# Remove alembic
rm -rf /home/user/deal-brain/apps/api/alembic

# Reinitialize
cd /home/user/deal-brain/apps/api
poetry run alembic init alembic

# Copy settings from backup
# Manually fix configuration to point to models
```

**Prevention Tips:**

- Avoid merging conflicting migration branches
- Always merge/resolve head conflicts before deploying
- Test migrations in CI/CD
- Document migration best practices for team
- Keep migration history clean and linear

---

## API Connection Issues

### NEXT_PUBLIC_API_URL Configuration

**Symptoms:**
- Frontend shows "Cannot connect to API"
- Blank pages or infinite loading
- Network tab shows failed requests to wrong URL
- localhost vs IP address confusion

**Root Causes:**
- `NEXT_PUBLIC_API_URL` not set correctly
- Using localhost in Docker (wrong - should use container name or IP)
- Environment variable not loaded in build
- Docker network isolation preventing access

**Solutions:**

1. **Verify current API URL:**
```bash
# Check environment variable
echo $NEXT_PUBLIC_API_URL

# Check in Docker container
docker-compose exec web env | grep NEXT_PUBLIC_API_URL

# Check in browser console (Network tab)
# Requests should go to the URL configured
```

2. **Configure correctly for your setup:**

**Local development (not Docker):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Docker Compose (default):**
```yaml
web:
  environment:
    NEXT_PUBLIC_API_URL: http://10.42.9.11:8020
```

**Docker on Mac/Windows:**
```bash
# Mac: Use host.docker.internal
NEXT_PUBLIC_API_URL=http://host.docker.internal:8020

# Windows: Use host.docker.internal
NEXT_PUBLIC_API_URL=http://host.docker.internal:8020
```

**Docker Compose (use service name from container):**
```yaml
# This only works from within Docker network
web:
  environment:
    NEXT_PUBLIC_API_URL: http://api:8000
```

3. **Update docker-compose.yml for your network:**
```bash
# Find your Docker host IP
docker-machine ip default      # VirtualBox
ifconfig | grep "inet "        # Find your IP

# Update docker-compose.yml with correct IP
sed -i 's/10.42.9.11/<YOUR_IP>/g' /home/user/deal-brain/docker-compose.yml

# Rebuild and restart
docker-compose down
docker-compose up --build
```

4. **Verify from within container:**
```bash
# Shell into web container
docker-compose exec web /bin/sh

# Test API endpoint
curl $NEXT_PUBLIC_API_URL/api/v1/health

# Should return 200 OK with health response
```

5. **Check Next.js build includes URL:**
```bash
# Rebuild Next.js with new URL
docker-compose down web
docker-compose build --no-cache web
docker-compose up web -d

# Check logs
docker-compose logs -f web | grep "NEXT_PUBLIC_API_URL\|listening"
```

**Prevention Tips:**

- Document API URL in `.env.example`
- Use different URLs for dev/staging/production
- Add health endpoint to API for verification
- Test connectivity before reporting issue
- Add API URL to browser console on page load for debugging

---

### CORS Errors

**Symptoms:**
- Browser console: "Cross-Origin Request Blocked"
- Network tab shows request blocked by CORS policy
- Frontend gets "Access to XMLHttpRequest denied"
- Preflight OPTIONS request returns 403/405

**Root Causes:**
- API CORS configuration missing frontend origin
- API CORS not configured at all
- Wrong origin format in allowed list
- API running on different port than expected
- Middleware processing order issue

**Solutions:**

1. **Check API CORS configuration:**
```python
# In apps/api/dealbrain_api/api/routes.py or main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",    # Local dev
        "http://localhost:3020",    # Docker
        "http://10.42.9.11:3020",   # Docker IP
        "https://yourdomain.com",   # Production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

2. **Find what origin frontend is making requests from:**
```bash
# In browser console
console.log(window.location.origin)

# Should match one of allowed_origins in API
```

3. **Update allowed origins:**
```python
# For development, allow all origins
allow_origins=["*"]  # WARNING: Only for development!

# For production, be specific
allow_origins=[
    "https://yourdomain.com",
    "https://www.yourdomain.com"
]
```

4. **Verify API is returning CORS headers:**
```bash
# Make preflight request
curl -i -X OPTIONS http://localhost:8020/api/v1/listings \
  -H "Origin: http://localhost:3020" \
  -H "Access-Control-Request-Method: GET"

# Should see Access-Control-Allow-Origin header
```

5. **Check middleware order:**
```python
# CORS middleware must be first in stack
app.add_middleware(CORSMiddleware, ...)  # Must be before other middleware

# Verify order
for middleware in app.middleware:
    print(middleware)
```

**Prevention Tips:**

- Add all possible origins to CORS config
- Log CORS errors in API
- Test API endpoints with curl before blaming frontend
- Use browser DevTools Network tab to inspect headers
- Document required CORS setup in deployment docs

---

### localhost vs Docker IP Issues

**Symptoms:**
- Frontend works when accessing `localhost:3020` but not via IP
- API accessible from localhost but not from Docker container
- Services can't connect to each other
- Port numbers don't match expected (3000 vs 3020)

**Root Causes:**
- Using `localhost` inside Docker (wrong - resolve to loopback, not host)
- Using container IP from outside container
- Port mappings confused (internal vs external)
- Service names not resolving
- Different Docker network contexts

**Solutions:**

1. **Understand Docker networking:**
```
INSIDE CONTAINER:
  - localhost:8000 = loopback inside that container (usually nothing)
  - api:8000 = service name "api" on internal network
  - 172.17.0.2:8000 = container IP address

FROM HOST:
  - localhost:8000 = host port 8000 (mapped to container)
  - 10.42.9.11:8000 = Docker host IP + port
  - container-name:8000 = not available from host

FROM BROWSER ON HOST:
  - localhost:3020 = local machine
  - 10.42.9.11:3020 = Docker machine IP
  - container-name:3020 = not resolved
```

2. **Fix frontend API URL for Docker:**
```yaml
# In docker-compose.yml for web service
web:
  environment:
    # From browser: use Docker host IP
    NEXT_PUBLIC_API_URL: http://10.42.9.11:8020
```

3. **Fix internal service communication:**
```python
# Inside API container connecting to Redis
REDIS_URL: redis://redis:6379/0  # Service name, not localhost

# Inside web container connecting to API
NEXT_PUBLIC_API_URL: http://api:8000  # Service name internally
```

4. **Verify port mappings:**
```bash
# Check docker-compose.yml ports
grep -A 2 "ports:" docker-compose.yml

# Should show: "8020:8000"
# This means: external port 8020 -> internal port 8000

# So access from host: http://localhost:8020
# Access from container: http://api:8000
```

5. **Test from different contexts:**
```bash
# From host machine
curl http://localhost:8020/api/v1/health

# From web container
docker-compose exec web curl http://api:8000/api/v1/health

# From db container
docker-compose exec db nc -zv api 8000
```

**Prevention Tips:**

- Document port mappings clearly
- Use service names inside Docker, IPs from host
- Add debugging endpoint to show which origin is being used
- Test connectivity from multiple contexts before deploying
- Document network setup in README

---

### API Not Accessible from Frontend

**Symptoms:**
- Frontend shows loading indefinitely
- Network requests fail with no response
- "ERR_CONNECTION_REFUSED" in Network tab
- 404 errors on API endpoints

**Root Causes:**
- API service not running
- API port not exposed/mapped
- Wrong API URL configured
- Firewall blocking requests
- API crashed or unhealthy

**Solutions:**

1. **Verify API is running:**
```bash
# Check container status
docker-compose ps | grep api

# Check if port is listening
docker-compose exec api ss -tlnp | grep 8000

# Check API logs
docker-compose logs api | tail -50
```

2. **Test API directly:**
```bash
# From host machine
curl -v http://localhost:8020/api/v1/health

# Should return 200 with health response
# If fails, API isn't accessible

# Try from web container
docker-compose exec web curl http://api:8000/api/v1/health
```

3. **Check API startup:**
```bash
# Look for startup errors
docker-compose logs api | grep -i "error\|failed\|exception"

# Check if database is ready
docker-compose exec api psql postgresql://dealbrain:dealbrain@db:5432/dealbrain -c "SELECT 1"

# Restart API if needed
docker-compose restart api
docker-compose logs -f api
```

4. **Verify API URL in frontend:**
```bash
# Check environment variable in web
docker-compose exec web env | grep NEXT_PUBLIC_API_URL

# Check what browser is requesting (Network tab)
# Should match environment variable

# If different, rebuild web
docker-compose down web
docker-compose up --build web
```

5. **Debug from browser:**
```javascript
// In browser console
console.log('API URL:', process.env.NEXT_PUBLIC_API_URL)

// Test fetch
fetch(process.env.NEXT_PUBLIC_API_URL + '/api/v1/health')
  .then(r => r.json())
  .then(console.log)
  .catch(e => console.error('API error:', e))
```

**Prevention Tips:**

- Add health endpoint and monitor it
- Test API before starting frontend
- Log all API requests and errors
- Add retry logic in frontend for transient failures
- Document expected response times

---

## Performance Debugging

### Slow Queries

**Symptoms:**
- Listings page takes 5+ seconds to load
- Database queries timeout
- API endpoints take 10+ seconds
- Occasional timeouts on regular operations

**Root Causes:**
- Missing database indexes
- N+1 queries (fetching related data one by one)
- Large table scans without filtering
- Inefficient JOINs
- Memory pressure on database

**Solutions:**

1. **Enable query logging:**
```python
# In apps/api/dealbrain_api/settings.py or main.py
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable SQLAlchemy echo
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Logs all SQL queries
    echo_pool=True,
)
```

2. **Analyze slow queries:**
```bash
# Connect to database
docker-compose exec db psql -U dealbrain -d dealbrain

# Enable query logging
SET log_min_duration_statement = 1000;  # Log queries >1 second

# Run query and check logs
\l  # List databases
SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;
```

3. **Add missing indexes:**
```python
# In apps/api/dealbrain_api/models/core.py, add indexes
from sqlalchemy import Index

class Listing(Base):
    __tablename__ = "listings"
    id = Column(Integer, primary_key=True)
    cpu_id = Column(Integer, ForeignKey("cpu.id"), index=True)  # Index on foreign key

    __table_args__ = (
        Index('idx_listing_cpu_price', 'cpu_id', 'price'),  # Composite index
    )

# Create migration for new indexes
poetry run alembic revision --autogenerate -m "add missing indexes"
poetry run alembic upgrade head
```

4. **Fix N+1 query problem:**
```python
# Bad: N+1 queries
listings = session.query(Listing).all()
for listing in listings:
    print(listing.cpu.name)  # Separate query per listing!

# Good: Eager load related data
from sqlalchemy.orm import joinedload
listings = session.query(Listing).options(joinedload(Listing.cpu)).all()
for listing in listings:
    print(listing.cpu.name)  # No additional queries
```

5. **Optimize filtering:**
```python
# Bad: Fetch all, then filter in Python
all_listings = session.query(Listing).all()
cheap = [l for l in all_listings if l.price < 1000]

# Good: Filter at database level
cheap = session.query(Listing).filter(Listing.price < 1000).all()
```

6. **Check database connections:**
```bash
# View active connections
docker-compose exec db psql -U dealbrain -d dealbrain -c "SELECT * FROM pg_stat_activity;"

# Check connection pool exhaustion
# Look for many "idle in transaction" connections
```

**Prevention Tips:**

- Enable slow query logging in production
- Monitor query performance regularly
- Add indexes before they're needed
- Use query profiling in development
- Set reasonable query timeouts
- Test performance with realistic data volume

---

### Memory Issues

**Symptoms:**
- Docker container killed with "OOMKilled"
- Python process crashes randomly
- Node.js heap out of memory error
- System becomes unresponsive during operations

**Root Causes:**
- Processing large datasets without pagination
- Memory leaks in long-running processes
- Unbounded cache growth
- Too many connections or requests
- Insufficient Docker memory allocation

**Solutions:**

1. **Check memory usage:**
```bash
# View Docker container memory
docker stats

# For specific service
docker-compose exec api top -b -n 1 | head -20

# Check memory limits
docker inspect <container-id> | grep -i memory
```

2. **Increase Docker memory:**
```yaml
# In docker-compose.yml
services:
  api:
    mem_limit: 2g      # Limit to 2GB
    mem_reservation: 1g # Reserve minimum 1GB
```

3. **Optimize Python memory usage:**
```python
# Use generators instead of loading everything
# Bad: loads all into memory
listings = session.query(Listing).all()

# Good: streams results
listings = session.query(Listing).yield_per(100)  # Fetch 100 at a time

# Use chunked processing
from itertools import islice
batch_size = 1000
for i in range(0, total_count, batch_size):
    batch = session.query(Listing).offset(i).limit(batch_size).all()
    process(batch)
```

4. **Fix memory leaks:**
```python
# Check for circular references
import gc
gc.collect()  # Force garbage collection

# Profile memory usage
import tracemalloc
tracemalloc.start()
# ... run code ...
current, peak = tracemalloc.get_traced_memory()
print(f"Current: {current / 1024 / 1024:.2f}MB; Peak: {peak / 1024 / 1024:.2f}MB")
```

5. **Check Node.js memory:**
```bash
# View Next.js process memory
docker-compose exec web node -e "console.log(require('os').totalmem() / 1024 / 1024 / 1024 + ' GB')"

# Increase Node memory limit
NODE_OPTIONS="--max-old-space-size=2048" pnpm dev
```

6. **Monitor over time:**
```bash
# Watch memory trends
watch -n 5 'docker stats --no-stream'

# Log memory usage
docker stats --no-stream > memory.log
```

**Prevention Tips:**

- Set memory limits in docker-compose.yml
- Use pagination for large queries
- Stream/chunk large operations
- Monitor memory in staging/production
- Profile with realistic data volumes
- Clean up resources explicitly (close connections, clear caches)

---

### Build Times

**Symptoms:**
- `docker-compose up --build` takes 10+ minutes
- `pnpm install` takes 5+ minutes
- `poetry install` takes 10+ minutes
- CI/CD pipelines timeout

**Root Causes:**
- Large dependencies being downloaded
- Downloading from slow mirror
- No Docker layer caching
- Redundant installations
- Network latency

**Solutions:**

1. **Optimize Docker builds:**
```dockerfile
# Bad: rebuilds on every change
COPY . .
RUN poetry install

# Good: only rebuild if dependencies change
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root
COPY . .
RUN poetry install
```

2. **Use Docker buildkit for faster builds:**
```bash
# Enable buildkit (faster, better caching)
export DOCKER_BUILDKIT=1
docker-compose build --no-cache

# Check build cache
docker system df  # See disk usage
```

3. **Optimize dependency installation:**
```bash
# Only install required dependencies
poetry install --no-dev  # Skip dev dependencies in production

# For pnpm, use frozen lockfile
pnpm install --frozen-lockfile
```

4. **Check network speed:**
```bash
# Test registry connectivity
npm ping
poetry repo list

# Try faster mirror if available
pnpm config set registry https://registry.npmjs.org/
poetry config repositories.pypi https://mirrors.aliyun.com/pypi/simple/
```

5. **Cache Docker layers:**
```bash
# Ensure Dockerfile has proper layer caching
docker-compose build --progress=plain 2>&1 | grep -E "^.*\s(CACHED|HIT)"

# If not hitting cache, check if early layers are changing
```

6. **Parallel builds:**
```bash
# Build multiple services in parallel
docker-compose build --parallel

# Check build progress
docker-compose build --progress=plain
```

**Prevention Tips:**

- Use Docker layer caching effectively
- Pin dependency versions to avoid re-resolving
- Separate install from code copy in Dockerfile
- Monitor build times regularly
- Use pre-built base images
- Keep dependencies lean and up-to-date

---

## Common Code Mistakes

### Import Errors

**Symptoms:**
- "ModuleNotFoundError: No module named 'X'"
- "ImportError: cannot import name 'Y' from 'X'"
- Circular import errors
- Import works locally but fails in Docker

**Root Causes:**
- Installed packages not in dependencies (pyproject.toml or package.json)
- Wrong import path or module name
- Circular dependencies between modules
- Different Python path in Docker vs local

**Solutions:**

1. **Verify package is installed:**
```bash
# Python
poetry show | grep package-name

# JavaScript
pnpm list package-name
npm list package-name
```

2. **Add missing dependency:**
```bash
# Python
poetry add package-name
poetry lock
poetry install

# JavaScript
pnpm add package-name
```

3. **Check import path:**
```python
# Wrong: relative import in wrong context
from models import Listing

# Right: absolute import
from apps.api.dealbrain_api.models import Listing

# Right: relative import (in same package)
from .models import Listing
```

4. **Find circular imports:**
```python
# Check import chain
python -c "import dealbrain_api" 2>&1 | grep -i circular

# Restructure to break cycle
# Move shared code to separate module
```

5. **Test in Docker context:**
```bash
# If works locally but fails in Docker, could be path issue
docker-compose exec api python -c "from dealbrain_api.models import Listing; print(Listing)"

# If fails, add to PYTHONPATH
docker-compose run --env PYTHONPATH=/app api python -m pytest
```

**Prevention Tips:**

- Always add dependencies to pyproject.toml or package.json
- Use absolute imports consistently
- Test imports in CI/CD
- Run `poetry check` before committing
- Use linters to catch import issues

---

### Missing Dependencies

**Symptoms:**
- "ModuleNotFoundError" when running code
- Import works in one environment but not another
- CI/CD fails with missing dependency
- Code runs locally but fails in Docker

**Root Causes:**
- Dependency not added to pyproject.toml or package.json
- Transitive dependency version conflict
- Different versions in lock file vs expected
- Environment-specific dependencies not installed

**Solutions:**

1. **Check dependencies are declared:**
```bash
# Python
grep -n "package-name" /home/user/deal-brain/pyproject.toml

# JavaScript
grep "package-name" /home/user/deal-brain/package.json
grep "package-name" /home/user/deal-brain/apps/web/package.json
```

2. **Add missing dependency:**
```bash
# Python
cd /home/user/deal-brain
poetry add package-name

# JavaScript (to root or specific workspace)
pnpm add package-name
pnpm --filter web add package-name
```

3. **Regenerate lock files:**
```bash
# Python
poetry lock --no-update
poetry install

# JavaScript
rm pnpm-lock.yaml
pnpm install
```

4. **Check transitive dependencies:**
```bash
# Python: show dependency tree
poetry show --tree | grep package-name

# JavaScript
pnpm ls package-name
```

5. **Verify in Docker:**
```bash
# Test in container
docker-compose exec api pip list | grep package-name
docker-compose exec web npm list package-name

# If missing, rebuild container
docker-compose build --no-cache api
docker-compose up api
```

**Prevention Tips:**

- Always use `poetry add` or `pnpm add`, never manual edits
- Review `pyproject.toml` and `package.json` in code reviews
- Test full install from lock file regularly
- Run linters in CI/CD
- Pin major versions in dependencies

---

### Type Errors

**Symptoms:**
- "Cannot assign to type 'X' with value of type 'Y'"
- Type mismatch in function arguments
- Property doesn't exist on type
- mypy or TypeScript errors

**Root Causes:**
- Type hints missing or incorrect
- Passing wrong type to function
- Missing type annotations
- Type narrowing not handled

**Solutions:**

1. **Check type hints:**
```python
# Python with type hints
def get_listing(id: int) -> Listing:  # Specify input/output types
    return session.query(Listing).filter(Listing.id == id).first()

# TypeScript
function getListing(id: number): Listing {
    return listings.find(l => l.id === id);
}
```

2. **Run type checker:**
```bash
# Python
poetry run mypy --strict .

# TypeScript/JavaScript
pnpm lint --fix

# Check specific file
poetry run mypy apps/api/dealbrain_api/models.py
```

3. **Fix type errors:**
```python
# Wrong: type mismatch
def process(count: int):
    return count + "1"  # Error: can't add int + str

# Right: consistent types
def process(count: int):
    return count + 1
```

4. **Add missing type annotations:**
```python
# Bad: no type hints
def create_listing(data):
    return Listing(**data)

# Good: clear types
def create_listing(data: dict[str, Any]) -> Listing:
    return Listing(**data)
```

5. **Use type narrowing:**
```python
# Type guard before using
if isinstance(value, str):
    print(value.upper())  # Safe - we know it's string
```

**Prevention Tips:**

- Enable strict type checking in mypy/TypeScript
- Run type checker in pre-commit hooks
- Add type hints to function signatures
- Test type checker in CI/CD before merging

---

### Async/Await Issues

**Symptoms:**
- "RuntimeError: Event loop is closed"
- Coroutine objects not awaited
- Database locks or hangs
- Race conditions in async code

**Root Causes:**
- Missing `await` on async function
- Mixing sync and async code incorrectly
- Database session shared across async contexts
- Event loop lifecycle issues

**Solutions:**

1. **Always await async functions:**
```python
# Wrong: forgot await
result = async_function()  # Returns coroutine, not result!

# Right: use await in async context
result = await async_function()

# Or use asyncio.run() in sync context
import asyncio
result = asyncio.run(async_function())
```

2. **Verify async context:**
```python
# Wrong: async function called in sync context
def sync_function():
    result = await async_function()  # SyntaxError!

# Right: wrap with asyncio.run
def sync_function():
    result = asyncio.run(async_function())

# Or make the caller async
async def sync_function():
    result = await async_function()
```

3. **Check database session:**
```python
# Wrong: session shared across async tasks
session = SessionLocal()
async def task1(): return session.query(Listing).all()
async def task2(): return session.query(CPU).all()
await asyncio.gather(task1(), task2())  # Race condition!

# Right: use session scope
async with AsyncSession(engine) as session:
    async with session.begin():
        result = await session.execute(select(Listing))
```

4. **Fix event loop issues:**
```python
# If getting "Event loop is closed"
# Usually in tests, make sure cleanup happens properly

import pytest

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    # Client closes automatically after yield
```

5. **Debug async code:**
```python
import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)

# Enable asyncio debug mode
asyncio.run(main_func(), debug=True)

# Check for unawaited coroutines
import warnings
warnings.filterwarnings('error', category=RuntimeWarning)
```

**Prevention Tips:**

- Use linters that catch missing await
- Enable asyncio debug mode during development
- Test async code with pytest-asyncio
- Use type hints for async functions (-> Coroutine[...])
- Avoid mixing sync and async in same codebase

---

## Quick Diagnostic Commands

Use these commands to quickly diagnose issues:

```bash
# Docker Status
docker-compose ps                    # View all services
docker-compose logs api              # View API logs
docker-compose logs -f api           # Follow API logs
docker stats                         # View memory/CPU usage

# Database
docker-compose exec db psql -U dealbrain -d dealbrain -c "SELECT 1"
poetry run alembic current           # Check migration status
docker-compose exec api alembic history | head -20

# API
curl http://localhost:8020/api/v1/health
curl -v http://localhost:8020/api/v1/listings | head -20

# Frontend
curl http://localhost:3020           # Should return HTML
docker-compose logs web | tail -50

# Network
docker network ls                    # List Docker networks
docker exec <container> nc -zv api 8000  # Test container connectivity

# Dependencies
poetry show --outdated               # Outdated Python packages
pnpm outdated                        # Outdated JavaScript packages
poetry lock --no-update              # Regenerate lock file
pnpm install                         # Reinstall everything

# Code Quality
poetry run ruff check .              # Lint Python
poetry run black --check .           # Check Python formatting
pnpm lint                            # Lint JavaScript
poetry run mypy .                    # Type check Python

# Testing
poetry run pytest -v                 # Run all tests
poetry run pytest tests/test_listings.py -v
pnpm --filter web test               # Run JavaScript tests
```

---

## Getting More Help

If these solutions don't resolve your issue:

1. **Check the documentation:**
   - [Setup Guide](technical/setup.md)
   - [Architecture Overview](architecture/architecture.md)
   - [CLAUDE.md](../CLAUDE.md)

2. **Review relevant code:**
   - Check `docker-compose.yml` for service configuration
   - Review `.env.example` for environment variables
   - Check `pyproject.toml` for Python dependencies
   - Check `package.json` for JavaScript dependencies

3. **Enable debug logging:**
   ```bash
   # Verbose Docker output
   docker-compose up --build 2>&1 | tee docker.log

   # Verbose Poetry
   poetry install -vv 2>&1 | tee poetry.log

   # Verbose pnpm
   pnpm install --verbose 2>&1 | tee pnpm.log
   ```

4. **Check system resources:**
   ```bash
   docker system df        # Docker disk usage
   docker stats            # Container memory/CPU
   df -h /                 # Host disk space
   free -h                 # Host memory
   ```

5. **Review recent changes:**
   ```bash
   git log --oneline -20   # Recent commits
   git diff HEAD~5         # Changes in last 5 commits
   docker-compose logs | grep -i error  # Error patterns
   ```

---

**Last Updated:** November 5, 2025

**Related Documentation:**
- [Installation & Setup](technical/setup.md)
- [Architecture Overview](architecture/architecture.md)
- [Development Guidelines](../CLAUDE.md)
- [Docker Compose Configuration](../docker-compose.yml)
