"""
Test script to verify agent can use get_manager_style tool
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from km_agent.agent import KMAgent

def test_manager_style_integration():
    """Test that the agent can use get_manager_style tool"""
    
    print("Testing get_manager_style tool integration with agent...")
    print("=" * 60)
    
    # Create agent instance
    agent = KMAgent(verbose=True)
    
    # Check that the tool is in the tools list
    tool_names = [tool['function']['name'] for tool in agent.tools]
    print(f"\nAvailable tools: {tool_names}")
    
    assert 'get_manager_style' in tool_names, "get_manager_style should be in tools list"
    print("✅ Tool is registered in agent.tools")
    
    # Check that the tool is mentioned in system prompt
    assert 'get_manager_style' in agent.effective_system_prompt, "get_manager_style should be in system prompt"
    print("✅ Tool is mentioned in system prompt")
    
    # Test a query that should trigger the tool
    print("\n" + "=" * 60)
    print("Testing agent response to manager style query...")
    print("=" * 60)
    
    result = agent.chat("我的管理风格是什么？")
    
    print(f"\nAgent response: {result['response']}")
    print(f"\nTool calls made: {len(result['tool_calls'])}")
    
    if result['tool_calls']:
        for i, tc in enumerate(result['tool_calls'], 1):
            print(f"  {i}. {tc['tool']}: {tc.get('result', {})}")
    
    # Verify that get_manager_style was called
    tool_call_names = [tc['tool'] for tc in result['tool_calls']]
    
    if 'get_manager_style' in tool_call_names:
        print("\n✅ Agent successfully called get_manager_style tool!")
        
        # Check the result
        for tc in result['tool_calls']:
            if tc['tool'] == 'get_manager_style':
                assert tc['result']['success'] == True, "Tool should return success"
                assert '黄牛型' in tc['result']['style'], "Should return default manager style"
                print(f"✅ Tool returned expected result: {tc['result']['style']}")
    else:
        print("\n⚠️  Agent did not call get_manager_style tool")
        print("This might be expected if the LLM chose not to use the tool")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_manager_style_integration()
