# SarvaSahay Platform Dockerfile
# Multi-stage build for production optimization

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    tesseract-ocr \
    tesseract-ocr-hin \
    tesseract-ocr-mar \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN groupadd -r sarvasahay && useradd -r -g sarvasahay sarvasahay

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements-dev.txt .
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-dev.txt

# Development stage
FROM base as development

# Copy application code
COPY . .

# Change ownership to application user
RUN chown -R sarvasahay:sarvasahay /app

# Switch to application user
USER sarvasahay

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run development server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production

# Install only production dependencies
RUN pip install --no-cache-dir -e ".[production]"

# Copy application code
COPY . .

# Remove development files
RUN rm -rf tests/ docs/ *.md requirements-dev.txt

# Change ownership to application user
RUN chown -R sarvasahay:sarvasahay /app

# Switch to application user
USER sarvasahay

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run production server
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]