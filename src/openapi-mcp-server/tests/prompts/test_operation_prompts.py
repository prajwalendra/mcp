"""Tests for the operation_prompts module."""

import pytest
from unittest.mock import MagicMock, patch
from awslabs.openapi_mcp_server.prompts.operation_prompts import (
    generate_operation_prompt,
    _format_schema,
    create_operation_prompt,
    is_complex_operation,
    _is_complex_schema,
)


def test_generate_operation_prompt_basic():
    """Test generating a basic operation prompt."""
    # Setup test data
    api_name = "test_api"
    operation_id = "getItem"
    mapping_type = "function"
    method = "GET"
    path = "/items/{itemId}"
    summary = "Get an item by ID"
    description = "Returns a single item by its ID"
    parameters = [
        {
            "name": "itemId",
            "in": "path",
            "required": True,
            "schema": {"type": "string"}
        }
    ]
    
    # Mock the generate_usage_example function
    with patch('awslabs.openapi_mcp_server.prompts.operation_prompts.generate_usage_example',
               return_value="mocked_example"):
        
        # Call the function
        result = generate_operation_prompt(
            api_name=api_name,
            operation_id=operation_id,
            mapping_type=mapping_type,
            method=method,
            path=path,
            summary=summary,
            description=description,
            parameters=parameters
        )
        
        # Verify the result
        assert "# getItem" in result
        assert "Get an item by ID" in result
        assert "Returns a single item by its ID" in result
        assert "**HTTP Method**: GET" in result
        assert "**Path**: `/items/{itemId}`" in result
        assert "**Mapping Type**: function" in result
        assert "## Parameters" in result
        assert "### Path Parameters" in result
        assert "**itemId** (required): string" in result
        assert "Usage Example:" in result
        assert "mocked_example" in result


def test_generate_operation_prompt_with_request_body():
    """Test generating an operation prompt with a request body."""
    # Setup test data
    api_name = "test_api"
    operation_id = "createItem"
    mapping_type = "function"
    method = "POST"
    path = "/items"
    summary = "Create a new item"
    description = "Creates a new item with the provided data"
    parameters = []
    request_body = {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "price": {"type": "number"}
                    },
                    "required": ["name"]
                }
            }
        }
    }
    
    # Mock the generate_usage_example function
    with patch('awslabs.openapi_mcp_server.prompts.operation_prompts.generate_usage_example',
               return_value="mocked_example"):
        
        # Call the function
        result = generate_operation_prompt(
            api_name=api_name,
            operation_id=operation_id,
            mapping_type=mapping_type,
            method=method,
            path=path,
            summary=summary,
            description=description,
            parameters=parameters,
            request_body=request_body
        )
        
        # Verify the result
        assert "# createItem" in result
        assert "Create a new item" in result
        assert "Creates a new item with the provided data" in result
        assert "**HTTP Method**: POST" in result
        assert "**Path**: `/items`" in result
        assert "## Request Body" in result
        assert "**Required**: Yes" in result
        assert "**Content Type**: `application/json`" in result
        assert "### Schema" in result
        assert "**Type**: Object" in result
        assert "**Properties**:" in result
        assert "**name** (required): string" in result
        assert "**description**: string" in result
        assert "**price**: number" in result


def test_generate_operation_prompt_with_responses():
    """Test generating an operation prompt with responses."""
    # Setup test data
    api_name = "test_api"
    operation_id = "getItem"
    mapping_type = "function"
    method = "GET"
    path = "/items/{itemId}"
    summary = "Get an item by ID"
    description = "Returns a single item by its ID"
    parameters = [
        {
            "name": "itemId",
            "in": "path",
            "required": True,
            "schema": {"type": "string"}
        }
    ]
    responses = {
        "200": {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "price": {"type": "number"}
                        }
                    }
                }
            }
        },
        "404": {
            "description": "Item not found"
        }
    }
    
    # Mock the generate_usage_example function
    with patch('awslabs.openapi_mcp_server.prompts.operation_prompts.generate_usage_example',
               return_value="mocked_example"):
        
        # Call the function
        result = generate_operation_prompt(
            api_name=api_name,
            operation_id=operation_id,
            mapping_type=mapping_type,
            method=method,
            path=path,
            summary=summary,
            description=description,
            parameters=parameters,
            responses=responses
        )
        
        # Verify the result
        assert "# getItem" in result
        assert "## Responses" in result
        assert "### 200 - Successful response" in result
        assert "**Content Type**: `application/json`" in result
        assert "#### Schema" in result
        assert "**Type**: Object" in result
        assert "**Properties**:" in result
        assert "**id**: string" in result
        assert "**name**: string" in result
        assert "**description**: string" in result
        assert "**price**: number" in result
        assert "### 404 - Item not found" in result


