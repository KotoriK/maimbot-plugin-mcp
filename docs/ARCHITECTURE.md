# MCP插件架构文档

## 设计理念

MCP插件作为**透明桥接层**，将MCP服务器的工具转换为Maimbot原生工具，让LLM可以直接使用，无需了解MCP协议的存在。

## 架构图

```
┌─────────────────────────────────────────────────┐
│              Maimbot Core                        │
│  ┌───────────────────────────────────────────┐  │
│  │         LLM Tool Registry                 │  │
│  │  - mcp_calculator_add                     │  │
│  │  - mcp_calculator_multiply                │  │
│  │  - mcp_weather_get_forecast               │  │
│  │  - ...                                    │  │
│  └───────────────────────────────────────────┘  │
│                     ▲                            │
│                     │ (BaseTool)                 │
└─────────────────────┼──────────────────────────┘
                      │
┌─────────────────────┼──────────────────────────┐
│              MCP Plugin                          │
│  ┌───────────────────────────────────────────┐  │
│  │      Dynamic Tool Wrapper Factory         │  │
│  │                                           │  │
│  │  create_mcp_tool_wrapper():               │  │
│  │  - Extract MCP tool schema                │  │
│  │  - Convert to ToolParamType               │  │
│  │  - Generate BaseTool subclass             │  │
│  │  - Implement execute() method             │  │
│  └───────────────────────────────────────────┘  │
│                     ▲                            │
│                     │ (MCP Protocol)             │
└─────────────────────┼──────────────────────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
         ▼            ▼            ▼
  ┌──────────┐ ┌──────────┐ ┌──────────┐
  │ MCP      │ │ MCP      │ │ MCP      │
  │ Server 1 │ │ Server 2 │ │ Server N │
  │ (stdio)  │ │ (stdio)  │ │ (stdio)  │
  └──────────┘ └──────────┘ └──────────┘
```

## 核心组件

### 1. 类型转换层

**函数**: `_mcp_type_to_tool_param_type(mcp_type: str) -> ToolParamType`

MCP JSON Schema类型到Maimbot类型的映射：

```python
{
    "string": ToolParamType.STRING,
    "number": ToolParamType.NUMBER,
    "integer": ToolParamType.INTEGER,
    "boolean": ToolParamType.BOOLEAN,
    "array": ToolParamType.ARRAY,
    "object": ToolParamType.OBJECT,
}
```

### 2. 参数提取层

**函数**: `_extract_mcp_tool_parameters(mcp_tool: MCPTool) -> List[Tuple]`

从MCP工具的`inputSchema`提取参数定义：

```python
# MCP输入
{
    "type": "object",
    "properties": {
        "city": {"type": "string", "description": "城市名称"},
        "days": {"type": "integer", "description": "天数"}
    },
    "required": ["city"]
}

# 转换为Maimbot格式
[
    ("city", ToolParamType.STRING, "城市名称", True, None),
    ("days", ToolParamType.INTEGER, "天数", False, None)
]
```

### 3. 动态工具包装器

**函数**: `create_mcp_tool_wrapper(server_name, server_params, mcp_tool) -> Type[BaseTool]`

动态创建BaseTool子类：

```python
class MCPToolWrapper(BaseTool):
    name = f"mcp_{server_name}_{mcp_tool.name}"
    description = mcp_tool.description
    parameters = _extract_mcp_tool_parameters(mcp_tool)
    available_for_llm = True
    
    # 存储MCP连接信息
    _mcp_server_name = server_name
    _mcp_tool_name = mcp_tool.name
    _mcp_server_params = server_params
    
    async def execute(self, function_args: dict) -> dict:
        # 连接MCP服务器
        async with stdio_client(self._mcp_server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                # 调用MCP工具
                result = await session.call_tool(
                    self._mcp_tool_name, 
                    arguments=function_args
                )
                # 提取文本结果
                return {"content": extracted_text}
```

### 4. 插件加载器

**类**: `MCPPlugin.on_load()`

插件启动时的工作流程：

1. **读取配置**
   ```python
   servers_config = self.get_config("mcp.servers", {})
   ```

2. **连接每个服务器**
   ```python
   server_params = StdioServerParameters(
       command=config["command"],
       args=config["args"],
       env=config.get("env", {})
   )
   ```

3. **发现工具**
   ```python
   async with stdio_client(server_params) as (read, write):
       async with ClientSession(read, write) as session:
           await session.initialize()
           tools = await session.list_tools()
   ```

4. **创建包装器**
   ```python
   for mcp_tool in tools:
       wrapper = create_mcp_tool_wrapper(server_name, server_params, mcp_tool)
       self._tool_wrappers.append((wrapper.get_tool_info(), wrapper))
   ```

5. **注册到系统**
   ```python
   def get_plugin_components(self):
       return self._tool_wrappers
   ```

## 数据流

### 工具注册流程

