"""Test fixtures for the lambda-mcp-server tests."""

import json
import os
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_lambda_client():
    """Create a mock boto3 Lambda client."""
    mock_client = MagicMock()

    # Mock list_functions response
    mock_client.list_functions.return_value = {
        'Functions': [
            {
                'FunctionName': 'test-function-1',
                'FunctionArn': 'arn:aws:lambda:us-east-1:123456789012:function:test-function-1',
                'Description': 'Test function 1 description',
            },
            {
                'FunctionName': 'test-function-2',
                'FunctionArn': 'arn:aws:lambda:us-east-1:123456789012:function:test-function-2',
                'Description': 'Test function 2 description',
            },
            {
                'FunctionName': 'prefix-test-function-3',
                'FunctionArn': 'arn:aws:lambda:us-east-1:123456789012:function:prefix-test-function-3',
                'Description': 'Test function 3 with prefix',
            },
            {
                'FunctionName': 'other-function',
                'FunctionArn': 'arn:aws:lambda:us-east-1:123456789012:function:other-function',
                'Description': '',  # Empty description
            },
        ]
    }

    # Mock list_tags response
    def mock_list_tags(Resource):
        if 'test-function-1' in Resource:
            return {'Tags': {'test-key': 'test-value'}}
        elif 'test-function-2' in Resource:
            return {'Tags': {'other-key': 'other-value'}}
        elif 'prefix-test-function-3' in Resource:
            return {'Tags': {'test-key': 'test-value'}}
        else:
            return {'Tags': {}}

    mock_client.list_tags.side_effect = mock_list_tags

    # Mock invoke response
    def mock_invoke(FunctionName, InvocationType, Payload):
        if FunctionName == 'test-function-1':
            mock_payload = MagicMock()
            mock_payload.read.return_value = json.dumps({'result': 'success'}).encode()
            return {
                'StatusCode': 200,
                'Payload': mock_payload,
            }
        elif FunctionName == 'test-function-2':
            mock_payload = MagicMock()
            mock_payload.read.return_value = b'Non-JSON response'
            return {
                'StatusCode': 200,
                'Payload': mock_payload,
            }
        elif FunctionName == 'error-function':
            mock_payload = MagicMock()
            mock_payload.read.return_value = json.dumps({'error': 'Function error'}).encode()
            return {
                'StatusCode': 200,
                'FunctionError': 'Handled',
                'Payload': mock_payload,
            }
        else:
            mock_payload = MagicMock()
            mock_payload.read.return_value = json.dumps({}).encode()
            return {
                'StatusCode': 200,
                'Payload': mock_payload,
            }

    mock_client.invoke.side_effect = mock_invoke

    return mock_client


@pytest.fixture
def mock_env_vars():
    """Set up and tear down environment variables for testing."""
    # Save original environment variables
    original_env = {}
    env_vars = [
        'AWS_PROFILE',
        'AWS_REGION',
        'FUNCTION_PREFIX',
        'FUNCTION_LIST',
        'FUNCTION_TAG_KEY',
        'FUNCTION_TAG_VALUE',
    ]

    for var in env_vars:
        if var in os.environ:
            original_env[var] = os.environ[var]
        else:
            original_env[var] = None

    # Set test environment variables
    os.environ['AWS_PROFILE'] = 'test-profile'
    os.environ['AWS_REGION'] = 'us-east-1'
    os.environ['FUNCTION_PREFIX'] = 'prefix-'
    os.environ['FUNCTION_LIST'] = 'test-function-1,test-function-2'
    os.environ['FUNCTION_TAG_KEY'] = 'test-key'
    os.environ['FUNCTION_TAG_VALUE'] = 'test-value'

    yield

    # Restore original environment variables
    for var in env_vars:
        if original_env[var] is not None:
            os.environ[var] = original_env[var]
        elif var in os.environ:
            del os.environ[var]


@pytest.fixture
def clear_env_vars():
    """Clear environment variables for testing."""
    # Save original environment variables
    original_env = {}
    env_vars = [
        'AWS_PROFILE',
        'AWS_REGION',
        'FUNCTION_PREFIX',
        'FUNCTION_LIST',
        'FUNCTION_TAG_KEY',
        'FUNCTION_TAG_VALUE',
    ]

    for var in env_vars:
        if var in os.environ:
            original_env[var] = os.environ[var]
        else:
            original_env[var] = None

    # Clear test environment variables
    for var in env_vars:
        if var in os.environ:
            del os.environ[var]

    yield

    # Restore original environment variables
    for var in env_vars:
        if original_env[var] is not None:
            os.environ[var] = original_env[var]
