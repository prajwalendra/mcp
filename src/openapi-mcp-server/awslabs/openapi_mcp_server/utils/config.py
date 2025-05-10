"""Configuration utilities for the OpenAPI MCP Server."""

import os

# Metrics configuration
METRICS_MAX_HISTORY = int(os.environ.get('METRICS_MAX_HISTORY', '100'))
USE_PROMETHEUS = os.environ.get('ENABLE_PROMETHEUS', 'false').lower() == 'true'
PROMETHEUS_PORT = int(os.environ.get('PROMETHEUS_PORT', '9090'))

# Operation prompts configuration
ENABLE_OPERATION_PROMPTS = os.environ.get('ENABLE_OPERATION_PROMPTS', 'true').lower() == 'true'
