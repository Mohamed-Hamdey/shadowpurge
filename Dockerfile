# ShadowPurge Dockerfile
# Multi-stage build for smaller production image

# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml README.md ./
COPY shadowpurge/ ./shadowpurge/
COPY data/ ./data/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .[search]

# Install Playwright browsers
RUN playwright install chromium && \
    playwright install-deps chromium

# Production stage
FROM python:3.11-slim as runtime

WORKDIR /app

# Create non-root user
RUN groupadd -r shadowpurge && useradd -r -g shadowpurge shadowpurge

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-6 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    && rm -rf /var/lib/apt/lists/*

# Copy from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app
COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright

# Create directories
RUN mkdir -p /app/data /app/exports /app/cache /app/logs && \
    chown -R shadowpurge:shadowpurge /app

# Switch to non-root user
USER shadowpurge

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright \
    SHADOWPURGE_DATA_DIR=/app/data \
    SHADOWPURGE_OUTPUT_EXPORT_DIR=/app/exports \
    SHADOWPURGE_CACHE_DIR=/app/cache \
    SHADOWPURGE_LOG_FILE=/app/logs/shadowpurge.log

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import shadowpurge; print('OK')" || exit 1

# Entry point
ENTRYPOINT ["python", "-m", "shadowpurge"]
CMD ["--help"]