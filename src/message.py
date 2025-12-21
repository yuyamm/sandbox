"""Message handling functions for Claude Agent SDK responses."""

from typing import Any

from claude_agent_sdk import (
    AssistantMessage,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)
from claude_agent_sdk.types import StreamEvent


def handle_stream_event(msg: StreamEvent) -> dict[str, Any] | None:
    """Handle StreamEvent messages and return response dict."""
    if msg.event["type"] == "content_block_start":
        return {"event": "content_block_start"}
    elif msg.event["type"] == "content_block_stop":
        return {"event": "content_block_stop"}
    elif msg.event["type"] == "content_block_delta":
        if msg.event["delta"]["type"] == "text_delta":
            text = msg.event.get("delta", {}).get("text", "")
            return {"result": text}
        elif msg.event["delta"]["type"] == "input_json_delta":
            delta = msg.event.get("delta", {})
            partial_json = delta.get("partial_json", "")
            return {"result": partial_json}
    return None


def handle_user_message(
    msg: UserMessage, tool_map: dict[str, str]
) -> list[dict[str, Any]]:
    """Handle UserMessage messages and return list of response dicts."""
    responses = []
    for block in msg.content:
        if isinstance(block, TextBlock):
            responses.append({"result": block.text})
        elif isinstance(block, ToolUseBlock):
            tool_map[block.id] = block.name
            responses.append({"result": f"{block.name} tool processing..."})
        elif isinstance(block, ToolResultBlock):
            tool_name = tool_map.get(block.tool_use_id, "Unknown")
            responses.append({"result": f"{tool_name} tool executed."})
    return responses


def handle_assistant_message(
    msg: AssistantMessage, tool_map: dict[str, str]
) -> list[dict[str, Any]]:
    """Handle AssistantMessage messages and return list of response dicts."""
    responses = []
    for block in msg.content:
        if isinstance(block, TextBlock):
            responses.append({"result": block.text})
        elif isinstance(block, ToolUseBlock):
            tool_map[block.id] = block.name
            responses.append({"result": f"{block.name} tool processing..."})
        elif isinstance(block, ToolResultBlock):
            tool_name = tool_map.get(block.tool_use_id, "Unknown")
            responses.append({"result": f"{tool_name} tool executed."})
    return responses


def handle_system_message(msg: SystemMessage) -> None:
    """Handle SystemMessage messages."""
    pass


def handle_result_message(msg: ResultMessage) -> dict[str, Any]:
    """Handle ResultMessage messages and return response dict."""
    return {"result": f"Completed. Cost: ${msg.total_cost_usd}"}
