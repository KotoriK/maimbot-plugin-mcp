# MCP Plugin Architecture

This document describes the technical architecture of the Maimbot MCP Plugin.

## Overview

The MCP Plugin acts as a bridge between Maimbot and Model Context Protocol (MCP) servers, allowing Maimbot to dynamically discover and use tools from any MCP-compliant service.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         Maimbot                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                   Plugin System                        │  │
│  └───────────────────────────────────────────────────────┘  │
│                            │                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                   MCP Plugin                           │  │
│  │                                                         │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │         MCPClientManager                        │  │  │
│  │  │  - Server Configuration                         │  │  │
│  │  │  - Session Management                           │  │  │
│  │  │  - Tool Discovery                               │  │  │
│  │  │  - Tool Execution                               │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                            │                            │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │         Command Classes                         │  │  │
│  │  │  - ListMCPServersCommand                        │  │  │
│  │  │  - ListMCPToolsCommand                          │  │  │
│  │  │  - CallMCPToolCommand                           │  │  │
│  │  │  - MCPHelpCommand                               │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │ MCP Server 1 │ │ MCP Server 2 │ │ MCP Server N │
    │  (stdio)     │ │  (stdio)     │ │  (stdio)     │
    └──────────────┘ └──────────────┘ └──────────────┘
