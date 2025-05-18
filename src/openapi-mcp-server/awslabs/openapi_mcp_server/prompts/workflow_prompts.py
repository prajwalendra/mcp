"""Workflow prompt generation for OpenAPI specifications."""

from awslabs.openapi_mcp_server import logger


def _generate_list_get_update_workflow(resource_type, list_op, get_op, update_op):
    """Generate a workflow for list → get → update pattern.

    Args:
        resource_type: The resource type
        list_op: The list operation
        get_op: The get operation
        update_op: The update operation

    Returns:
        str: The generated workflow

    """
    list_op_id = list_op.get('operationId')
    get_op_id = get_op.get('operationId')
    update_op_id = update_op.get('operationId')

    workflow = f"""### List, Get, and Update {resource_type}s

This workflow demonstrates how to list {resource_type}s, get details for a specific {resource_type}, and update it.

```python
# Step 1: List all {resource_type}s
{resource_type.lower()}_list = await {list_op_id}()
print(f"Found {{len({resource_type.lower()}_list)}} {resource_type}s")

# Step 2: Get details for a specific {resource_type}
if {resource_type.lower()}_list:
    # Get the first {resource_type}'s ID
    {resource_type.lower()}_id = {resource_type.lower()}_list[0]['id']

    # Get detailed information
    {resource_type.lower()}_details = await {get_op_id}({resource_type.lower()}_id)
    print(f"Details for {resource_type} {{{{resource_type.lower()}}_id}}:")
    print({resource_type.lower()}_details)

    # Step 3: Update the {resource_type}
    update_data = {{
        "name": "Updated {resource_type} Name",
        "description": "This {resource_type} was updated via API"
    }}

    updated_{resource_type.lower()} = await {update_op_id}({resource_type.lower()}_id, update_data)
    print(f"Updated {resource_type}:")
    print(updated_{resource_type.lower()})
```

This workflow demonstrates a common pattern for managing {resource_type}s:
1. List all available {resource_type}s
2. Select a specific {resource_type} by ID
3. Get detailed information about the {resource_type}
4. Update the {resource_type} with new information
"""

    return workflow


def _generate_search_create_workflow(search_op, create_op):
    """Generate a workflow for search → create pattern.

    Args:
        search_op: The search operation
        create_op: The create operation

    Returns:
        str: The generated workflow

    """
    search_op_id = search_op.get('operationId')
    create_op_id = create_op.get('operationId')

    # Try to determine the resource type from the operation IDs
    resource_type = 'Resource'

    # Extract resource type from create operation ID
    if create_op_id:
        if create_op_id.startswith('create'):
            resource_type = create_op_id[6:]  # Remove "create" prefix
        elif 'create' in create_op_id:
            parts = create_op_id.split('create')
            if len(parts) > 1 and parts[1]:
                resource_type = parts[1]

    workflow = f"""### Search and Create {resource_type}

This workflow demonstrates how to search for {resource_type}s and create a new one if needed.

```python
# Step 1: Search for {resource_type}s with specific criteria
search_criteria = {{
    "name": "Example {resource_type}",
    "status": "active"
}}

search_results = await {search_op_id}(**search_criteria)
print(f"Found {{len(search_results)}} matching {resource_type}s")

# Step 2: Create a new {resource_type} if not found
if not search_results:
    print(f"No matching {resource_type}s found. Creating a new one...")

    new_{resource_type.lower()}_data = {{
        "name": "New {resource_type}",
        "description": "This is a new {resource_type} created via API",
        "status": "active"
    }}

    new_{resource_type.lower()} = await {create_op_id}(new_{resource_type.lower()}_data)
    print(f"Created new {resource_type}:")
    print(new_{resource_type.lower()})
else:
    print(f"Using existing {resource_type}:")
    print(search_results[0])
```

This workflow demonstrates a common pattern:
1. Search for {resource_type}s matching specific criteria
2. If no matching {resource_type}s are found, create a new one
3. Otherwise, use an existing {resource_type}
"""

    return workflow


