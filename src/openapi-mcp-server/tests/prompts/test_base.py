"""Tests for the base module."""

import pytest
from unittest.mock import patch
from awslabs.openapi_mcp_server.prompts.base import (
    format_markdown_table,
    format_code_block,
    format_parameter_description,
)


def test_format_markdown_table():
    """Test formatting a markdown table."""
    # Setup test data
    headers = ["Name", "Type", "Description"]
    rows = [
        ["id", "string", "The ID of the item"],
        ["name", "string", "The name of the item"],
        ["price", "number", "The price of the item"]
    ]
    
    # Call the function
    result = format_markdown_table(headers, rows)
    
    # Verify the result
    expected = (
        "| Name | Type | Description |\n"
        "| --- | --- | --- |\n"
        "| id | string | The ID of the item |\n"
        "| name | string | The name of the item |\n"
        "| price | number | The price of the item |\n"
    )
    assert result == expected


def test_format_markdown_table_empty():
    """Test formatting an empty markdown table."""
    # Setup test data
    headers = ["Name", "Type", "Description"]
    rows = []
    
    # Call the function
    result = format_markdown_table(headers, rows)
    
    # Verify the result
    assert result == ""


def test_format_code_block():
    """Test formatting a code block."""
    # Setup test data
    code = "print('Hello, world!')"
    
    # Call the function with default language
    result = format_code_block(code)
    
    # Verify the result
    expected = "```python\nprint('Hello, world!')\n```"
    assert result == expected
    
    # Call the function with custom language
    result = format_code_block(code, language="javascript")
    
    # Verify the result
    expected = "```javascript\nprint('Hello, world!')\n```"
    assert result == expected


def test_format_parameter_description():
    """Test formatting a parameter description."""
    # Setup test data - required parameter with schema
    param = {
        "name": "itemId",
        "in": "path",
        "required": True,
        "description": "The ID of the item",
        "schema": {
            "type": "string"
        }
    }
    
    # Call the function
    result = format_parameter_description(param)
    
    # Verify the result
    assert result == "**itemId** (required): string - The ID of the item"
    
    # Test with optional parameter
    param["required"] = False
    result = format_parameter_description(param)
    assert result == "**itemId** (optional): string - The ID of the item"
    
    # Test with enum values
    param["schema"]["enum"] = ["id1", "id2", "id3"]
    result = format_parameter_description(param)
    assert "**itemId** (optional): string - The ID of the item" in result
    assert "Allowed values: `id1`, `id2`, `id3`" in result
    
    # Test with default value
    param["schema"]["default"] = "id1"
    result = format_parameter_description(param)
    assert "**itemId** (optional): string - The ID of the item" in result
    assert "Allowed values: `id1`, `id2`, `id3`" in result
    assert "Default: `id1`" in result
