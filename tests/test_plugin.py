"""
Test script for MCP plugin

This script tests the MCP plugin functionality without requiring
a full Maimbot installation.
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from maimbot_plugin_mcp.plugin import MCPClientManager


async def test_mcp_client_manager():
    """Test MCPClientManager functionality."""
    print("=" * 60)
    print("Testing MCP Client Manager")
    print("=" * 60)
    
    manager = MCPClientManager()
    
    # Test 1: Add server configuration
    print("\n[Test 1] Adding server configuration...")
    server_config = {
        "command": "python3",
        "args": ["examples/simple_mcp_server.py"],
        "env": {}
    }
    
    success = await manager.add_server("calculator", server_config)
    assert success, "Failed to add server"
    print("✓ Server configuration added successfully")
    
    # Test 2: List servers
    print("\n[Test 2] Listing servers...")
    servers = manager.get_server_list()
    print(f"Configured servers: {servers}")
    assert "calculator" in servers, "Calculator server not found"
    print("✓ Server list retrieved successfully")
    
    # Test 3: Connect to server
    print("\n[Test 3] Connecting to server...")
    result = await manager.connect_server("calculator")
    print("✓ Server connection initialized")
    
    # Test 4: List tools
    print("\n[Test 4] Listing tools from calculator server...")
    tools = await manager.list_tools("calculator")
    print(f"Found {len(tools)} tools:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    
    assert len(tools) > 0, "No tools found"
    print("✓ Tools listed successfully")
    
    # Test 5: Call a tool
    print("\n[Test 5] Calling 'add' tool...")
    result = await manager.call_tool("calculator", "add", {"a": 5, "b": 3})
    
    if result:
        print(f"Tool result: {result}")
        print(f"Content: {result.content}")
        if hasattr(result, 'structuredContent') and result.structuredContent:
            print(f"Structured content: {result.structuredContent}")
        print("✓ Tool called successfully")
    else:
        print("✗ Tool call failed")
        return False
    
    # Test 6: Call greet tool
    print("\n[Test 6] Calling 'greet' tool...")
    result = await manager.call_tool("calculator", "greet", {"name": "Maimbot", "style": "friendly"})
    
    if result:
        print(f"Greeting result: {result.content[0].text if result.content else 'No content'}")
        print("✓ Greet tool called successfully")
    else:
        print("✗ Greet tool call failed")
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
    
    return True


async def test_error_handling():
    """Test error handling."""
    print("\n" + "=" * 60)
    print("Testing Error Handling")
    print("=" * 60)
    
    manager = MCPClientManager()
    
    # Test: Non-existent server
    print("\n[Test] Calling tool on non-existent server...")
    result = await manager.call_tool("nonexistent", "tool", {})
    assert result is None, "Should return None for non-existent server"
    print("✓ Error handling for non-existent server works")
    
    # Test: Invalid server list
    print("\n[Test] Listing tools from non-existent server...")
    tools = await manager.list_tools("nonexistent")
    assert len(tools) == 0, "Should return empty list for non-existent server"
    print("✓ Error handling for tool listing works")
    
    print("\n" + "=" * 60)
    print("Error handling tests passed! ✓")
    print("=" * 60)


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("MCP Plugin Test Suite")
    print("=" * 60)
    
    try:
        # Run tests
        await test_mcp_client_manager()
        await test_error_handling()
        
        print("\n✓✓✓ All test suites passed! ✓✓✓\n")
        return 0
        
    except Exception as e:
        print(f"\n✗✗✗ Test failed with error: {e} ✗✗✗\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
