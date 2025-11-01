# maimbot-plugin-mcp

Maimbot的MCP（Model Context Protocol）透明桥接插件。

## 简介

此插件作为Maimbot和MCP服务之间的**透明桥接层**，自动将MCP服务器的工具转换为Maimbot原生工具，让LLM可以直接调用，无需了解MCP实现细节。

### 核心特性

- **透明桥接**: MaimBot上层应用无需了解MCP，只看到工具
- **自动发现**: 启动时自动发现所有MCP服务器的工具
- **直接调用**: LLM可以直接调用工具，无需特殊命令
- **动态注册**: 每个MCP工具自动注册为Maimbot工具组件

## 工作原理

```
配置文件 → MCP服务器 → 工具发现 → BaseTool封装 → LLM直接调用
```

1. **配置阶段**: 在config.toml中配置MCP服务器
2. **发现阶段**: 插件启动时连接每个服务器，发现可用工具
3. **注册阶段**: 为每个MCP工具动态创建BaseTool wrapper
4. **使用阶段**: LLM像使用其他Maimbot工具一样直接调用

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

## 配置

编辑 `maimbot_plugin_mcp/config.toml` 文件来配置MCP服务器：

```toml
[plugin]
enabled = true
config_version = "0.2.0"

[mcp.servers]
# 计算器示例
calculator = { command = "python3", args = ["examples/simple_mcp_server.py"] }

# 天气服务
weather = { command = "npx", args = ["-y", "@modelcontextprotocol/server-weather"] }

# GitHub服务
github = { 
    command = "npx", 
    args = ["-y", "@modelcontextprotocol/server-github"],
    env = { "GITHUB_TOKEN" = "your_token_here" }
}
```

### 配置格式

```toml
server_name = { 
    command = "命令",        # 启动命令 (如 python3, npx, node)
    args = ["参数列表"],     # 命令参数
    env = { "VAR" = "值" }   # 可选: 环境变量
}
```

## 使用方式

**重要**: 此插件不提供用户命令，工具直接暴露给LLM。

### 工具命名

MCP工具会以以下格式注册：
```
mcp_<服务器名>_<工具名>
```

例如：
- calculator服务器的add工具 → `mcp_calculator_add`
- weather服务器的get_forecast工具 → `mcp_weather_get_forecast`

### LLM调用示例

LLM可以直接调用工具（无需用户手动输入）：

```python
# LLM内部调用示例（自动）
mcp_calculator_add(a=5, b=3)  # 返回: 8
mcp_weather_get_forecast(city="北京", days=7)  # 返回天气预报
```

用户只需正常聊天，LLM会在需要时自动调用工具：

```
用户: 帮我算一下 5 + 3
LLM: (自动调用 mcp_calculator_add) 结果是 8

用户: 北京明天天气怎么样？
LLM: (自动调用 mcp_weather_get_forecast) 明天北京...
```

## MCP服务器示例

### 官方服务器

```toml
# 天气服务
weather = { command = "npx", args = ["-y", "@modelcontextprotocol/server-weather"] }

# 文件系统访问
filesystem = { 
    command = "npx", 
    args = ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/files"]
}

# GitHub API
github = { 
    command = "npx", 
    args = ["-y", "@modelcontextprotocol/server-github"],
    env = { "GITHUB_TOKEN" = "ghp_..." }
}

# PostgreSQL数据库
postgres = { 
    command = "npx", 
    args = ["-y", "@modelcontextprotocol/server-postgres"],
    env = { "POSTGRES_CONNECTION_STRING" = "postgresql://..." }
}
```

### 自定义服务器

参考 `examples/simple_mcp_server.py`:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("My Custom Server")

@mcp.tool()
def my_tool(arg1: str, arg2: int) -> str:
    """工具描述"""
    return f"Result: {arg1} {arg2}"

if __name__ == "__main__":
    mcp.run()
