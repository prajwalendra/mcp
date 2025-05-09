"""API discovery and introspection utilities."""

from awslabs.openapi_mcp_server import logger, register_custom_tool
from awslabs.openapi_mcp_server.utils.metrics_provider import metrics
from awslabs.openapi_mcp_server.utils.openapi_validator import extract_api_structure
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Any, Dict, List


class ApiInfo(BaseModel):
    """Information about an API."""

    name: str = Field(..., description='Name of the API')
    title: str = Field(..., description='Title of the API')
    version: str = Field(..., description='Version of the API')
    description: str = Field('', description='Description of the API')
    base_url: str = Field(..., description='Base URL of the API')
    paths: int = Field(..., description='Number of paths in the API')
    operations: int = Field(..., description='Number of operations in the API')
    schemas: int = Field(..., description='Number of schemas in the API')


class ToolInfo(BaseModel):
    """Information about a tool."""

    name: str = Field(..., description='Name of the tool')
    description: str = Field('', description='Description of the tool')
    method: str = Field(..., description='HTTP method of the tool')
    path: str = Field(..., description='Path of the tool')
    parameters: List[Dict[str, Any]] = Field([], description='Parameters of the tool')
    usage_count: int = Field(0, description='Number of times the tool has been used')
    error_rate: float = Field(0.0, description='Error rate of the tool')
    avg_duration_ms: float = Field(0.0, description='Average duration of the tool in milliseconds')


class ApiStats(BaseModel):
    """Statistics about API usage."""

    total_calls: int = Field(..., description='Total number of API calls')
    error_count: int = Field(..., description='Number of API call errors')
    error_rate: float = Field(..., description='Error rate of API calls')
    unique_paths: int = Field(..., description='Number of unique API paths called')
    recent_errors: List[Dict[str, Any]] = Field([], description='Recent API call errors')


async def get_api_info(
    server: FastMCP, api_name: str, openapi_spec: Dict[str, Any], base_url: str
) -> ApiInfo:
    """Get information about an API.

    Args:
        server: The MCP server
        api_name: Name of the API
        openapi_spec: The OpenAPI specification
        base_url: Base URL of the API

    Returns:
        ApiInfo: Information about the API
    """
    # Extract API structure
    structure = extract_api_structure(openapi_spec)

    return ApiInfo(
        name=api_name,
        title=structure['info']['title'],
        version=structure['info']['version'],
        description=structure['info']['description'],
        base_url=base_url,
        paths=len(structure['paths']),
        operations=len(structure['operations']),
        schemas=len(structure['schemas']),
    )


async def get_api_tools(server: FastMCP, api_name: str) -> List[ToolInfo]:
    """Get information about tools for an API.

    Args:
        server: The MCP server
        api_name: Name of the API

    Returns:
        List[ToolInfo]: Information about tools for the API
    """
    tools = []

    # Get all tools for this API
    try:
        all_tools = await server.get_tools()
        api_tools = [tool for tool in all_tools.values() if isinstance(tool.name, str) and tool.name.startswith(f'{api_name}_')]

        # Get tool stats
        tool_stats = metrics.get_tool_stats()

        for tool in api_tools:
            # Extract method and path from description
            method = 'GET'  # Default
            path = ''
            if isinstance(tool.description, str):
                description_lines = tool.description.split('\n')
                for line in description_lines:
                    if line.startswith('HTTP'):
                        parts = line.split(' ', 2)
                        if len(parts) >= 2:
                            method = parts[1]
                        if len(parts) >= 3:
                            path = parts[2]
                        break

            # Get parameters
            parameters = []
            if hasattr(tool, 'parameters') and tool.parameters:
                for param in tool.parameters:
                    if hasattr(param, 'name'):
                        param_info = {
                            'name': param.name,
                            'type': str(getattr(param, 'type', 'unknown')),
                            'required': getattr(param, 'required', False),
                            'description': getattr(param, 'description', ''),
                        }
                        parameters.append(param_info)

            # Get usage stats
            stats = tool_stats.get(tool.name, {}) if isinstance(tool.name, str) else {}
            usage_count = stats.get('count', 0)
            error_rate = stats.get('error_rate', 0.0)
            avg_duration_ms = stats.get('avg_duration_ms', 0.0)

            # Get first line of description or use empty string if description is not a string
            first_line = ''
            if isinstance(tool.description, str):
                description_parts = tool.description.split('\n')
                if description_parts:
                    first_line = description_parts[0]

            tools.append(
                ToolInfo(
                    name=tool.name,
                    description=first_line,
                    method=method,
                    path=path,
                    parameters=parameters,
                    usage_count=usage_count,
                    error_rate=error_rate,
                    avg_duration_ms=avg_duration_ms,
                )
            )

    except Exception as e:
        logger.warning(f'Error getting tools: {e}')

    return tools


async def get_api_stats() -> ApiStats:
    """Get statistics about API usage.

    Returns:
        ApiStats: Statistics about API usage
    """
    summary = metrics.get_summary()
    api_calls = summary['api_calls']

    return ApiStats(
        total_calls=api_calls['total'],
        error_count=api_calls['errors'],
        error_rate=api_calls['error_rate'],
        unique_paths=api_calls['paths'],
        recent_errors=metrics.get_recent_errors(limit=5),
    )


def register_discovery_tools(
    server: FastMCP, api_name: str, openapi_spec: Dict[str, Any], base_url: str
) -> None:
    """Register discovery tools with the MCP server.

    Args:
        server: The MCP server
        api_name: Name of the API
        openapi_spec: The OpenAPI specification
        base_url: Base URL of the API
    """

    # Register get_api_info tool
    async def api_info_tool() -> ApiInfo:
        """Get information about the API.

        Returns:
            ApiInfo: Information about the API
        """
        return await get_api_info(server, api_name, openapi_spec, base_url)

    register_custom_tool(
        server,
        api_info_tool,
        name=f'{api_name}_getApiInfo',
        description=f'Get information about the {api_name} API',
    )

    # Register get_api_tools tool
    async def api_tools_tool() -> List[ToolInfo]:
        """Get information about tools for the API.

        Returns:
            List[ToolInfo]: Information about tools for the API
        """
        return await get_api_tools(server, api_name)

    register_custom_tool(
        server,
        api_tools_tool,
        name=f'{api_name}_getApiTools',
        description=f'Get information about tools for the {api_name} API',
    )

    # Register get_api_stats tool
    async def api_stats_tool() -> ApiStats:
        """Get statistics about API usage.

        Returns:
            ApiStats: Statistics about API usage
        """
        return await get_api_stats()

    register_custom_tool(
        server,
        api_stats_tool,
        name=f'{api_name}_getApiStats',
        description=f'Get statistics about {api_name} API usage',
    )

    logger.info(f'Registered discovery tools for {api_name} API')
