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
    """
    Handle StreamEvent messages and return response dict.

    StreamEvent contains real-time streaming data from Claude:
    - content_block_start: Start of a content block (text or tool_use)
    - content_block_delta: Incremental content updates
    - content_block_stop: End of a content block
    """
    if msg.event["type"] == "content_block_start":
        # Check if this is a tool_use block
        content_block = msg.event.get("content_block", {})
        if content_block.get("type") == "tool_use":
            tool_name = content_block.get("name", "Unknown")
            return {"event": f"🔧 {tool_name}"}
        return {"event": "content_block_start"}

    elif msg.event["type"] == "content_block_stop":
        return {"event": "content_block_stop"}

    elif msg.event["type"] == "content_block_delta":
        if msg.event["delta"]["type"] == "text_delta":
            # Stream text content in real-time
            text = msg.event.get("delta", {}).get("text", "")
            return {"event": text}
        elif msg.event["delta"]["type"] == "input_json_delta":
            # Don't send tool argument streaming (too verbose)
            return None

    return None


def handle_user_message(
    msg: UserMessage, tool_map: dict[str, str]
) -> list[dict[str, Any]]:
    """
    Handle UserMessage messages and return list of response dicts.

    UserMessage contains tool execution results from the system.
    Only send ToolResultBlock content (tool execution results).
    """
    responses = []
    for block in msg.content:
        if isinstance(block, TextBlock):
            # Don't send - UserMessage TextBlocks are rare and not important
            pass
        elif isinstance(block, ToolUseBlock):
            # Register tool name for later reference, but don't send
            tool_map[block.id] = block.name
        elif isinstance(block, ToolResultBlock):
            # Send tool execution result
            tool_name = tool_map.get(block.tool_use_id, "Unknown")
            if block.content and len(block.content) > 0:
                result_text = block.content[0].get("text", "")
                responses.append({"result": f"✅ {tool_name}: {result_text}"})
    return responses


def handle_assistant_message(
    msg: AssistantMessage, tool_map: dict[str, str]
) -> list[dict[str, Any]]:
    """
    Handle AssistantMessage messages and return list of response dicts.

    AssistantMessage contains the final assembled content.
    Since we already streamed TextBlocks via StreamEvent, don't send them again.
    Just register ToolUseBlocks for reference.
    """
    responses = []
    for block in msg.content:
        if isinstance(block, TextBlock):
            # Don't send - already streamed via text_delta events
            pass
        elif isinstance(block, ToolUseBlock):
            # Register tool name for later reference, but don't send
            tool_map[block.id] = block.name
        elif isinstance(block, ToolResultBlock):
            # Don't send - will be handled in UserMessage
            pass
    return responses


def handle_system_message(msg: SystemMessage) -> None:
    """
    Handle SystemMessage messages.

    SystemMessage contains system-level information (init, etc).
    No need to send to client.
    """
    pass


def handle_result_message(msg: ResultMessage) -> dict[str, Any]:
    """
    Handle ResultMessage messages and return response dict.

    ResultMessage contains final summary with cost and usage information.
    """
    return {"result": f"💰 Cost: ${msg.total_cost_usd}"}
