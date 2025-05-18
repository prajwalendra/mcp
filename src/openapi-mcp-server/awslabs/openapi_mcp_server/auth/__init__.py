"""Authentication package for OpenAPI MCP Server."""

from awslabs.openapi_mcp_server.auth.auth_provider import AuthProvider, NullAuthProvider
from awslabs.openapi_mcp_server.auth.auth_factory import get_auth_provider, is_auth_type_available

# Import register module to auto-register providers
import awslabs.openapi_mcp_server.auth.register
