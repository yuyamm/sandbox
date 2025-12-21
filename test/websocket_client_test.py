"""
WebSocket client for testing AgentCore Runtime with short-lived connections.
Each message creates a new connection, but uses the same session_id for continuity.
"""

import asyncio
import json
import uuid

import websockets


class AgentClient:
    """
    AgentCore WebSocket client with session management.
    Uses short-lived connections (one message per connection).
    """

    def __init__(self, ws_url: str = "ws://localhost:8080/ws"):
        self.ws_url = ws_url
        self.session_id = str(uuid.uuid4())  # Unique session ID for conversation
        print(f"Session ID: {self.session_id}")

    async def send_message(self, prompt: str) -> list[str]:
        """
        Send a single message and receive streaming responses.
        Connection is automatically closed after receiving all responses.
        """
        responses = []

        try:
            # Create new connection for this message
            async with websockets.connect(self.ws_url) as websocket:
                # Send message with session_id for continuity
                await websocket.send(
                    json.dumps({"prompt": prompt, "session_id": self.session_id})
                )

                # Receive streaming responses
                async for message in websocket:
                    data = json.loads(message)

                    if "error" in data:
                        print(f"❌ Error: {data['error']}")
                        break

                    if "result" in data:
                        result = data["result"]
                        responses.append(result)
                        print(f"📩 {result}")

                        # Check for completion
                        if "Completed" in result:
                            break

            # Connection automatically closes here
            return responses

        except ConnectionRefusedError:
            print("❌ Connection refused. Make sure the agent is running locally.")
            print("   Run: uv run agentcore dev")
            return []
        except Exception as e:
            print(f"❌ Error: {e}")
            return []


async def test_short_lived_connections():
    """Test short-lived connection pattern with session continuity."""
    client = AgentClient()

    print("\n=== Test 1: Simple Greeting ===")
    await client.send_message("Hello! Who are you?")

    print("\n=== Test 2: Math Tool ===")
    await client.send_message("What is 15 + 27? Use the add_numbers tool.")

    print("\n=== Test 3: Conversation Continuity (Same Session) ===")
    await client.send_message("What was the result of the calculation I just asked?")

    print("\n=== Test 4: New Session (Different Client) ===")
    new_client = AgentClient()  # New session ID
    await new_client.send_message(
        "Do you know what calculation the previous user asked?"
    )

    print("\n=== All tests completed! ===")


async def interactive_mode():
    """Interactive mode for manual testing."""
    client = AgentClient()

    print("\n=== Interactive Mode ===")
    print("Type your messages (or 'quit' to exit)")
    print(f"Session ID: {client.session_id}\n")

    while True:
        try:
            prompt = input("You: ")
            if prompt.lower() in ["quit", "exit", "q"]:
                break

            if not prompt.strip():
                continue

            await client.send_message(prompt)
            print()  # Empty line for readability

        except KeyboardInterrupt:
            print("\n\nExiting...")
            break


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        asyncio.run(interactive_mode())
    else:
        asyncio.run(test_short_lived_connections())
