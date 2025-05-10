"""Operation-specific instructions generation for OpenAPI specifications."""

import os
import re
from awslabs.openapi_mcp_server import get_caller_info, logger
from mcp.server.fastmcp import FastMCP
from typing import Any, Dict, List


# Import CustomPrompt directly
try:
    from mcp.prompts import CustomPrompt  # type: ignore
except ImportError:
    try:
        from fastmcp.prompts.prompt import CustomPrompt  # type: ignore
    except ImportError:
        # Define a simple CustomPrompt class if neither is available
        class CustomPrompt:
            """Simple fallback implementation of CustomPrompt class."""

            def __init__(self, name: str, description: str, content: str):
                """Initialize a CustomPrompt.

                Args:
                    name: The name of the prompt
                    description: A description of the prompt
                    content: The prompt content
                """
                self.name = name
                self.description = description
                self.content = content


def get_required_parameters(operation: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get required parameters from an operation.

    Args:
        operation: The operation details

    Returns:
        List[Dict[str, Any]]: List of required parameters
    """
    parameters = operation.get('parameters', [])
    return [p for p in parameters if p.get('required', False)]


def get_required_body_fields(operation: Dict[str, Any], components: Dict[str, Any]) -> List[str]:
    """Get required fields from request body.

    Args:
        operation: The operation details
        components: The components section of the OpenAPI spec

    Returns:
        List[str]: List of required field names
    """
    request_body = operation.get('requestBody', {})
    if not request_body or not request_body.get('required', False):
        return []

    # Try to find schema reference
    for content_type, content_info in request_body.get('content', {}).items():
        schema = content_info.get('schema', {})
        if '$ref' in schema:
            ref = schema['$ref']
            schema_name = ref.split('/')[-1]

            # Get required fields from schema
            if components and 'schemas' in components and schema_name in components['schemas']:
                schema_obj = components['schemas'][schema_name]
                return schema_obj.get('required', [])

    return []


def generate_simple_prompt(
    operation_id: str,
    method: str,
    path: str,
    operation: Dict[str, Any],
    components: Dict[str, Any],
) -> str:
    """Generate a simple natural language prompt for an operation.

    Args:
        operation_id: The operation ID
        method: The HTTP method
        path: The API path
        operation: The operation details
        components: The components section of the OpenAPI spec

    Returns:
        str: A simple natural language prompt
    """
    # Get operation summary or create one
    summary = operation.get('summary', '')
    if not summary:
        # Create a summary from the operation ID
        words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', operation_id)
        summary = ' '.join(word.lower() for word in words)
        summary = summary.capitalize() + '.'
    else:
        # Ensure summary ends with a period
        if not summary.endswith('.'):
            summary += '.'

    # Get required parameters
    required_params = get_required_parameters(operation)

    # Get required body fields
    required_fields = get_required_body_fields(operation, components)

    # Build the prompt
    prompt_parts = [summary]

    # Add required parameters
    for param in required_params:
        name = param.get('name', '')
        prompt_parts.append(f'The {name} is {{{name}}}.')

    # Add required body fields
    for field in required_fields:
        prompt_parts.append(f'The {field} is {{{field}}}.')

    return ' '.join(prompt_parts)


async def generate_operation_prompts(
    server: FastMCP, api_name: str, openapi_spec: Dict[str, Any]
) -> None:
    """Generate simple natural language prompts for each API operation.

    Args:
        server: The MCP server
        api_name: The name of the API
        openapi_spec: The OpenAPI specification
    """
    # Check if operation prompts are enabled (default to True)
    enable_prompts = os.environ.get('ENABLE_OPERATION_PROMPTS', 'true').lower() in (
        'true',
        'yes',
        '1',
    )
    if not enable_prompts:
        logger.info('Operation prompts generation is disabled by ENABLE_OPERATION_PROMPTS')
        return

    logger.info(f'Generating operation-specific prompts for {api_name} API')

    # Get caller information for debugging
    caller_info = get_caller_info()
    logger.debug(f'Called from {caller_info}')

    # Extract paths and operations from the spec
    paths = openapi_spec.get('paths', {})
    components = openapi_spec.get('components', {})

    # Track created prompts
    created_prompts = []

    # Process each path and operation
    for path, path_item in paths.items():
        for method, operation in path_item.items():
            if method not in ['get', 'post', 'put', 'delete', 'patch']:
                continue

            # Extract operation details
            operation_id = operation.get('operationId')
            if not operation_id:
                logger.warning(
                    f'Operation at {method.upper()} {path} has no operationId, skipping'
                )
                continue

            try:
                # Generate a simple prompt for this operation
                prompt_content = generate_simple_prompt(
                    operation_id=operation_id,
                    method=method,
                    path=path,
                    operation=operation,
                    components=components,
                )

                # Create a CustomPrompt
                prompt = CustomPrompt(
                    name=f'{api_name}_{operation_id}_prompt',
                    description=f'Simple prompt for {operation_id} operation',
                    content=prompt_content,
                )

                # Add to server using the public API
                server.add_prompt(prompt)  # type: ignore
                created_prompts.append(prompt.name)
                logger.info(f'Added operation prompt: {prompt.name}')
            except Exception as e:
                logger.warning(f'Failed to generate prompt for {operation_id}: {e}')

    logger.info(f'Created {len(created_prompts)} operation-specific prompts')
