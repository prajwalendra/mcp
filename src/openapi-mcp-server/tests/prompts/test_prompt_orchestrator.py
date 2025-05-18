"""Tests for the prompt_orchestrator module."""

import pytest
from awslabs.openapi_mcp_server.prompts.prompt_orchestrator import (
    generate_api_instructions,
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
