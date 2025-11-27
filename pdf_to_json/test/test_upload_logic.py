
import sys
import os
import time
import threading
import json

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

from pdf_vectorizer import PDFVectorizer

def test_upload_logic(pdf_path):
    print(f"Testing upload logic for: {pdf_path}")
    
    # Initialize vectorizer
    vectorizer = PDFVectorizer()
    owner = "test_user"
    filename = os.path.basename(pdf_path)
    
    # Function to run vectorization in a thread (mimicking api.py)
    def vectorize():
        try:
            print("Starting vectorization thread...")
            vectorizer.vectorize_pdf(
                pdf_path,
                owner=owner,
                display_filename=filename,
                verbose=True
            )
            print("Vectorization thread finished.")
        except Exception as e:
            print(f"Vectorization failed: {e}")

    # Start thread
    thread = threading.Thread(target=vectorize)
    thread.start()
    
    # Poll progress (mimicking api.py)
    print("Starting progress polling...")
    last_page = -1
    start_time = time.time()
    
    while thread.is_alive():
        progress_data = vectorizer.progress.get()
        
        # Print progress if it changes or periodically
        stage = progress_data.get('stage')
        percent = progress_data.get('progress_percent')
        current_page = progress_data.get('current_page')
        message = progress_data.get('message')
        
        print(f"[POLL] Stage: {stage}, Progress: {percent}%, Page: {current_page}, Msg: {message}")
        
        if progress_data.get('stage') == 'completed':
            break
            
        if progress_data.get('stage') == 'error':
            print(f"Error detected: {progress_data.get('error')}")
            break
            
        time.sleep(1.0) # Poll every second
        
    thread.join()
    print("Test finished.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_upload_logic.py <pdf_path>")
        sys.exit(1)
        
    pdf_path = sys.argv[1]
    test_upload_logic(pdf_path)
