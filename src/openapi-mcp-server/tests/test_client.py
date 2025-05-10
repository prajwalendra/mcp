#!/usr/bin/env python3
"""Test client for OpenAPI MCP Server."""

import asyncio
import logging
import sys
from typing import Any, Dict, List


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
)
logger = logging.getLogger('test_client')

# Import MCP client
try:
    from mcp.client import MCPClient  # type: ignore
except ImportError:
    logger.error('Failed to import MCPClient. Make sure MCP is installed.')
    sys.exit(1)


async def list_prompts(client: MCPClient) -> List[str]:
    """List all prompts available from the server.

    Args:
        client: The MCP client

    Returns:
        List[str]: List of prompt names
    """
    prompts = await client.list_prompts()
    logger.info(f'Found {len(prompts)} prompts')
    return prompts


async def get_prompt_content(client: MCPClient, prompt_name: str) -> Dict[str, Any]:
    """Get the content of a specific prompt.

    Args:
        client: The MCP client
        prompt_name: The name of the prompt

    Returns:
        Dict[str, Any]: The prompt content
    """
    try:
        prompt = await client.get_prompt(prompt_name)
        logger.info(f'Retrieved prompt: {prompt_name}')
        return prompt
    except Exception as e:
        logger.error(f'Failed to get prompt {prompt_name}: {e}')
        return {}


async def list_tools(client: MCPClient) -> List[Dict[str, Any]]:
    """List all tools available from the server.

    Args:
        client: The MCP client

    Returns:
        List[Dict[str, Any]]: List of tool descriptions
    """
    tools = await client.list_tools()
    logger.info(f'Found {len(tools)} tools')
    return tools


async def main() -> None:
    """Main function to test the OpenAPI MCP Server."""
    # Create MCP client
    client = MCPClient('http://localhost:8000')
    logger.info('Connected to MCP server')

    # List all prompts
    prompts = await list_prompts(client)
    logger.info('Available prompts:')
    for prompt in prompts:
        logger.info(f'- {prompt}')

    # Check for operation prompts
    operation_prompts = [p for p in prompts if p.endswith('_prompt')]
    logger.info(f'\nFound {len(operation_prompts)} operation prompts')

    # Get content of a few sample prompts
    sample_prompts = operation_prompts[:3] if len(operation_prompts) >= 3 else operation_prompts
    for prompt_name in sample_prompts:
        logger.info(f'\nContent of {prompt_name}:')
        prompt_content = await get_prompt_content(client, prompt_name)
        if prompt_content:
            messages = prompt_content.get('messages', [])
            for message in messages:
                if isinstance(message, dict) and 'content' in message:
                    logger.info(message['content'])

    # List all tools
    tools = await list_tools(client)
    logger.info('\nAvailable tools:')
    for tool in tools:
        logger.info(f'- {tool.get("name")}: {tool.get("description")}')


if __name__ == '__main__':
    asyncio.run(main())
