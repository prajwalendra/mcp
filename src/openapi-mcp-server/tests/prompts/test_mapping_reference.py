"""Tests for the mapping_reference module."""

import pytest
from unittest.mock import MagicMock, patch
from awslabs.openapi_mcp_server.prompts.mapping_reference import (
    generate_mapping_reference,
    create_mapping_reference_prompt,
)


def test_generate_mapping_reference():
    """Test generating a mapping reference."""
    # Setup test data
    api_name = "test_api"
    paths = {
        "/items": {
            "get": {"operationId": "listItems"},
            "post": {"operationId": "createItem"}
        },
        "/items/{itemId}": {
            "get": {"operationId": "getItem"},
            "put": {"operationId": "updateItem"},
            "delete": {"operationId": "deleteItem"}
        }
    }
    operation_mappings = {
        "listItems": {
            "mapping_type": "function",
            "method": "get",
            "path": "/items",
            "parameters": []
        },
        "getItem": {
            "mapping_type": "function",
            "method": "get",
            "path": "/items/{itemId}",
            "parameters": [
                {"name": "itemId", "in": "path", "required": True}
            ]
        },
        "createItem": {
            "mapping_type": "function",
            "method": "post",
            "path": "/items",
            "parameters": []
        },
        "updateItem": {
            "mapping_type": "resource",
            "method": "put",
            "path": "/items/{itemId}",
            "resource_uri": "test_api+items+{itemId}"
        },
        "deleteItem": {
            "mapping_type": "resource",
            "method": "delete",
            "path": "/items/{itemId}",
            "resource_uri": "test_api+items+{itemId}"
        }
    }
    
    # Call the function
    result = generate_mapping_reference(
        api_name=api_name,
        paths=paths,
        operation_mappings=operation_mappings
    )
    
    # Verify the result
    assert "# test_api API Mapping Reference" in result
    
    # Check function mappings
    assert "## Function Mappings" in result
    assert "listItems" in result
    assert "getItem" in result
    assert "createItem" in result
    assert "test_api_listItems" in result
    assert "test_api_getItem" in result
    assert "test_api_createItem" in result
    
    # Check resource mappings
    assert "## Resource Mappings" in result
    assert "updateItem" in result
    assert "deleteItem" in result
    assert "test_api+items+{itemId}" in result
    
    # Check parameter mappings
    assert "## Parameter Mappings" in result
    assert "itemId" in result
    assert "path" in result
    
    # Check usage examples
    assert "## Usage Examples" in result
    assert "### Function Example" in result
    assert "### Resource Example" in result


def test_generate_mapping_reference_empty():
    """Test generating a mapping reference with empty data."""
    # Setup test data
    api_name = "test_api"
    paths = {}
    operation_mappings = {}
    
    # Call the function
    result = generate_mapping_reference(
        api_name=api_name,
        paths=paths,
        operation_mappings=operation_mappings
    )
    
    # Verify the result
    assert "# test_api API Mapping Reference" in result
    assert "## Function Mappings" in result
    assert "No function mappings found" in result
    assert "## Resource Mappings" in result
    assert "No resource mappings found" in result
    assert "## Parameter Mappings" in result
    assert "No parameter mappings found" in result
    assert "## Usage Examples" in result


def test_create_mapping_reference_prompt():
    """Test creating a mapping reference prompt."""
    # Setup test data
    server = MagicMock()
    server._prompt_manager = MagicMock()
    
    api_name = "test_api"
    paths = {
        "/items": {
            "get": {"operationId": "listItems"}
        }
    }
    operation_mappings = {
        "listItems": {
            "mapping_type": "function",
            "method": "get",
            "path": "/items",
            "parameters": []
        }
    }
    
    # Mock the generate_mapping_reference function
    with patch('awslabs.openapi_mcp_server.prompts.mapping_reference.generate_mapping_reference',
               return_value="mocked_mapping_reference"):
        with patch('awslabs.openapi_mcp_server.prompts.mapping_reference.Prompt') as mock_prompt:
            # Call the function
            create_mapping_reference_prompt(
                server=server,
                api_name=api_name,
                paths=paths,
                operation_mappings=operation_mappings
            )
            
            # Verify the result
            mock_prompt.assert_called_once_with(
                name="test_api_mapping_reference",
                content="mocked_mapping_reference",
                description="Mapping reference for the test_api API"
            )
            server._prompt_manager.add_prompt.assert_called_once()
