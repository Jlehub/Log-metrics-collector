# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set metadata labels
LABEL maintainer="elloh347@gmail.com"
LABEL github="github.com/Jlehub"
LABEL version="1.0.0"
LABEL description="Log & Metrics Collector - System Monitoring Tool"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_APP=main.py
ENV FLASK_ENV=production

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

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