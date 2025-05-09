# OpenAPI MCP Server Tests

This directory contains tests for the OpenAPI MCP Server project.

## Test Structure

The tests are organized by module:

- `tests/api/`: Tests for API-related modules
  - `test_config.py`: Tests for API configuration handling
  - `test_discovery.py`: Tests for the API discovery module

- `tests/prompts/`: Tests for prompt-related modules
  - `test_instructions.py`: Tests for dynamic instruction generation

- `tests/utils/`: Tests for utility modules
  - `test_cache_provider.py`: Tests for the cache provider module
  - `test_http_client.py`: Tests for the HTTP client utilities
  - `test_metrics_provider.py`: Tests for the metrics provider module
  - `test_openapi_validator.py`: Tests for the OpenAPI validation utilities

- `tests/test_init.py`: Tests for module initialization
- `tests/test_main.py`: Tests for the main entry point
- `tests/test_server.py`: Tests for the server creation and configuration

## Running Tests

To run the tests, use pytest:

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=awslabs

# Run specific test file
pytest tests/utils/test_cache_provider.py

# Run tests with verbose output
pytest -v
```

## Test Coverage

The tests aim to cover:

1. **Unit Tests**: Testing individual components in isolation
   - Configuration handling
   - OpenAPI spec loading and validation
   - Caching mechanisms
   - Metrics collection
   - HTTP client functionality
   - API discovery tools

2. **Integration Tests**: Testing components working together
   - Server creation and configuration
   - API mounting and tool registration
   - Authentication handling
   - Dynamic prompt generation

## Environment Variables for Testing

Some tests can be influenced by environment variables:

- `MCP_USE_CACHETOOLS=true`: Test with cachetools integration
- `MCP_USE_PROMETHEUS=true`: Test with Prometheus metrics
- `MCP_USE_TENACITY=true`: Test with tenacity retry logic
- `MCP_USE_OPENAPI_CORE=true`: Test with openapi-core validation

## Mock Strategy

The tests use mocking to isolate components:

- External HTTP requests are mocked using `httpx` mocks
- File operations are mocked using `mock_open`
- Environment variables are temporarily set and restored
- Async functions are tested using `pytest.mark.asyncio` and `AsyncMock`

## Adding New Tests

When adding new tests:

1. Follow the existing module structure
2. Use appropriate mocking to avoid external dependencies
3. Test both success and failure paths
4. Include tests for edge cases
5. Ensure tests are isolated and don't depend on external state
