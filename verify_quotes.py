import requests
import json
import sys

BASE_URL = "http://localhost:5000/api/quotes"

def print_result(name, response):
    print(f"=== {name} ===")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"Response: {response.text}")
    print("\n")
    return response

def main():
    # 1. Create a new quote
    print("1. Creating a new quote...")
    data = {
        "content": "Test Quote " + str(sys.argv[1] if len(sys.argv) > 1 else "1"),
        "is_fixed": 0
    }
    resp = requests.post(BASE_URL, json=data)
    print_result("Create Quote", resp)
    
    if resp.status_code != 200:
        print("Failed to create quote. Exiting.")
        return

    quote_id = resp.json().get('id')
    print(f"Created quote with ID: {quote_id}")

    # 2. Get quote list
    print("2. Getting quote list...")
    resp = requests.get(BASE_URL)
    print_result("Get Quote List", resp)

    # 3. Update the quote
    print("3. Updating the quote...")
    update_data = {
        "content": "Updated Quote Content",
        "is_fixed": 1
    }
    resp = requests.put(f"{BASE_URL}/{quote_id}", json=update_data)
    print_result("Update Quote", resp)

    # 4. Get quote list again to verify update and fixed status
    print("4. Getting quote list to verify update...")
    resp = requests.get(BASE_URL)
    print_result("Get Quote List (After Update)", resp)

    # 5. Delete the quote
    print("5. Deleting the quote...")
    resp = requests.delete(f"{BASE_URL}/{quote_id}")
    print_result("Delete Quote", resp)

    # 6. Get quote list again to verify deletion
    print("6. Getting quote list to verify deletion...")
    resp = requests.get(BASE_URL)
    print_result("Get Quote List (After Delete)", resp)

if __name__ == "__main__":
    main()
