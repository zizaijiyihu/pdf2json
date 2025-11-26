
import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from km_agent.agent import KMAgent

def test_chat_stream():
    print("Initializing KMAgent with verbose=True...")
    agent = KMAgent(verbose=True)
    
    print("\nStarting chat stream...")
    print("=" * 50)
    
    # Simple query to trigger LLM call
    query = "你好，请做一个简单的自我介绍"
    
    try:
        # Consume the generator to ensure execution
        for chunk in agent.chat_stream(query):
            if chunk['type'] == 'content':
                print(chunk['data'], end="", flush=True)
            elif chunk['type'] == 'tool_call':
                print(f"\n[Tool Call] {chunk['data']}")
            elif chunk['type'] == 'done':
                print("\n[Done]")
                
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    test_chat_stream()
