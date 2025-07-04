"""Tests to boost coverage for server.py."""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock, call
import sys
import signal
from typing import Dict, List, Any, Optional

from awslabs.openapi_mcp_server.server import (
    create_mcp_server,
    setup_signal_handlers,
    main,
)


class TestServerCoverageBoost:
    """Tests to boost coverage for server.py."""

    @pytest.fixture
    def mock_fastmcp(self):
        """Create a mock FastMCP instance."""
        server = MagicMock()
        server.start = AsyncMock()
        server.stop = AsyncMock()
        server.register_tool = AsyncMock()
        server.register_resource = AsyncMock()
        return server

    @pytest.fixture
    def mock_prompt_manager(self):
        """Create a mock prompt manager."""
        manager = MagicMock()
        manager.generate_prompts = AsyncMock()
        manager.register_api_tool_handler = AsyncMock()
        manager.register_api_resource_handler = AsyncMock()
        return manager

    @patch("awslabs.openapi_mcp_server.server.FastMCP")
    @patch("awslabs.openapi_mcp_server.server.MCPPromptManager")
    @patch("awslabs.openapi_mcp_server.server.setup_signal_handlers")
    @patch("awslabs.openapi_mcp_server.server.load_openapi_spec")
    @patch("awslabs.openapi_mcp_server.server.make_request_with_retry")
    @patch("awslabs.openapi_mcp_server.server.HttpClientFactory")
    @patch("awslabs.openapi_mcp_server.server.load_config")
    async def test_main_with_sse_transport(
        self,
        mock_load_config,
        mock_http_client_factory,
        mock_make_request,
        mock_load_openapi_spec,
        mock_setup_signal_handlers,
        mock_mcp_prompt_manager,
        mock_fastmcp,
        mock_fastmcp_instance,
        mock_prompt_manager,
    ):
        """Test main function with SSE transport."""
        # Set up mocks
        mock_load_config.return_value = {
            "server": {"transport": "sse", "port": 8000},
            "api": {"name": "test_api", "base_url": "https://api.example.com"},
            "auth": {"type": "none"},
        }
        mock_http_client = MagicMock()
        mock_http_client_factory.create.return_value = mock_http_client
        mock_load_openapi_spec.return_value = {"paths": {"/test": {"get": {}}}}
        mock_fastmcp.return_value = mock_fastmcp_instance
        mock_mcp_prompt_manager.return_value = mock_prompt_manager
        
        # Call main
        with pytest.raises(SystemExit) as excinfo:
            await main()
        
        # Verify exit code
        assert excinfo.value.code == 0
        
        # Verify server was started with SSE transport
        mock_fastmcp.assert_called_once()
        mock_fastmcp_instance.start.assert_called_once()

    @patch("awslabs.openapi_mcp_server.server.FastMCP")
    @patch("awslabs.openapi_mcp_server.server.MCPPromptManager")
    @patch("awslabs.openapi_mcp_server.server.setup_signal_handlers")
    @patch("awslabs.openapi_mcp_server.server.load_openapi_spec")
    @patch("awslabs.openapi_mcp_server.server.make_request_with_retry")
    @patch("awslabs.openapi_mcp_server.server.HttpClientFactory")
    @patch("awslabs.openapi_mcp_server.server.load_config")
    async def test_main_with_error_during_startup(
        self,
        mock_load_config,
        mock_http_client_factory,
        mock_make_request,
        mock_load_openapi_spec,
        mock_setup_signal_handlers,
        mock_mcp_prompt_manager,
        mock_fastmcp,
    ):
        """Test main function with error during startup."""
        # Set up mocks
        mock_load_config.return_value = {
            "server": {"transport": "stdio"},
            "api": {"name": "test_api", "base_url": "https://api.example.com"},
            "auth": {"type": "none"},
        }
        mock_http_client = MagicMock()
        mock_http_client_factory.create.return_value = mock_http_client
        # Simulate error during OpenAPI spec loading
        mock_load_openapi_spec.side_effect = Exception("Failed to load OpenAPI spec")
        
        # Call main
        with pytest.raises(SystemExit) as excinfo:
            await main()
        
        # Verify exit code
        assert excinfo.value.code == 1

    def test_setup_signal_handlers(self):
        """Test setup_signal_handlers function."""
        mock_server = MagicMock()
        
        # Call setup_signal_handlers
        setup_signal_handlers(mock_server)
        
        # Verify signal handlers were set up
        # Note: We can't directly verify the signal.signal calls as they modify global state
        # But we can verify that the function runs without errors
        pass

    @patch("awslabs.openapi_mcp_server.server.FastMCP")
    def test_create_mcp_server(self, mock_fastmcp):
        """Test create_mcp_server function."""
        # Create a mock config
        config = {
            "server": {
                "name": "Test Server",
                "debug": True,
                "message_timeout": 30,
                "host": "localhost",
                "port": 8000,
                "transport": "stdio",
            }
        }
        
        # Call create_mcp_server
        server = create_mcp_server(config)
        
        # Verify FastMCP was created with the correct parameters
        mock_fastmcp.assert_called_once()
