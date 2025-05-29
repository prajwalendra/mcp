"""Extended tests for the HTTP client module."""

import httpx
from awslabs.openapi_mcp_server.utils.http_client import (
    HttpClientFactory,
)
from unittest.mock import MagicMock, patch


@patch('awslabs.openapi_mcp_server.utils.http_client.httpx.AsyncClient')
def test_http_client_factory_create_client(mock_async_client):
    """Test creating an HTTP client with default settings."""
    # Setup mock
    mock_client = MagicMock()
    mock_async_client.return_value = mock_client

    # Call the function
    client = HttpClientFactory.create_client(base_url='https://example.com')

    # Verify the result
    assert client == mock_client
    mock_async_client.assert_called_once()

    # Check that the client was created with the correct parameters
    call_args = mock_async_client.call_args[1]
    assert call_args['base_url'] == 'https://example.com'
    # The timeout is now a httpx.Timeout object, not a float
    assert isinstance(call_args['timeout'], httpx.Timeout)
    assert call_args['timeout'].connect == 30.0
    assert call_args['limits'].max_connections == 100
    assert call_args['limits'].max_keepalive_connections == 20


@patch('awslabs.openapi_mcp_server.utils.http_client.httpx.AsyncClient')
def test_http_client_factory_create_client_with_custom_settings(mock_async_client):
    """Test creating an HTTP client with custom settings."""
    # Setup mock
    mock_client = MagicMock()
    mock_async_client.return_value = mock_client

    # Custom headers, auth, and cookies
    headers = {'X-Custom-Header': 'value'}
    auth = httpx.BasicAuth(username='user', password='pass')
    cookies = {'session': '123456'}

    # Call the function
    client = HttpClientFactory.create_client(
        base_url='https://example.com', headers=headers, auth=auth, cookies=cookies, timeout=60.0
    )

    # Verify the result
    assert client == mock_client
    mock_async_client.assert_called_once()

    # Check that the client was created with the correct parameters
    call_args = mock_async_client.call_args[1]
    assert call_args['base_url'] == 'https://example.com'
    assert call_args['headers'] == headers
    assert call_args['auth'] == auth
    assert call_args['cookies'] == cookies
    # The timeout is now a httpx.Timeout object, not a float
    assert isinstance(call_args['timeout'], httpx.Timeout)
    assert call_args['timeout'].connect == 60.0
