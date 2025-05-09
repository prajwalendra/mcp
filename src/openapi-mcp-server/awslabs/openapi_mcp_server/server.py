"""awslabs openapi MCP Server implementation."""

import argparse
import asyncio
import signal
import sys

# Import from our modules - use direct imports from sub-modules for better patching in tests
from awslabs.openapi_mcp_server import logger, register_custom_tool
from awslabs.openapi_mcp_server.api.config import Config, load_config
from awslabs.openapi_mcp_server.api.discovery import register_discovery_tools
from awslabs.openapi_mcp_server.prompts.instructions import generate_api_instructions
from awslabs.openapi_mcp_server.utils.http_client import HttpClientFactory, make_request_with_retry
from awslabs.openapi_mcp_server.utils.metrics_provider import metrics
from awslabs.openapi_mcp_server.utils.openapi import load_openapi_spec
from awslabs.openapi_mcp_server.utils.openapi_validator import validate_openapi_spec
from fastmcp import FastMCP
from typing import Any, Dict


def create_mcp_server(config: Config) -> FastMCP:
    """Create and configure the FastMCP server.

    Args:
        config: Server configuration

    Returns:
        FastMCP: The configured FastMCP server
    """
    logger.info('Creating FastMCP server')

    # Create the FastMCP server
    server = FastMCP(
        'awslabs.openapi-mcp-server',
        instructions='This server acts as a bridge between OpenAPI specifications and LLMs, allowing models to have a better understanding of available API capabilities without requiring manual tool definitions.',
        dependencies=[
            'pydantic',
            'loguru',
            'httpx',
        ],
    )

    try:
        # Load OpenAPI spec
        if not config.api_spec_url and not config.api_spec_path:
            logger.error('No API spec URL or path provided')
            raise ValueError('Either api_spec_url or api_spec_path must be provided')

        logger.debug(
            f'Loading OpenAPI spec from URL: {config.api_spec_url} or path: {config.api_spec_path}'
        )
        openapi_spec = load_openapi_spec(url=config.api_spec_url, path=config.api_spec_path)

        # Validate the OpenAPI spec
        if not validate_openapi_spec(openapi_spec):
            logger.warning('OpenAPI specification validation failed, but continuing anyway')

        # Create a client for the API
        if not config.api_base_url:
            logger.error('No API base URL provided')
            raise ValueError('API base URL must be provided')

        # Configure authentication
        headers = {}
        auth = None
        cookies = None
        query_params = {}

        if config.auth_type == 'basic':
            if not config.auth_username or not config.auth_password:
                logger.warning('Basic authentication enabled but username or password is missing')
            else:
                import httpx

                auth = httpx.BasicAuth(
                    username=config.auth_username,
                    password=config.auth_password,
                )
                logger.info(f'Using Basic authentication for user: {config.auth_username}')

        elif config.auth_type == 'bearer':
            if not config.auth_token:
                logger.warning('Bearer authentication enabled but token is missing')
            else:
                headers['Authorization'] = f'Bearer {config.auth_token}'
                logger.info('Using Bearer token authentication')

        elif config.auth_type == 'api_key':
            if not config.auth_api_key:
                logger.warning('API key authentication enabled but API key is missing')
            else:
                if config.auth_api_key_in == 'header':
                    headers[config.auth_api_key_name] = config.auth_api_key
                    logger.info(
                        f'Using API key authentication in header: {config.auth_api_key_name}'
                    )
                elif config.auth_api_key_in == 'query':
                    query_params[config.auth_api_key_name] = config.auth_api_key
                    logger.info(
                        f'Using API key authentication in query parameter: {config.auth_api_key_name}'
                    )
                elif config.auth_api_key_in == 'cookie':
                    cookies = {config.auth_api_key_name: config.auth_api_key}
                    logger.info(
                        f'Using API key authentication in cookie: {config.auth_api_key_name}'
                    )
                else:
                    logger.warning(f'Unsupported API key location: {config.auth_api_key_in}')

        # Create the HTTP client with authentication and connection pooling
        client = HttpClientFactory.create_client(
            base_url=config.api_base_url,
            headers=headers,
            auth=auth,
            cookies=cookies,
        )
        logger.info(f'Created HTTP client for API base URL: {config.api_base_url}')

        # Create a FastMCP server from the OpenAPI specification
        server = FastMCP.from_openapi(openapi_spec=openapi_spec, client=client)
        logger.info(f'Successfully configured {config.api_name} API')

        # Register discovery tools
        register_discovery_tools(server, config.api_name, openapi_spec, config.api_base_url)
        logger.info(f'Registered discovery tools for {config.api_name} API')

        # Generate dynamic instructions
        logger.info(f'Generating instructions for API: {config.api_name}')
        asyncio.run(generate_api_instructions(server, config.api_name, openapi_spec))

        # Register health check tool
        async def health_check() -> Dict[str, Any]:
            """Check the health of the server and API.

            Returns:
                Dict[str, Any]: Health check results
            """
            api_health = True
            api_message = 'API is reachable'

            # Try to make a simple request to the API
            try:
                # Use the retry-enabled request function
                response = await make_request_with_retry(
                    client=client, method='GET', url='/', max_retries=2, retry_delay=0.5
                )
                status_code = response.status_code
                if status_code >= 400:
                    api_health = False
                    api_message = f'API returned status code {status_code}'
            except Exception as e:
                api_health = False
                api_message = f'Error connecting to API: {str(e)}'

            # Get metrics summary
            summary = metrics.get_summary()

            return {
                'server': {
                    'status': 'healthy',
                    'version': config.version,
                    'uptime': 'N/A',  # Would require tracking start time
                },
                'api': {
                    'name': config.api_name,
                    'status': 'healthy' if api_health else 'unhealthy',
                    'message': api_message,
                    'base_url': config.api_base_url,
                },
                'metrics': summary,
            }

        register_custom_tool(
            server,
            health_check,
            name='healthCheck',
            description='Check the health of the server and API',
        )

    except Exception as e:
        logger.error(f'Error setting up API: {e}')

    return server


