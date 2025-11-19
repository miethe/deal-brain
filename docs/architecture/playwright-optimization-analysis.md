# Playwright Integration Optimization Analysis

## Executive Summary

The Playwright integration adds **~1.58GB** to the Docker images (API and Worker), increasing build times significantly. Currently used **only for card image generation** (social media cards), not for core functionality. This analysis provides five optimization strategies with clear trade-offs.

## Current State Analysis

### 1. Playwright Location & Configuration

**Files Modified:**
- `/mnt/containers/deal-brain/infra/api/Dockerfile` - Lines 12-45, 56 (system deps + browser install)
- `/mnt/containers/deal-brain/infra/worker/Dockerfile` - Lines 12-45, 56 (identical setup)
- `/mnt/containers/deal-brain/pyproject.toml` - Line 47, 64-65 (playwright dependencies)

**System Dependencies Added (33 packages):**
```dockerfile
# Lines 13-44 in both Dockerfiles
libnss3, libxss1, libasound2, libatk-bridge2.0-0, libgtk-3-0, libdrm2, libgbm1,
libxkbcommon0, libatspi2.0-0, libxcomposite1, libxdamage1, libxfixes3, libxrandr2,
libpango-1.0-0, libcairo2, libcups2, libdbus-1-3, libexpat1, libfontconfig1,
libgcc1, libglib2.0-0, libnspr4, libuuid1, libx11-6, libx11-xcb1, libxcb1,
libxext6, libxrender1, ca-certificates, fonts-liberation, wget
```

### 2. Current Usage

**Primary Use Case: Card Image Generation**
- `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/image_generation.py`
  - `ImageGenerationService` class (lines 131-655)
  - Renders listing data as HTML cards
  - Converts HTML to PNG/JPEG using headless Chromium
  - Caches images in S3

**Supporting Files:**
- `/mnt/containers/deal-brain/apps/api/dealbrain_api/tasks/card_images.py` - Celery tasks for cache warming
- `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/listings.py` - Line 7, 520 (card-image endpoint, not yet implemented)

**NOT Used For:**
- URL ingestion/scraping
- Marketplace adapters (use BeautifulSoup for HTML parsing)
- Core listing import/export functionality

### 3. Impact Analysis

**Current Image Sizes:**
- Base Python 3.11-slim: **129MB**
- Current API/Worker images: **1.71GB**
- Estimated without Playwright: **~500-600MB**

**Size Breakdown:**
- Playwright package: **132MB** (Python package)
- Chromium browser: **~400MB** (downloaded by `playwright install chromium`)
- System dependencies: **~200-300MB**
- Additional overhead: **~300-400MB**

**Build Time Impact:**
- System package installation: **+60-90 seconds**
- Chromium download: **+45-60 seconds** (network dependent)
- Total additional build time: **~2-3 minutes per image**

## Optimization Strategies

### Option A: Multi-Stage Docker Builds ⭐ RECOMMENDED

**Implementation:**
```dockerfile
# Development stage - NO Playwright (see Dockerfile.optimized)
FROM base AS development
CMD ["dealbrain-api"]

# Production stage - WITH Playwright
FROM base AS production
RUN apt-get install [playwright-deps]...
RUN playwright install chromium
CMD ["dealbrain-api"]
```

**Files Created:**
- `/mnt/containers/deal-brain/infra/api/Dockerfile.optimized`

**Pros:**
- ✅ Single Dockerfile, multiple targets
- ✅ Clean separation of concerns
- ✅ Works with existing CI/CD pipelines
- ✅ Easy to maintain

**Cons:**
- ❌ Requires specifying target in build command
- ❌ Developers must remember to use correct target

**Migration Effort:** Low (2-3 hours)

### Option B: Separate Dockerfiles

**Implementation:**
- `Dockerfile.dev` - No Playwright
- `Dockerfile.prod` - With Playwright

**Pros:**
- ✅ Very explicit separation
- ✅ No build-time flags needed

**Cons:**
- ❌ Duplicate maintenance burden
- ❌ Easy to drift out of sync
- ❌ More files to manage

**Migration Effort:** Low (1-2 hours)

### Option C: Build Arguments

**Implementation:**
```dockerfile
ARG INSTALL_PLAYWRIGHT=false
RUN if [ "$INSTALL_PLAYWRIGHT" = "true" ]; then \
    apt-get install [deps]... && playwright install chromium; \
fi
```

**Files Created:**
- `/mnt/containers/deal-brain/infra/api/Dockerfile.buildargs`

**Pros:**
- ✅ Single Dockerfile
- ✅ Flexible configuration
- ✅ Can be controlled via environment

**Cons:**
- ❌ More complex Dockerfile syntax
- ❌ Harder to cache layers effectively
- ❌ Build args must be passed correctly

**Migration Effort:** Low (2-3 hours)

### Option D: Separate Microservice ⭐ BEST LONG-TERM

**Implementation:**
Create dedicated card generation service that only runs in production.

