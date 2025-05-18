"""Tests for the prompt_orchestrator module."""

import pytest
from awslabs.openapi_mcp_server.prompts.prompt_orchestrator import (
    generate_api_instructions,
    generate_unified_prompts,
)
from unittest.mock import AsyncMock, MagicMock, patch


class MockPromptManager:
    """Mock prompt manager for testing."""

    def __init__(self):
        """Initialize the mock prompt manager."""
        self._prompts = {}

    def add_prompt(self, prompt):
        """Add a prompt to the manager."""
        self._prompts[prompt.name] = prompt


@pytest.mark.asyncio
async def test_generate_api_instructions():
    """Test generating API instructions."""
    # Setup test data
    server = MagicMock()
    server.get_tools = AsyncMock(return_value={})
    server.get_resources = AsyncMock(return_value={})
    server._prompt_manager = MockPromptManager()

    api_name = 'test-api'
    openapi_spec = {
        'info': {'title': 'Test API Title', 'description': 'This is a test API description'},
        'paths': {},
    }

    # Mock the required functions
    with patch(
        'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.generate_unified_prompts'
    ) as mock_unified:
        # Call the function
        await generate_api_instructions(server, api_name, openapi_spec)

        # Verify the result
        mock_unified.assert_called_once_with(server, api_name, openapi_spec)


@pytest.mark.asyncio
async def test_generate_unified_prompts_minimal():
    """Test generating unified prompts with minimal data."""
    # Setup test data
    server = MagicMock()
    server.get_tools = AsyncMock(return_value={})
    server.get_resources = AsyncMock(return_value={})
    server._prompt_manager = MockPromptManager()

    api_name = 'test-api'
    openapi_spec = {
        'info': {'title': 'Test API Title', 'description': 'This is a test API description'},
        'paths': {},
    }

    # Mock the required functions - use module path instead of function path
    with patch(
        'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.create_api_overview_prompt'
    ) as mock_overview:
        with patch(
            'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.create_mapping_reference_prompt'
        ) as mock_mapping:
            with patch(
                'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.generate_generic_workflow_prompts',
                return_value='Mock workflow section',
            ):
                # Call the function
                await generate_unified_prompts(server, api_name, openapi_spec)

                # Verify the result
                mock_overview.assert_called_once()
                mock_mapping.assert_called_once()


@pytest.mark.asyncio
async def test_generate_unified_prompts_with_paths():
    """Test generating unified prompts with API paths."""
    # Setup test data
    server = MagicMock()
    server.get_tools = AsyncMock(return_value={})
    server.get_resources = AsyncMock(return_value={})
    server._prompt_manager = MockPromptManager()

    api_name = 'test-api'
    openapi_spec = {
        'info': {'title': 'Test API Title', 'description': 'This is a test API description'},
        'paths': {
            '/items': {
                'get': {'operationId': 'listItems', 'summary': 'List all items', 'tags': ['items']}
            },
            '/items/{itemId}': {
                'get': {
                    'operationId': 'getItem',
                    'summary': 'Get an item by ID',
                    'tags': ['items'],
                }
            },
        },
    }

    # Mock the required functions - use module path instead of function path
    with patch(
        'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.create_api_overview_prompt'
    ) as mock_overview:
        with patch(
            'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.create_mapping_reference_prompt'
        ) as mock_mapping:
            with patch(
                'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.generate_generic_workflow_prompts',
                return_value='Mock workflow section',
            ):
                with patch(
                    'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.create_operation_prompt'
                ) as mock_operation:
                    with patch(
                        'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.ENABLE_OPERATION_PROMPTS',
                        True,
                    ):
                        # Call the function
                        await generate_unified_prompts(server, api_name, openapi_spec)

                        # Verify the result
                        mock_overview.assert_called_once()
                        assert mock_operation.call_count >= 1
                        mock_mapping.assert_called_once()


@pytest.mark.asyncio
async def test_generate_unified_prompts_with_components():
    """Test generating unified prompts with components."""
    # Setup test data
    server = MagicMock()
    server.get_tools = AsyncMock(return_value={})
    server.get_resources = AsyncMock(return_value={})
    server._prompt_manager = MockPromptManager()

    api_name = 'test-api'
    openapi_spec = {
        'info': {'title': 'Test API Title', 'description': 'This is a test API description'},
        'paths': {},
        'components': {
            'schemas': {
                'Item': {
                    'type': 'object',
                    'properties': {'id': {'type': 'string'}, 'name': {'type': 'string'}},
                }
            }
        },
    }

    # Mock the required functions - use module path instead of function path
    with patch(
        'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.create_api_overview_prompt'
    ) as mock_overview:
        with patch(
            'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.create_mapping_reference_prompt'
        ) as mock_mapping:
            with patch(
                'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.generate_generic_workflow_prompts',
                return_value='Mock workflow section',
            ):
                # Call the function
                await generate_unified_prompts(server, api_name, openapi_spec)

                # Verify the result
                mock_overview.assert_called_once()
                mock_mapping.assert_called_once()


