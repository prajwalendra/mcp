# AWS Labs OpenAPI MCP Server

This project is a server that dynamically creates Machine Conversation Protocol (MCP) tools and resources from OpenAPI specifications. It allows Large Language Models (LLMs) to interact with APIs through the Machine Conversation Protocol.

## Features

- **Dynamic Tool Generation**: Automatically creates MCP tools from OpenAPI endpoints
- **Dynamic Prompt Generation**: Creates helpful prompts based on API structure
- **Multiple Transport Options**: Supports SSE and stdio transports
- **Flexible Configuration**: Configure via environment variables or command line arguments
- **OpenAPI Support**: Works with OpenAPI 3.x specifications in JSON or YAML format
- **Authentication Support**: Supports multiple authentication methods (Basic, Bearer Token, API Key)
- **AWS Best Practices**: Implements AWS best practices for caching, resilience, and observability
- **Comprehensive Testing**: Includes extensive unit and integration tests with high code coverage
- **Metrics Collection**: Tracks API calls, tool usage, errors, and performance metrics

## Installation

### From PyPI

```bash
pip install "awslabs.openapi-mcp-server"
```

### From Source

```bash
git clone https://github.com/awslabs/mcp.git
cd mcp/src/openapi-mcp-server
pip install -e .
```

### Using MCP Configuration

Here are some ways you can work with MCP across AWS (e.g. for Amazon Q Developer CLI MCP, `~/.aws/amazonq/mcp.json`):

```json
{
  "mcpServers": {
    "awslabs.openapi-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.openapi-mcp-server@latest"],
      "env": {
        "API_NAME": "your-api-name",
        "API_BASE_URL": "https://api.example.com",
        "API_SPEC_URL": "https://api.example.com/openapi.json",
        "LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## Usage

### Basic Usage

```bash
# Start with default settings (Petstore API)
awslabs.openapi-mcp-server
```

### Custom API

```bash
# Use a different API
awslabs.openapi-mcp-server --api-name myapi --api-url https://api.example.com --spec-url https://api.example.com/openapi.json
```

### Authenticated API

```bash
# Basic Authentication
awslabs.openapi-mcp-server --api-name myapi --api-url https://api.example.com --spec-url https://api.example.com/openapi.json --auth-type basic --auth-username YOUR_USERNAME --auth-password YOUR_PASSWORD # pragma: allowlist secret

# Bearer Token Authentication
awslabs.openapi-mcp-server --api-name myapi --api-url https://api.example.com --spec-url https://api.example.com/openapi.json --auth-type bearer --auth-token YOUR_TOKEN # pragma: allowlist secret

# API Key Authentication (in header)
awslabs.openapi-mcp-server --api-name myapi --api-url https://api.example.com --spec-url https://api.example.com/openapi.json --auth-type api_key --auth-api-key YOUR_API_KEY --auth-api-key-name X-API-Key --auth-api-key-in header # pragma: allowlist secret
```

### Local OpenAPI Specification

```bash
# Use a local OpenAPI specification file
awslabs.openapi-mcp-server --spec-path ./openapi.json
```

### YAML OpenAPI Specification

```bash
# Use a YAML OpenAPI specification file (requires pyyaml)
pip install "awslabs.openapi-mcp-server[yaml]"
awslabs.openapi-mcp-server --spec-path ./openapi.yaml
```

## Configuration

### Environment Variables

```bash
# Server configuration
export SERVER_NAME="My API Server"
export SERVER_DEBUG=true
export SERVER_MESSAGE_TIMEOUT=60
export SERVER_HOST="0.0.0.0"
export SERVER_PORT=8000
export SERVER_TRANSPORT="sse"  # Options: sse, stdio
export LOG_LEVEL="INFO"  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

# API configuration
export API_NAME="myapi"
export API_BASE_URL="https://api.example.com"
export API_SPEC_URL="https://api.example.com/openapi.json"
export API_SPEC_PATH="/path/to/local/openapi.json"  # Optional: local file path

# Authentication configuration
export AUTH_TYPE="none"  # Options: none, basic, bearer, api_key
export AUTH_USERNAME="PLACEHOLDER_USERNAME"  # For basic authentication # pragma: allowlist secret
export AUTH_PASSWORD="PLACEHOLDER_PASSWORD"  # For basic authentication # pragma: allowlist secret
export AUTH_TOKEN="PLACEHOLDER_TOKEN"  # For bearer token authentication # pragma: allowlist secret
export AUTH_API_KEY="PLACEHOLDER_API_KEY"  # For API key authentication # pragma: allowlist secret
export AUTH_API_KEY_NAME="X-API-Key"  # Name of the API key (default: api_key)
export AUTH_API_KEY_IN="header"  # Where to place the API key (options: header, query, cookie)
```

## AWS Best Practices

The OpenAPI MCP Server implements AWS best practices for building resilient, observable, and efficient cloud applications. These include:

- **Caching**: Robust caching system with multiple backend options
- **Resilience**: Patterns to handle transient failures and ensure high availability
- **Observability**: Comprehensive monitoring, metrics, and logging features

For detailed information about these features, including implementation details and configuration options, see [AWS_BEST_PRACTICES.md](AWS_BEST_PRACTICES.md).

## Docker Deployment

The project includes a Dockerfile for containerized deployment. To build and run:

```bash
# Build the Docker image
docker build -t openapi-mcp-server:latest .

# Run with default settings
docker run -p 8000:8000 openapi-mcp-server:latest

# Run with custom configuration
docker run -p 8000:8000 \
  -e API_NAME=myapi \
  -e API_BASE_URL=https://api.example.com \
  -e API_SPEC_URL=https://api.example.com/openapi.json \
  -e SERVER_TRANSPORT=sse \
  openapi-mcp-server:latest
```

For detailed information about Docker deployment, AWS service integration, and SSE transport considerations, see the [DEPLOYMENT.md](DEPLOYMENT.md) file.

## Testing

The project includes a comprehensive test suite covering unit tests, integration tests, and API functionality tests.

### Running Tests

```bash
# Install test dependencies
pip install "awslabs.openapi-mcp-server[test]"

# Run all tests
pytest

# Run tests with coverage
pytest --cov=awslabs

# Run specific test modules
pytest tests/api/
pytest tests/utils/
```

The test suite covers:

1. **API Configuration**: Tests for API configuration handling and validation
2. **API Discovery**: Tests for API endpoint discovery and tool generation
3. **Caching**: Tests for the caching system and providers
4. **HTTP Client**: Tests for the HTTP client with resilience features
5. **Metrics**: Tests for metrics collection and reporting
6. **OpenAPI Validation**: Tests for OpenAPI specification validation

For more information about the test structure and strategy, see the [tests/README.md](tests/README.md) file.

## Instructions

This server acts as a bridge between OpenAPI specifications and LLMs, allowing models to have a better understanding of available API capabilities without requiring manual tool definitions. The server creates structured MCP tools that LLMs can use to understand and interact with your API endpoints, parameters, and response formats. Point the server to your API by providing: API name, API base URL and Auth Details, OpenAPI specification URL or local file path. Set up appropriate authentication if your API requires it (Basic, Bearer Token, or API Key). Choose between SSE or stdio transport options based on your needs.
