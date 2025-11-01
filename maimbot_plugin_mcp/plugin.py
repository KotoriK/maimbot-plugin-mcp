"""
Maimbot MCP Plugin

This plugin acts as a transparent bridge between Maimbot and Model Context Protocol (MCP) servers.
It dynamically creates BaseTool wrappers for MCP tools, making them directly available to LLMs
without exposing MCP implementation details to Maimbot.
"""

import asyncio
import json
from typing import Any, List, Tuple, Type, Optional, Dict

from src.plugin_system import (
    BasePlugin,
    register_plugin,
    ComponentInfo,
    ConfigField,
)
from src.plugin_system.base.base_tool import BaseTool, ToolParamType
from src.common.logger import get_logger

# MCP imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool as MCPTool, CallToolResult, TextContent

logger = get_logger("mcp_plugin")


def _mcp_type_to_tool_param_type(mcp_type: str) -> ToolParamType:
    """Convert MCP JSON Schema type to Maimbot ToolParamType."""
    type_mapping = {
        "string": ToolParamType.STRING,
        "number": ToolParamType.NUMBER,
        "integer": ToolParamType.INTEGER,
        "boolean": ToolParamType.BOOLEAN,
        "array": ToolParamType.ARRAY,
        "object": ToolParamType.OBJECT,
    }
    return type_mapping.get(mcp_type, ToolParamType.STRING)


def _extract_mcp_tool_parameters(mcp_tool: MCPTool) -> List[Tuple[str, ToolParamType, str, bool, List[str] | None]]:
    """Extract parameters from MCP tool schema."""
    parameters = []
    
    if not mcp_tool.inputSchema or "properties" not in mcp_tool.inputSchema:
        return parameters
    
    properties = mcp_tool.inputSchema.get("properties", {})
    required_params = mcp_tool.inputSchema.get("required", [])
    
    for param_name, param_schema in properties.items():
        param_type = _mcp_type_to_tool_param_type(param_schema.get("type", "string"))
        param_description = param_schema.get("description", f"Parameter: {param_name}")
        is_required = param_name in required_params
        enum_values = param_schema.get("enum", None)
        
        parameters.append((param_name, param_type, param_description, is_required, enum_values))
    
    return parameters


def create_mcp_tool_wrapper(server_name: str, server_params: StdioServerParameters, mcp_tool: MCPTool) -> Type[BaseTool]:
    """Dynamically create a BaseTool subclass that wraps an MCP tool."""
    
    class MCPToolWrapper(BaseTool):
        """Dynamically generated wrapper for MCP tool."""
        
        name = f"mcp_{server_name}_{mcp_tool.name}"
        description = mcp_tool.description or f"Tool {mcp_tool.name} from {server_name}"
        parameters = _extract_mcp_tool_parameters(mcp_tool)
        available_for_llm = True
        
        # Store MCP-specific info
        _mcp_server_name = server_name
        _mcp_tool_name = mcp_tool.name
        _mcp_server_params = server_params
        
        async def execute(self, function_args: dict[str, Any]) -> dict[str, Any]:
            """Execute the MCP tool."""
            try:
                logger.info(f"Executing MCP tool {self._mcp_tool_name} on {self._mcp_server_name} with args: {function_args}")
                
                # Connect to MCP server and call tool
                async with stdio_client(self._mcp_server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool(self._mcp_tool_name, arguments=function_args)
                        
                        # Extract text content from result
                        content_parts = []
                        for content in result.content:
                            if isinstance(content, TextContent):
                                content_parts.append(content.text)
                        
                        combined_content = "\n".join(content_parts) if content_parts else "Tool executed successfully"
                        
                        # Return result in Maimbot tool format
                        return {"content": combined_content}
                        
            except Exception as e:
                logger.error(f"Failed to execute MCP tool {self._mcp_tool_name}: {e}")
                return {"content": f"Error executing tool: {str(e)}"}
    
    # Set a descriptive class name
    MCPToolWrapper.__name__ = f"MCPTool_{server_name}_{mcp_tool.name}"
    MCPToolWrapper.__qualname__ = MCPToolWrapper.__name__
    
    return MCPToolWrapper





@register_plugin
class MCPPlugin(BasePlugin):
    """MCP (Model Context Protocol) Bridge Plugin for Maimbot.
    
    This plugin transparently exposes MCP server tools as native Maimbot tools,
    allowing LLMs to use them directly without knowing about MCP implementation.
    """

    # Plugin basic info
    plugin_name: str = "mcp_plugin"
    enable_plugin: bool = True
    dependencies: List[str] = []
    python_dependencies: List[str] = ["mcp>=1.0.0"]
    config_file_name: str = "config.toml"

    # Config section descriptions
    config_section_descriptions = {
        "plugin": "插件基本信息",
        "mcp": "MCP服务器配置",
    }

    # Config schema
    config_schema: dict = {
        "plugin": {
            "enabled": ConfigField(type=bool, default=True, description="是否启用插件"),
            "config_version": ConfigField(type=str, default="0.2.0", description="配置文件版本"),
        },
        "mcp": {
            "servers": ConfigField(
                type=dict,
                default={},
                description="MCP服务器配置字典，格式: {name: {command: str, args: list, env: dict}}",
            ),
        },
    }
    
    def __init__(self):
        super().__init__()
        self._tool_wrappers: List[Tuple[ComponentInfo, Type[BaseTool]]] = []

    async def on_load(self) -> None:
        """Initialize plugin and discover MCP tools."""
        logger.info("MCP Plugin loading...")
        
        # Load MCP server configurations
        servers_config = self.get_config("mcp.servers", {})
        
        if not servers_config:
            logger.warning("No MCP servers configured")
            logger.info("MCP Plugin loaded with no tools")
            return
        
        # Discover tools from each MCP server
        for server_name, server_config in servers_config.items():
            try:
                logger.info(f"Discovering tools from MCP server: {server_name}")
                
                # Create server parameters
                command = server_config.get("command", "npx")
                args = server_config.get("args", [])
                env = server_config.get("env", {})
                
                server_params = StdioServerParameters(
                    command=command,
                    args=args,
                    env=env,
                )
                
                # Connect to MCP server and list tools
                async with stdio_client(server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        tools_response = await session.list_tools()
                        mcp_tools = tools_response.tools
                        
                        logger.info(f"Found {len(mcp_tools)} tools from {server_name}")
                        
                        # Create wrapper for each MCP tool
                        for mcp_tool in mcp_tools:
                            try:
                                wrapper_class = create_mcp_tool_wrapper(server_name, server_params, mcp_tool)
                                tool_info = wrapper_class.get_tool_info()
                                self._tool_wrappers.append((tool_info, wrapper_class))
                                logger.info(f"  - Registered tool: {wrapper_class.name}")
                            except Exception as e:
                                logger.error(f"Failed to create wrapper for {mcp_tool.name}: {e}")
                
            except Exception as e:
                logger.error(f"Failed to load tools from {server_name}: {e}")
                continue

        logger.info(f"MCP Plugin loaded successfully with {len(self._tool_wrappers)} tools")

    def get_plugin_components(self) -> List[Tuple[ComponentInfo, Type]]:
        """Return list of dynamically created tool components."""
        return self._tool_wrappers