```
config.toml
    ↓ (读取配置)
MCPPlugin.on_load()
    ↓ (连接服务器)
MCP Server
    ↓ (list_tools)
MCP Tool Schema
    ↓ (转换)
create_mcp_tool_wrapper()
    ↓ (生成)
BaseTool Subclass
    ↓ (注册)
Maimbot Tool Registry
    ↓ (暴露)
LLM
```

### 工具调用流程

```
LLM决定调用工具
    ↓
mcp_calculator_add(a=5, b=3)
    ↓
MCPToolWrapper.execute({"a": 5, "b": 3})
    ↓
连接MCP服务器 (stdio)
    ↓
session.call_tool("add", {"a": 5, "b": 3})
    ↓
MCP服务器处理
    ↓
CallToolResult { content: [TextContent("8")] }
    ↓
提取文本: "8"
    ↓
返回: {"content": "8"}
    ↓
LLM接收结果
```

## 工具命名规范

MCP工具以以下格式注册：
```
mcp_<服务器名>_<工具名>
```

示例：
- calculator服务器的add工具 → `mcp_calculator_add`
- weather服务器的get_forecast → `mcp_weather_get_forecast`
- github服务器的create_issue → `mcp_github_create_issue`

这种命名避免了：
- 不同服务器的同名工具冲突
- 与Maimbot内置工具名称冲突
- 清晰标识工具来源

## 错误处理

### 服务器连接失败
```python
try:
    async with stdio_client(server_params) as (read, write):
        # ...
except Exception as e:
    logger.error(f"Failed to load tools from {server_name}: {e}")
    continue  # 继续加载其他服务器
```

### 工具包装失败
```python
for mcp_tool in mcp_tools:
    try:
        wrapper = create_mcp_tool_wrapper(...)
        self._tool_wrappers.append(...)
    except Exception as e:
        logger.error(f"Failed to create wrapper for {mcp_tool.name}: {e}")
        # 继续处理其他工具
```

### 工具执行失败
```python
async def execute(self, function_args):
    try:
        # 执行MCP工具
        return {"content": result}
    except Exception as e:
        logger.error(f"Failed to execute MCP tool: {e}")
        return {"content": f"Error: {str(e)}"}
```

## 性能考虑

### 连接管理
- **按需连接**: 每次工具调用创建新连接
- **好处**: 无状态，可靠性高
- **代价**: 略高延迟（通常可接受）

### 工具发现
- **一次性**: 仅在插件加载时发现工具
- **缓存**: 工具列表在内存中缓存
- **重载**: 需要重启Maimbot才能发现新工具

### 扩展性
- **并发**: 多个工具调用可并发执行
- **隔离**: 每个工具调用独立的会话
- **容错**: 单个工具失败不影响其他工具

## 配置示例

```toml
[plugin]
enabled = true
config_version = "0.2.0"

[mcp.servers]
# 本地Python服务器
calculator = { 
    command = "python3", 
    args = ["examples/simple_mcp_server.py"] 
}

# NPX包服务器
weather = { 
    command = "npx", 
    args = ["-y", "@modelcontextprotocol/server-weather"] 
}

# 带环境变量的服务器
github = { 
    command = "npx", 
    args = ["-y", "@modelcontextprotocol/server-github"],
    env = { "GITHUB_TOKEN" = "ghp_..." }
}
```

## 日志输出

典型的加载日志：

```
[INFO] MCP Plugin loading...
[INFO] Discovering tools from MCP server: calculator
[INFO] Found 5 tools from calculator
[INFO]   - Registered tool: mcp_calculator_add
[INFO]   - Registered tool: mcp_calculator_subtract
[INFO]   - Registered tool: mcp_calculator_multiply
[INFO]   - Registered tool: mcp_calculator_divide
[INFO]   - Registered tool: mcp_calculator_greet
[INFO] MCP Plugin loaded successfully with 5 tools
```

## 扩展点

### 支持新的传输协议
当前仅支持stdio，可扩展支持：
- SSE (Server-Sent Events)
- HTTP/WebSocket
- 其他自定义传输

### 高级参数映射
当前基本类型映射，可扩展：
- 嵌套对象映射
- 复杂数组类型
- 条件参数
- 参数验证增强

### 工具元数据
可扩展支持：
- 工具分类/标签
- 使用统计
- 性能监控
- 动态启用/禁用

## 与v0.1.0的对比

| 特性 | v0.1.0 (旧) | v0.2.0 (新) |
|------|-------------|-------------|
| 用户界面 | `/mcp` 命令 | 无命令，透明 |
| 工具暴露 | 手动调用 | LLM直接访问 |
| MCP感知 | 用户需了解 | 完全透明 |
| 架构 | 命令+管理器 | 动态包装器 |
| 代码行数 | ~379行 | ~212行 |
| 复杂度 | 较高 | 较低 |

## 参考

- [Model Context Protocol规范](https://modelcontextprotocol.io/)
- [MCP Tools文档](https://modelcontextprotocol.io/docs/learn/server-concepts#how-tools-work)
- [Maimbot BaseTool API](https://docs.mai-mai.org/)
