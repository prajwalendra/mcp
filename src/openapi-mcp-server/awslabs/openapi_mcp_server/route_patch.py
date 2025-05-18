"""Patch for FastMCP OpenAPI route mapping.

This module patches the _determine_route_type function in the FastMCP OpenAPI module
to handle query parameters correctly. It maps GET operations with query parameters
to TOOLS instead of RESOURCES, making them easier to use by LLMs.

Usage:
    import fastmcp.server.openapi
    from awslabs.openapi_mcp_server.route_patch import apply_route_patch

    # Apply the patch
    apply_route_patch(fastmcp.server.openapi)
"""

from awslabs.openapi_mcp_server import logger
from fastmcp.server.openapi import RouteType, _determine_route_type
from typing import Any, List


# Configuration
ENABLE_ROUTE_PATCH = True
DEBUG_LOGGING = True

# Store the original function
original_determine_route_type = _determine_route_type


def patched_determine_route_type(route: Any, mappings: List[Any]) -> RouteType:
    """Patched version of _determine_route_type that handles query parameters.

    This function checks if the route is a GET operation with query parameters.
    If it is, it maps it to a TOOL instead of a RESOURCE, making it easier for
    LLMs to use operations with query parameters.

    Args:
        route: An HTTPRoute object from the OpenAPI specification
        mappings: A list of RouteMap objects

    Returns:
        RouteType: The component type to use for this route

    """
    # Check if the patch is enabled
    global ENABLE_ROUTE_PATCH
    if not ENABLE_ROUTE_PATCH:
        return original_determine_route_type(route, mappings)

    # Log the route being processed if debug logging is enabled
    global DEBUG_LOGGING
    if DEBUG_LOGGING:
        logger.debug(f'Processing route: {route.method} {route.path}')

    try:
        # Check if this is a GET operation with query parameters
        has_query_params = any(p.location == 'query' for p in route.parameters)
        if route.method == 'GET' and has_query_params:
            query_param_names = [p.name for p in route.parameters if p.location == 'query']

            if DEBUG_LOGGING:
                logger.debug(f'Found GET operation with query parameters: {query_param_names}')
                logger.debug(f'Mapping {route.method} {route.path} to TOOL instead of RESOURCE')

            return RouteType.TOOL
    except Exception as e:
        # Log the error and fall back to the original function
        logger.warning(f'Error in patched_determine_route_type: {e}')

    # Fall back to the original function for other cases
    original_result = original_determine_route_type(route, mappings)

    if DEBUG_LOGGING:
        logger.debug(f'Original mapping for {route.method} {route.path}: {original_result.name}')

    return original_result


def apply_route_patch(module: Any, enable: bool = True, debug: bool = True) -> None:
    """Apply the route patch to the specified module.

    This function applies the route patch to the specified module, replacing
    the _determine_route_type function with our patched version.

    Args:
        module: The module to patch (usually fastmcp.server.openapi)
        enable: Whether to enable the route patch
        debug: Whether to enable debug logging

    """
    global ENABLE_ROUTE_PATCH, DEBUG_LOGGING

    # Update configuration
    ENABLE_ROUTE_PATCH = enable
    DEBUG_LOGGING = debug

    # Apply the patch
    module._determine_route_type = patched_determine_route_type

    if DEBUG_LOGGING:
        # Get function names safely
        original_name = getattr(original_determine_route_type, '__name__', 'unknown')
        patched_name = getattr(patched_determine_route_type, '__name__', 'unknown')

        logger.info(f'Route mapping patch applied: {original_name} -> {patched_name}')
        logger.info(f'Route patch enabled: {ENABLE_ROUTE_PATCH}')
