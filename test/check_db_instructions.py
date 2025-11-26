
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from instruction_repository.db import get_all_instructions

def check_instructions():
    # Check for both potential users
    users = ["hu", "huxiaoxiao", "default"]
    
    print("Checking instructions in database...")
    print("=" * 50)
    
    for user in users:
        print(f"\nUser: {user}")
        try:
            instructions = get_all_instructions(user, include_inactive=True)
            if not instructions:
                print("  No instructions found.")
            else:
                for inst in instructions:
                    status = "Active" if inst['is_active'] else "Inactive"
                    print(f"  [{inst['id']}] {status} (Priority: {inst['priority']}): {inst['content']}")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    check_instructions()
