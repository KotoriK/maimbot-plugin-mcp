"""
Maimbot MCP Plugin

This plugin enables Maimbot to use tools from Model Context Protocol (MCP) servers.
It acts as a bridge between Maimbot and MCP services configured by users.
"""

import asyncio
import json
from typing import Any, List, Tuple, Type, Optional, Dict

from src.plugin_system import (
    BasePlugin,
    register_plugin,
    BaseCommand,
    ComponentInfo,
    ConfigField,
)
from src.common.logger import get_logger

# MCP imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool, CallToolResult, TextContent

logger = get_logger("mcp_plugin")


class MCPClientManager:
    """Manages MCP client connections and tool execution."""

    def __init__(self):
        self.servers: Dict[str, Dict[str, Any]] = {}
        self.sessions: Dict[str, ClientSession] = {}

    async def add_server(self, name: str, config: Dict[str, Any]) -> bool:
        """
        Add an MCP server configuration.
        
        Args:
            name: Server name
            config: Server configuration with 'command' and 'args'
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.servers[name] = config
            logger.info(f"Added MCP server: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add MCP server {name}: {e}")
            return False

    async def connect_server(self, name: str) -> Optional[ClientSession]:
        """
        Connect to an MCP server.
        
        Args:
            name: Server name
            
        Returns:
            ClientSession if successful, None otherwise
        """
        if name not in self.servers:
            logger.error(f"Server {name} not found in configuration")
            return None

        if name in self.sessions:
            # Already connected
            return self.sessions[name]

        try:
            config = self.servers[name]
            command = config.get("command", "npx")
            args = config.get("args", [])
            env = config.get("env", {})

            server_params = StdioServerParameters(
                command=command,
                args=args,
                env=env,
            )

            # Note: This creates a connection context that needs to be managed
            # In a real implementation, this would need proper lifecycle management
            logger.info(f"Connecting to MCP server: {name}")
            
            # For now, we'll store the server params and create sessions on-demand
            self.servers[name]["params"] = server_params
            
            return None  # Will be handled in commands
        except Exception as e:
            logger.error(f"Failed to connect to server {name}: {e}")
            return None

    async def list_tools(self, server_name: str) -> List[Tool]:
        """
        List available tools from an MCP server.
        
        Args:
            server_name: Name of the MCP server
            
        Returns:
            List of available tools
        """
        if server_name not in self.servers:
            logger.error(f"Server {server_name} not found")
            return []

        try:
            config = self.servers[server_name]
            if "params" not in config:
                await self.connect_server(server_name)
                config = self.servers[server_name]

            server_params = config["params"]
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools_response = await session.list_tools()
                    return tools_response.tools
        except Exception as e:
            logger.error(f"Failed to list tools from {server_name}: {e}")
            return []

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Optional[CallToolResult]:
        """
        Call a tool on an MCP server.
        
        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool result if successful, None otherwise
        """
        if server_name not in self.servers:
            logger.error(f"Server {server_name} not found")
            return None

        try:
            config = self.servers[server_name]
            if "params" not in config:
                await self.connect_server(server_name)
                config = self.servers[server_name]

            server_params = config["params"]
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments=arguments)
                    return result
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name} on {server_name}: {e}")
            return None

    def get_server_list(self) -> List[str]:
        """Get list of configured server names."""
        return list(self.servers.keys())


# Global MCP client manager instance
mcp_manager = MCPClientManager()


class ListMCPServersCommand(BaseCommand):
    """List all configured MCP servers."""

    command_name = "list_mcp_servers"
    command_description = "列出所有已配置的MCP服务器"
    command_pattern = r"^/mcp servers$"

    async def execute(self) -> Tuple[bool, str, bool]:
        """List all configured MCP servers."""
        servers = mcp_manager.get_server_list()
        
        if not servers:
            message = "未配置任何MCP服务器\n使用配置文件添加MCP服务器"
            await self.send_text(message)
            return True, message, True

        message_lines = ["📋 已配置的MCP服务器:"]
        for i, server_name in enumerate(servers, 1):
            message_lines.append(f"{i}. {server_name}")

        message = "\n".join(message_lines)
        await self.send_text(message)
        return True, message, True


class ListMCPToolsCommand(BaseCommand):
    """List available tools from an MCP server."""

    command_name = "list_mcp_tools"
    command_description = "列出MCP服务器的可用工具"
    command_pattern = r"^/mcp tools\s+(.+)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        """List tools from specified MCP server."""
        import re
        match = re.match(self.command_pattern, self.message.raw_message)
        
        if not match:
            message = "用法: /mcp tools <server_name>"
            await self.send_text(message)
            return False, message, False

        server_name = match.group(1).strip()
        
        await self.send_text(f"正在获取 {server_name} 的工具列表...")
        
        tools = await mcp_manager.list_tools(server_name)
        
        if not tools:
            message = f"❌ 服务器 {server_name} 没有可用工具或连接失败"
            await self.send_text(message)
            return False, message, False

        message_lines = [f"🔧 {server_name} 可用工具:"]
        for i, tool in enumerate(tools, 1):
            tool_info = f"{i}. {tool.name}"
            if tool.description:
                tool_info += f"\n   描述: {tool.description}"
            message_lines.append(tool_info)

        message = "\n".join(message_lines)
        await self.send_text(message)
        return True, message, True


class CallMCPToolCommand(BaseCommand):
    """Call a tool from an MCP server."""

    command_name = "call_mcp_tool"
    command_description = "调用MCP服务器的工具"
    command_pattern = r"^/mcp call\s+(\S+)\s+(\S+)(?:\s+(.+))?$"

    async def execute(self) -> Tuple[bool, str, bool]:
        """Call a tool on an MCP server."""
        import re
        match = re.match(self.command_pattern, self.message.raw_message)
        
        if not match:
            message = "用法: /mcp call <server_name> <tool_name> [arguments_json]"
            await self.send_text(message)
            return False, message, False

        server_name = match.group(1).strip()
        tool_name = match.group(2).strip()
        args_str = match.group(3).strip() if match.group(3) else "{}"

        # Parse arguments
        try:
            arguments = json.loads(args_str)
        except json.JSONDecodeError as e:
            message = f"❌ 参数JSON格式错误: {e}"
            await self.send_text(message)
            return False, message, False

        await self.send_text(f"正在调用 {server_name}.{tool_name}...")

        # Call the tool
        result = await mcp_manager.call_tool(server_name, tool_name, arguments)

        if not result:
            message = f"❌ 调用工具失败: {server_name}.{tool_name}"
            await self.send_text(message)
            return False, message, False

        # Format result
        message_lines = [f"✅ 工具调用成功: {server_name}.{tool_name}"]
        
        # Extract text content
        for content in result.content:
            if isinstance(content, TextContent):
                message_lines.append(f"\n结果:\n{content.text}")

        # Show structured content if available
        if hasattr(result, 'structuredContent') and result.structuredContent:
            structured_json = json.dumps(result.structuredContent, ensure_ascii=False, indent=2)
            message_lines.append(f"\n结构化数据:\n{structured_json}")

        message = "\n".join(message_lines)
        await self.send_text(message)
        return True, message, True


class MCPHelpCommand(BaseCommand):
    """Show MCP plugin help."""

    command_name = "mcp_help"
    command_description = "显示MCP插件帮助"
    command_pattern = r"^/mcp help$"

    async def execute(self) -> Tuple[bool, str, bool]:
        """Show help message."""
        help_text = """
