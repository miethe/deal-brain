# Dedicated card generation service Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Playwright system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        # Required for Chromium
        libnss3 \
        libxss1 \
        libasound2 \
        libatk-bridge2.0-0 \
        libgtk-3-0 \
        libdrm2 \
        libgbm1 \
        libxkbcommon0 \
        libatspi2.0-0 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxrandr2 \
        libpango-1.0-0 \
        libcairo2 \
        libcups2 \
        libdbus-1-3 \
        libexpat1 \
        libfontconfig1 \
        libgcc1 \
        libglib2.0-0 \
        libnspr4 \
        libuuid1 \
        libx11-6 \
        libx11-xcb1 \
        libxcb1 \
        libxext6 \
        libxrender1 \
        ca-certificates \
        fonts-liberation \
        wget \
    && rm -rf /var/lib/apt/lists/*

# Install minimal dependencies for card generation service
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn==0.24.0.post1 \
    playwright==1.41.2 \
    jinja2==3.1.3 \
    boto3==1.34.0 \
    pillow==10.2.0 \
    httpx==0.25.2

# Install Chromium browser
RUN playwright install chromium

# Copy only necessary files for card generation
COPY apps/api/dealbrain_api/templates /app/templates
COPY apps/api/dealbrain_api/services/image_generation.py /app/services/image_generation.py

# Simple FastAPI app for card generation
RUN cat > /app/main.py << 'EOF'
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
from services.image_generation import ImageGenerationService

app = FastAPI(title="Card Generator Service")

class CardRequest(BaseModel):
    listing_id: int
    title: str
    price: float
    adjusted_price: float | None
    cpu: str | None
    ram: int | None
    storage: int | None
    manufacturer: str | None
    series: str | None
    style: str = "light"
    format: str = "png"
    size: str = "social"

@app.post("/generate")
async def generate_card(request: CardRequest):
    """Generate card image from listing data."""
    try:
        # Service would generate the card
        # This is a simplified example
        return {"status": "success", "url": f"/cards/{request.listing_id}.{request.format}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy"}
EOF

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]