def test_generate_operation_prompt_with_security():
    """Test generating an operation prompt with security requirements."""
    # Setup test data
    api_name = "test_api"
    operation_id = "getItem"
    mapping_type = "function"
    method = "GET"
    path = "/items/{itemId}"
    summary = "Get an item by ID"
    description = "Returns a single item by its ID"
    parameters = [
        {
            "name": "itemId",
            "in": "path",
            "required": True,
            "schema": {"type": "string"}
        }
    ]
    security = [
        {"api_key": []},
        {"oauth2": ["read:items"]}
    ]
    
    # Mock the generate_usage_example function
    with patch('awslabs.openapi_mcp_server.prompts.operation_prompts.generate_usage_example',
               return_value="mocked_example"):
        
        # Call the function
        result = generate_operation_prompt(
            api_name=api_name,
            operation_id=operation_id,
            mapping_type=mapping_type,
            method=method,
            path=path,
            summary=summary,
            description=description,
            parameters=parameters,
            security=security
        )
        
        # Verify the result
        assert "# getItem" in result
        assert "## Security" in result
        assert "**api_key**" in result
        assert "**oauth2**" in result
        assert "Scopes: read:items" in result


def test_format_schema_object():
    """Test formatting an object schema."""
    # Setup test data
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string", "description": "The item name"},
            "price": {"type": "number"},
            "tags": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["name"]
    }
    
    # Call the function
    result = _format_schema(schema)
    
    # Verify the result
    assert "**Type**: Object" in result
    assert "**Properties**:" in result
    assert "**id**: string" in result
    assert "**name** (required): string" in result
    assert "The item name" in result
    assert "**price**: number" in result
    assert "**tags**: array" in result
    assert "**Items Type**: string" in result


def test_format_schema_array():
    """Test formatting an array schema."""
    # Setup test data
    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"}
            }
        }
    }
    
    # Call the function
    result = _format_schema(schema)
    
    # Verify the result
    assert "**Type**: Array" in result
    assert "**Items Type**: object" in result
    assert "**Properties**:" in result
    assert "**id**: string" in result
    assert "**name**: string" in result


def test_format_schema_primitive():
    """Test formatting a primitive schema."""
    # Setup test data
    schema = {
        "type": "string",
        "format": "email",
        "enum": ["admin", "user", "guest"]
    }
    
    # Call the function
    result = _format_schema(schema)
    
    # Verify the result
    assert "**Type**: string" in result
    assert "**Format**: email" in result
    assert "**Allowed Values**: `admin`, `user`, `guest`" in result


def test_create_operation_prompt():
    """Test creating an operation prompt."""
    # Setup test data
    server = MagicMock()
    server._prompt_manager = MagicMock()
    
    api_name = "test_api"
    operation_id = "getItem"
    mapping_type = "function"
    method = "GET"
    path = "/items/{itemId}"
    summary = "Get an item by ID"
    description = "Returns a single item by its ID"
    parameters = [
        {
            "name": "itemId",
            "in": "path",
            "required": True,
            "schema": {"type": "string"}
        }
    ]
    
    # Mock the generate_operation_prompt function
    with patch('awslabs.openapi_mcp_server.prompts.operation_prompts.generate_operation_prompt',
               return_value="mocked_prompt_content"):
        with patch('awslabs.openapi_mcp_server.prompts.operation_prompts.Prompt') as mock_prompt:
            # Call the function
            create_operation_prompt(
                server=server,
                api_name=api_name,
                operation_id=operation_id,
                mapping_type=mapping_type,
                method=method,
                path=path,
                summary=summary,
                description=description,
                parameters=parameters
            )
            
            # Verify the result
            mock_prompt.assert_called_once_with(
                name="test_api_getItem",
                content="mocked_prompt_content",
                description="Documentation for getItem operation"
            )
            server._prompt_manager.add_prompt.assert_called_once()


def test_is_complex_operation():
    """Test determining if an operation is complex."""
    # Test with many parameters
    parameters = [
        {"name": "param1", "in": "path", "schema": {"type": "string"}},
        {"name": "param2", "in": "path", "schema": {"type": "string"}},
        {"name": "param3", "in": "query", "schema": {"type": "string"}}
    ]
    assert is_complex_operation(parameters) is True
    
    # Test with complex request body
    parameters = []
    request_body = {
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "address": {
                            "type": "object",
                            "properties": {
                                "street": {"type": "string"},
                                "city": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
    }
    assert is_complex_operation(parameters, request_body) is True
    
    # Test with complex response
    parameters = []
    request_body = None
    responses = {
        "200": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "name": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
    }
    assert is_complex_operation(parameters, request_body, responses) is True
    
    # Test with simple operation
    parameters = [{"name": "id", "in": "path", "schema": {"type": "string"}}]
    request_body = None
    responses = {
        "200": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "string"
                    }
                }
            }
        }
    }
    assert is_complex_operation(parameters, request_body, responses) is False


def test_is_complex_schema():
    """Test determining if a schema is complex."""
    # Test with object with many properties
    schema = {
        "type": "object",
        "properties": {
            "prop1": {"type": "string"},
            "prop2": {"type": "string"},
            "prop3": {"type": "string"},
            "prop4": {"type": "string"}
        }
    }
    assert _is_complex_schema(schema) is True
    
    # Test with nested object
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "address": {
                "type": "object",
                "properties": {
                    "street": {"type": "string"},
                    "city": {"type": "string"}
                }
            }
        }
    }
    assert _is_complex_schema(schema) is True
    
    # Test with array of objects
    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"}
            }
        }
    }
    assert _is_complex_schema(schema) is True
    
    # Test with simple object
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"}
        }
    }
    assert _is_complex_schema(schema) is False
    
    # Test with simple array
    schema = {
        "type": "array",
        "items": {
            "type": "string"
        }
    }
    assert _is_complex_schema(schema) is False
