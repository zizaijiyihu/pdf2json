#!/usr/bin/env python3
"""
Quick script to query specific pages from 0cd2ede3be2b45a84ec5a324cc3b126f.pdf
"""

import sys
import os

# Import configuration and vectorizer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdf_vectorizer import PDFVectorizer

# Configuration from service_demo.py
OPENAI_CONFIG = {
    "api_key": "85c923cc-9dcf-467a-89d5-285d3798014d",
    "base_url": "https://kspmas.ksyun.com/v1/",
    "model": "DeepSeek-V3.1-Ksyun"
}

EMBEDDING_CONFIG = {
    "url": "http://10.69.86.20/v1/embeddings",
    "api_key": "7c64b222-4988-4e6a-bb26-48594ceda8a9"
}

QDRANT_CONFIG = {
    "url": "http://120.92.109.164:6333/",
    "api_key": "rsdyxjh"
}

def main():
    # Initialize vectorizer
    print("Initializing PDFVectorizer...")
    vectorizer = PDFVectorizer(
        openai_api_key=OPENAI_CONFIG["api_key"],
        openai_base_url=OPENAI_CONFIG["base_url"],
        openai_model=OPENAI_CONFIG["model"],
        embedding_url=EMBEDDING_CONFIG["url"],
        embedding_api_key=EMBEDDING_CONFIG["api_key"],
        qdrant_url=QDRANT_CONFIG["url"],
        qdrant_api_key=QDRANT_CONFIG["api_key"],
        collection_name="pdf_knowledge_base",
        vector_size=4096
    )

    # Query pages 1 and 2
    print("\n" + "="*80)
    print("Querying: 0cd2ede3be2b45a84ec5a324cc3b126f.pdf, Pages 1 and 2")
    print("="*80)

    results = vectorizer.get_pages(
        filename="0cd2ede3be2b45a84ec5a324cc3b126f.pdf",
        page_numbers=[1, 2],
        verbose=True
    )

    # Display results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)

    for page in results:
        print(f"\n{'='*80}")
        print(f"PAGE {page.get('page_number')}")
        print(f"{'='*80}")
        print(f"Owner: {page.get('owner')}")
        print(f"Filename: {page.get('filename')}")

        print(f"\n📝 SUMMARY:")
        print("-"*80)
        print(page.get('summary', 'N/A'))

        print(f"\n📄 CONTENT:")
        print("-"*80)
        content = page.get('content', 'N/A')
        print(content)
        print()

    print("="*80)
    print(f"Total pages retrieved: {len(results)}")
    print("="*80)

if __name__ == "__main__":
    main()