```

配置：
```toml
custom = { command = "python3", args = ["path/to/my_server.py"] }
```

## 技术架构

### 核心组件

1. **`create_mcp_tool_wrapper()`**: 动态创建BaseTool子类
   - 将MCP工具schema转换为Maimbot参数格式
   - 实现execute()方法调用MCP服务器
   - 自动处理连接和错误

2. **`MCPPlugin.on_load()`**: 插件初始化
   - 读取配置中的MCP服务器
   - 连接每个服务器并发现工具
   - 动态注册所有工具组件

3. **`MCPPlugin.get_plugin_components()`**: 返回工具列表
   - 返回所有动态创建的BaseTool包装器
   - Maimbot将这些工具注册到系统中
   - LLM可以访问和调用这些工具

### 类型转换

MCP JSON Schema → Maimbot ToolParamType:
```
string  → STRING
number  → NUMBER
integer → INTEGER
boolean → BOOLEAN
array   → ARRAY
object  → OBJECT
```

### 执行流程

```
LLM调用工具
  ↓
MCPToolWrapper.execute()
  ↓
连接MCP服务器 (stdio)
  ↓
调用MCP工具
  ↓
提取文本结果
  ↓
返回给LLM
```

## 与原实现的区别

### 旧实现 (v0.1.0)
- ❌ 提供 `/mcp` 系列命令
- ❌ 用户需要手动调用工具
- ❌ LLM不能直接使用工具
- ❌ 需要管理服务器连接

### 新实现 (v0.2.0)
- ✅ 工具直接暴露给LLM
- ✅ LLM自动调用工具
- ✅ 透明桥接，无需特殊命令
- ✅ 自动发现和注册

## 故障排除

### 问题：工具未注册

**检查**:
1. 查看Maimbot日志中的 "Registered tool:" 消息
2. 确认MCP服务器配置正确
3. 测试MCP服务器可独立运行

### 问题：工具调用失败

**检查**:
1. 日志中的错误信息
2. MCP服务器进程是否正常启动
3. 环境变量是否正确设置

### 问题：参数类型错误

**原因**: MCP schema与Maimbot类型不匹配

**解决**: 检查MCP工具的inputSchema定义

## 开发

### 项目结构

```
maimbot-plugin-mcp/
├── maimbot_plugin_mcp/
│   ├── __init__.py
│   ├── _manifest.json     # 插件清单文件 (必需)
│   ├── plugin.py          # 核心实现
│   └── config.toml        # 配置模板
├── examples/
│   └── simple_mcp_server.py  # 示例MCP服务器
├── tests/
│   └── test_mcp_client.py    # 测试
└── README.md
```

### 插件清单 (_manifest.json)

根据[Maimbot插件规范](https://docs.mai-mai.org/develop/plugin_develop/manifest-guide.html)，所有插件都需要一个`_manifest.json`文件来描述插件的元数据：

- **manifest_version**: 清单格式版本
- **name**: 插件显示名称
- **version**: 插件版本号
- **description**: 插件功能描述
- **author**: 作者信息
- **plugin_info**: 插件类型和组件信息
  - `plugin_type`: "tool_provider" (此插件提供工具)
  - `components`: 动态注册的MCP工具
  - `dependencies`: Python包依赖 (mcp>=1.0.0)

### 关键函数

- `_mcp_type_to_tool_param_type()`: 类型转换
- `_extract_mcp_tool_parameters()`: 参数提取
- `create_mcp_tool_wrapper()`: 动态类创建
- `MCPPlugin.on_load()`: 工具发现和注册

## 参考资料

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Maimbot插件开发](https://docs.mai-mai.org/develop/plugin_develop/)
- [官方MCP服务器](https://github.com/modelcontextprotocol/servers)

## 许可证

MIT License

## 更新日志

### v0.2.0 (2024-11-01)
- 🎉 完全重构为透明桥接架构
- ✅ 移除所有 `/mcp` 命令
- ✅ 工具直接注册为BaseTool组件
- ✅ LLM可以直接调用MCP工具
- ✅ 自动工具发现和动态注册

### v0.1.0
- 初始实现（已弃用）
- 提供 `/mcp` 命令系列
