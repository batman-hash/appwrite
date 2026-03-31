# CyberGhost Web App - Docker Configuration
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    iproute2 \
    net-tools \
    iputils-ping \
    dnsutils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs

# Make scripts executable
RUN chmod +x /app/mac_rotation.py
RUN chmod +x /app/docker/entrypoint.sh

# Expose port
EXPOSE 8011

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8011
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8011/api/health || exit 1

# Run with a small entrypoint that enables HTTPS when certs are present
CMD ["/app/docker/entrypoint.sh"]
