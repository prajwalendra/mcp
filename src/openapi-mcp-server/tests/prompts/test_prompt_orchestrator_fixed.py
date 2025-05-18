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