```

## Core Components

### 1. MCPClientManager

**Responsibilities:**
- Manage MCP server configurations
- Establish and maintain connections to MCP servers
- Handle tool discovery and listing
- Execute tool calls and return results
- Handle errors and timeouts

**Key Methods:**
```python
async def add_server(name: str, config: Dict[str, Any]) -> bool
async def connect_server(name: str) -> Optional[ClientSession]
async def list_tools(server_name: str) -> List[Tool]
async def call_tool(server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Optional[CallToolResult]
def get_server_list() -> List[str]
```

**Design Decisions:**
- Uses async/await for non-blocking I/O operations
- Creates sessions on-demand to minimize resource usage
- Stores server parameters for lazy initialization
- Implements comprehensive error handling

### 2. Command Classes

All command classes inherit from `BaseCommand` and implement the Maimbot plugin pattern.

#### ListMCPServersCommand
- **Pattern:** `/mcp servers`
- **Purpose:** Display all configured MCP servers
- **Output:** Numbered list of server names

#### ListMCPToolsCommand
- **Pattern:** `/mcp tools <server_name>`
- **Purpose:** List available tools from a specific server
- **Output:** Tool names and descriptions

#### CallMCPToolCommand
- **Pattern:** `/mcp call <server_name> <tool_name> [arguments_json]`
- **Purpose:** Execute a tool on an MCP server
- **Output:** Tool results (text and structured)

#### MCPHelpCommand
- **Pattern:** `/mcp help`
- **Purpose:** Display usage instructions
- **Output:** Help text with examples

### 3. Configuration System

**Configuration Structure:**
```toml
[plugin]
enabled = true
config_version = "0.1.0"

[mcp.servers]
server_name = { 
    command = "command", 
    args = ["arg1", "arg2"], 
    env = { "VAR" = "value" } 
}
```

**Features:**
- TOML-based configuration
- Flexible server definition
- Environment variable support
- Hot-reloadable (on Maimbot restart)

### 4. MCP Plugin Class

**Purpose:** Main plugin registration and lifecycle management

**Lifecycle Hooks:**
- `on_load()`: Load server configurations
- `get_plugin_components()`: Register command classes

## Data Flow

### Tool Discovery Flow

```
User -> /mcp tools server
  ↓
ListMCPToolsCommand.execute()
  ↓
MCPClientManager.list_tools(server)
  ↓
Connect to MCP server (stdio)
  ↓
ClientSession.list_tools()
  ↓
Parse and format tool list
  ↓
Display to user
```

### Tool Execution Flow

```
User -> /mcp call server tool {"args": "values"}
  ↓
CallMCPToolCommand.execute()
  ↓
Parse JSON arguments
  ↓
MCPClientManager.call_tool(server, tool, args)
  ↓
Connect to MCP server (stdio)
  ↓
ClientSession.call_tool(tool, arguments)
  ↓
Receive CallToolResult
  ↓
Extract text and structured content
  ↓
Format and display results
```

## Error Handling

The plugin implements multiple layers of error handling:

### 1. Configuration Errors
- Invalid TOML syntax
- Missing required fields
- Invalid server parameters

### 2. Connection Errors
- Server not found
- Command not available
- Connection timeout
- Process startup failure

### 3. Execution Errors
- Tool not found
- Invalid arguments
- Tool execution failure
- Response parsing errors

**Error Reporting:**
All errors are logged and user-friendly messages are displayed in Chinese.

## Transport Layer

The plugin currently supports **stdio transport** for MCP servers:

```python
StdioServerParameters(
    command="command",
    args=["arg1", "arg2"],
    env={"VAR": "value"}
)
```

**Future Extensions:**
- SSE (Server-Sent Events) transport
- Streamable HTTP transport
- WebSocket transport

## Security Considerations

### 1. Command Execution
- User-configured commands are executed as subprocesses
- No arbitrary command execution from chat
- Environment variables properly isolated

### 2. Data Validation
- JSON arguments are validated before sending
- Tool names are validated against available tools
- Server names are validated against configuration

### 3. Resource Management
- Connections are properly closed after use
- Timeouts prevent hanging connections
- Resource limits can be configured

### 4. Error Information
- Sensitive information is not exposed in errors
- Stack traces are logged but not displayed to users

## Performance Considerations

### 1. Lazy Initialization
- Servers are not connected until first use
- Minimizes startup time and resource usage

### 2. On-Demand Sessions
- Each operation creates a fresh session
- Prevents state management complexity
- Ensures clean slate for each request

### 3. Async Operations
- All I/O operations are async
- Non-blocking execution
- Better concurrency support

**Trade-offs:**
- Slightly higher latency per request (connection overhead)
- Better reliability (no persistent connection issues)
- Simpler implementation (no connection pooling needed)

## Extension Points

### 1. Custom Transport Support
Add new transport types by extending the connection logic in `MCPClientManager`:
```python
if transport == "http":
    # HTTP transport logic
elif transport == "websocket":
    # WebSocket transport logic
```

### 2. Tool Result Formatters
Add custom formatters for different content types:
```python
def format_image_result(content: ImageContent) -> str:
    # Custom image formatting
    pass
```

### 3. Additional Commands
Add new command classes following the existing pattern:
```python
class CustomMCPCommand(BaseCommand):
    command_name = "custom_mcp"
    command_pattern = r"^/mcp custom .*$"
    
    async def execute(self) -> Tuple[bool, str, bool]:
        # Implementation
        pass
```

## Testing Strategy

### 1. Unit Tests
- Test MCPClientManager methods in isolation
- Mock MCP server responses
- Validate error handling

### 2. Integration Tests
- Test with actual MCP server (simple_mcp_server.py)
- Validate end-to-end flows
- Test multiple tool types

### 3. Manual Testing
- Test in actual Maimbot environment
- Validate user interactions
- Test with various MCP servers

## Dependencies

### Core Dependencies
- `mcp>=1.0.0`: MCP Python SDK
- Standard library: `asyncio`, `json`, `typing`

### Maimbot Dependencies
- `src.plugin_system`: Plugin framework
- `src.common.logger`: Logging utilities

## Future Enhancements

### Planned Features
1. **Resource Support**: Access MCP resources, not just tools
2. **Prompt Support**: Use MCP prompts for context
3. **Caching**: Cache tool lists to reduce latency
4. **Connection Pooling**: Reuse connections for better performance
5. **Batch Operations**: Execute multiple tools in sequence
6. **Streaming Results**: Support streaming tool responses
7. **Tool Suggestions**: AI-powered tool recommendations
8. **Access Control**: User-based tool access permissions

### Compatibility
- Python 3.10+
- Maimbot Plugin System v1.x
- MCP Protocol Specification 2024-11-05

## Contributing

When contributing to the plugin:

1. **Code Style**: Follow existing patterns
2. **Error Handling**: Always handle errors gracefully
3. **Logging**: Use appropriate log levels
4. **Documentation**: Update docs for new features
5. **Testing**: Add tests for new functionality
6. **Localization**: Keep messages in Chinese

## References

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [MCP Python SDK Documentation](https://github.com/modelcontextprotocol/python-sdk)
- [Maimbot Plugin Development](https://docs.mai-mai.org/develop/plugin_develop/)
