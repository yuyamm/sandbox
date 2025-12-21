.PHONY: dev invoke invoke-dev launch ws ws-dev help

# Default target
.DEFAULT_GOAL := help

# Development server
dev:
	uv run agentcore dev

# Invoke agent (production)
invoke:
	@if [ -z "$(prompt)" ]; then \
		echo "Error: prompt is required. Usage: make invoke prompt='your prompt here'"; \
		exit 1; \
	fi
	uv run agentcore invoke '{"prompt": "$(prompt)"}'

# Invoke agent (development)
invoke-dev:
	@if [ -z "$(prompt)" ]; then \
		echo "Error: prompt is required. Usage: make invoke-dev prompt='your prompt here'"; \
		exit 1; \
	fi
	uv run agentcore invoke '{"prompt": "$(prompt)"}' --dev

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
		echo "Usage: make ws-dev prompt='your prompt' [session_id='session-id']"; \
		echo ""; \
		echo "Examples:"; \
		echo "  make ws-dev prompt='Hello!'"; \
		echo "  make ws-dev prompt='What is 5+3?' session_id='my-session-123'"; \
		exit 1; \
	fi
	@if [ -n "$(session_id)" ]; then \
		uv run python websocket_client.py "ws://localhost:8080/ws" "$(prompt)" "$(session_id)"; \
	else \
		uv run python websocket_client.py "ws://localhost:8080/ws" "$(prompt)" ""; \
	fi

# WebSocket client (production)
ws:
	@if [ -z "$(prompt)" ]; then \
		echo "Error: prompt is required."; \
		echo "Usage: make ws prompt='your prompt' [session_id='session-id']"; \
		echo ""; \
		echo "Examples:"; \
		echo "  make ws prompt='Hello!'"; \
		echo "  make ws prompt='What is 5+3?' session_id='my-session-123'"; \
		exit 1; \
	fi; \
	runtime_arn="arn:aws:bedrock-agentcore:ap-northeast-1:585768166368:runtime/hello_agent-kzxOU1FBzD"; \
	ws_url="wss://bedrock-agentcore.ap-northeast-1.amazonaws.com/runtimes/$$runtime_arn/ws"; \
	if [ -n "$(session_id)" ]; then \
		uv run python websocket_client.py "$$ws_url" "$(prompt)" "$(session_id)" "$$runtime_arn"; \
	else \
		uv run python websocket_client.py "$$ws_url" "$(prompt)" "" "$$runtime_arn"; \
	fi

# Show help
help:
	@echo "Available commands:"
	@echo ""
	@echo "  make dev           - Start development server"
	@echo "                       (uv run agentcore dev)"
	@echo ""
	@echo "  make invoke-dev    - Invoke agent in development mode via HTTP"
	@echo "                       Usage: make invoke-dev prompt='your prompt'"
	@echo "                       (uv run agentcore invoke '{\"prompt\": \"...\"}' --dev)"
	@echo ""
	@echo "  make invoke        - Invoke agent in production mode via HTTP"
	@echo "                       Usage: make invoke prompt='your prompt'"
	@echo "                       (uv run agentcore invoke '{\"prompt\": \"...\"}' )"
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