@pytest.mark.asyncio
async def test_generate_unified_prompts_with_security_schemes():
    """Test generating unified prompts with security schemes."""
    # Setup test data
    server = MagicMock()
    server.get_tools = AsyncMock(return_value={})
    server.get_resources = AsyncMock(return_value={})
    server._prompt_manager = MockPromptManager()

    api_name = 'test-api'
    openapi_spec = {
        'info': {'title': 'Test API Title', 'description': 'This is a test API description'},
        'paths': {},
        'components': {
            'securitySchemes': {'apiKey': {'type': 'apiKey', 'in': 'header', 'name': 'X-API-Key'}}
        },
    }

    # Mock the required functions - use module path instead of function path
    with patch(
        'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.create_api_overview_prompt'
    ) as mock_overview:
        with patch(
            'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.create_mapping_reference_prompt'
        ) as mock_mapping:
            with patch(
                'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.generate_generic_workflow_prompts',
                return_value='Mock workflow section',
            ):
                # Call the function
                await generate_unified_prompts(server, api_name, openapi_spec)

                # Verify the result
                mock_overview.assert_called_once()
                mock_mapping.assert_called_once()


@pytest.mark.asyncio
async def test_generate_unified_prompts_with_servers():
    """Test generating unified prompts with servers information."""
    # Setup test data
    server = MagicMock()
    server.get_tools = AsyncMock(return_value={})
    server.get_resources = AsyncMock(return_value={})
    server._prompt_manager = MockPromptManager()

    api_name = 'test-api'
    openapi_spec = {
        'info': {'title': 'Test API Title', 'description': 'This is a test API description'},
        'paths': {},
        'servers': [
            {'url': 'https://api.example.com/v1', 'description': 'Production server'},
            {'url': 'https://staging-api.example.com/v1', 'description': 'Staging server'},
        ],
    }

    # Mock the required functions - use module path instead of function path
    with patch(
        'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.create_api_overview_prompt'
    ) as mock_overview:
        with patch(
            'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.create_mapping_reference_prompt'
        ) as mock_mapping:
            with patch(
                'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.generate_generic_workflow_prompts',
                return_value='Mock workflow section',
            ):
                # Call the function
                await generate_unified_prompts(server, api_name, openapi_spec)

                # Verify the result
                mock_overview.assert_called_once()
                mock_mapping.assert_called_once()


