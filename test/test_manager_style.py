"""
Test script for get_manager_style tool
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from km_agent.tools import AgentTools

def test_get_manager_style():
    """Test the get_manager_style tool"""
    
    # Create a minimal tools instance (we don't need vectorizer or user_info_service for this test)
    tools = AgentTools(vectorizer=None, user_info_service=None, verbose=True)
    
    # Test the tool execution
    print("Testing get_manager_style tool...")
    result = tools.execute_tool("get_manager_style", {})
    
    print(f"\nResult: {result}")
    
    # Verify the result
    import json
    result_dict = json.loads(result)
    
    assert result_dict["success"] == True, "Tool should return success"
    assert "style" in result_dict, "Result should contain 'style' field"
    assert result_dict["style"] == "黄牛型,大部分工作都自己亲力亲为", "Should return default manager style"
    
    print("\n✅ Test passed! Manager style tool is working correctly.")

if __name__ == "__main__":
    test_get_manager_style()
