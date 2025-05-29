#!/usr/bin/env python3

import json
from awslabs.openapi_mcp_server.prompts.generators.operation_prompts import create_operation_prompt
from fastmcp import FastMCP


# Create a mock server
server = FastMCP(name='test-server')

# Create a test operation
operation_id = 'findPetsByStatus'
method = 'get'
path = '/pet/findByStatus'
summary = 'Finds Pets by status'
description = 'Multiple status values can be provided with comma separated strings'
parameters = [
    {
        'name': 'status',
        'in': 'query',
        'description': 'Status values that need to be considered for filter',
        'required': False,
        'schema': {
            'type': 'string',
            'default': 'available',
            'enum': ['available', 'pending', 'sold'],
        },
    }
]
responses = {
    '200': {
        'description': 'successful operation',
        'content': {
            'application/json': {
                'schema': {'type': 'array', 'items': {'$ref': '#/components/schemas/Pet'}}
            }
        },
    },
    '400': {'description': 'Invalid status value'},
}
paths = {
    '/pet/findByStatus': {
        'get': {
            'tags': ['pet'],
            'summary': 'Finds Pets by status',
            'description': 'Multiple status values can be provided with comma separated strings',
            'operationId': 'findPetsByStatus',
            'parameters': parameters,
            'responses': responses,
        }
    }
}

# Create the operation prompt
success = create_operation_prompt(
    server=server,
    api_name='petstore',
    operation_id=operation_id,
    method=method,
    path=path,
    summary=summary,
    description=description,
    parameters=parameters,
    responses=responses,
    paths=paths,
)

# Print the result
print(f'Prompt creation success: {success}')

# Print the prompt
if success and hasattr(server, '_prompt_manager') and hasattr(server._prompt_manager, '_prompts'):
    prompt = server._prompt_manager._prompts.get(operation_id)
    if prompt:
        # Convert to dict and remove function reference for serialization
        prompt_dict = prompt.model_dump()
        prompt_dict.pop('fn', None)

        # Convert sets to lists for JSON serialization
        if 'tags' in prompt_dict and isinstance(prompt_dict['tags'], set):
            prompt_dict['tags'] = list(prompt_dict['tags'])

        # Print the prompt structure
        print(f'Prompt structure for {operation_id}:')
        print(json.dumps(prompt_dict, indent=2))
