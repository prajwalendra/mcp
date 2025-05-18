"""Tests for Cognito authentication provider."""

import base64
import json
import time
import threading
import pytest
from unittest.mock import MagicMock, patch, PropertyMock, create_autospec

from awslabs.openapi_mcp_server.api.config import Config
from awslabs.openapi_mcp_server.auth.auth_errors import (
    MissingCredentialsError,
    InvalidCredentialsError,
    ConfigurationError,
    NetworkError,
    ExpiredTokenError,
)
from awslabs.openapi_mcp_server.auth.cognito_auth import CognitoAuthProvider


class TestCognitoAuthProvider:
    """Test cases for Cognito authentication provider."""
    
    @patch('awslabs.openapi_mcp_server.auth.cognito_auth.boto3')
    def test_init_with_missing_client_id(self, mock_boto3):
        """Test initialization with missing client ID."""
        # Create a configuration without client ID
        config = Config()
        config.auth_type = 'cognito'
        config.auth_cognito_client_id = ''  # Empty client ID
        config.auth_cognito_username = 'test_username'
        config.auth_cognito_password = 'test_password'
        
        # Creating the provider should raise an exception
        with pytest.raises(MissingCredentialsError) as excinfo:
            CognitoAuthProvider(config)
        
        # Check the error message
        assert "Cognito authentication requires a client ID" in str(excinfo.value)

    @patch('awslabs.openapi_mcp_server.auth.cognito_auth.boto3')
    def test_init_with_missing_username(self, mock_boto3):
        """Test initialization with missing username."""
        # Create a configuration without username
        config = Config()
        config.auth_type = 'cognito'
        config.auth_cognito_client_id = 'test_client_id'
        config.auth_cognito_username = ''  # Empty username
        config.auth_cognito_password = 'test_password'
        
        # Creating the provider should raise an exception
        with pytest.raises(MissingCredentialsError) as excinfo:
            CognitoAuthProvider(config)
        
        # Check the error message
        assert "Cognito authentication requires a username" in str(excinfo.value)

    @patch('awslabs.openapi_mcp_server.auth.cognito_auth.boto3')
    def test_init_with_missing_password(self, mock_boto3):
        """Test initialization with missing password."""
        # Create a configuration without password
        config = Config()
        config.auth_type = 'cognito'
        config.auth_cognito_client_id = 'test_client_id'
        config.auth_cognito_username = 'test_username'
        config.auth_cognito_password = ''  # Empty password
        
        # Creating the provider should raise an exception
        with pytest.raises(MissingCredentialsError) as excinfo:
            CognitoAuthProvider(config)
        
        # Check the error message
        assert "Cognito authentication requires a password" in str(excinfo.value)

    def test_extract_token_expiry_direct(self):
        """Test token expiry extraction directly."""
        # Create a sample JWT token with an expiry claim
        # This is a mock token, not a real one
        expiry_time = int(time.time()) + 3600  # 1 hour from now
        token_payload = {
            "exp": expiry_time,
            "sub": "test-user",
            "iss": "https://cognito-idp.region.amazonaws.com/user-pool-id"
        }
        
        # Create a provider instance for testing the method directly
        provider = CognitoAuthProvider.__new__(CognitoAuthProvider)  # Create without calling __init__
        
        # Mock jwt.decode to return our payload
        with patch('awslabs.openapi_mcp_server.auth.cognito_auth.jwt.decode', return_value=token_payload):
            # Call the method directly
            result = provider._extract_token_expiry("mock_token")
            
            # Check the result
            assert result == expiry_time

    def test_extract_token_expiry_error_direct(self):
        """Test token expiry extraction with error directly."""
        # Create a provider instance for testing the method directly
        provider = CognitoAuthProvider.__new__(CognitoAuthProvider)  # Create without calling __init__
        
        # Mock jwt.decode to raise an exception
        with patch('awslabs.openapi_mcp_server.auth.cognito_auth.jwt.decode', side_effect=Exception('Invalid token')):
            # Call the method directly
            result = provider._extract_token_expiry("invalid_token")
            
            # Check that it returns a default value (1 hour from now)
            # Allow for a small time difference in the test
            assert abs(result - (int(time.time()) + 3600)) < 5

    def test_log_validation_error_direct(self):
        """Test logging of validation error directly."""
        # Create a provider instance for testing the method directly
        provider = CognitoAuthProvider.__new__(CognitoAuthProvider)  # Create without calling __init__
        
        # Mock the logger
        with patch('awslabs.openapi_mcp_server.auth.cognito_auth.logger') as mock_logger:
            # Call the method directly
            provider._log_validation_error()
            
            # Check that logger.error was called
            assert mock_logger.error.call_count >= 2
            # Check that the error messages contain the expected text
            assert any("Cognito authentication requires" in str(call) for call in mock_logger.error.call_args_list)

    def test_is_token_expired_or_expiring_soon_direct(self):
        """Test token expiry check directly."""
        # Create a provider instance for testing the method directly
        provider = CognitoAuthProvider.__new__(CognitoAuthProvider)  # Create without calling __init__
        
        # Test with token that is not expiring soon
        provider._token_expires_at = int(time.time()) + 3600  # 1 hour from now
        assert not provider._is_token_expired_or_expiring_soon()
        
        # Test with token that is expiring soon
        provider._token_expires_at = int(time.time()) + 60  # 1 minute from now
        assert provider._is_token_expired_or_expiring_soon()
        
        # Test with expired token
        provider._token_expires_at = int(time.time()) - 3600  # 1 hour ago
        assert provider._is_token_expired_or_expiring_soon()

    def test_provider_name_direct(self):
        """Test provider_name property directly."""
        # Create a provider instance for testing the property directly
        provider = CognitoAuthProvider.__new__(CognitoAuthProvider)  # Create without calling __init__
        
        # Check the property value
        assert provider.provider_name == 'cognito'

    # Test for _refresh_token method
    def test_refresh_token_method_direct(self):
        """Test the _refresh_token method."""
        # Create a provider instance for testing the method directly
        provider = CognitoAuthProvider.__new__(CognitoAuthProvider)  # Create without calling __init__
        provider._token = 'old_token'
        provider._refresh_token_value = 'test_refresh_token'
        provider._auth_headers = {'Authorization': 'Bearer old_token'}
        provider._username = 'test_username'  # Add missing attribute
        
        # Mock _refresh_cognito_token to return a new token
        with patch.object(provider, '_refresh_cognito_token', return_value='new_token'):
            # Mock _generate_auth_headers
            with patch.object(provider, '_generate_auth_headers', return_value={'Authorization': 'Bearer new_token'}):
                # Call the method
                provider._refresh_token()
                
                # Check that _refresh_cognito_token was called
                provider._refresh_cognito_token.assert_called_once()
                
                # Check that token was updated
                assert provider._token == 'new_token'
                
                # Check that auth headers were updated
                provider._generate_auth_headers.assert_called_once_with('new_token')
                assert provider._auth_headers == {'Authorization': 'Bearer new_token'}

    # Test for _refresh_token method with error
    def test_refresh_token_error_direct(self):
        """Test handling of errors in _refresh_token method."""
        # Create a provider instance for testing the method directly
        provider = CognitoAuthProvider.__new__(CognitoAuthProvider)  # Create without calling __init__
        provider._token = 'old_token'
        provider._refresh_token_value = 'test_refresh_token'
        provider._username = 'test_username'  # Add missing attribute
        
        # Mock _refresh_cognito_token to raise an exception
        with patch.object(provider, '_refresh_cognito_token', side_effect=Exception('Refresh error')):
            # Call the method, should raise ExpiredTokenError
            with pytest.raises(ExpiredTokenError) as excinfo:
                provider._refresh_token()
            
            # Check the error message
            assert "Token refresh failed" in str(excinfo.value)

    # Test for get_auth_headers with mocking of parent class method
    def test_get_auth_headers_direct(self):
        """Test get_auth_headers directly."""
        # Create a provider instance for testing the method directly
        provider = CognitoAuthProvider.__new__(CognitoAuthProvider)  # Create without calling __init__
        provider._token = 'test_token'
        provider._token_expires_at = int(time.time()) + 3600  # Expires in 1 hour
        provider._auth_headers = {'Authorization': 'Bearer test_token'}
        provider._token_lock = threading.RLock()  # Create a real lock
        provider._is_valid = True  # Add missing attribute required by parent class
        
        # Mock _is_token_expired_or_expiring_soon to return False
        with patch.object(provider, '_is_token_expired_or_expiring_soon', return_value=False):
            # Mock super().get_auth_headers to return headers directly
            with patch('awslabs.openapi_mcp_server.auth.bearer_auth.BearerAuthProvider.get_auth_headers', 
                      return_value={'Authorization': 'Bearer test_token'}):
                # Call get_auth_headers
                headers = provider.get_auth_headers()
                
                # Check the headers
                assert headers == {'Authorization': 'Bearer test_token'}

    # Test for get_auth_headers with token refresh
    def test_get_auth_headers_with_refresh_direct(self):
        """Test get_auth_headers with token refresh."""
        # Create a provider instance for testing the method directly
        provider = CognitoAuthProvider.__new__(CognitoAuthProvider)  # Create without calling __init__
        provider._token = 'old_token'
        provider._token_expires_at = int(time.time()) - 60  # Expired 1 minute ago
        provider._auth_headers = {'Authorization': 'Bearer old_token'}
        provider._token_lock = threading.RLock()  # Create a real lock
        provider._is_valid = True  # Add missing attribute required by parent class
        
        # Mock _is_token_expired_or_expiring_soon to return True
        with patch.object(provider, '_is_token_expired_or_expiring_soon', return_value=True):
            # Mock _refresh_token
            with patch.object(provider, '_refresh_token'):
                # Mock super().get_auth_headers to return headers directly
                with patch('awslabs.openapi_mcp_server.auth.bearer_auth.BearerAuthProvider.get_auth_headers', 
                          return_value={'Authorization': 'Bearer old_token'}):
                    # Call get_auth_headers
                    headers = provider.get_auth_headers()
                    
                    # Check that _refresh_token was called
                    provider._refresh_token.assert_called_once()
                    
                    # Check the headers
                    assert headers == {'Authorization': 'Bearer old_token'}

    # Add tests for boto3 client methods with proper exception handling
    @patch('awslabs.openapi_mcp_server.auth.cognito_auth.boto3')
    def test_get_cognito_token_success_direct(self, mock_boto3):
        """Test successful token acquisition directly."""
        # Create a provider instance for testing the method directly
        provider = CognitoAuthProvider.__new__(CognitoAuthProvider)  # Create without calling __init__
        provider._client_id = 'test_client_id'
        provider._username = 'test_username'
        provider._password = 'test_password'
        provider._region = 'us-east-1'
        provider._user_pool_id = None
        
        # Create a mock boto3 client
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        # Mock the exceptions attribute on the client
        mock_client.exceptions = MagicMock()
        
        # Create exception classes that inherit from Exception
        class NotAuthorizedException(Exception): pass
        class UserNotConfirmedException(Exception): pass
        class InvalidParameterException(Exception): pass
        class ResourceNotFoundException(Exception): pass
        
        # Assign the exception classes to the client.exceptions
        mock_client.exceptions.NotAuthorizedException = NotAuthorizedException
        mock_client.exceptions.UserNotConfirmedException = UserNotConfirmedException
        mock_client.exceptions.InvalidParameterException = InvalidParameterException
        mock_client.exceptions.ResourceNotFoundException = ResourceNotFoundException
        
        # Mock successful authentication response
        mock_client.initiate_auth.return_value = {
            'AuthenticationResult': {
                'AccessToken': 'test_access_token',
                'IdToken': 'test_id_token',
                'RefreshToken': 'test_refresh_token',
            }
        }
        
        # Mock token expiry extraction
        with patch.object(provider, '_extract_token_expiry', return_value=int(time.time()) + 3600):
            # Call the method directly
            result = provider._get_cognito_token()
            
            # Check the result
            assert result == 'test_access_token'
            
            # Check that initiate_auth was called with the right parameters
            mock_client.initiate_auth.assert_called_with(
                ClientId='test_client_id',
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': 'test_username',
                    'PASSWORD': 'test_password'
                }
            )

    @patch('awslabs.openapi_mcp_server.auth.cognito_auth.boto3')
    def test_get_cognito_token_with_user_pool_id_direct(self, mock_boto3):
        """Test token acquisition with user pool ID directly."""
        # Create a provider instance for testing the method directly
        provider = CognitoAuthProvider.__new__(CognitoAuthProvider)  # Create without calling __init__
        provider._client_id = 'test_client_id'
        provider._username = 'test_username'
        provider._password = 'test_password'
        provider._region = 'us-east-1'
        provider._user_pool_id = 'test_user_pool_id'
        
        # Create a mock boto3 client
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        # Mock the exceptions attribute on the client
        mock_client.exceptions = MagicMock()
        
        # Create exception classes that inherit from Exception
        class NotAuthorizedException(Exception): pass
        class UserNotConfirmedException(Exception): pass
        class InvalidParameterException(Exception): pass
        class ResourceNotFoundException(Exception): pass
        
        # Assign the exception classes to the client.exceptions
        mock_client.exceptions.NotAuthorizedException = NotAuthorizedException
        mock_client.exceptions.UserNotConfirmedException = UserNotConfirmedException
        mock_client.exceptions.InvalidParameterException = InvalidParameterException
        mock_client.exceptions.ResourceNotFoundException = ResourceNotFoundException
        
        # Mock successful authentication response
        mock_client.initiate_auth.return_value = {
            'AuthenticationResult': {
                'AccessToken': 'test_access_token',
                'IdToken': 'test_id_token',
                'RefreshToken': 'test_refresh_token',
            }
        }
        
        # Mock token expiry extraction
        with patch.object(provider, '_extract_token_expiry', return_value=int(time.time()) + 3600):
            # Call the method directly
            result = provider._get_cognito_token()
            
            # Check the result
            assert result == 'test_access_token'
            
            # Check that initiate_auth was called with the right parameters
            mock_client.initiate_auth.assert_called_with(
                ClientId='test_client_id',
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': 'test_username',
                    'PASSWORD': 'test_password',
                    'UserPoolId': 'test_user_pool_id'
                }
            )

    @patch('awslabs.openapi_mcp_server.auth.cognito_auth.boto3')
    def test_get_cognito_token_admin_fallback_direct(self, mock_boto3):
        """Test fallback to admin auth flow directly."""
        # Create a provider instance for testing the method directly
        provider = CognitoAuthProvider.__new__(CognitoAuthProvider)  # Create without calling __init__
        provider._client_id = 'test_client_id'
        provider._username = 'test_username'
        provider._password = 'test_password'
        provider._region = 'us-east-1'
        provider._user_pool_id = 'test_user_pool_id'
        
        # Create a mock boto3 client
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        # Mock the exceptions attribute on the client
        mock_client.exceptions = MagicMock()
        
        # Create exception classes that inherit from Exception
        class NotAuthorizedException(Exception): pass
        class UserNotConfirmedException(Exception): pass
        class InvalidParameterException(Exception): pass
        class ResourceNotFoundException(Exception): pass
        
        # Assign the exception classes to the client.exceptions
        mock_client.exceptions.NotAuthorizedException = NotAuthorizedException
        mock_client.exceptions.UserNotConfirmedException = UserNotConfirmedException
        mock_client.exceptions.InvalidParameterException = InvalidParameterException
        mock_client.exceptions.ResourceNotFoundException = ResourceNotFoundException
        
        # Make initiate_auth raise InvalidParameterException
        mock_client.initiate_auth.side_effect = InvalidParameterException('Invalid parameter')
        
        # Mock successful admin authentication response
        mock_client.admin_initiate_auth.return_value = {
            'AuthenticationResult': {
                'AccessToken': 'test_admin_access_token',
                'IdToken': 'test_admin_id_token',
                'RefreshToken': 'test_admin_refresh_token',
            }
        }
        
        # Mock token expiry extraction
        with patch.object(provider, '_extract_token_expiry', return_value=int(time.time()) + 3600):
            # Call the method directly
            result = provider._get_cognito_token()
            
            # Check the result
            assert result == 'test_admin_access_token'
            
            # Check that admin_initiate_auth was called with the right parameters
            mock_client.admin_initiate_auth.assert_called_with(
                UserPoolId='test_user_pool_id',
                ClientId='test_client_id',
                AuthFlow='ADMIN_USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': 'test_username',
                    'PASSWORD': 'test_password'
                }
            )

    @patch('awslabs.openapi_mcp_server.auth.cognito_auth.boto3')
    def test_get_cognito_token_not_authorized_direct(self, mock_boto3):
        """Test handling of NotAuthorizedException directly."""
        # Create a provider instance for testing the method directly
        provider = CognitoAuthProvider.__new__(CognitoAuthProvider)  # Create without calling __init__
        provider._client_id = 'test_client_id'
        provider._username = 'test_username'
        provider._password = 'test_password'
        provider._region = 'us-east-1'
        provider._user_pool_id = None
        
        # Create a mock boto3 client
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        # Mock the exceptions attribute on the client
        mock_client.exceptions = MagicMock()
        
        # Create exception classes that inherit from Exception
        class NotAuthorizedException(Exception): pass
        class UserNotConfirmedException(Exception): pass
        class InvalidParameterException(Exception): pass
        class ResourceNotFoundException(Exception): pass
        
        # Assign the exception classes to the client.exceptions
        mock_client.exceptions.NotAuthorizedException = NotAuthorizedException
        mock_client.exceptions.UserNotConfirmedException = UserNotConfirmedException
        mock_client.exceptions.InvalidParameterException = InvalidParameterException
        mock_client.exceptions.ResourceNotFoundException = ResourceNotFoundException
        
        # Make initiate_auth raise NotAuthorizedException
        mock_client.initiate_auth.side_effect = NotAuthorizedException('Not authorized')
        
        # Call the method, should raise InvalidCredentialsError
        with pytest.raises(InvalidCredentialsError) as excinfo:
            provider._get_cognito_token()
        
        # Check the error message
        assert "Invalid Cognito credentials" in str(excinfo.value)

    @patch('awslabs.openapi_mcp_server.auth.cognito_auth.boto3')
    def test_refresh_cognito_token_success_direct(self, mock_boto3):
        """Test successful token refresh directly."""
        # Create a provider instance for testing the method directly
        provider = CognitoAuthProvider.__new__(CognitoAuthProvider)  # Create without calling __init__
        provider._client_id = 'test_client_id'
        provider._username = 'test_username'
        provider._region = 'us-east-1'
        provider._user_pool_id = None
        provider._refresh_token_value = 'test_refresh_token'
        
        # Create a mock boto3 client
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        # Mock the exceptions attribute on the client
        mock_client.exceptions = MagicMock()
        
        # Create exception classes that inherit from Exception
        class NotAuthorizedException(Exception): pass
        class InvalidParameterException(Exception): pass
        
        # Assign the exception classes to the client.exceptions
        mock_client.exceptions.NotAuthorizedException = NotAuthorizedException
        mock_client.exceptions.InvalidParameterException = InvalidParameterException
        
        # Mock successful refresh response
        mock_client.initiate_auth.return_value = {
            'AuthenticationResult': {
                'AccessToken': 'new_access_token',
                'IdToken': 'new_id_token',
            }
        }
        
        # Mock token expiry extraction
        with patch.object(provider, '_extract_token_expiry', return_value=int(time.time()) + 3600):
            # Call the method directly
            result = provider._refresh_cognito_token()
            
            # Check the result
            assert result == 'new_access_token'
            
            # Check that initiate_auth was called with the right parameters
            mock_client.initiate_auth.assert_called_with(
                ClientId='test_client_id',
                AuthFlow='REFRESH_TOKEN_AUTH',
                AuthParameters={
                    'REFRESH_TOKEN': 'test_refresh_token'
                }
            )

    @patch('awslabs.openapi_mcp_server.auth.cognito_auth.boto3')
    def test_refresh_cognito_token_admin_fallback_direct(self, mock_boto3):
        """Test fallback to admin refresh flow directly."""
        # Create a provider instance for testing the method directly
        provider = CognitoAuthProvider.__new__(CognitoAuthProvider)  # Create without calling __init__
        provider._client_id = 'test_client_id'
        provider._username = 'test_username'
        provider._region = 'us-east-1'
        provider._user_pool_id = 'test_user_pool_id'
        provider._refresh_token_value = 'test_refresh_token'
        
        # Create a mock boto3 client
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        # Mock the exceptions attribute on the client
        mock_client.exceptions = MagicMock()
        
        # Create exception classes that inherit from Exception
        class NotAuthorizedException(Exception): pass
        class InvalidParameterException(Exception): pass
        
        # Assign the exception classes to the client.exceptions
        mock_client.exceptions.NotAuthorizedException = NotAuthorizedException
        mock_client.exceptions.InvalidParameterException = InvalidParameterException
        
        # Make initiate_auth raise InvalidParameterException
        mock_client.initiate_auth.side_effect = InvalidParameterException('Invalid parameter')
        
        # Mock successful admin refresh response
        mock_client.admin_initiate_auth.return_value = {
            'AuthenticationResult': {
                'AccessToken': 'new_admin_access_token',
                'IdToken': 'new_admin_id_token',
            }
        }
        
        # Mock token expiry extraction
        with patch.object(provider, '_extract_token_expiry', return_value=int(time.time()) + 3600):
            # Call the method directly
            result = provider._refresh_cognito_token()
            
            # Check the result
            assert result == 'new_admin_access_token'
            
            # Check that admin_initiate_auth was called with the right parameters
            mock_client.admin_initiate_auth.assert_called_with(
                UserPoolId='test_user_pool_id',
                ClientId='test_client_id',
                AuthFlow='REFRESH_TOKEN',
                AuthParameters={
                    'REFRESH_TOKEN': 'test_refresh_token'
                }
            )

    @patch('awslabs.openapi_mcp_server.auth.cognito_auth.boto3')
    def test_refresh_cognito_token_not_authorized_direct(self, mock_boto3):
        """Test handling of NotAuthorizedException during refresh directly."""
        # Create a provider instance for testing the method directly
        provider = CognitoAuthProvider.__new__(CognitoAuthProvider)  # Create without calling __init__
        provider._client_id = 'test_client_id'
        provider._username = 'test_username'
        provider._region = 'us-east-1'
        provider._user_pool_id = None
        provider._refresh_token_value = 'test_refresh_token'
        
        # Create a mock boto3 client
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        # Mock the exceptions attribute on the client
        mock_client.exceptions = MagicMock()
        
        # Create exception classes that inherit from Exception
        class NotAuthorizedException(Exception): pass
        class InvalidParameterException(Exception): pass
        
        # Assign the exception classes to the client.exceptions
        mock_client.exceptions.NotAuthorizedException = NotAuthorizedException
        mock_client.exceptions.InvalidParameterException = InvalidParameterException
        
        # Make initiate_auth raise NotAuthorizedException
        mock_client.initiate_auth.side_effect = NotAuthorizedException('Not authorized')
        
        # Mock _get_cognito_token to return a new token
        with patch.object(provider, '_get_cognito_token', return_value='new_token'):
            # Call the method directly
            result = provider._refresh_cognito_token()
            
            # Check that _get_cognito_token was called
            provider._get_cognito_token.assert_called_once()
            
            # Check the result
            assert result == 'new_token'

    @patch('awslabs.openapi_mcp_server.auth.cognito_auth.boto3')
    def test_refresh_cognito_token_error_direct(self, mock_boto3):
        """Test handling of generic exceptions during refresh directly."""
        # Create a provider instance for testing the method directly
        provider = CognitoAuthProvider.__new__(CognitoAuthProvider)  # Create without calling __init__
        provider._client_id = 'test_client_id'
        provider._username = 'test_username'
        provider._region = 'us-east-1'
        provider._user_pool_id = None
        provider._refresh_token_value = 'test_refresh_token'
        
        # Create a mock boto3 client
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        # Mock the exceptions attribute on the client
        mock_client.exceptions = MagicMock()
        
        # Create exception classes that inherit from Exception
        class NotAuthorizedException(Exception): pass
        class InvalidParameterException(Exception): pass
        
        # Assign the exception classes to the client.exceptions
        mock_client.exceptions.NotAuthorizedException = NotAuthorizedException
        mock_client.exceptions.InvalidParameterException = InvalidParameterException
        
        # Make initiate_auth raise a generic exception
        mock_client.initiate_auth.side_effect = Exception('Refresh error')
        
        # Call the method, should raise ExpiredTokenError
        with pytest.raises(ExpiredTokenError) as excinfo:
            provider._refresh_cognito_token()
        
        # Check the error message
        assert "Token refresh failed" in str(excinfo.value)