async def generate_generic_workflow_prompts(server, api_name, api_structure, components):
    """Generate generic workflow prompts based on API structure analysis.

    Args:
        server: The MCP server
        api_name: The name of the API
        api_structure: The API structure
        components: The API components

    Returns:
        str: The generated workflow section for the API overview

    """
    # Validate that inputs are dictionaries
    if not isinstance(api_structure, dict):
        logger.warning(
            f"API structure is not a dictionary, it's a {type(api_structure).__name__}. Cannot generate workflows."
        )
        return '\n## Common Workflows\n\nNo common workflows could be generated due to unexpected API structure format.'

    if not isinstance(components, dict):
        logger.warning(
            f"Components is not a dictionary, it's a {type(components).__name__}. Continuing without component schemas."
        )
        # Components is not used directly in this function, so we can continue

    workflow_section = '\n## Common Workflows\n\n'
    workflows = []

    # Find resource types and their operations
    resource_operations = {}

    # Group operations by resource type
    try:
        for path, path_info in api_structure.items():
            # Skip if path_info is not a dictionary
            if not isinstance(path_info, dict):
                logger.debug(f'Path info for {path} is not a dictionary, skipping')
                continue

            # Try to extract resource type from path
            path_parts = path.strip('/').split('/')
            resource_type = None

            # Look for resource identifier in path
            for part in path_parts:
                if part and not part.startswith('{'):
                    # Convert to singular form if plural
                    if part.endswith('s'):
                        resource_type = part[:-1].capitalize()
                    else:
                        resource_type = part.capitalize()
                    break

            # Skip if we couldn't determine a resource type
            if not resource_type:
                logger.debug(f'Could not determine resource type for path {path}, skipping')
                continue

            # Initialize resource operations if not exists
            if resource_type not in resource_operations:
                resource_operations[resource_type] = {
                    'list': None,
                    'get': None,
                    'create': None,
                    'update': None,
                    'delete': None,
                    'search': None,
                }

            # Categorize operations
            for method, operation in path_info.items():
                # Skip if operation is not a dictionary
                if not isinstance(operation, dict):
                    logger.debug(f'Operation for {method} {path} is not a dictionary, skipping')
                    continue

                op_id = operation.get('operationId', '')

                if not op_id:
                    logger.debug(f'No operationId for {method} {path}, skipping')
                    continue

                op_id_lower = op_id.lower()

                # Categorize based on method and operation ID
                if method == 'get':
                    if 'list' in op_id_lower or 'getall' in op_id_lower:
                        resource_operations[resource_type]['list'] = operation
                    elif 'search' in op_id_lower or 'find' in op_id_lower or 'query' in op_id_lower:
                        resource_operations[resource_type]['search'] = operation
                    else:
                        resource_operations[resource_type]['get'] = operation
                elif method == 'post':
                    if 'create' in op_id_lower or 'add' in op_id_lower:
                        resource_operations[resource_type]['create'] = operation
                    elif 'search' in op_id_lower or 'find' in op_id_lower or 'query' in op_id_lower:
                        resource_operations[resource_type]['search'] = operation
                elif method == 'put' or method == 'patch':
                    if 'update' in op_id_lower or 'modify' in op_id_lower:
                        resource_operations[resource_type]['update'] = operation
                elif method == 'delete':
                    resource_operations[resource_type]['delete'] = operation

        # Generate workflows based on available operations
        for resource_type, operations in resource_operations.items():
            try:
                # List -> Get -> Update workflow
                list_op = operations['list']
                get_op = operations['get']
                update_op = operations['update']

                if list_op and get_op and update_op:
                    workflows.append(
                        _generate_list_get_update_workflow(
                            resource_type, list_op, get_op, update_op
                        )
                    )

                # Search -> Create workflow
                search_op = operations['search']
                create_op = operations['create']

                if search_op and create_op:
                    workflows.append(_generate_search_create_workflow(search_op, create_op))
            except Exception as e:
                logger.warning(f'Error generating workflows for resource type {resource_type}: {e}')
                continue

    except Exception as e:
        logger.warning(f'Error processing API structure: {e}')

    # Add workflows to the section
    if workflows:
        workflow_section += '\n\n'.join(workflows)
    else:
        workflow_section += 'No common workflows identified for this API.'

    return workflow_section
