
import requests
import sys
import os
import json

def test_api_upload(pdf_path):
    url = "http://localhost:5000/api/upload"
    
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        return

    print(f"Uploading file: {pdf_path}")
    print(f"Target URL: {url}")
    
    files = {
        'file': (os.path.basename(pdf_path), open(pdf_path, 'rb'), 'application/pdf')
    }
    data = {'is_public': 0}
    
    try:
        response = requests.post(url, files=files, data=data, stream=True)
        print(f"Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            return

        print("\n--- SSE Stream Start ---")
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                print(decoded_line)
                # Optional: Parse JSON to verify structure
                if decoded_line.startswith('data: '):
                    try:
                        json_data = json.loads(decoded_line[6:])
                        stage = json_data.get('stage')
                        percent = json_data.get('progress_percent')
                        msg = json_data.get('message')
                        # print(f"Parsed: Stage={stage}, Progress={percent}%, Msg={msg}")
                    except:
                        pass
        print("--- SSE Stream End ---")
        
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_api_upload.py <pdf_path>")
        sys.exit(1)
        
    pdf_path = sys.argv[1]
    test_api_upload(pdf_path)