@pytest.mark.asyncio
async def test_generate_unified_prompts_with_complex_operations():
    """Test generating unified prompts with complex operations."""
    # Setup test data
    server = MagicMock()
    server.get_tools = AsyncMock(return_value={})
    server.get_resources = AsyncMock(return_value={})
    server._prompt_manager = MockPromptManager()

    api_name = 'test-api'
    openapi_spec = {
        'info': {'title': 'Test API Title', 'description': 'This is a test API description'},
        'paths': {
            '/items': {
                'post': {
                    'operationId': 'createItem',
                    'summary': 'Create a new item',
                    'tags': ['items'],
                    'requestBody': {
                        'required': True,
                        'content': {
                            'application/json': {
                                'schema': {
                                    'type': 'object',
                                    'properties': {
                                        'name': {'type': 'string'},
                                        'description': {'type': 'string'},
                                    },
                                }
                            }
                        },
                    },
                    'responses': {
                        '201': {
                            'description': 'Item created',
                            'content': {
                                'application/json': {
                                    'schema': {
                                        'type': 'object',
                                        'properties': {
                                            'id': {'type': 'string'},
                                            'name': {'type': 'string'},
                                            'description': {'type': 'string'},
                                        },
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
    }

    # Mock the required functions - use module path instead of function path
    with patch(
        'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.create_api_overview_prompt'
    ) as mock_overview:
        with patch(
            'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.create_mapping_reference_prompt'
        ) as mock_mapping:
            with patch(
                'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.generate_generic_workflow_prompts',
                return_value='Mock workflow section',
            ):
                with patch(
                    'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.create_operation_prompt'
                ) as mock_operation:
                    with patch(
                        'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.ENABLE_OPERATION_PROMPTS',
                        True,
                    ):
                        with patch(
                            'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.GENERATE_PROMPTS_FOR_COMPLEX_OPERATIONS_ONLY',
                            True,
                        ):
                            with patch(
                                'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.is_complex_operation',
                                return_value=True,
                            ):
                                # Call the function
                                await generate_unified_prompts(server, api_name, openapi_spec)

                                # Verify the result
                                mock_overview.assert_called_once()
                                mock_operation.assert_called()
                                mock_mapping.assert_called_once()


@pytest.mark.asyncio
async def test_generate_unified_prompts_skip_simple_operations():
    """Test generating unified prompts with simple operations that should be skipped."""
    # Setup test data
    server = MagicMock()
    server.get_tools = AsyncMock(return_value={})
    server.get_resources = AsyncMock(return_value={})
    server._prompt_manager = MockPromptManager()

    api_name = 'test-api'
    openapi_spec = {
        'info': {'title': 'Test API Title', 'description': 'This is a test API description'},
        'paths': {
            '/items': {
                'get': {'operationId': 'listItems', 'summary': 'List all items', 'tags': ['items']}
            }
        },
    }

    # Mock the required functions - use module path instead of function path
    with patch(
        'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.create_api_overview_prompt'
    ) as mock_overview:
        with patch(
            'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.create_mapping_reference_prompt'
        ) as mock_mapping:
            with patch(
                'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.generate_generic_workflow_prompts',
                return_value='Mock workflow section',
            ):
                with patch(
                    'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.create_operation_prompt'
                ) as mock_operation:
                    with patch(
                        'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.ENABLE_OPERATION_PROMPTS',
                        True,
                    ):
                        with patch(
                            'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.GENERATE_PROMPTS_FOR_COMPLEX_OPERATIONS_ONLY',
                            True,
                        ):
                            with patch(
                                'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.is_complex_operation',
                                return_value=False,
                            ):
                                # Call the function
                                await generate_unified_prompts(server, api_name, openapi_spec)

                                # Verify the result
                                mock_overview.assert_called_once()
                                mock_operation.assert_not_called()  # Should be skipped
                                mock_mapping.assert_called_once()


@pytest.mark.asyncio
async def test_generate_unified_prompts_error_handling():
    """Test error handling in generate_unified_prompts."""
    # Setup test data
    server = MagicMock()
    server.get_tools = AsyncMock(side_effect=Exception('Failed to get tools'))
    server.get_resources = AsyncMock(return_value={})
    server._prompt_manager = MockPromptManager()

    api_name = 'test-api'
    openapi_spec = {
        'info': {'title': 'Test API Title', 'description': 'This is a test API description'},
        'paths': {},
    }

    # Mock the required functions - use module path instead of function path
    with patch(
        'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.create_api_overview_prompt'
    ) as mock_overview:
        with patch(
            'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.create_mapping_reference_prompt'
        ) as mock_mapping:
            with patch(
                'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.generate_generic_workflow_prompts',
                side_effect=Exception('Workflow error'),
            ):
                # Call the function - should not raise an exception
                await generate_unified_prompts(server, api_name, openapi_spec)

                # Verify the result - overview should still be called even if workflow fails
                mock_overview.assert_called_once()
                mock_mapping.assert_called_once()


@pytest.mark.asyncio
async def test_generate_unified_prompts_operation_error():
    """Test error handling for operation prompt generation."""
    # Setup test data
    server = MagicMock()
    server.get_tools = AsyncMock(return_value={})
    server.get_resources = AsyncMock(return_value={})
    server._prompt_manager = MockPromptManager()

    api_name = 'test-api'
    openapi_spec = {
        'info': {'title': 'Test API Title', 'description': 'This is a test API description'},
        'paths': {
            '/items': {
                'get': {'operationId': 'listItems', 'summary': 'List all items', 'tags': ['items']}
            }
        },
    }

    # Mock the required functions - use module path instead of function path
    with patch(
        'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.create_api_overview_prompt'
    ) as mock_overview:
        with patch(
            'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.create_mapping_reference_prompt'
        ) as mock_mapping:
            with patch(
                'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.generate_generic_workflow_prompts',
                return_value='Mock workflow section',
            ):
                with patch(
                    'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.create_operation_prompt',
                    side_effect=Exception('Operation error'),
                ):
                    with patch(
                        'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.ENABLE_OPERATION_PROMPTS',
                        True,
                    ):
                        with patch(
                            'awslabs.openapi_mcp_server.prompts.prompt_orchestrator.GENERATE_PROMPTS_FOR_COMPLEX_OPERATIONS_ONLY',
                            False,
                        ):
                            # Call the function - should not raise an exception
                            await generate_unified_prompts(server, api_name, openapi_spec)

                            # Verify the result
                            mock_overview.assert_called_once()
                            mock_mapping.assert_called_once()  # Should still be called
