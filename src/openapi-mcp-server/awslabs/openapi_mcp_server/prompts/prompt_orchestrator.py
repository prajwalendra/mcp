"""Unified prompt generation for OpenAPI specifications.

This module serves as the main entry point for prompt generation,
coordinating the generation of different types of prompts.
"""

from awslabs.openapi_mcp_server import get_caller_info, logger
from awslabs.openapi_mcp_server.prompts.api_overview import create_api_overview_prompt
from awslabs.openapi_mcp_server.prompts.base import GENERATE_PROMPTS_FOR_COMPLEX_OPERATIONS_ONLY
from awslabs.openapi_mcp_server.prompts.mapping_reference import create_mapping_reference_prompt
from awslabs.openapi_mcp_server.prompts.operation_prompts import (
    create_operation_prompt,
    is_complex_operation,
)
from awslabs.openapi_mcp_server.prompts.workflow_prompts import generate_generic_workflow_prompts
from awslabs.openapi_mcp_server.utils.config import ENABLE_OPERATION_PROMPTS
from awslabs.openapi_mcp_server.utils.openapi_validator import extract_api_structure
from mcp.server.fastmcp import FastMCP
from typing import Any, Dict


async def generate_api_instructions(
    server: FastMCP, api_name: str, openapi_spec: Dict[str, Any]
) -> None:
    """Generate API instructions for the OpenAPI specification.

    This is an alias for generate_unified_prompts to maintain compatibility.

    Args:
        server: The MCP server instance.
        api_name: The name of the API.
        openapi_spec: The OpenAPI specification.

    """
    return await generate_unified_prompts(server, api_name, openapi_spec)


async def generate_unified_prompts(
    server: FastMCP, api_name: str, openapi_spec: Dict[str, Any]
) -> None:
    """Generate unified prompts for an OpenAPI specification.

    This function generates three types of prompts:
    1. API Overview - General information about the API
    2. Operation-specific prompts - Detailed information about each operation
    3. Mapping Reference - A comprehensive guide to how operations are mapped

    Args:
        server: The MCP server
        api_name: The name of the API
        openapi_spec: The OpenAPI specification

    """
    # Format API name for logging
    if api_name.upper().endswith('API'):
        logger.info(f'Generating unified prompts for {api_name}')
    else:
        logger.info(f'Generating unified prompts for {api_name} API')

    # Get caller information for debugging
    caller_info = get_caller_info()
    logger.debug(f'Called from {caller_info}')

    # Extract API information
    api_info = openapi_spec.get('info', {})
    api_title = api_info.get('title', api_name)
    api_description = api_info.get('description', '')
    api_version = api_info.get('version', '')

    # Extract paths and components
    paths = openapi_spec.get('paths', {})
    components = openapi_spec.get('components', {})
    # Ensure components is a dictionary
    if not isinstance(components, dict):
        logger.warning(
            f"Components is not a dictionary, it's a {type(components).__name__}. Using empty dict instead."
        )
        components = {}
    servers = openapi_spec.get('servers', [])
    security_schemes = components.get('securitySchemes', {}) if isinstance(components, dict) else {}

    # Extract API structure for workflow generation
    try:
        api_structure = extract_api_structure(openapi_spec)
    except Exception as e:
        logger.warning(f'Error extracting API structure: {e}')
        api_structure = paths

    # Generate workflow section for API overview
    try:
        # Ensure components is a dictionary before passing it
        if not isinstance(components, dict):
            logger.warning('Cannot generate workflow prompts with non-dict components')
            workflow_section = None
        else:
            workflow_section = await generate_generic_workflow_prompts(
                server, api_name, api_structure, components
            )
    except Exception as e:
        logger.warning(f'Error generating workflow prompts: {e}')
        workflow_section = None

    # Create API overview prompt
    create_api_overview_prompt(
        server=server,
        api_name=api_name,
        api_title=api_title,
        api_description=api_description,
        api_version=api_version,
        paths=paths,
        components=components,
        servers=servers,
        security_schemes=security_schemes,
        workflow_section=workflow_section,
    )

    # Create operation-specific prompts if enabled
    if ENABLE_OPERATION_PROMPTS:
        # Format API name for logging
        if api_name.upper().endswith('API'):
            logger.info(f'Generating operation-specific prompts for {api_name}')
        else:
            logger.info(f'Generating operation-specific prompts for {api_name} API')

        # Track operation mappings for the mapping reference
        operation_mappings = {}

        # Process each path and operation
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method not in ['get', 'post', 'put', 'patch', 'delete']:
                    continue

                operation_id = operation.get('operationId')
                if not operation_id:
                    continue

                # Determine mapping type (function or resource)
                mapping_type = 'function'  # Default to function mapping

                # Extract operation details
                summary = operation.get('summary', '')
                description = operation.get('description', '')
                parameters = operation.get('parameters', [])
                request_body = operation.get('requestBody')
                responses = operation.get('responses', {})
                security = operation.get('security', [])

                # Skip simple operations if configured to do so
                if GENERATE_PROMPTS_FOR_COMPLEX_OPERATIONS_ONLY:
                    # Determine if this is a complex operation
                    parameters = operation.get('parameters', [])
                    request_body = operation.get('requestBody')
                    responses = operation.get('responses', {})

                    if not is_complex_operation(parameters, request_body, responses):
                        logger.debug(f'Skipping simple operation: {operation_id}')
                        continue

                # Store operation mapping for reference
                operation_mappings[operation_id] = {
                    'mapping_type': mapping_type,
                    'method': method,
                    'path': path,
                    'parameters': parameters,
                }

                try:
                    # Generate detailed prompt for this operation
                    create_operation_prompt(
                        server=server,
                        api_name=api_name,
                        operation_id=operation_id,
                        mapping_type=mapping_type,
                        method=method,
                        path=path,
                        summary=summary,
                        description=description,
                        parameters=parameters,
                        request_body=request_body,
                        responses=responses,
                        security=security,
                    )
                except Exception as e:
                    logger.error(f'Error generating prompt for {operation_id}: {e}')

        # Create mapping reference prompt
        create_mapping_reference_prompt(
            server=server,
            api_name=api_name,
            paths=paths,
            operation_mappings=operation_mappings,
        )
