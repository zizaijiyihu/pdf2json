import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quote_repository.db import create_quote, update_quote, delete_quote, get_quotes, _ensure_table_exists

def test_quotes():
    print("--- Starting KS Quotes Verification ---")
    
    # Ensure table exists (idempotent)
    _ensure_table_exists()
    
    # 1. Create Quotes
    print("\n1. Testing Creation...")
    q1 = create_quote("Quote 1: Normal", is_fixed=0)
    print(f"Created Q1: {q1}")
    
    q2 = create_quote("Quote 2: Fixed", is_fixed=1)
    print(f"Created Q2 (Fixed): {q2}")
    
    # Verify Q2 is fixed
    quotes = get_quotes(page=1, page_size=10)
    items = quotes['items']
    print(f"Current quotes count: {quotes['total']}")
    
    # 2. Test Single Fixed Constraint (Insert)
    print("\n2. Testing Single Fixed Constraint (Insert)...")
    q3 = create_quote("Quote 3: New Fixed", is_fixed=1)
    print(f"Created Q3 (New Fixed): {q3}")
    
    # Verify Q2 is now 0 and Q3 is 1
    quotes = get_quotes(page=1, page_size=10)
    for item in quotes['items']:
        if item['id'] == q2['id']:
            print(f"Q2 is_fixed: {item['is_fixed']} (Expected: 0)")
            assert item['is_fixed'] == 0
        if item['id'] == q3['id']:
            print(f"Q3 is_fixed: {item['is_fixed']} (Expected: 1)")
            assert item['is_fixed'] == 1

    # 3. Test Single Fixed Constraint (Update)
    print("\n3. Testing Single Fixed Constraint (Update)...")
    # Update Q1 to be fixed
    update_quote(q1['id'], is_fixed=1)
    print(f"Updated Q1 to be fixed")
    
    # Verify Q3 is now 0 and Q1 is 1
    quotes = get_quotes(page=1, page_size=10)
    for item in quotes['items']:
        if item['id'] == q3['id']:
            print(f"Q3 is_fixed: {item['is_fixed']} (Expected: 0)")
            assert item['is_fixed'] == 0
        if item['id'] == q1['id']:
            print(f"Q1 is_fixed: {item['is_fixed']} (Expected: 1)")
            assert item['is_fixed'] == 1

    # 4. Test Pagination
    print("\n4. Testing Pagination...")
    # Create more quotes to ensure we have enough for pagination
    for i in range(4, 15):
        create_quote(f"Quote {i}", is_fixed=0)
        
    page1 = get_quotes(page=1, page_size=5)
    print(f"Page 1 items: {len(page1['items'])} (Expected: 5)")
    assert len(page1['items']) == 5
    
    page2 = get_quotes(page=2, page_size=5)
    print(f"Page 2 items: {len(page2['items'])} (Expected: 5)")
    assert len(page2['items']) == 5
    
    print(f"Total items: {page1['total']}")

    # 5. Test Deletion
    print("\n5. Testing Deletion...")
    delete_quote(q1['id'])
    print(f"Deleted Q1")
    
    try:
        update_quote(q1['id'], content="Should fail")
    except ValueError:
        print("Verified: Cannot update deleted quote")
        
    print("\n--- Verification Completed Successfully ---")

if __name__ == "__main__":
    try:
        test_quotes()
    except Exception as e:
        print(f"\nFAILED: {e}")
        import traceback
        traceback.print_exc()
