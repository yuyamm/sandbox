"""
WebSocket client for testing AgentCore Runtime.
Simple CLI tool for sending messages to the agent.
"""

import asyncio
import json
import sys
import uuid

import websockets

try:
    from bedrock_agentcore.runtime import AgentCoreRuntimeClient

    HAS_AGENTCORE = True
except ImportError:
    HAS_AGENTCORE = False


async def send_message(
    ws_url: str,
    prompt: str,
    session_id: str | None = None,
    agent_session_id: str | None = None,
    runtime_arn: str | None = None,
):
    """
    Send a single message to the agent and receive streaming responses.
    Connection is automatically closed after receiving all responses.

    Args:
        ws_url: WebSocket URL
        prompt: Message to send to the agent
        session_id: Optional Claude Agent SDK session ID for conversation continuity
        agent_session_id: Optional AgentCore Runtime session ID
        runtime_arn: Optional runtime ARN for AWS authentication
    """
    if not agent_session_id:
        agent_session_id = str(uuid.uuid4())
        print(f"🆔 Agent Session ID: {agent_session_id}\n")

    if session_id:
        print(f"🔄 Claude Session ID: {session_id}\n")

    try:
        # Check if this is an AWS connection (wss://)
        is_aws = ws_url.startswith("wss://bedrock-agentcore")

        if is_aws and runtime_arn and HAS_AGENTCORE:
            # Use AWS authentication for production
            print("🔐 Connecting with AWS SigV4 authentication...")

            # Extract region from URL
            # wss://bedrock-agentcore.ap-northeast-1.amazonaws.com/...
            import re

            region_match = re.search(
                r"bedrock-agentcore\.([^.]+)\.amazonaws\.com", ws_url
            )
            region = region_match.group(1) if region_match else "us-west-2"

            # Initialize AWS client
            client = AgentCoreRuntimeClient(region=region)

            # Generate authenticated WebSocket connection
            auth_url, headers = client.generate_ws_connection(
                runtime_arn=runtime_arn, session_id=agent_session_id
            )

            # Use authenticated URL and headers
            async with websockets.connect(
                auth_url, additional_headers=headers
            ) as websocket:
                await _handle_websocket(websocket, prompt, session_id)

        elif is_aws:
            print("❌ AWS connection requires bedrock-agentcore package")
            print("   Install: uv add bedrock-agentcore")
            return

        else:
            # Local development - no authentication needed
            async with websockets.connect(ws_url) as websocket:
                await _handle_websocket(websocket, prompt, session_id)

    except ConnectionRefusedError:
        print("❌ Connection refused. Make sure the agent is running locally.")
        print("   Run: uv run agentcore dev")
    except Exception as e:
        print(f"❌ Error: {e}")


async def _handle_websocket(websocket, prompt: str, session_id: str | None):
    """Handle WebSocket communication"""
    try:
        # Send message with optional session_id
        message = {"prompt": prompt}
        if session_id:
            message["session_id"] = session_id
        await websocket.send(json.dumps(message))

        # Receive streaming responses
        async for message in websocket:
            data = json.loads(message)

            if "error" in data:
                print(f"❌ Error: {data['error']}")
                break

            # Handle tool permission requests
            if data.get("type") == "tool_permission_request":
                tool_name = data.get("tool_name", "Unknown")
                tool_input = data.get("input", {})

                print(f"\n⚠️  Permission required for tool: {tool_name}")
                print(f"   Input: {json.dumps(tool_input, indent=2)}")

                # Ask user for approval (non-blocking async input)
                loop = asyncio.get_event_loop()
                approved = False

                while True:
                    # Run input() in thread pool to avoid blocking the event loop
                    response = await loop.run_in_executor(
                        None, lambda: input("   Approve? (y/n): ").strip().lower()
                    )
                    if response in ["y", "n"]:
                        approved = response == "y"
                        break
                    print("   Please enter 'y' or 'n'")

                # Send approval response back to agent
                await websocket.send(
                    json.dumps(
                        {"type": "tool_permission_response", "approved": approved}
                    )
                )

                if approved:
                    print("   ✅ Approved")
                else:
                    print("   ❌ Denied")

                continue

            # Handle event-based streaming messages
            if "event" in data:
                event_data = data["event"]

                if event_data == "content_block_start":
                    # Don't print anything, just mark the start
                    pass

                elif event_data == "content_block_stop":
                    # Print newline at the end of streaming
                    print()

                else:
                    # Stream data: "🔧 tool_name", "I'll use", " the multiply...", etc.
                    print(event_data, end="", flush=True)

            # Handle result content (non-streaming messages)
            if "result" in data:
                result = data["result"]
                # Always print with newline (these are discrete results)
                print(result)

                # Check for completion
                if "Completed" in result:
                    break

    except Exception as e:
        print(f"❌ WebSocket error: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python websocket_client.py <prompt> "
            "[session_id] [agent_session_id] [ws_url] [runtime_arn]"
        )
        print("\nFor local development:")
        print("  python websocket_client.py 'Hello!'")
        print("  python websocket_client.py 'Continue' 'claude-session-123'")
        print("\nFor AWS deployment:")
        print("  python websocket_client.py 'Hello!' '' '' 'wss://...' 'arn:aws:...'")
        sys.exit(1)

    prompt = sys.argv[1]
    session_id = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else None
    agent_session_id = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else None
    ws_url = (
        sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] else "ws://localhost:8080/ws"
    )
    runtime_arn = sys.argv[5] if len(sys.argv) > 5 else None

    asyncio.run(send_message(ws_url, prompt, session_id, agent_session_id, runtime_arn))
