.PHONY: dev invoke invoke-dev launch help

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

# Show help
help:
	@echo "Available commands:"
	@echo ""
	@echo "  make dev           - Start development server"
	@echo "                       (uv run agentcore dev)"
	@echo ""
	@echo "  make invoke-dev    - Invoke agent in development mode"
	@echo "                       Usage: make invoke-dev prompt='your prompt'"
	@echo "                       (uv run agentcore invoke '{\"prompt\": \"...\"}' --dev)"
	@echo ""
	@echo "  make invoke        - Invoke agent in production mode"
	@echo "                       Usage: make invoke prompt='your prompt'"
	@echo "                       (uv run agentcore invoke '{\"prompt\": \"...\"}' )"
	@echo ""
	@echo "  make launch        - Launch agent"
	@echo "                       (uv run agentcore launch)"
	@echo ""
	@echo "  make help          - Show this help message"
	@echo ""