def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown."""

    def signal_handler(sig, frame):
        logger.info(f'Received signal {sig}, shutting down...')
        # Log final metrics
        summary = metrics.get_summary()
        logger.info(f'Final metrics: {summary}')
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main():
    """Run the MCP server with CLI argument support."""
    parser = argparse.ArgumentParser(
        description='This project is a server that dynamically creates Machine Conversation Protocol (MCP) tools and resources from OpenAPI specifications. It allows Large Language Models (LLMs) to interact with APIs through the Machine Conversation Protocol.'
    )
    # Server configuration
    parser.add_argument('--sse', action='store_true', help='Use SSE transport')
    parser.add_argument('--port', type=int, help='Port to run the server on')
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Set logging level',
    )
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    # API configuration
    parser.add_argument('--api-name', help='Name of the API (default: petstore)')
    parser.add_argument('--api-url', help='Base URL of the API')
    parser.add_argument('--spec-url', help='URL of the OpenAPI specification')
    parser.add_argument('--spec-path', help='Local path to the OpenAPI specification file')

    # Authentication configuration
    parser.add_argument(
        '--auth-type',
        choices=['none', 'basic', 'bearer', 'api_key'],
        help='Authentication type to use (default: none)',
    )
    parser.add_argument('--auth-username', help='Username for basic authentication')
    parser.add_argument('--auth-password', help='Password for basic authentication')
    parser.add_argument('--auth-token', help='Token for bearer authentication')
    parser.add_argument('--auth-api-key', help='API key for API key authentication')
    parser.add_argument('--auth-api-key-name', help='Name of the API key (default: api_key)')
    parser.add_argument(
        '--auth-api-key-in',
        choices=['header', 'query', 'cookie'],
        help='Where to place the API key (default: header)',
    )

    args = parser.parse_args()

    # Set up logging with loguru at specified level
    logger.remove()
    logger.add(lambda msg: print(msg, end=''), level=args.log_level)
    logger.info(f'Starting server with logging level: {args.log_level}')

    # Set up signal handlers
    setup_signal_handlers()

    # Load configuration
    logger.debug('Loading configuration from arguments and environment')
    config = load_config(args)
    logger.debug(f'Configuration loaded: api_name={config.api_name}, transport={config.transport}')

    # Create and run the MCP server
    logger.info('Creating MCP server')
    mcp_server = create_mcp_server(config)

    # Run server with appropriate transport
    if config.transport == 'sse':
        logger.info(f'Running server with SSE transport on port {config.port}')
        mcp_server.settings.port = config.port
        mcp_server.run(transport='sse')
    else:
        logger.info('Running server with stdio transport')
        mcp_server.run()


if __name__ == '__main__':
    main()
