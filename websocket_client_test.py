"""
WebSocket client for testing AgentCore Runtime.
Simple CLI tool for sending messages to the agent.
"""

import asyncio
import json
import sys
import uuid

import websockets


async def send_message(
    prompt: str, session_id: str | None = None, ws_url: str = "ws://localhost:8080/ws"
):
    """
    Send a single message to the agent and receive streaming responses.
    Connection is automatically closed after receiving all responses.
    """
    if not session_id:
        session_id = str(uuid.uuid4())
        print(f"🆔 Session ID: {session_id}\n")

    try:
        # Create connection
        async with websockets.connect(ws_url) as websocket:
            # Send message
            await websocket.send(
                json.dumps({"prompt": prompt, "session_id": session_id})
            )

            # Receive streaming responses
            async for message in websocket:
                data = json.loads(message)

                if "error" in data:
                    print(f"❌ Error: {data['error']}")
                    break

                if "result" in data:
                    result = data["result"]
                    print(result, end="", flush=True)

                    # Check for completion
                    if "Completed" in result:
                        print()  # Final newline
                        break

    except ConnectionRefusedError:
        print("❌ Connection refused. Make sure the agent is running locally.")
        print("   Run: uv run agentcore dev")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python websocket_client_test.py 'your prompt' [session_id]")
        print("\nExamples:")
        print("  python websocket_client_test.py 'Hello!'")
        print(
            "  python websocket_client_test.py "
            "'What was my previous question?' session-123"
        )
        sys.exit(1)

    prompt = sys.argv[1]
    session_id = sys.argv[2] if len(sys.argv) > 2 else None

    asyncio.run(send_message(prompt, session_id))
