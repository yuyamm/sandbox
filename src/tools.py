"""Custom tools for Claude Agent SDK."""

from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool


@tool("add_numbers", "Add two numbers together", {"a": int, "b": int})
async def add_numbers(args: dict[str, Any]) -> dict[str, Any]:
    """Return the sum of two numbers"""
    result = args["a"] + args["b"]
    return {
        "content": [{"type": "text", "text": f"{args['a']} + {args['b']} = {result}"}]
    }


@tool("multiply_numbers", "Multiply two numbers together", {"a": int, "b": int})
async def multiply_numbers(args: dict[str, Any]) -> dict[str, Any]:
    """Return the product of two numbers"""
    result = args["a"] * args["b"]
    return {
        "content": [{"type": "text", "text": f"{args['a']} × {args['b']} = {result}"}]
    }


# Create SDK MCP server with custom tools
tools_server = create_sdk_mcp_server(
    name="custom_tools", version="1.0.0", tools=[add_numbers, multiply_numbers]
)
