.PHONY: dev invoke invoke-dev launch ws ws-dev help

# Default target
.DEFAULT_GOAL := help

# Development server
dev:
	uv run agentcore dev

# Invoke agent (production)
invoke:
	@if [ -z "$(prompt)" ]; then \
		echo "Error: prompt is required."; \
		echo "Usage: make invoke prompt='your prompt' [session_id='session-id']"; \
		echo ""; \
		echo "Examples:"; \
		echo "  make invoke prompt='Hello!'"; \
		echo "  make invoke prompt='What is 5+3?' session_id='claude-session-123'"; \
		exit 1; \
	fi
	@if [ -n "$(session_id)" ]; then \
		uv run agentcore invoke '{"prompt": "$(prompt)", "session_id": "$(session_id)"}'; \
	else \
		uv run agentcore invoke '{"prompt": "$(prompt)"}'; \
	fi

# Invoke agent (development)
invoke-dev:
	@if [ -z "$(prompt)" ]; then \
		echo "Error: prompt is required."; \
		echo "Usage: make invoke-dev prompt='your prompt' [session_id='session-id']"; \
		echo ""; \
		echo "Examples:"; \
		echo "  make invoke-dev prompt='Hello!'"; \
		echo "  make invoke-dev prompt='What is 5+3?' session_id='claude-session-123'"; \
		exit 1; \
	fi
	@if [ -n "$(session_id)" ]; then \
		uv run agentcore invoke '{"prompt": "$(prompt)", "session_id": "$(session_id)"}' --dev; \
	else \
		uv run agentcore invoke '{"prompt": "$(prompt)"}' --dev; \
	fi

# Launch agent
launch:
	@if [ ! -f .env ]; then \
		echo "Error: .env file not found. Please create .env file from .env.example"; \
		exit 1; \
	fi
	@ENV_ARGS=$$(grep -v '^#' .env | grep -v '^$$' | sed 's/^/--env /'); \
	uv run agentcore launch $$ENV_ARGS

# WebSocket client (development)
ws-dev:
	@if [ -z "$(prompt)" ]; then \
		echo "Error: prompt is required."; \
		echo "Usage: make ws-dev prompt='your prompt' [session_id='session-id'] [agent_session_id='agent-session-id']"; \
		echo ""; \
		echo "Examples:"; \
		echo "  make ws-dev prompt='Hello!'"; \
		echo "  make ws-dev prompt='What is 5+3?' session_id='claude-session-123'"; \
		echo "  make ws-dev prompt='Continue' session_id='claude-123' agent_session_id='agent-456'"; \
		exit 1; \
	fi
	@uv run python websocket_client.py "$(prompt)" "$(session_id)" "$(agent_session_id)"

# WebSocket client (production)
ws:
	@if [ -z "$(prompt)" ]; then \
		echo "Error: prompt is required."; \
		echo "Usage: make ws prompt='your prompt' [session_id='session-id'] [agent_session_id='agent-session-id']"; \
		echo ""; \
		echo "Examples:"; \
		echo "  make ws prompt='Hello!'"; \
		echo "  make ws prompt='What is 5+3?' session_id='claude-session-123'"; \
		echo "  make ws prompt='Continue' session_id='claude-123' agent_session_id='agent-456'"; \
		exit 1; \
	fi; \
	runtime_arn="arn:aws:bedrock-agentcore:ap-northeast-1:585768166368:runtime/hello_agent-kzxOU1FBzD"; \
	ws_url="wss://bedrock-agentcore.ap-northeast-1.amazonaws.com/runtimes/$$runtime_arn/ws"; \
	uv run python websocket_client.py "$(prompt)" "$(session_id)" "$(agent_session_id)" "$$ws_url" "$$runtime_arn"

# Show help
help:
	@echo "Available commands:"
	@echo ""
	@echo "  make dev           - Start development server"
	@echo "                       (uv run agentcore dev)"
	@echo ""
	@echo "  make invoke-dev    - Invoke agent in development mode via HTTP"
	@echo "                       Usage: make invoke-dev prompt='your prompt' [session_id='id']"
	@echo "                       Examples:"
	@echo "                         make invoke-dev prompt='Hello!'"
	@echo "                         make invoke-dev prompt='What is 5+3?' session_id='my-session'"
	@echo ""
	@echo "  make invoke        - Invoke agent in production mode via HTTP"
	@echo "                       Usage: make invoke prompt='your prompt' [session_id='id']"
	@echo "                       Examples:"
	@echo "                         make invoke prompt='Hello!'"
	@echo "                         make invoke prompt='What is 5+3?' session_id='my-session'"
	@echo ""
	@echo "  make ws-dev        - Invoke agent development mode via WebSocket"
	@echo "                       Usage: make ws-dev prompt='your prompt' [session_id='id']"
	@echo "                       Examples:"
	@echo "                         make ws-dev prompt='Hello!'"
	@echo "                         make ws-dev prompt='What is 5+3?' session_id='my-session'"
	@echo ""
	@echo "  make ws            - Invoke agent production mode via WebSocket"
	@echo "                       Usage: make ws prompt='your prompt' [session_id='id']"
	@echo "                       (Not yet implemented - use ws-dev for now)"
	@echo ""
	@echo "  make launch        - Launch agent"
	@echo "                       (uv run agentcore launch)"
	@echo ""
	@echo "  make help          - Show this help message"
	@echo ""
