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
    UserMessage,
)
from claude_agent_sdk.types import StreamEvent
from dotenv import load_dotenv

from src.message import (
    handle_assistant_message,
    handle_result_message,
    handle_stream_event,
    handle_system_message,
    handle_user_message,
)
from src.tools import tools_server

# Load environment variables
load_dotenv()

app = BedrockAgentCoreApp()
log = app.logger

# Verify Anthropic API key is set
if not os.getenv("ANTHROPIC_API_KEY"):
    log.warning("ANTHROPIC_API_KEY is not set. Please set it in .env file.")


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
async def invoke(event: dict[str, Any]):
    """
    HTTP entrypoint for invoking the agent with SSE streaming.
    Yields response events that are sent to client via Server-Sent Events.

    Expected event format:
        {
            "prompt": "Your message here",
            "session_id": "optional-session-id"  # For conversation continuity
        }
    """
    log.info(f"Invoke entrypoint called with event: {event}")
    log_claude_projects_files()

    prompt = event.get("prompt", event.get("inputText", ""))
    if not prompt:
        yield {"error": "No prompt or inputText provided"}
        return

    session_id = event.get("session_id")
    if session_id:
        log.info(f"Resuming session: {session_id}")
    else:
        log.info("Starting new session")

    try:
        # Configure Claude Agent SDK options (auto-approve for HTTP)
        options = ClaudeAgentOptions(
            model="claude-sonnet-4-5",
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
            mcp_servers={"tools": tools_server},
            permission_mode="acceptEdits",
            system_prompt="""
            You are a helpful assistant with various capabilities:
            - You can read, write, and edit files
            - You can run bash commands
            - You can use custom tools like add_numbers and multiply_numbers
            - You can search through files using Glob and Grep

            Always be helpful, clear, and precise in your responses.
            When using tools, explain what you're doing.
            """,
            max_turns=10,
            include_partial_messages=True,
            resume=session_id,
        )

        # Use Claude SDK Client
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)

            tool_map: dict[str, str] = {}

            # Stream response events
            async for msg in client.receive_response():
                if isinstance(msg, StreamEvent):
                    log.info("StreamEvent")
                    log.info(f"Event: {msg}")
                    response = handle_stream_event(msg)
                    if response:
                        yield response
                elif isinstance(msg, UserMessage):
                    log.info("UserMessage")
                    log.info(f"User: {msg}")
                    responses = handle_user_message(msg, tool_map)
                    for response in responses:
                        yield response
                elif isinstance(msg, AssistantMessage):
                    log.info("AssistantMessage")
                    log.info(f"Claude: {msg}")
                    responses = handle_assistant_message(msg, tool_map)
                    for response in responses:
                        yield response
                elif isinstance(msg, SystemMessage):
                    log.info("SystemMessage")
                    log.info(f"System: {msg}")
                    handle_system_message(msg)
                elif isinstance(msg, ResultMessage):
                    log.info("ResultMessage")
                    log.info(f"Result: {msg}")
                    log.info(f"Cost: {msg.total_cost_usd}")
                    yield handle_result_message(msg)
                else:
                    log.warning(f"Unexpected message type found: {type(msg)}")

    except Exception as e:
        error_msg = f"Invoke error: {str(e)}"
        log.error(error_msg)
        yield {"error": error_msg}


# @app.websocket
# async def websocket_handler(websocket, context):
#     """
#     WebSocket handler for bidirectional streaming.
#     Enables real-time, continuous conversations with interrupt support.

#     Expected message format:
#         {
#             "prompt": "Your message here",
#             "session_id": "optional-session-id"  # For conversation continuity
#         }
#     """
#     log.info(f"WebSocket connection established. Context: {context}")

#     # Log Claude projects files at the start
#     log_claude_projects_files()

#     # Accept the WebSocket connection
#     await websocket.accept()

#     # WebSocketスコープ内でcan_use_toolハンドラーを定義（クロージャ）
#     async def can_use_tool_with_approval(
#         tool_name: str,
#         input_data: dict[str, Any],
#         tool_context: Any,
#     ) -> dict[str, Any]:
#         """WebSocket経由でユーザー承認を待つツール実行ハンドラー."""

#         # websocketへはクロージャでアクセス
#         if not websocket:
#             log.warning(
#                 f"WebSocket not available for tool {tool_name},"""
#                 "auto-approving"
#             )
#             return {"behavior": "allow", "updatedInput": input_data}

