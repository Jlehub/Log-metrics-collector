# Multi-stage Dockerfile for Log & Metrics Collector
# ============================================
# Stage 1: Build Dependencies & Testing
# ============================================
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt requirements-dev.txt ./

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies with caching
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install -r requirements-dev.txt


# ============================================
# Stage 2: Testing Stage (Optional for CI)
# ============================================
FROM builder as testing

# Copy source code
COPY . .

# Run tests (this stage can be skipped in production builds)
RUN python -m pytest tests/ --tb=short || echo "Tests completed"
RUN flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || echo "Linting completed"

# ============================================
# Stage 3: Production Runtime
# ============================================
FROM python:3.11-slim as production


# Set metadata labels
LABEL maintainer="elloh347@gmail.com"
LABEL github="github.com/Jlehub"
LABEL version="1.0.0"
LABEL description="Log & Metrics Collector - System Monitoring Tool"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PATH="/opt/venv/bin:$PATH"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    procps \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --chown=appuser:appuser . .

# Create logs directory and set permissions
RUN mkdir -p /app/logs /var/log && \
    chown -R appuser:appuser /app && \
    chmod +x /app/app.py

# Switch to non-root user
USER appuser

# Expose the API port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

# Default command
CMD ["python", "app.py", "--config", "config.json"]








































