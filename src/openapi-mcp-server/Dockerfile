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

# Stage 1: Build dependencies using Python 3.10
FROM public.ecr.aws/sam/build-python3.10@sha256:84738adb2767299571443d742c006d2f153c809c7181b099468583ac97be2dda AS builder

# Update system packages to latest versions for security
RUN yum update -y && yum clean all -y && rm -rf /var/cache/yum

# Install the project into `/app`
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Prefer the system python
ENV UV_PYTHON_PREFERENCE=only-system

# Run without updating the uv.lock file like running with `--frozen`
ENV UV_FROZEN=true

# Upgrade system pip and install uv for better dependency management
RUN python -m pip install --upgrade pip setuptools>=78.1.1 wheel && \
    pip install --no-cache-dir uv

# Copy the required files first
COPY pyproject.toml uv.lock ./

# Install the project's dependencies using uv (more secure than pip with hashes)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev --no-editable

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

# Stage 2: Create minimal runtime image
FROM public.ecr.aws/sam/build-python3.10@sha256:84738adb2767299571443d742c006d2f153c809c7181b099468583ac97be2dda

# Update system packages for security and remove unnecessary packages
RUN yum update -y && \
    yum install -y lsof && \
    # Remove unnecessary packages that might have vulnerabilities
    yum remove -y perl* && \
    yum clean all -y && \
    rm -rf /var/cache/yum

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH:/usr/sbin"

# Set security-related environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Create non-root user for security
RUN groupadd --force --system app && \
    useradd app -g app -d /app && \
    mkdir -p /app

# Copy only what's needed from the builder stage
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app/awslabs /app/awslabs

# Get healthcheck script
COPY ./docker-healthcheck.sh /usr/local/bin/docker-healthcheck.sh
RUN chmod +x /usr/local/bin/docker-healthcheck.sh

# Upgrade system Python packages that might have CVEs
# This upgrades the system Python 3.10 setuptools from 65.5.1 to ≥78.1.1
RUN /var/lang/bin/python3 -m pip install --upgrade pip setuptools>=78.1.1 wheel || true

# SECURITY: Remove old Python 3.7 packages with known CVEs
# Application uses Python 3.10 in the virtual environment
RUN rm -rf /usr/lib/python3.7 && \
    rm -rf /usr/lib64/python3.7 && \
    rm -rf /usr/include/python3.7* && \
    rm -rf /usr/share/licenses/python3-setuptools-49* && \
    rm -rf /usr/share/doc/python3-setuptools-49* && \
    rm -f /usr/bin/python3.7* && \
    rm -f /usr/lib64/libpython3.7* && \
    rm -f /usr/share/man/man1/python3.7* && \
    echo "Completely removed Python 3.7 and setuptools-49.1.3 with CVEs"

# SECURITY: Remove vulnerable urllib3 1.26.19 from system runtime (CVE fix)
# ApplicationI uses urllib3 2.5.0 in the virtual environment, so this is safe
RUN rm -rf /var/runtime/urllib3* && \
    rm -rf /var/runtime/botocore/vendored/requests/packages/urllib3 && \
    echo "Removed vulnerable urllib3 1.26.19 from system runtime"

# Run as non-root
USER app
WORKDIR /app

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD [ "docker-healthcheck.sh" ]
ENTRYPOINT ["python", "-m", "awslabs.openapi_mcp_server.server"]