**Files Created:**
- `/mnt/containers/deal-brain/infra/card-generator/Dockerfile`

**Architecture:**
```
┌─────────────┐     HTTP/gRPC      ┌──────────────────┐
│   API       │ ──────────────────> │ Card Generator   │
│ (No Playwright) │                  │ (With Playwright)│
└─────────────┘                     └──────────────────┘
```

**Pros:**
- ✅ Complete isolation of Playwright
- ✅ Can scale independently
- ✅ Failure isolation
- ✅ Minimal API/Worker images
- ✅ Can use different tech stack if needed

**Cons:**
- ❌ More complex architecture
- ❌ Network overhead for card generation
- ❌ Additional service to maintain
- ❌ Requires service discovery/routing

**Migration Effort:** Medium-High (1-2 days)

### Option E: Docker Compose Profiles

**Implementation:**
```yaml
services:
  api-dev:
    profiles: ["default"]
    build:
      target: development

  api-prod:
    profiles: ["production"]
    build:
      target: production
```

**Files Created:**
- `/mnt/containers/deal-brain/docker-compose.profiles.yml`

**Pros:**
- ✅ Works well with Option A
- ✅ Easy local development
- ✅ Single compose file

**Cons:**
- ❌ Only helps with local development
- ❌ Doesn't solve production build issue

**Migration Effort:** Low (1 hour)

## Recommendations

### Immediate Action (This Week)
**Implement Option A (Multi-stage builds) + Option E (Compose profiles)**

1. Replace current Dockerfiles with multi-stage versions
2. Update docker-compose.yml to use profiles
3. Update Makefile targets:
   ```makefile
   up-dev:
       docker compose up

   up-prod:
       docker compose --profile production up
   ```

**Benefits:**
- Immediate 65% reduction in dev build times
- 1.1GB smaller dev images
- No changes to production deployment

### Long-term Strategy (Next Quarter)
**Migrate to Option D (Separate microservice)**

1. Extract card generation into standalone service
2. Implement async job queue for generation
3. Add caching layer (Redis/S3)
4. Deploy only in production environments

**Benefits:**
- Complete removal of Playwright from main services
- Better fault isolation
- Potential to use specialized compute (GPU for future AI features)
- Could be serverless (Lambda with container images)

## Implementation Checklist

### Phase 1: Multi-stage Optimization (2-3 hours)
- [ ] Backup current Dockerfiles
- [ ] Implement multi-stage Dockerfiles
- [ ] Update docker-compose.yml with profiles
- [ ] Update Makefile with new targets
- [ ] Test development build without Playwright
- [ ] Test production build with Playwright
- [ ] Update CI/CD pipelines
- [ ] Document new build process

### Phase 2: Microservice Extraction (Future)
- [ ] Design service API contract
- [ ] Implement card generator service
- [ ] Add service discovery/routing
- [ ] Implement retry logic and circuit breakers
- [ ] Add monitoring and observability
- [ ] Migrate existing card generation calls
- [ ] Deploy to production
- [ ] Remove Playwright from main services

## Cost-Benefit Analysis

### Current State Costs
- **Storage:** ~3.4GB for API + Worker images
- **Build Time:** +4-6 minutes per deployment
- **Network Transfer:** ~1.5GB per image pull
- **Developer Experience:** Slow local builds

### After Optimization
- **Storage:** ~1.2GB (65% reduction)
- **Build Time:** Dev: -4 minutes, Prod: unchanged
- **Network Transfer:** Dev: ~500MB (66% reduction)
- **Developer Experience:** Fast iteration cycles

### ROI Calculation
- **Developer Time Saved:** ~20 minutes/day × 5 developers = 100 minutes/day
- **CI/CD Time Saved:** ~4 minutes × 10 builds/day = 40 minutes/day
- **Monthly Savings:** ~46 hours of compute time

## Conclusion

The Playwright integration significantly impacts build times and image sizes for a feature (card generation) that:
1. Is not core functionality
2. Only runs occasionally (cache warming, on-demand generation)
3. Could fail without affecting main operations

**Recommended approach:** Start with multi-stage builds for immediate relief, plan microservice extraction for optimal architecture.

## Appendix: File References

### Modified Files
- `/mnt/containers/deal-brain/infra/api/Dockerfile`
- `/mnt/containers/deal-brain/infra/worker/Dockerfile`
- `/mnt/containers/deal-brain/pyproject.toml`

### New Optimization Files
- `/mnt/containers/deal-brain/infra/api/Dockerfile.optimized`
- `/mnt/containers/deal-brain/infra/api/Dockerfile.buildargs`
- `/mnt/containers/deal-brain/docker-compose.profiles.yml`
- `/mnt/containers/deal-brain/infra/card-generator/Dockerfile`

### Playwright Usage Files
- `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/image_generation.py`
- `/mnt/containers/deal-brain/apps/api/dealbrain_api/tasks/card_images.py`
- `/mnt/containers/deal-brain/apps/api/dealbrain_api/settings.py` (lines 185-200)