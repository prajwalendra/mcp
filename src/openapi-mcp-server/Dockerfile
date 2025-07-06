# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Stage 1: Build dependencies using Python 3.13.5-alpine3.21
FROM public.ecr.aws/docker/library/python:3.13.5-alpine3.21 AS builder

# Set environment variables for better Python behavior
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies in a single layer with virtual package for easy cleanup
RUN apk add --no-cache --virtual .build-deps \
    build-base \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    && pip install --no-cache-dir --upgrade pip setuptools>=78.1.1 wheel

# Create app directory
WORKDIR /app

# Copy files needed for package metadata and installation
COPY pyproject.toml README.md LICENSE NOTICE ./
COPY awslabs ./awslabs

# Install dependencies to a specific target directory for cleaner copying
RUN pip install --no-cache-dir --target /opt/venv .

# Stage 2: Create minimal runtime image
FROM public.ecr.aws/docker/library/python:3.13.5-alpine3.21

# Set environment variables for better Python and logging behavior
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    # Suppress Python warnings
    PYTHONWARNINGS="ignore"

# Install only essential runtime dependencies
RUN apk add --no-cache \
    ca-certificates \
    && update-ca-certificates

# Create non-root user for security
RUN addgroup -S app && \
    adduser -S app -G app -h /app

# Copy only what's needed from the builder stage
COPY --from=builder --chown=app:app /opt/venv /opt/venv
COPY --from=builder --chown=app:app /app/awslabs /app/awslabs

# Get healthcheck script and entrypoint script
COPY --chown=app:app ./docker-healthcheck.sh /usr/local/bin/docker-healthcheck.sh
RUN chmod +x /usr/local/bin/docker-healthcheck.sh

# Run as non-root
USER app
WORKDIR /app

# Optimize healthcheck intervals for better performance
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 \
    CMD ["docker-healthcheck.sh"]

# Use exec form for better signal handling
ENTRYPOINT ["python", "-m", "awslabs.openapi_mcp_server.server"]
