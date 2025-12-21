.PHONY: dev invoke invoke-dev launch ws help

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

# WebSocket client
ws:
	@if [ -z "$(prompt)" ]; then \
		echo "Error: prompt is required."; \
		echo "Usage: make ws prompt='your prompt' [session_id='session-id']"; \
		echo ""; \
		echo "Examples:"; \
		echo "  make ws prompt='Hello!'"; \
		echo "  make ws prompt='What is 5+3?' session_id='my-session-123'"; \
		exit 1; \
	fi
	@if [ -n "$(session_id)" ]; then \
		uv run python websocket_client_test.py "$(prompt)" "$(session_id)"; \
	else \
		uv run python websocket_client_test.py "$(prompt)"; \
	fi

# Show help
help:
	@echo "Available commands:"
	@echo ""
	@echo "  make dev           - Start development server"
	@echo "                       (uv run agentcore dev)"
	@echo ""
	@echo "  make invoke-dev    - Invoke agent in development mode vi HTTP"
	@echo "                       Usage: make invoke-dev prompt='your prompt'"
	@echo "                       (uv run agentcore invoke '{\"prompt\": \"...\"}' --dev)"
	@echo ""
	@echo "  make invoke        - Invoke agent in production mode vi HTTP"
	@echo "                       Usage: make invoke prompt='your prompt'"
	@echo "                       (uv run agentcore invoke '{\"prompt\": \"...\"}' )"
	@echo ""
	@echo "  make ws            - Invoke agent via WebSocket"
	@echo "                       Usage: make ws prompt='your prompt' [session_id='session-id']"
	@echo "                       Examples:"
	@echo "                         make ws prompt='Hello!'"
	@echo "                         make ws prompt='What is 5+3?' session_id='my-session'"
	@echo ""
	@echo "  make launch        - Launch agent"
	@echo "                       (uv run agentcore launch)"
	@echo ""
	@echo "  make help          - Show this help message"
	@echo ""
