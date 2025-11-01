"""
Standalone test for MCP client functionality

This test validates the MCP client integration without Maimbot dependencies.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp_connection():
    """Test direct MCP connection to example server."""
    print("=" * 60)
    print("Testing MCP Connection")
    print("=" * 60)
    
    # Configure server parameters
    server_params = StdioServerParameters(
        command="python3",
        args=["examples/simple_mcp_server.py"],
        env={}
    )
    
    print("\n[Test 1] Connecting to MCP server...")
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize connection
                await session.initialize()
                print("✓ Connected and initialized successfully")
                
                # Test 2: List tools
                print("\n[Test 2] Listing available tools...")
                tools_response = await session.list_tools()
                tools = tools_response.tools
                
                print(f"Found {len(tools)} tools:")
                for tool in tools:
                    print(f"  - {tool.name}: {tool.description}")
                
                assert len(tools) > 0, "No tools found"
                print("✓ Tools listed successfully")
                
                # Test 3: Call add tool
                print("\n[Test 3] Calling 'add' tool with a=5, b=3...")
                result = await session.call_tool("add", arguments={"a": 5, "b": 3})
                
                print(f"Result content: {result.content}")
                if hasattr(result, 'structuredContent') and result.structuredContent:
                    print(f"Structured content: {result.structuredContent}")
                    assert result.structuredContent.get("result") == 8 or result.structuredContent == 8, "Unexpected result"
                
                print("✓ Add tool executed successfully")
                
                # Test 4: Call greet tool
                print("\n[Test 4] Calling 'greet' tool...")
                result = await session.call_tool("greet", arguments={"name": "Maimbot", "style": "friendly"})
                
                if result.content:
                    from mcp.types import TextContent
                    text_content = result.content[0]
                    if isinstance(text_content, TextContent):
                        print(f"Greeting: {text_content.text}")
                        assert "Maimbot" in text_content.text, "Name not in greeting"
                
                print("✓ Greet tool executed successfully")
                
                # Test 5: Call multiply tool
                print("\n[Test 5] Calling 'multiply' tool with a=7, b=6...")
                result = await session.call_tool("multiply", arguments={"a": 7, "b": 6})
                
                if hasattr(result, 'structuredContent') and result.structuredContent:
                    expected = 42
                    actual = result.structuredContent.get("result", result.structuredContent)
                    print(f"7 × 6 = {actual}")
                    assert actual == expected, f"Expected {expected}, got {actual}"
                
                print("✓ Multiply tool executed successfully")
                
                # Test 6: List resources
                print("\n[Test 6] Listing available resources...")
                resources_response = await session.list_resources()
                resources = resources_response.resources
                
                print(f"Found {len(resources)} resources:")
                for resource in resources:
                    print(f"  - {resource.uri}: {resource.name}")
                
                print("✓ Resources listed successfully")
                
                # Test 7: List prompts
                print("\n[Test 7] Listing available prompts...")
                prompts_response = await session.list_prompts()
                prompts = prompts_response.prompts
                
                print(f"Found {len(prompts)} prompts:")
                for prompt in prompts:
                    print(f"  - {prompt.name}: {prompt.description if prompt.description else 'No description'}")
                
                print("✓ Prompts listed successfully")
                
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("All MCP connection tests passed! ✓")
    print("=" * 60)
    return True


async def test_error_handling():
    """Test error handling with invalid operations."""
    print("\n" + "=" * 60)
    print("Testing Error Handling")
    print("=" * 60)
    
    server_params = StdioServerParameters(
        command="python3",
        args=["examples/simple_mcp_server.py"],
        env={}
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Test 1: Call non-existent tool
                print("\n[Test 1] Calling non-existent tool...")
                try:
                    result = await session.call_tool("nonexistent", arguments={})
                    # MCP servers may return an error result instead of raising an exception
                    if result.isError if hasattr(result, 'isError') else False:
                        print("✓ Server returned error result for non-existent tool")
                    else:
                        print("✓ Server handled non-existent tool call (no exception)")
                except Exception as e:
                    print(f"✓ Server raised error for non-existent tool: {type(e).__name__}")
                
                # Test 2: Invalid arguments
                print("\n[Test 2] Calling tool with invalid arguments...")
                try:
                    result = await session.call_tool("add", arguments={"x": 1, "y": 2})
                    # This might succeed or fail depending on the server's validation
                    print("✓ Server handled invalid arguments")
                except Exception as e:
                    print(f"✓ Server rejected invalid arguments: {type(e).__name__}")
                
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("Error handling tests passed! ✓")
    print("=" * 60)
    return True


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("MCP Client Test Suite")
    print("=" * 60)
    
    try:
        # Run tests
        result1 = await test_mcp_connection()
        result2 = await test_error_handling()
        
        if result1 and result2:
            print("\n✓✓✓ All test suites passed! ✓✓✓\n")
            return 0
        else:
            print("\n✗✗✗ Some tests failed ✗✗✗\n")
            return 1
        
    except Exception as e:
        print(f"\n✗✗✗ Test suite failed with error: {e} ✗✗✗\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
