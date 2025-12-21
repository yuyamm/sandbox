# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **AI agent application** built with:
- **AWS Bedrock AgentCore** - Runtime framework for agent execution
- **Claude Agent SDK** - Anthropic's SDK for building autonomous agents
- **Python 3.12** - Core implementation language

The application demonstrates how to build a custom agent with tools that integrates with Claude AI through the Anthropic API.

## Development Commands

### Package Management (uv)

```bash
# Install dependencies (uses uv.lock for reproducible installs)
uv sync --all-extras --dev

# Update lock file after pyproject.toml changes
uv lock

# Upgrade dependencies to latest versions (use sparingly)
uv sync --upgrade --all-extras --dev

# Run commands in the virtual environment
uv run <command>
```

**Important**: Always use `uv sync` without `--upgrade` for regular installs to prevent unintended version changes. Only use `--upgrade` when explicitly updating dependencies.

### Code Quality

```bash
# Format code (automatically fixes style issues)
uv run ruff format .

# Lint code (with auto-fix for fixable issues)
uv run ruff check --fix .

# Type checking
uv run ty check

# Security vulnerability scanning
uv run pip-audit

# Run all pre-commit hooks
pre-commit run --all-files
```

### Running the Application

#### Local

```bash
# Launch agent
uv run agentcore dev

# Invoke agent
uv run agentcore invoke --dev '{"prompt": "Hello Agent!"}'
```

#### Public

```bash
# Invoke agent
uv run agentcore invoke '{"prompt": "Hello Agent!"}'
```

## Architecture Overview

### Core Structure

```
src/main.py               # Main entrypoint (98 lines)
├── BedrockAgentCoreApp   # AWS runtime framework
├── Custom Tools          # @tool decorated functions
├── MCP Server            # Tool registry and routing
└── ClaudeSDKClient       # Anthropic API integration
```

### Key Components

**BedrockAgentCoreApp (`app`)**
- Main application runtime provided by `bedrock-agentcore`
- Handles deployment, logging, and lifecycle management
- Entry point defined with `@app.entrypoint` decorator

**Custom Tool System**
- Tools defined with `@tool` decorator: `@tool(name, description, schema)`
- Example tools: `add_numbers`, `multiply_numbers`
- Tools must return dict with `content` array of message blocks
- Tools are async functions taking `args: dict[str, Any]`

**MCP Server**
- Created via `create_sdk_mcp_server(name, version, tools)`
- Registers custom tools for agent use
- Integrates with Claude SDK's tool system

**ClaudeSDKClient**
- Manages communication with Anthropic API
- Configured via `ClaudeAgentOptions`:
  - `model`: Model to use (e.g., "claude-sonnet-4-5")
  - `allowed_tools`: Built-in tools like Read, Write, Bash, Edit, Glob, Grep
  - `mcp_servers`: Custom tool servers
  - `permission_mode`: Controls tool execution ("acceptEdits" auto-approves file changes)
  - `system_prompt`: Agent instructions and capabilities
  - `max_turns`: Conversation turn limit
  - `include_partial_messages`: Enable streaming responses

**Streaming Response Handling**
- Agent yields responses as async generator
- Message types:
  - `AssistantMessage`: Contains text and tool use blocks
  - `ResultMessage`: Final result with cost information
  - `TextBlock`: Text content to display
  - `ToolUseBlock`: Tool invocation details

### Built-in Tools

The agent has access to these built-in tools (configured in `allowed_tools`):
- **Read**: Read file contents
- **Write**: Create or overwrite files
- **Edit**: Modify existing files
- **Bash**: Execute shell commands
- **Glob**: Find files matching patterns
- **Grep**: Search file contents

### Adding Custom Tools

To add a new tool:

1. Define the tool function in `src/main.py`:
```python
@tool("tool_name", "Description of what it does", {"param": type})
async def tool_name(args: dict[str, Any]) -> dict[str, Any]:
    # Implementation
    return {
        "content": [{"type": "text", "text": "Result"}]
    }
```

2. Add to MCP server tools list:
```python
tools_server = create_sdk_mcp_server(
    name="custom_tools",
    version="1.0.0",
    tools=[add_numbers, multiply_numbers, tool_name]  # Add here
)
```

## Configuration Files

### .env (Required)
```bash
ANTHROPIC_API_KEY=your_api_key_here  # Required: Get from console.anthropic.com
AWS_REGION=us-east-1                  # Optional: For AWS services
```

### .bedrock_agentcore.yaml
- Defines agent configuration (name, entrypoint, runtime)
- AWS deployment settings (region, account, role ARNs)
- Memory configuration (STM_AND_LTM mode)
- Agent ID: `hello_agent-kzxOU1FBzD`
- Region: `ap-northeast-1`

### ruff.toml
- Target Python: 3.12
- Line length: 88 (Black standard)
- Enabled rules: E, W, F, I, N, UP, B, C4, SIM
- Auto-fix enabled for all fixable issues
- isort configured with `sandbox` as first-party

### .pre-commit-config.yaml
Runs automatically on `git commit`:
- Trailing whitespace removal
- EOF fixer
- YAML validation
- Ruff linting and formatting
- Type checking (`ty`)
- Security scanning (`pip-audit`)

## Agent Execution Flow

1. **Invocation**: Agent receives payload with `prompt`
2. **Setup**: ClaudeSDKClient initialized with options
3. **Query**: User prompt sent via `client.query(prompt)`
4. **Streaming**: Async iteration over `client.receive_response()`
5. **Response Handling**:
   - Text blocks yielded to user
   - Tool uses logged for debugging
   - Final cost information displayed
6. **Completion**: ResultMessage indicates end of response

## Memory Management

The agent uses **STM_AND_LTM** (Short-Term and Long-Term Memory):
- Short-term: Current session context
- Long-term: Persistent across sessions
- Memory ID: `hello_agent_mem-IwM6eD5kAp`
- Event expiry: 30 days

## Development Guidelines

### Code Style
- Follow PEP 8 (enforced by Ruff)
- Use type hints for all function parameters and returns
- Line length: 88 characters
- Use double quotes for strings
- Run `uv run ruff format .` before committing

### Adding Dependencies
1. Add to `pyproject.toml` under `dependencies` or `[dependency-groups] dev`
2. Run `uv lock` to update lock file
3. Run `uv sync --all-extras --dev` to install

### Security
- Never commit `.env` file (in `.gitignore`)
- Use `pip-audit` to scan for vulnerabilities
- Keep dependencies updated with security patches
- Validate all tool inputs in custom tools

## AWS Bedrock AgentCore

### Agent Details
- **Agent ID**: `hello_agent-kzxOU1FBzD`
- **Region**: ap-northeast-1 (Tokyo)
- **Runtime**: Python 3.12, linux/arm64
- **Memory**: STM_AND_LTM with 30-day expiry
- **Network**: PUBLIC mode

### Deployment
Managed by Bedrock AgentCore SDK:
- Direct code deployment (no container)
- S3 storage for sources
- Observability enabled
- Auto-created execution role

## Common Development Workflows

### Making Changes
1. Create feature branch
2. Make code changes
3. Run `uv run ruff format .` and `uv run ruff check --fix .`
4. Run `uv run ty check` for type safety
5. Test with `uv run python src/main.py`
6. Commit (pre-commit hooks run automatically)

### Debugging
- Check logs from `app.logger` (BedrockAgentCore logger)
- Tool usage logged at INFO level
- Cost information in ResultMessage
- Use `log.info()`, `log.warning()`, `log.error()`
