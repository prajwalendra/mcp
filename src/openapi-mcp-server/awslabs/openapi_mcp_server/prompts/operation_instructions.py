"""Operation-specific instructions generation for OpenAPI specifications."""

import re
from awslabs.openapi_mcp_server import get_caller_info, logger
from mcp.server.fastmcp import FastMCP
from typing import Any, Dict, List, Tuple


# Try to import Prompt from different locations
try:
    from mcp.prompts import Prompt  # type: ignore
except ImportError:
    try:
        from fastmcp.prompts.prompt import Prompt  # type: ignore
    except ImportError:
        # Define a simple Prompt class if neither is available
        class Prompt:
            """Simple fallback implementation of Prompt class."""

            @staticmethod
            def from_function(fn: Any, name: str, description: str):
                """Create a simple prompt from a function."""
                return {'fn': fn, 'name': name, 'description': description}


def format_parameter_info(param: Dict[str, Any]) -> List[str]:
    """Format parameter information in a readable way.

    Args:
        param: Parameter information

    Returns:
        List[str]: Lines of formatted parameter information
    """
    result = []

    name = param.get('name', 'unknown')
    param_in = param.get('in', 'query')
    required = param.get('required', False)
    description = param.get('description', '')

    # Extract schema information if available
    schema_type = 'string'
    example = None
    enum_values = None

    if 'schema' in param:
        schema = param['schema']
        schema_type = schema.get('type', 'string')
        example = schema.get('example')
        enum_values = schema.get('enum')

    # Build the parameter description
    req_str = 'required' if required else 'optional'
    result.append(f'- `{name}` ({param_in}, {req_str}): {description}')

    # Add schema details if available
    if schema_type:
        result.append(f'  - Type: `{schema_type}`')

    if enum_values:
        enum_str = ', '.join([f'`{val}`' for val in enum_values[:5]])
        if len(enum_values) > 5:
            enum_str += ', ...'
        result.append(f'  - Allowed values: {enum_str}')

    if example is not None:
        result.append(f'  - Example: `{example}`')

    return result


def format_schema_info(schema: Dict[str, Any], components: Dict[str, Any]) -> List[str]:
    """Format schema information in a readable way.

    Args:
        schema: Schema information
        components: Components from OpenAPI spec

    Returns:
        List[str]: Lines of formatted schema information
    """
    result = []

    if '$ref' in schema:
        # Extract schema reference
        ref = schema['$ref']
        schema_name = ref.split('/')[-1]
        result.append(f'Schema: `{schema_name}`')

        # Try to get the actual schema from components
        if components and 'schemas' in components and schema_name in components['schemas']:
            schema_obj = components['schemas'][schema_name]

            # Add required fields
            if 'required' in schema_obj and schema_obj['required']:
                req_fields = ', '.join([f'`{f}`' for f in schema_obj['required']])
                result.append(f'Required fields: {req_fields}')

            # Add properties
            if 'properties' in schema_obj:
                result.append('Properties:')
                for prop_name, prop in schema_obj['properties'].items():
                    prop_type = prop.get('type', 'string')
                    prop_desc = prop.get('description', '')
                    result.append(f'- `{prop_name}` ({prop_type}): {prop_desc}')

                    # Add enum values if available
                    if 'enum' in prop:
                        enum_values = ', '.join([f'`{v}`' for v in prop['enum']])
                        result.append(f'  - Allowed values: {enum_values}')

                    # Add example if available
                    if 'example' in prop:
                        result.append(f'  - Example: `{prop["example"]}`')
    elif 'type' in schema:
        result.append(f'Type: `{schema["type"]}`')

        # Handle array type
        if schema['type'] == 'array' and 'items' in schema:
            result.append('Array items:')
            items_schema = schema['items']
            items_info = format_schema_info(items_schema, components)
            for line in items_info:
                result.append(f'  {line}')

    return result


def format_request_body_info(
    request_body: Dict[str, Any], components: Dict[str, Any]
) -> List[str]:
    """Format request body information in a readable way.

    Args:
        request_body: Request body information
        components: Components from OpenAPI spec

    Returns:
        List[str]: Lines of formatted request body information
    """
    result = []

    if not request_body:
        return result

    required = request_body.get('required', False)
    result.append(f'Request body is {"required" if required else "optional"}')

    # Process content types
    for content_type, content_schema in request_body.get('content', {}).items():
        result.append(f'Content Type: `{content_type}`')

        schema = content_schema.get('schema', {})
        schema_info = format_schema_info(schema, components)
        result.extend(schema_info)

    return result


