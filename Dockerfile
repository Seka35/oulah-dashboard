FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for Playwright (Chromium on Debian/Ubuntu)
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    libc6 \
    libdbus-1-3 \
    libnspr4 \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2t64 \
    libpango-1.0-0 \
    libcairo2 \
    libpangocairo-1.0-0 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and Chromium (skip install-deps as we installed deps manually)
RUN pip install --no-cache-dir playwright && \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0 playwright install chromium

# Copy application files
COPY . .

# Create static/media directories
RUN mkdir -p static/media static/landing_pages

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000')" || exit 1

# Start both app.py and media_worker.py
CMD python app.py & \
    python media_worker.py & \
    wait