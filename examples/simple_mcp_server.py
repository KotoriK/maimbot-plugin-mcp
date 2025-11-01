"""
Simple MCP Server Example

This is a simple example MCP server for testing the Maimbot MCP plugin.
It provides basic calculator and greeting tools.

Run with:
    python simple_mcp_server.py
    or
    uv run simple_mcp_server.py
"""

import asyncio
from mcp.server.fastmcp import FastMCP

# Create MCP server
mcp = FastMCP("Simple Calculator Server")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract b from a."""
    return a - b


@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b


@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


@mcp.tool()
def greet(name: str, style: str = "friendly") -> str:
    """
    Generate a greeting message.
    
    Args:
        name: The name to greet
        style: The greeting style (friendly, formal, casual)
    """
    styles = {
        "friendly": f"Hi {name}! How are you doing today? 😊",
        "formal": f"Good day, {name}. It's a pleasure to meet you.",
        "casual": f"Hey {name}! What's up? 👋",
    }
    return styles.get(style, styles["friendly"])


@mcp.resource("info://server")
def get_server_info() -> str:
    """Get information about this MCP server."""
    return """
    Simple Calculator Server
    
    This is a demonstration MCP server that provides:
    - Basic arithmetic operations (add, subtract, multiply, divide)
    - Greeting generator
    
    Version: 1.0.0
    """


@mcp.prompt()
def calculate_prompt(operation: str, a: int, b: int) -> str:
    """Generate a calculation prompt."""
    return f"Please perform the {operation} operation on {a} and {b}."


if __name__ == "__main__":
    # Run the server
    print("Starting Simple MCP Server...")
    print("Use this server with:")
    print('  /mcp call calculator add {"a": 5, "b": 3}')
    print('  /mcp call calculator greet {"name": "Alice", "style": "friendly"}')
    mcp.run()
