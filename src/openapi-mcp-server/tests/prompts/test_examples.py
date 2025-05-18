"""Tests for the examples module."""

import pytest
from awslabs.openapi_mcp_server.prompts.examples import (
    generate_usage_example,
    _generate_function_example,
    _generate_resource_example,
)


def test_generate_usage_example_function():
    """Test generating a function usage example."""
    # Setup test data
    api_name = "test_api"
    operation_id = "getItem"
    mapping_type = "function"
    method = "GET"
    path = "/items/{itemId}"
    parameters = [
        {
            "name": "itemId",
            "in": "path",
            "required": True,
            "schema": {"type": "string"}
        },
        {
            "name": "filter",
            "in": "query",
            "required": False,
            "schema": {"type": "string"}
        }
    ]
    
    # Call the function
    result = generate_usage_example(
        api_name=api_name,
        operation_id=operation_id,
        mapping_type=mapping_type,
        method=method,
        path=path,
        parameters=parameters
    )
    
    # Verify the result
    assert "await test_api_getItem" in result
    assert 'itemId="example_itemId"' in result
    assert 'filter="example"' in result
    assert "print(result)" in result


def test_generate_usage_example_resource():
    """Test generating a resource usage example."""
    # Setup test data
    api_name = "test_api"
    operation_id = "getItem"
    mapping_type = "resource"
    method = "GET"
    path = "/items/{itemId}"
    parameters = [
        {
            "name": "itemId",
            "in": "path",
            "required": True,
            "schema": {"type": "string"}
        }
    ]
    
    # Call the function
    result = generate_usage_example(
        api_name=api_name,
        operation_id=operation_id,
        mapping_type=mapping_type,
        method=method,
        path=path,
        parameters=parameters
    )
    
    # Verify the result
    assert "await get_resource" in result
    assert "test_api+example_itemId" in result
    assert "print(resource.id)" in result
    assert "print(resource.name)" in result


def test_generate_usage_example_unknown_mapping_type():
    """Test generating an example with an unknown mapping type."""
    # Setup test data
    api_name = "test_api"
    operation_id = "getItem"
    mapping_type = "unknown"
    method = "GET"
    path = "/items/{itemId}"
    parameters = [
        {
            "name": "itemId",
            "in": "path",
            "required": True,
            "schema": {"type": "string"}
        }
    ]
    
    # Call the function
    result = generate_usage_example(
        api_name=api_name,
        operation_id=operation_id,
        mapping_type=mapping_type,
        method=method,
        path=path,
        parameters=parameters
    )
    
    # Verify the result - should default to function example
    assert "await test_api_getItem" in result
    assert 'itemId="example_itemId"' in result
    assert "print(result)" in result


def test_generate_function_example_with_different_parameter_types():
    """Test generating a function example with different parameter types."""
    # Setup test data
    api_name = "test_api"
    operation_id = "createItem"
    path_params = [
        {
            "name": "categoryId",
            "in": "path",
            "required": True,
            "schema": {"type": "integer"}
        }
    ]
    query_params = [
        {
            "name": "name",
            "in": "query",
            "required": True,
            "schema": {"type": "string"}
        },
        {
            "name": "active",
            "in": "query",
            "required": False,
            "schema": {"type": "boolean"}
        },
        {
            "name": "tags",
            "in": "query",
            "required": False,
            "schema": {"type": "array"}
        }
    ]
    
    # Call the function
    result = _generate_function_example(
        api_name=api_name,
        operation_id=operation_id,
        path_params=path_params,
        query_params=query_params
    )
    
    # Verify the result
    assert "await test_api_createItem" in result
    assert "categoryId=123" in result  # Integer parameter
    assert 'name="example"' in result  # String parameter
    assert "active=True" in result     # Boolean parameter
    assert "tags=None" in result       # Array parameter (defaults to None)
    assert "print(result)" in result


def test_generate_resource_example_with_different_parameter_types():
    """Test generating a resource example with different parameter types."""
    # Setup test data
    api_name = "test_api"
    operation_id = "getItem"
    path_params = [
        {
            "name": "itemId",
            "in": "path",
            "required": True,
            "schema": {"type": "integer"}
        },
        {
            "name": "version",
            "in": "path",
            "required": True,
            "schema": {"type": "string"}
        },
        {
            "name": "format",
            "in": "path",
            "required": True,
            "schema": {"type": "object"}
        }
    ]
    query_params = []  # Not used in resource examples
    
    # Call the function
    result = _generate_resource_example(
        api_name=api_name,
        operation_id=operation_id,
        path_params=path_params,
        query_params=query_params
    )
    
    # Verify the result
    assert "await get_resource" in result
    assert "test_api+123+example_version+{format}" in result
    assert "print(resource.id)" in result
    assert "print(resource.name)" in result


def test_generate_resource_example_without_path_params():
    """Test generating a resource example without path parameters."""
    # Setup test data
    api_name = "test_api"
    operation_id = "listItems"
    path_params = []
    query_params = []
    
    # Call the function
    result = _generate_resource_example(
        api_name=api_name,
        operation_id=operation_id,
        path_params=path_params,
        query_params=query_params
    )
    
    # Verify the result
    assert "await get_resource" in result
    assert "test_api" in result
    assert "print(resource.id)" in result
    assert "print(resource.name)" in result
