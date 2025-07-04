"""Tests to boost coverage for cognito_auth.py."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
import httpx
import time
from datetime import datetime, timedelta

from awslabs.openapi_mcp_server.auth.cognito_auth import (
    CognitoAuthProvider,
)
from awslabs.openapi_mcp_server.api.config import Config
from awslabs.openapi_mcp_server.auth.auth_errors import (
    ConfigurationError,
    ExpiredTokenError,
    InvalidCredentialsError,
    MissingCredentialsError,
    NetworkError,
)


class TestCognitoAuthBoostCoverage:
    """Tests to boost coverage for cognito_auth.py."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config for testing."""
        config = MagicMock(spec=Config)
        config.auth_cognito_client_id = "test_client_id"
        config.auth_cognito_username = "test_username"
        config.auth_cognito_password = "test_password"
        config.auth_cognito_client_secret = "test_client_secret"
        config.auth_cognito_domain = "test-domain"
        config.auth_cognito_region = "us-east-1"
        config.auth_cognito_scopes = "scope1 scope2"
        return config

    @pytest.fixture
    def mock_boto3_client(self):
        """Create a mock boto3 client."""
        client = MagicMock()
        return client

    @patch("boto3.client")
    def test_cognito_auth_provider_init(self, mock_boto3, mock_config):
        """Test CognitoAuthProvider initialization."""
        # Set up mock boto3 client
        mock_boto3.return_value = MagicMock()
        
        # Create CognitoAuthProvider
        auth_provider = CognitoAuthProvider(mock_config)
        
        # Verify attributes were set correctly
        assert auth_provider._client_id == "test_client_id"
        assert auth_provider._username == "test_username"
        assert auth_provider._password == "test_password"
        
        # Verify boto3 client was created
        mock_boto3.assert_called_once_with(
            "cognito-idp", region_name="us-east-1"
        )

    @patch("boto3.client")
    def test_is_configured_with_username_password(self, mock_boto3, mock_config):
        """Test is_configured with username and password."""
        # Set up mock boto3 client
        mock_boto3.return_value = MagicMock()
        
        # Create CognitoAuthProvider
        auth_provider = CognitoAuthProvider(mock_config)
        
        # Verify is_configured returns True
        assert auth_provider.is_configured() is True

    @patch("boto3.client")
    def test_is_configured_with_client_credentials(self, mock_boto3, mock_config):
        """Test is_configured with client credentials."""
        # Set up mock boto3 client
        mock_boto3.return_value = MagicMock()
        
        # Modify config to remove username/password
        mock_config.auth_cognito_username = None
        mock_config.auth_cognito_password = None
        
        # Create CognitoAuthProvider
        auth_provider = CognitoAuthProvider(mock_config)
        
        # Verify is_configured returns True
        assert auth_provider.is_configured() is True

    @patch("boto3.client")
    def test_is_configured_missing_credentials(self, mock_boto3, mock_config):
        """Test is_configured with missing credentials."""
        # Set up mock boto3 client
        mock_boto3.return_value = MagicMock()
        
        # Modify config to remove all credentials
        mock_config.auth_cognito_username = None
        mock_config.auth_cognito_password = None
        mock_config.auth_cognito_client_secret = None
        
        # Create CognitoAuthProvider
        auth_provider = CognitoAuthProvider(mock_config)
        
        # Verify is_configured returns False
        assert auth_provider.is_configured() is False

    @patch("boto3.client")
    def test_get_auth_headers(self, mock_boto3, mock_config):
        """Test get_auth_headers method."""
        # Set up mock boto3 client
        mock_boto3.return_value = MagicMock()
        
        # Create CognitoAuthProvider
        auth_provider = CognitoAuthProvider(mock_config)
        
        # Set token
        auth_provider._token = "test_token"
        
        # Get auth headers
        headers = auth_provider.get_auth_headers()
        
        # Verify headers
        assert headers == {"Authorization": "Bearer test_token"}

    @patch("boto3.client")
    def test_get_auth_headers_no_token(self, mock_boto3, mock_config):
        """Test get_auth_headers method with no token."""
        # Set up mock boto3 client
        mock_boto3.return_value = MagicMock()
        mock_client = mock_boto3.return_value
        
        # Set up mock response for initiate_auth
        mock_client.initiate_auth.return_value = {
            "AuthenticationResult": {
                "AccessToken": "new_access_token",
                "IdToken": "new_id_token",
                "RefreshToken": "new_refresh_token",
                "ExpiresIn": 3600,
            }
        }
        
        # Create CognitoAuthProvider
        auth_provider = CognitoAuthProvider(mock_config)
        
        # Get auth headers
        headers = auth_provider.get_auth_headers()
        
        # Verify headers
        assert headers == {"Authorization": "Bearer new_access_token"}
        
        # Verify initiate_auth was called
        mock_client.initiate_auth.assert_called_once()

    @patch("boto3.client")
    def test_refresh_token(self, mock_boto3, mock_config):
        """Test refresh_token method."""
        # Set up mock boto3 client
        mock_boto3.return_value = MagicMock()
        mock_client = mock_boto3.return_value
        
        # Set up mock response for initiate_auth
        mock_client.initiate_auth.return_value = {
            "AuthenticationResult": {
                "AccessToken": "new_access_token",
                "IdToken": "new_id_token",
                "RefreshToken": "new_refresh_token",
                "ExpiresIn": 3600,
            }
        }
        
        # Create CognitoAuthProvider
        auth_provider = CognitoAuthProvider(mock_config)
        
        # Set expired token
        auth_provider._token = "old_token"
        auth_provider._refresh_token = "old_refresh_token"
        auth_provider._token_expiry = time.time() - 100  # Expired 100 seconds ago
        
        # Refresh token
        auth_provider.refresh_token()
        
        # Verify token was refreshed
        assert auth_provider._token == "new_access_token"
        assert auth_provider._refresh_token == "new_refresh_token"
        assert auth_provider._token_expiry > time.time()  # Expiry is in the future
