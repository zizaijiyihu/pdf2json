#!/usr/bin/env python3
"""
Test script for PDF Vectorizer module
"""

import sys
import os

# Import configuration from service_demo.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the vectorizer
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


def test_vectorize_pdf(pdf_path, owner="hu"):
    """Test vectorizing a PDF file"""
    print("="*60)
    print("Test: Vectorize PDF and Store in Qdrant")
    print("="*60)

    # Create vectorizer instance
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

    # Vectorize the PDF with owner
    result = vectorizer.vectorize_pdf(pdf_path, owner=owner, verbose=True)

    print("\n" + "="*60)
    print("Vectorization Result:")
    print("="*60)
    print(f"Filename: {result['filename']}")
    print(f"Total Pages: {result['total_pages']}")
    print(f"Processed Pages: {result['processed_pages']}")
    print(f"Collection: {result['collection']}")
    print("="*60)

    return vectorizer


def test_get_pages(vectorizer, filename):
    """Test getting specific pages by filename and page numbers"""
    print("\n\n" + "="*60)
    print("Test: Get Specific Pages")
    print("="*60)

    # Test 1: Get all fields for pages 1 and 2
    print("\n[Test 1] Get all fields for pages 1 and 2")
    print("-"*60)
    results = vectorizer.get_pages(
        filename=filename,
        page_numbers=[1, 2],
        verbose=True
    )

    print("\nResults:")
    for page in results:
        print(f"\n--- Page {page.get('page_number')} ---")
        print(f"Owner: {page.get('owner')}")
        print(f"Filename: {page.get('filename')}")
        print(f"\nSummary:")
        print(page.get('summary', 'N/A'))
        print(f"\nContent (first 300 chars):")
        content = page.get('content', 'N/A')
        print(content[:300] if content != 'N/A' else 'N/A')
        if len(content) > 300:
            print("...")

    # Test 2: Get only specific fields
    print("\n\n[Test 2] Get only page_number and summary for pages 1, 2, 3")
    print("-"*60)
    results = vectorizer.get_pages(
        filename=filename,
        page_numbers=[1, 2, 3],
        fields=["page_number", "summary"],
        verbose=True
    )

    print("\nResults:")
    for page in results:
        print(f"\n📄 Page {page.get('page_number')}:")
        print(page.get('summary', 'N/A'))

    # Test 3: Get with owner filter
    print("\n\n[Test 3] Get pages 1-2 with owner filter")
    print("-"*60)
    results = vectorizer.get_pages(
        filename=filename,
        page_numbers=[1, 2],
        fields=["page_number", "owner", "summary"],
        owner="hu",
        verbose=True
    )

    print("\nResults:")
    for page in results:
        print(f"\n📄 Page {page.get('page_number')} (Owner: {page.get('owner')})")
        print(page.get('summary', 'N/A')[:200] + "...")


def test_search(vectorizer):
    """Test searching in the vector database"""
    print("\n\n" + "="*60)
    print("Test: Search in Vector Database")
    print("="*60)

    # Test queries
    queries = [
        "关于北京人才网信息",
        "个人诚信声明信息说明"
    ]

    # Test Mode 1: Dual retrieval (default)
    print("\n" + "🔥"*30)
    print("MODE 1: DUAL RETRIEVAL (Summary + Content)")
    print("🔥"*30)
    for query in queries:
        results = vectorizer.search(query, limit=3, mode="dual", verbose=True)

        print("\n" + "="*60)
        print("Comparison Summary:")
        print("="*60)
        print(f"Summary Path Results: {len(results.get('summary_results', []))}")
        print(f"Content Path Results: {len(results.get('content_results', []))}")
        print("="*60)

    # Test Mode 2: Summary only
    print("\n\n" + "📝"*30)
    print("MODE 2: SUMMARY ONLY RETRIEVAL")
    print("📝"*30)
    query = queries[0]
    results = vectorizer.search(query, limit=3, mode="summary", verbose=True)

    # Test Mode 3: Content only
    print("\n\n" + "📄"*30)
    print("MODE 3: CONTENT ONLY RETRIEVAL")
    print("📄"*30)
    results = vectorizer.search(query, limit=3, mode="content", verbose=True)


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_vectorizer.py <pdf_file_path>")
        print("\nThis script will:")
        print("  1. Parse PDF to JSON using pdf_to_json")
        print("  2. Generate summary for each page using LLM")
        print("  3. Vectorize summaries using embedding service")
        print("  4. Store in Qdrant vector database (owner: 'hu')")
        print("  5. Test search functionality")
        print("  6. Test delete functionality")
        print("\nConfiguration is loaded from service_demo.py")
        sys.exit(1)

    pdf_path = sys.argv[1]
    owner = "hu"  # Default owner for testing

    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)

    try:
        # Test vectorization
        vectorizer = test_vectorize_pdf(pdf_path, owner=owner)

        # Test get_pages functionality
        filename = os.path.basename(pdf_path)
        test_get_pages(vectorizer, filename)

        # Test search
        test_search(vectorizer)

        # Test delete functionality
        print("\n\n" + "🗑️"*30)
        print("Test: Delete Document by Filename and Owner")
        print("🗑️"*30)

        filename = os.path.basename(pdf_path)
        print(f"\nDeleting document: {filename} (owner: {owner})")
        vectorizer.delete_document(filename, owner, verbose=True)

        print("\nVerifying deletion - searching again...")
        results = vectorizer.search("测试查询", limit=3, mode="summary", verbose=True)
        if not results.get("summary_results"):
            print("✓ Document successfully deleted - no results found")

        print("\n\n" + "="*60)
        print("ALL TESTS COMPLETED SUCCESSFULLY ✓")
        print("="*60)

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
