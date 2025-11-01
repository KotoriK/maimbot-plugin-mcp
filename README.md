# maimbot-plugin-mcp

Maimbot的MCP（Model Context Protocol）插件，用于让Maimbot能够使用来自任意MCP服务提供的工具。

## 简介

此插件作为Maimbot和MCP服务之间的桥梁，允许Maimbot：
- 连接到多个MCP服务器
- 发现和列出可用的工具
- 调用MCP工具并获取结果
- 通过配置文件灵活管理MCP服务

## 功能特性

- ✅ 支持多个MCP服务器配置
- ✅ 动态工具发现和列表
- ✅ 工具调用与结果解析
- ✅ 支持stdio传输协议
- ✅ 完整的中文界面
- ✅ 灵活的配置管理

## 安装

1. 克隆此仓库到Maimbot插件目录：
```bash
cd /path/to/maimbot/plugins
git clone https://github.com/KotoriK/maimbot-plugin-mcp.git
```

2. 安装依赖：
```bash
cd maimbot-plugin-mcp
pip install -e .
```

或使用uv：
```bash
uv pip install -e .
```

## 配置

编辑 `maimbot_plugin_mcp/config.toml` 文件来配置MCP服务器：

```toml
[plugin]
enabled = true
config_version = "0.1.0"

[mcp.servers]
# 天气服务器示例
weather = { command = "npx", args = ["-y", "@modelcontextprotocol/server-weather"] }

# 文件系统服务器示例
filesystem = { command = "npx", args = ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/files"] }

# GitHub服务器示例（需要GITHUB_TOKEN）
github = { 
    command = "npx", 
    args = ["-y", "@modelcontextprotocol/server-github"], 
    env = { "GITHUB_TOKEN" = "your_token_here" } 
}

# 自定义Python服务器示例
custom = { command = "python", args = ["/path/to/your_mcp_server.py"] }
```

### 配置格式说明

每个MCP服务器配置包含：
- `command`: 启动命令（如 "npx", "python", "node", "uv"）
- `args`: 命令参数列表
- `env`: （可选）环境变量字典

## 使用方法

### 1. 查看已配置的服务器

```
/mcp servers
```

### 2. 列出服务器的可用工具

```
/mcp tools <server_name>
```

示例：
```
/mcp tools weather
```

### 3. 调用MCP工具

```
/mcp call <server_name> <tool_name> [arguments_json]
```

示例：
```
/mcp call weather get_weather {"city": "北京"}
/mcp call filesystem read_file {"path": "/path/to/file.txt"}
```

### 4. 查看帮助

```
/mcp help
```

## 命令详解

### /mcp servers
列出所有已配置的MCP服务器名称。

**输出示例：**
```
📋 已配置的MCP服务器:
1. weather
2. github
3. filesystem
```

### /mcp tools <server_name>
列出指定MCP服务器提供的所有工具及其描述。

**输出示例：**
```
🔧 weather 可用工具:
1. get_weather
   描述: Get current weather for a city
2. get_forecast
   描述: Get weather forecast
```

### /mcp call <server_name> <tool_name> [arguments_json]
调用指定服务器的工具。参数需要以JSON格式提供。

**参数说明：**
- `server_name`: 配置的服务器名称
- `tool_name`: 要调用的工具名称
- `arguments_json`: JSON格式的工具参数（可选）

**输出示例：**
```
✅ 工具调用成功: weather.get_weather

结果:
Weather in 北京: 22°C, Sunny
Humidity: 45%

结构化数据:
{
  "temperature": 22,
  "condition": "Sunny",
  "humidity": 45
}
```

## MCP服务器示例

以下是一些常用的MCP服务器：

### 官方服务器

1. **Weather Server** - 天气信息
   ```toml
   weather = { command = "npx", args = ["-y", "@modelcontextprotocol/server-weather"] }
   ```

2. **Filesystem Server** - 文件系统访问
   ```toml
   filesystem = { command = "npx", args = ["-y", "@modelcontextprotocol/server-filesystem", "/allowed/path"] }
   ```

3. **GitHub Server** - GitHub API访问
   ```toml
   github = { command = "npx", args = ["-y", "@modelcontextprotocol/server-github"], env = { "GITHUB_TOKEN" = "token" } }
   ```

4. **PostgreSQL Server** - 数据库访问
   ```toml
   postgres = { command = "npx", args = ["-y", "@modelcontextprotocol/server-postgres"], env = { "POSTGRES_CONNECTION_STRING" = "postgresql://..." } }
   ```

### 自定义服务器

你可以创建自己的MCP服务器。参考：
- [MCP Python SDK文档](https://github.com/modelcontextprotocol/python-sdk)
- [MCP规范](https://modelcontextprotocol.io/)

## 开发

### 项目结构

```
maimbot-plugin-mcp/
├── maimbot_plugin_mcp/
│   ├── __init__.py          # 包初始化
│   ├── plugin.py            # 主插件实现
│   └── config.toml          # 默认配置文件
├── pyproject.toml           # 项目配置
├── README.md                # 本文件
└── LICENSE                  # MIT许可证
```

### 技术栈

- **Python**: 3.10+
- **MCP SDK**: 用于MCP协议客户端
- **Maimbot Plugin System**: Maimbot插件框架

### 架构说明

插件主要组件：

1. **MCPClientManager**: 管理MCP服务器连接和工具调用
   - 服务器配置管理
   - 会话生命周期管理
   - 工具发现和执行

2. **命令类**:
   - `ListMCPServersCommand`: 列出服务器
   - `ListMCPToolsCommand`: 列出工具
   - `CallMCPToolCommand`: 调用工具
   - `MCPHelpCommand`: 显示帮助

3. **MCPPlugin**: 主插件类
   - 加载配置
   - 注册命令
   - 生命周期管理

## 故障排除

### 问题：服务器连接失败

**解决方法：**
1. 检查服务器命令和参数是否正确
2. 确认所需的环境变量已设置
3. 验证依赖是否已安装（如npx、node等）
4. 查看日志获取详细错误信息

### 问题：工具调用失败

**解决方法：**
1. 确认参数JSON格式正确
2. 检查工具是否存在（使用 `/mcp tools` 查看）
3. 验证参数是否符合工具要求
4. 查看日志获取详细错误信息

### 问题：无法找到MCP服务器

**解决方法：**
1. 确认服务器已在config.toml中配置
2. 检查配置语法是否正确
3. 重启Maimbot以重新加载配置

## 参考资料

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Maimbot插件开发文档](https://docs.mai-mai.org/develop/plugin_develop/tool-components.html)
- [官方MCP服务器列表](https://github.com/modelcontextprotocol/servers)

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 致谢

- Maimbot团队提供的优秀插件系统
- Anthropic的Model Context Protocol规范
- MCP社区的各种服务器实现