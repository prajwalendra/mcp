"""
OpenAPI MCP Server - A server that dynamically creates MCP tools and resources from OpenAPI specifications.
"""

__version__ = '0.1.0'


import sys
import inspect
from loguru import logger

# Remove default loguru handler
logger.remove()

# Set up enhanced logging format to include function name, line number, and logger name
# Fixed the whitespace issue after log level by removing padding
logger.add(
    sys.stdout,
    format='<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>',
    level='INFO',
)


def get_caller_info():
    """Get information about the caller of a function.

    Returns:
        str: A string containing information about the caller
    """
    # Get the current frame
    current_frame = inspect.currentframe()
    if not current_frame:
        return 'unknown'

    # Go up one frame
    parent_frame = current_frame.f_back
    if not parent_frame:
        return 'unknown'

    # Go up another frame to find the caller
    caller_frame = parent_frame.f_back
    if not caller_frame:
        return 'unknown'

    # Get filename, function name, and line number
    caller_info = inspect.getframeinfo(caller_frame)
    return f'{caller_info.filename}:{caller_info.function}:{caller_info.lineno}'


# Define custom tool registration function
def register_custom_tool(server, tool_func, name=None, description=None):
    """Register a custom tool with the MCP server.

    Args:
        server: The MCP server
        tool_func: The function to register as a tool
        name: Optional name for the tool (defaults to function name)
        description: Optional description for the tool
    """
    try:
        server.add_tool(
            tool_func,
            name=name or tool_func.__name__,
            description=description or tool_func.__doc__,
        )
        logger.info(f'Registered custom tool: {name or tool_func.__name__}')
        return True
    except Exception as e:
        logger.error(f'Failed to register tool {name or tool_func.__name__}: {e}')
        return False


__all__ = ['__version__', 'logger', 'get_caller_info', 'register_custom_tool']
