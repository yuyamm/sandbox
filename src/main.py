import os
from pathlib import Path
from typing import Any

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
    create_sdk_mcp_server,
    tool,
)
from claude_agent_sdk.types import StreamEvent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = BedrockAgentCoreApp()
log = app.logger

# Verify Anthropic API key is set
if not os.getenv("ANTHROPIC_API_KEY"):
    log.warning("ANTHROPIC_API_KEY is not set. Please set it in .env file.")


# Define custom tools
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


def log_claude_projects_files() -> None:
    """
    Log the list of files in ~/.claude/projects/-var-task/ directory.
    """
    projects_dir = Path.home() / ".claude" / "projects" / "-var-task"

    if not projects_dir.exists():
        log.warning(f"Claude projects directory does not exist: {projects_dir}")
        return

    if not projects_dir.is_dir():
        log.warning(f"Claude projects path is not a directory: {projects_dir}")
        return

    try:
        files = list(projects_dir.iterdir())
        log.info(f"Claude projects directory: {projects_dir}")
        log.info(f"Total files/directories: {len(files)}")

        for file_path in sorted(files):
            file_type = "DIR" if file_path.is_dir() else "FILE"
            log.info(f"  [{file_type}] {file_path.name}")
    except Exception as e:
        log.error(f"Error reading Claude projects directory: {e}")


@app.entrypoint
async def invoke(payload, context):
    """
    Main entrypoint for the AgentCore Runtime.
    Uses Claude Agent SDK with Anthropic API for inference.
    """
    # Log Claude projects files at the start
    log_claude_projects_files()

    session_id = getattr(context, "session_id", "default")
    prompt = payload.get("prompt", "")

    if not prompt:
        yield "Error: No prompt provided"
        return

    log.info(f"Processing request for session: {session_id}")

    # Configure Claude Agent SDK options
    options = ClaudeAgentOptions(
        # Use Anthropic API directly
        model="claude-sonnet-4-5",
        # Enable basic tools
        allowed_tools=[
            "Read",
            "Write",
            "Bash",
            "Edit",
            "Glob",
            "Grep",
            "mcp__tools__add_numbers",
            "mcp__tools__multiply_numbers",
        ],
        # Add custom MCP tools
        mcp_servers={"tools": tools_server},
        # Auto-accept file edits for smoother interaction
        permission_mode="acceptEdits",
        # System prompt
        system_prompt="""
        You are a helpful assistant with various capabilities:
        - You can read, write, and edit files
        - You can run bash commands
        - You can use custom tools like add_numbers and multiply_numbers
        - You can search through files using Glob and Grep

        Always be helpful, clear, and precise in your responses.
        When using tools, explain what you're doing.
        """,
        # Execution limits
        max_turns=10,
        # Enable streaming for partial messages
        include_partial_messages=True,
    )

    try:
        # Use Claude SDK Client
        async with ClaudeSDKClient(options=options) as client:
            # Send the user's query
            await client.query(prompt)

            tool_map: dict[str, str] = {}

            # Stream the response
            async for msg in client.receive_response():
                log.info("")

                if isinstance(msg, UserMessage):
                    log.info("UserMessage")
                    log.info(f"User: {msg}")
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            log.info("UserMessage > TextBlock")
                            log.info(f"Text: {block.text}")
                            yield block.text
                        elif isinstance(block, ToolUseBlock):
                            tool_map[block.id] = block.name
                            yield f"{block.name} tool is proccessed..."
                        elif isinstance(block, ToolResultBlock):
                            tool_name = tool_map[block.tool_use_id]
                            yield f"{tool_name} tool was executed."
                elif isinstance(msg, AssistantMessage):
                    log.info("AssistantMessage")
                    log.info(f"Claude: {msg}")
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            log.info("AssistantMessage > TextBlock")
                            log.info(f"Text: {block.text}")
                            yield block.text
                        elif isinstance(block, ToolUseBlock):
                            tool_map[block.id] = block.name
                            yield f"{block.name} tool is proccessed..."
                        elif isinstance(block, ToolResultBlock):
                            tool_name = tool_map[block.tool_use_id]
                            yield f"{tool_name} tool was executed."
                elif isinstance(msg, SystemMessage):
                    log.info("SystemMessage")
                    log.info(f"System: {msg}")
                elif isinstance(msg, ResultMessage):
                    log.info("ResultMessage")
                    log.info(f"Result: {msg}")
                    log.info(f"Cost: {msg.total_cost_usd}")
                elif isinstance(msg, StreamEvent):
                    log.info("StreamEvent")
                    log.info(f"Event: {msg.event}")
                else:
                    log.warning(f"Unexpected message type found: {type(msg)}")

    except Exception as e:
        error_msg = f"Error processing request: {str(e)}"
        log.error(error_msg)
        yield error_msg


if __name__ == "__main__":
    app.run()
