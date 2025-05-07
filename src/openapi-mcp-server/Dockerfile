FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only the files needed to install dependencies first
COPY pyproject.toml README.md /app/

# Copy project files
COPY awslabs/ /app/awslabs/
COPY docker-healthcheck.sh /usr/local/bin/docker-healthcheck.sh

# Make health check script executable
RUN chmod +x /usr/local/bin/docker-healthcheck.sh

# Install the package
RUN pip install --no-cache-dir -e .

# Set default environment variables
ENV SERVER_PORT=8888 \
    SERVER_HOST=0.0.0.0

# Expose the default port
EXPOSE 8888

# Configure health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 CMD ["docker-healthcheck.sh"]

# Run the server
CMD ["python", "-m", "awslabs.openapi_mcp_server.server"]
