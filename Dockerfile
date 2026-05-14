FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for Playwright (Chromium) and general tools
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

# Install Playwright and Chromium
RUN pip install --no-cache-dir playwright && \
    playwright install chromium

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p static/media static/landing_pages logs

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

# Default port
EXPOSE 5000
EXPOSE 5001

# Health check (default for main app)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:5000/ || exit 1

# Default command (can be overridden in docker-compose)
CMD ["python", "app.py"]