#         log.info(f"Requesting permission for tool: {tool_name}")
#         await websocket.send_json(
#             {
#                 "type": "tool_permission_request",
#                 "tool_name": tool_name,
#                 "input": input_data,
#             }
#         )

#         try:
#             response = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)

#             if response.get("type") == "tool_permission_response":
#                 approved = response.get("approved", False)

#                 if approved:
#                     log.info(f"Tool {tool_name} approved by user")
#                     return {"behavior": "allow", "updatedInput": input_data}
#                 else:
#                     log.info(f"Tool {tool_name} denied by user")
#                     return {
#                         "behavior": "deny",
#                         "message": "User denied permission for this tool",
#                     }
#             else:
#                 log.warning(f"Unexpected response type: {response.get('type')}")
#                 return {"behavior": "deny", "message": "Invalid permission response"}

#         except TimeoutError:
#             log.warning(f"Tool {tool_name} permission request timed out")
#             return {
#                 "behavior": "deny",
#                 "message": "Permission request timed out (30s)",
#             }
#         except Exception as e:
#             log.error(f"Error in permission request for {tool_name}: {e}")
#             return {"behavior": "deny", "message": f"Permission error: {str(e)}"}

#     try:
#         # Receive message from client to get session_id
#         data = await websocket.receive_json()
#         log.info(f"Received WebSocket message: {data}")

#         prompt = data.get("prompt", data.get("inputText", ""))
#         if not prompt:
#             await websocket.send_json({"error": "No prompt or inputText provided"})
#             return

#         session_id = data.get("session_id")
#         if session_id:
#             log.info(f"Resuming session: {session_id}")
#         else:
#             log.info("Starting new session")

#         # Configure Claude Agent SDK options with permission system
#         options = ClaudeAgentOptions(
#             model="claude-sonnet-4-5",
#             allowed_tools=[
#                 "Read",
#                 "Write",
#                 "Bash",
#                 "Edit",
#                 "Glob",
#                 "Grep",
#                 "mcp__tools__add_numbers",
#                 "mcp__tools__multiply_numbers",
#             ],
#             mcp_servers={"tools": tools_server},
#             can_use_tool=can_use_tool_with_approval,
#             permission_mode="default",
#             system_prompt="""
#             You are a helpful assistant with various capabilities:
#             - You can read, write, and edit files
#             - You can run bash commands
#             - You can use custom tools like add_numbers and multiply_numbers
#             - You can search through files using Glob and Grep

#             Always be helpful, clear, and precise in your responses.
#             When using tools, explain what you're doing.
#             """,
#             max_turns=10,
#             include_partial_messages=True,
#             resume=session_id,
#         )

#         # Use Claude SDK Client
#         async with ClaudeSDKClient(options=options) as client:
#             # Send the user's query to Claude
#             await client.query(prompt)

#             tool_map: dict[str, str] = {}

#             # Stream the response back to client
#             async for msg in client.receive_response():
#                 if isinstance(msg, StreamEvent):
#                     log.info("StreamEvent")
#                     log.info(f"Event: {msg}")
#                     response = handle_stream_event(msg)
#                     if response:
#                         await websocket.send_json(response)
#                 elif isinstance(msg, UserMessage):
#                     log.info("UserMessage")
#                     log.info(f"User: {msg}")
#                     responses = handle_user_message(msg, tool_map)
#                     for response in responses:
#                         await websocket.send_json(response)
#                 elif isinstance(msg, AssistantMessage):
#                     log.info("AssistantMessage")
#                     log.info(f"Claude: {msg}")
#                     responses = handle_assistant_message(msg, tool_map)
#                     for response in responses:
#                         await websocket.send_json(response)
#                 elif isinstance(msg, SystemMessage):
#                     log.info("SystemMessage")
#                     log.info(f"System: {msg}")
#                     handle_system_message(msg)
#                 elif isinstance(msg, ResultMessage):
#                     log.info("ResultMessage")
#                     log.info(f"Result: {msg}")
#                     log.info(f"Cost: {msg.total_cost_usd}")
#                     await websocket.send_json(handle_result_message(msg))
#                 else:
#                     log.warning(f"Unexpected message type found: {type(msg)}")

#     except Exception as e:
#         error_msg = f"WebSocket connection error: {str(e)}"
#         log.error(error_msg)
#         try:
#             await websocket.send_json({"error": error_msg})
#         except Exception:
#             log.error("Failed to send error message to client")

#     finally:
#         log.info("Closing WebSocket connection")
#         await websocket.close()


if __name__ == "__main__":
    app.run()
