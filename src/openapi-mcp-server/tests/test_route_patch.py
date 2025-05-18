"""Unit tests for the route_patch module."""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch


# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from awslabs.openapi_mcp_server.route_patch import (
    DEBUG_LOGGING,
    ENABLE_ROUTE_PATCH,
    apply_route_patch,
    patched_determine_route_type,
)
from fastmcp.server.openapi import RouteType


class TestRoutePatch(unittest.TestCase):
    """Test the route_patch module."""

    def setUp(self):
        """Set up the test case."""
        # Create a mock route
        self.mock_route = MagicMock()
        self.mock_route.method = 'GET'
        self.mock_route.path = '/test'
        self.mock_route.parameters = []

        # Create a mock mappings list
        self.mock_mappings = []

        # Create a mock original_determine_route_type function
        self.mock_original = MagicMock()
        self.mock_original.return_value = RouteType.RESOURCE

        # Patch the original_determine_route_type function
        self.patcher = patch(
            'awslabs.openapi_mcp_server.route_patch.original_determine_route_type',
            self.mock_original,
        )
        self.patcher.start()

    def tearDown(self):
        """Tear down the test case."""
        # Stop the patcher
        self.patcher.stop()

    def test_patched_determine_route_type_with_query_params(self):
        """Test patched_determine_route_type with query parameters."""
        # Create a mock parameter with location="query"
        mock_param = MagicMock()
        mock_param.location = 'query'
        mock_param.name = 'test_param'
        self.mock_route.parameters = [mock_param]

        # Call the function
        result = patched_determine_route_type(self.mock_route, self.mock_mappings)

        # Check the result
        self.assertEqual(result, RouteType.TOOL)
        # The original function should not be called
        self.mock_original.assert_not_called()

    def test_patched_determine_route_type_without_query_params(self):
        """Test patched_determine_route_type without query parameters."""
        # Create a mock parameter with location="path"
        mock_param = MagicMock()
        mock_param.location = 'path'
        mock_param.name = 'test_param'
        self.mock_route.parameters = [mock_param]

        # Call the function
        result = patched_determine_route_type(self.mock_route, self.mock_mappings)

        # Check the result
        self.assertEqual(result, RouteType.RESOURCE)
        # The original function should be called
        self.mock_original.assert_called_once_with(self.mock_route, self.mock_mappings)

    def test_patched_determine_route_type_non_get_method(self):
        """Test patched_determine_route_type with a non-GET method."""
        # Set the method to POST
        self.mock_route.method = 'POST'

        # Create a mock parameter with location="query"
        mock_param = MagicMock()
        mock_param.location = 'query'
        mock_param.name = 'test_param'
        self.mock_route.parameters = [mock_param]

        # Call the function
        result = patched_determine_route_type(self.mock_route, self.mock_mappings)

        # Check the result
        self.assertEqual(result, RouteType.RESOURCE)
        # The original function should be called
        self.mock_original.assert_called_once_with(self.mock_route, self.mock_mappings)

    @patch('awslabs.openapi_mcp_server.route_patch.ENABLE_ROUTE_PATCH', False)
    def test_patched_determine_route_type_disabled(self):
        """Test patched_determine_route_type when disabled."""
        # Create a mock parameter with location="query"
        mock_param = MagicMock()
        mock_param.location = 'query'
        mock_param.name = 'test_param'
        self.mock_route.parameters = [mock_param]

        # Call the function
        result = patched_determine_route_type(self.mock_route, self.mock_mappings)

        # Check the result
        self.assertEqual(result, RouteType.RESOURCE)
        # The original function should be called
        self.mock_original.assert_called_once_with(self.mock_route, self.mock_mappings)

    def test_patched_determine_route_type_exception(self):
        """Test patched_determine_route_type when an exception occurs."""
        # Create a mock route that will raise an exception
        mock_route = MagicMock()
        mock_route.method = 'GET'
        mock_route.path = '/test'
        # This will raise an AttributeError when accessing parameters
        delattr(mock_route, 'parameters')

        # Call the function
        result = patched_determine_route_type(mock_route, self.mock_mappings)

        # Check the result
        self.assertEqual(result, RouteType.RESOURCE)
        # The original function should be called
        self.mock_original.assert_called_once_with(mock_route, self.mock_mappings)

    def test_patched_determine_route_type_original_returns_tool(self):
        """Test patched_determine_route_type when original returns TOOL."""
        # Set up the mock to return TOOL
        self.mock_original.return_value = RouteType.TOOL

        # Create a mock parameter with location="path"
        mock_param = MagicMock()
        mock_param.location = 'path'
        mock_param.name = 'test_param'
        self.mock_route.parameters = [mock_param]

        # Call the function
        result = patched_determine_route_type(self.mock_route, self.mock_mappings)

        # Check the result
        self.assertEqual(result, RouteType.TOOL)
        # The original function should be called
        self.mock_original.assert_called_once_with(self.mock_route, self.mock_mappings)

    def test_apply_route_patch(self):
        """Test apply_route_patch."""
        # Create a mock module
        mock_module = MagicMock()

        # Mock the logger to avoid actual logging
        with patch('awslabs.openapi_mcp_server.route_patch.logger'):
            # Call the function with debug=False and enable=True
            apply_route_patch(mock_module, enable=True, debug=False)

            # Check that the module's _determine_route_type was set to patched_determine_route_type
            self.assertEqual(mock_module._determine_route_type, patched_determine_route_type)

    def test_debug_logging(self):
        """Test debug logging functionality."""
        # Create a mock route with query parameters
        mock_route = MagicMock()
        mock_route.method = 'GET'
        mock_route.path = '/test'
        mock_param = MagicMock()
        mock_param.location = 'query'
        mock_param.name = 'test_param'
        mock_route.parameters = [mock_param]

        # Create a mock mappings list
        mock_mappings = []

        # Create a mock logger
        mock_logger = MagicMock()

        # Patch the logger and DEBUG_LOGGING
        with (
            patch('awslabs.openapi_mcp_server.route_patch.logger', mock_logger),
            patch('awslabs.openapi_mcp_server.route_patch.DEBUG_LOGGING', True),
        ):
            # Call the function
            result = patched_determine_route_type(mock_route, mock_mappings)

            # Check the result
            self.assertEqual(result, RouteType.TOOL)

            # Check that debug logs were called
            mock_logger.debug.assert_any_call('Processing route: GET /test')
            mock_logger.debug.assert_any_call(
                "Found GET operation with query parameters: ['test_param']"
            )
            mock_logger.debug.assert_any_call('Mapping GET /test to TOOL instead of RESOURCE')

    def test_apply_route_patch_with_debug(self):
        """Test apply_route_patch with debug logging."""
        # Create a mock module
        mock_module = MagicMock()

        # Create a mock logger
        mock_logger = MagicMock()

        # Patch the logger
        with patch('awslabs.openapi_mcp_server.route_patch.logger', mock_logger):
            # Call the function with debug=True
            apply_route_patch(mock_module, enable=True, debug=True)

            # Check that the module's _determine_route_type was set to patched_determine_route_type
            self.assertEqual(mock_module._determine_route_type, patched_determine_route_type)

            # Check that info logs were called
            mock_logger.info.assert_called()

            # Check that the global variables were updated
            self.assertTrue(ENABLE_ROUTE_PATCH)
            self.assertTrue(DEBUG_LOGGING)


if __name__ == '__main__':
    unittest.main()
