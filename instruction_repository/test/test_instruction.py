"""
Test script for instruction_repository module
"""

import sys
import os

# Add parent directory to path (go up two levels from test/ to project root)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from instruction_repository import (
    create_instruction,
    get_active_instructions,
    get_all_instructions,
    update_instruction,
    delete_instruction
)


def test_instruction_repository():
    """Test all CRUD operations"""
    test_owner = "test_user"
    
    print("=" * 60)
    print("Testing Instruction Repository")
    print("=" * 60)
    
    # Test 1: Create instruction
    print("\n1. Testing create_instruction...")
    try:
        result = create_instruction(
            owner=test_owner,
            content="回答要简洁明了，不超过3句话",
            priority=10
        )
        print(f"✓ Created instruction: {result}")
        instruction_id = result['instruction_id']
    except Exception as e:
        print(f"✗ Create failed: {e}")
        return
    
    # Test 2: Get active instructions
    print("\n2. Testing get_active_instructions...")
    try:
        instructions = get_active_instructions(test_owner)
        print(f"✓ Found {len(instructions)} active instructions:")
        for inst in instructions:
            print(f"   - ID:{inst['id']} Priority:{inst['priority']} Content:{inst['content'][:30]}...")
    except Exception as e:
        print(f"✗ Get active failed: {e}")
    
    # Test 3: Get all instructions
    print("\n3. Testing get_all_instructions...")
    try:
        all_instructions = get_all_instructions(test_owner, include_inactive=True)
        print(f"✓ Found {len(all_instructions)} total instructions")
    except Exception as e:
        print(f"✗ Get all failed: {e}")
    
    # Test 4: Update instruction
    print("\n4. Testing update_instruction...")
    try:
        result = update_instruction(
            instruction_id=instruction_id,
            owner=test_owner,
            content="回答要详细一些，包含代码示例",
            priority=5
        )
        print(f"✓ Updated instruction: {result}")
    except Exception as e:
        print(f"✗ Update failed: {e}")
    
    # Test 5: Verify update
    print("\n5. Verifying update...")
    try:
        instructions = get_active_instructions(test_owner)
        updated = [i for i in instructions if i['id'] == instruction_id][0]
        print(f"✓ Updated content: {updated['content']}")
        print(f"✓ Updated priority: {updated['priority']}")
    except Exception as e:
        print(f"✗ Verification failed: {e}")
    
    # Test 6: Disable instruction
    print("\n6. Testing disable instruction...")
    try:
        result = update_instruction(
            instruction_id=instruction_id,
            owner=test_owner,
            is_active=0
        )
        print(f"✓ Disabled instruction: {result}")
        
        active = get_active_instructions(test_owner)
        print(f"✓ Active instructions after disable: {len(active)}")
    except Exception as e:
        print(f"✗ Disable failed: {e}")
    
    # Test 7: Delete instruction
    print("\n7. Testing delete_instruction...")
    try:
        result = delete_instruction(instruction_id, test_owner)
        print(f"✓ Deleted instruction: {result}")
    except Exception as e:
        print(f"✗ Delete failed: {e}")
    
    # Test 8: Test validation - 400 char limit
    print("\n8. Testing 400-char limit validation...")
    try:
        create_instruction(test_owner, "x" * 401, 0)
        print("✗ Should have raised ValueError")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    # Test 9: Test permission validation
    print("\n9. Testing permission validation...")
    try:
        # Create instruction for test_user
        result = create_instruction(test_owner, "test instruction", 0)
        inst_id = result['instruction_id']
        
        # Try to delete with different owner
        delete_instruction(inst_id, "wrong_user")
        print("✗ Should have raised ValueError")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")
        # Clean up
        delete_instruction(inst_id, test_owner)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == '__main__':
    test_instruction_repository()
