# MCP插件使用指南

本指南详细介绍如何使用Maimbot MCP插件。

## 快速开始

### 1. 安装插件

```bash
# 克隆仓库到Maimbot插件目录
cd /path/to/maimbot/plugins
git clone https://github.com/KotoriK/maimbot-plugin-mcp.git

# 安装依赖
cd maimbot-plugin-mcp
pip install -e .
```

### 2. 配置MCP服务器

编辑 `maimbot_plugin_mcp/config.toml`:

```toml
[plugin]
enabled = true

[mcp.servers]
# 添加你想要使用的MCP服务器
calculator = { command = "python3", args = ["examples/simple_mcp_server.py"] }
```

### 3. 重启Maimbot

重启Maimbot以加载插件。

### 4. 开始使用

在聊天中使用命令：

```
/mcp help
```

## 命令详解

### 查看帮助

```
/mcp help
```

显示所有可用的MCP命令和使用说明。

### 列出服务器

```
/mcp servers
```

**示例输出：**
```
📋 已配置的MCP服务器:
1. calculator
2. weather
3. github
```

### 列出工具

```
/mcp tools <server_name>
```

**示例：**
```
/mcp tools calculator
```

**输出：**
```
🔧 calculator 可用工具:
1. add
   描述: Add two numbers together.
2. subtract
   描述: Subtract b from a.
3. multiply
   描述: Multiply two numbers.
4. divide
   描述: Divide a by b.
5. greet
   描述: Generate a greeting message.
```

### 调用工具

```
/mcp call <server_name> <tool_name> [arguments_json]
```

**示例：**

1. 简单计算：
```
/mcp call calculator add {"a": 5, "b": 3}
```

输出：
```
✅ 工具调用成功: calculator.add

结果:
8

结构化数据:
{
  "result": 8
}
```

2. 问候消息：
```
/mcp call calculator greet {"name": "张三", "style": "friendly"}
```

输出：
```
✅ 工具调用成功: calculator.greet

结果:
Hi 张三! How are you doing today? 😊
```

3. 除法运算：
```
/mcp call calculator divide {"a": 42, "b": 6}
```

## 配置MCP服务器

### 配置格式

```toml
[mcp.servers]
server_name = { command = "命令", args = ["参数1", "参数2", ...], env = { "环境变量" = "值" } }
```

### 配置示例

#### 1. Python服务器

```toml
calculator = { command = "python3", args = ["path/to/server.py"] }
```

#### 2. Node.js/NPX服务器

```toml
weather = { command = "npx", args = ["-y", "@modelcontextprotocol/server-weather"] }
```

#### 3. 带环境变量的服务器

```toml
github = { 
    command = "npx", 
    args = ["-y", "@modelcontextprotocol/server-github"],
    env = { "GITHUB_TOKEN" = "ghp_your_token_here" }
}
```

#### 4. 使用UV运行的服务器

```toml
custom = { command = "uv", args = ["run", "my-mcp-server"] }
```

#### 5. 文件系统服务器（指定路径）

```toml
filesystem = { 
    command = "npx", 
    args = ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/documents"]
}
```

## 常用MCP服务器

### 官方服务器

查看更多MCP服务器：
- [官方服务器列表](https://github.com/modelcontextprotocol/servers)
- [社区服务器](https://github.com/topics/mcp-server)

## 故障排除

### 问题：找不到服务器

**症状：**
```
❌ 服务器 xxx 没有可用工具或连接失败
```

**解决方法：**
1. 检查配置文件中的服务器名称是否正确
2. 确认服务器命令和参数配置正确
3. 验证依赖是否已安装（如npx, python3等）
4. 查看Maimbot日志获取详细错误

### 问题：工具调用失败

**症状：**
```
❌ 调用工具失败: server.tool
```

**解决方法：**
1. 使用 `/mcp tools server` 确认工具名称正确
2. 检查参数JSON格式是否正确
3. 验证参数是否符合工具要求
4. 查看日志获取详细错误信息

### 问题：参数格式错误

**症状：**
```
❌ 参数JSON格式错误: ...
```

**解决方法：**
1. 确保JSON格式正确（使用双引号，逗号分隔）
2. 特殊字符需要转义
3. 可以先在JSON验证器中验证格式

## 开发自定义MCP服务器

如果现有服务器不满足需求，可以开发自定义服务器：

1. 参考[MCP Python SDK文档](https://github.com/modelcontextprotocol/python-sdk)
2. 查看 `examples/simple_mcp_server.py` 示例
3. 实现你需要的工具
4. 在配置中添加自定义服务器

示例：
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("My Custom Server")

@mcp.tool()
def my_tool(arg1: str, arg2: int) -> str:
    """My custom tool description."""
    return f"Processed: {arg1} with {arg2}"

if __name__ == "__main__":
    mcp.run()
```

配置：
```toml
custom = { command = "python3", args = ["/path/to/my_server.py"] }
```

## 社区资源

- [MCP官方文档](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [官方服务器](https://github.com/modelcontextprotocol/servers)
- [Maimbot文档](https://docs.mai-mai.org/)

## 获取帮助

如果遇到问题：
1. 查看本文档的故障排除部分
2. 检查GitHub Issues
3. 提交新的Issue并提供：
   - 详细的错误信息
   - 配置文件（移除敏感信息）
   - 复现步骤
   - 环境信息（Python版本、OS等）