🔌 MCP插件使用说明

MCP (Model Context Protocol) 插件允许Maimbot使用来自各种MCP服务的工具。

可用命令:
• /mcp servers - 列出所有已配置的MCP服务器
• /mcp tools <server_name> - 列出指定服务器的可用工具
• /mcp call <server_name> <tool_name> [args] - 调用工具
  示例: /mcp call weather get_weather {"city": "北京"}
• /mcp help - 显示此帮助信息

配置方式:
在配置文件中添加MCP服务器配置:
[mcp.servers]
weather = { command = "npx", args = ["-y", "@modelcontextprotocol/server-weather"] }
github = { command = "npx", args = ["-y", "@modelcontextprotocol/server-github"] }
"""
        await self.send_text(help_text)
        return True, help_text, True


@register_plugin
class MCPPlugin(BasePlugin):
    """MCP (Model Context Protocol) Bridge Plugin for Maimbot."""

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
            "config_version": ConfigField(type=str, default="0.1.0", description="配置文件版本"),
        },
        "mcp": {
            "servers": ConfigField(
                type=dict,
                default={},
                description="MCP服务器配置字典，格式: {name: {command: str, args: list, env: dict}}",
            ),
        },
    }

    async def on_load(self) -> None:
        """Initialize plugin on load."""
        logger.info("MCP Plugin loading...")
        
        # Load MCP server configurations
        servers_config = self.get_config("mcp.servers", {})
        
        if servers_config:
            for server_name, server_config in servers_config.items():
                await mcp_manager.add_server(server_name, server_config)
                logger.info(f"Loaded MCP server config: {server_name}")
        else:
            logger.warning("No MCP servers configured")

        logger.info("MCP Plugin loaded successfully")

    def get_plugin_components(self) -> List[Tuple[ComponentInfo, Type]]:
        """Return list of plugin components."""
        return [
            (MCPHelpCommand.get_command_info(), MCPHelpCommand),
            (ListMCPServersCommand.get_command_info(), ListMCPServersCommand),
            (ListMCPToolsCommand.get_command_info(), ListMCPToolsCommand),
            (CallMCPToolCommand.get_command_info(), CallMCPToolCommand),
        ]