def format_responses_info(responses: Dict[str, Any], components: Dict[str, Any]) -> List[str]:
    """Format responses information in a readable way.

    Args:
        responses: Responses information
        components: Components from OpenAPI spec

    Returns:
        List[str]: Lines of formatted responses information
    """
    result = []

    if not responses:
        return result

    # Sort status codes to show success responses first
    status_codes = sorted(responses.keys(), key=lambda x: 0 if x.startswith('2') else 1)

    for status_code in status_codes:
        response = responses[status_code]
        description = response.get('description', '')
        result.append(f'### Status {status_code}')
        result.append(description)

        # Add content types and schemas
        for content_type, content_schema in response.get('content', {}).items():
            result.append(f'Content Type: `{content_type}`')

            schema = content_schema.get('schema', {})
            schema_info = format_schema_info(schema, components)
            result.extend(schema_info)

    return result


def extract_resource_from_operation_id(operation_id: str) -> str:
    """Extract resource name from operation ID.

    Args:
        operation_id: Operation ID

    Returns:
        str: Resource name
    """
    # Common patterns: getPet, createPet, etc.
    for prefix in ['get', 'create', 'update', 'delete', 'list', 'find', 'add', 'remove', 'upload']:
        if operation_id.lower().startswith(prefix.lower()):
            resource = operation_id[len(prefix) :]
            # Check if the first character is uppercase
            if resource and resource[0].isupper():
                return resource

    # Try to extract from camelCase (e.g., getPetById -> Pet)
    matches = re.findall(r'[A-Z][a-z]+', operation_id)
    if matches:
        return matches[0]

    # If no resource found, use "Other"
    return 'Other'


def generate_operation_prompt(
    api_name: str,
    operation_id: str,
    method: str,
    path: str,
    operation: Dict[str, Any],
    components: Dict[str, Any],
) -> str:
    """Generate a detailed prompt for a specific API operation.

    Args:
        api_name: The name of the API
        operation_id: The operation ID
        method: The HTTP method
        path: The API path
        operation: The operation details
        components: The components section of the OpenAPI spec

    Returns:
        str: A detailed prompt for the operation
    """
    # Extract operation details
    summary = operation.get('summary', '')
    description = operation.get('description', '')
    parameters = operation.get('parameters', [])
    request_body = operation.get('requestBody', {})
    responses = operation.get('responses', {})

    # Build the prompt content
    content = [f'# {operation_id} Operation Guide\n']

    if summary:
        content.append(f'## Summary\n{summary}\n')

    if description:
        content.append(f'## Description\n{description}\n')

    # Add endpoint details
    content.append(f'## Endpoint\n`{method.upper()} {path}`\n')

    # Add parameters section
    if parameters:
        content.append('## Parameters')
        for param in parameters:
            param_info = format_parameter_info(param)
            content.extend(param_info)
        content.append('')

    # Add request body section
    if request_body:
        content.append('## Request Body')
        request_body_info = format_request_body_info(request_body, components)
        content.extend(request_body_info)
        content.append('')

    # Add responses section
    if responses:
        content.append('## Responses')
        responses_info = format_responses_info(responses, components)
        content.extend(responses_info)
        content.append('')

    # Add usage examples
    content.append('## Usage Example')

    # Create a tool usage example
    tool_name = f'{api_name}_{operation_id}'
    example_params = []

    # Add path parameters to example
    path_params = [p for p in parameters if p.get('in') == 'path']
    for param in path_params:
        name = param.get('name', '')
        example = 'value'
        if 'schema' in param:
            if 'example' in param['schema']:
                example = param['schema']['example']
            elif 'enum' in param['schema'] and param['schema']['enum']:
                example = param['schema']['enum'][0]
            elif param['schema'].get('type') == 'integer':
                example = 1
        example_params.append(f'{name}={example}')

    # Add a few query parameters to example
    query_params = [p for p in parameters if p.get('in') == 'query']
    for param in query_params[:2]:  # Limit to 2 query parameters
        name = param.get('name', '')
        example = 'value'
        if 'schema' in param:
            if 'example' in param['schema']:
                example = param['schema']['example']
            elif 'enum' in param['schema'] and param['schema']['enum']:
                example = param['schema']['enum'][0]
        example_params.append(f"{name}='{example}'")

    # Add request body example if needed
    if request_body:
        # Try to create a simplified example based on the schema
        example_body = '{ ... }'  # Default placeholder

        # Check if we have a schema reference
        for content_type, content_schema in request_body.get('content', {}).items():
            schema = content_schema.get('schema', {})
            if '$ref' in schema:
                ref = schema['$ref']
                schema_name = ref.split('/')[-1]
                example_body = f'{{ /* {schema_name} object */ }}'
                break

        example_params.append(f'data={example_body}')

    # Format the example
    if example_params:
        params_str = ', '.join(example_params)
        content.append(f'```\n{tool_name}({params_str})\n```\n')
    else:
        content.append(f'```\n{tool_name}()\n```\n')

    # Add notes and best practices
    content.append('## Notes and Best Practices')
    content.append('- Always check the response status code to handle errors appropriately')
    if any(p.get('required', False) for p in parameters):
        content.append('- Ensure all required parameters are provided')
    if request_body and request_body.get('required', False):
        content.append('- Ensure the request body contains all required fields')

    return '\n'.join(content)


