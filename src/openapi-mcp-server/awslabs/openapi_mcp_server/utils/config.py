"""Configuration utilities for the OpenAPI MCP Server.

This module centralizes configuration settings from environment variables
to ensure consistent behavior across the application.
"""

import os
from typing import Any, Dict


# HTTP client configuration
USE_TENACITY = os.environ.get('MCP_USE_TENACITY', 'true').lower() in ('true', '1', 'yes')
HTTP_MAX_CONNECTIONS = int(os.environ.get('MCP_HTTP_MAX_CONNECTIONS', '20'))
HTTP_MAX_KEEPALIVE = int(os.environ.get('MCP_HTTP_MAX_KEEPALIVE', '10'))
HTTP_TIMEOUT = float(os.environ.get('MCP_HTTP_TIMEOUT', '30.0'))

# Metrics configuration
USE_PROMETHEUS = os.environ.get('MCP_USE_PROMETHEUS', 'true').lower() in ('true', '1', 'yes')
PROMETHEUS_PORT = int(os.environ.get('MCP_PROMETHEUS_PORT', '0'))
METRICS_MAX_HISTORY = int(os.environ.get('MCP_METRICS_MAX_HISTORY', '100'))

# Cache configuration
USE_CACHETOOLS = os.environ.get('MCP_USE_CACHETOOLS', 'true').lower() in ('true', '1', 'yes')
CACHE_MAXSIZE = int(os.environ.get('MCP_CACHE_MAXSIZE', '128'))
CACHE_TTL = int(os.environ.get('MCP_CACHE_TTL', '3600'))  # Default: 1 hour


def get_config() -> Dict[str, Any]:
    """Get all configuration settings as a dictionary.

    Returns:
        Dict[str, Any]: All configuration settings
    """
    return {
        'http': {
            'use_tenacity': USE_TENACITY,
            'max_connections': HTTP_MAX_CONNECTIONS,
            'max_keepalive': HTTP_MAX_KEEPALIVE,
            'timeout': HTTP_TIMEOUT,
        },
        'metrics': {
            'use_prometheus': USE_PROMETHEUS,
            'prometheus_port': PROMETHEUS_PORT,
            'max_history': METRICS_MAX_HISTORY,
        },
        'cache': {
            'use_cachetools': USE_CACHETOOLS,
            'maxsize': CACHE_MAXSIZE,
            'ttl': CACHE_TTL,
        },
    }