def generate_operations_index(api_name: str, operation_prompts: List[Tuple[str, str, str]]) -> str:
    """Generate an index of all operation prompts.

    Args:
        api_name: The name of the API
        operation_prompts: List of (prompt_name, operation_id, resource) tuples

    Returns:
        str: An index of all operation prompts
    """
    content = [f'# {api_name} API Operations\n']
    content.append('This is an index of all available operation guides for this API.\n')
    content.append('## Available Operation Guides\n')

    # Group operations by resource/entity
    grouped_operations = {}
    for prompt_name, operation_id, resource in operation_prompts:
        if resource not in grouped_operations:
            grouped_operations[resource] = []

        grouped_operations[resource].append((prompt_name, operation_id))

    # Add grouped operations to content
    for resource, operations in sorted(grouped_operations.items()):
        content.append(f'### {resource}\n')
        for prompt_name, operation_id in sorted(operations, key=lambda x: x[1]):
            content.append(f'- {operation_id}: Use prompt `{prompt_name}`')
        content.append('')

    content.append('## How to Use\n')
    content.append(
        'To get detailed information about a specific operation, request the corresponding prompt by name.'
    )
    content.append(
        f"For example, to learn about the 'getPet' operation, request the '{api_name}_getPet_guide' prompt.\n"
    )

    return '\n'.join(content)


async def generate_operation_prompts(
    server: FastMCP, api_name: str, openapi_spec: Dict[str, Any]
) -> None:
    """Generate detailed prompts for each API operation.

    Args:
        server: The MCP server
        api_name: The name of the API
        openapi_spec: The OpenAPI specification
    """
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
                continue

            # Extract resource name
            resource = extract_resource_from_operation_id(operation_id)

            # Generate a detailed prompt for this operation
            prompt_content = generate_operation_prompt(
                api_name=api_name,
                operation_id=operation_id,
                method=method,
                path=path,
                operation=operation,
                components=components,
            )

            # Create a prompt function
            def create_prompt_fn(content):
                def prompt_fn():
                    return [{'role': 'user', 'content': content}]

                return prompt_fn

            prompt_fn = create_prompt_fn(prompt_content)
            prompt_name = f'{api_name}_{operation_id}_guide'

            # Create and add the prompt
            prompt = Prompt.from_function(
                fn=prompt_fn,
                name=prompt_name,
                description=f'Usage guide for {operation_id} operation',
            )

            # Add to server
            try:
                server._prompt_manager.add_prompt(prompt)
                created_prompts.append((prompt_name, operation_id, resource))
                logger.info(f'Added operation prompt: {prompt_name}')
            except Exception as e:
                logger.error(f'Failed to add prompt {prompt_name}: {e}')

    logger.info(f'Created {len(created_prompts)} operation-specific prompts')

    # Create an index prompt that lists all available operation prompts
    if created_prompts:
        index_content = generate_operations_index(api_name, created_prompts)

        def index_prompt_fn():
            return [{'role': 'user', 'content': index_content}]

        index_prompt = Prompt.from_function(
            fn=index_prompt_fn,
            name=f'{api_name}_operations_index',
            description=f'Index of all {api_name} API operation guides',
        )

        try:
            server._prompt_manager.add_prompt(index_prompt)
            logger.info(f'Added operations index prompt: {api_name}_operations_index')
        except Exception as e:
            logger.error(f'Failed to add operations index prompt: {e}')
