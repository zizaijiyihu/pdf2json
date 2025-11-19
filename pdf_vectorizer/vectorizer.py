"""
PDF Vectorizer

Converts PDF files to vectors and stores them in Qdrant database.
"""

import os
import json
import requests
from typing import Dict, List, Optional
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, NamedVector, Filter, FieldCondition, MatchValue
import sys

# Import pdf_to_json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pdf_to_json import PDFToJSONConverter


class VectorizationProgress:
    """
    Progress tracking object for PDF vectorization.
    Application layer can query this object to get current progress.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset progress to initial state"""
        self._data = {
            "stage": "idle",  # idle, init, parsing, processing, storing, completed, error
            "total_pages": 0,
            "current_page": 0,
            "progress_percent": 0.0,
            "message": "",
            "current_step": "",
            "error": None,
            "data": {}
        }

    def update(self, **kwargs):
        """Update progress data"""
        self._data.update(kwargs)

    def get(self):
        """Get current progress snapshot"""
        return self._data.copy()

    def get_field(self, field):
        """Get specific field value"""
        return self._data.get(field)

    @property
    def is_completed(self):
        """Check if processing is completed"""
        return self._data["stage"] == "completed"

    @property
    def is_error(self):
        """Check if there's an error"""
        return self._data["stage"] == "error"

    @property
    def is_processing(self):
        """Check if currently processing"""
        return self._data["stage"] in ["init", "parsing", "processing", "storing"]


class PDFVectorizer:
    """
    Vectorize PDF content and store in Qdrant database.

    Features:
    - Parse PDF using pdf_to_json
    - Generate summary for each page using LLM
    - Vectorize both summary and full content (dual vectors)
    - Store in Qdrant with metadata
    - Support dual-path retrieval (summary + content)
    - Auto deduplication by filename
    - Real-time progress tracking via progress object
    """

    def __init__(
        self,
        openai_api_key: str,
        openai_base_url: str,
        openai_model: str,
        embedding_url: str,
        embedding_api_key: str,
        qdrant_url: str,
        qdrant_api_key: str,
        collection_name: str = "pdf_knowledge_base",
        vector_size: int = 4096
    ):
        """
        Initialize PDFVectorizer.

        Args:
            openai_api_key: OpenAI API key for LLM
            openai_base_url: OpenAI base URL
            openai_model: Model name for summarization
            embedding_url: Embedding service URL
            embedding_api_key: Embedding service API key
            qdrant_url: Qdrant server URL
            qdrant_api_key: Qdrant API key
            collection_name: Qdrant collection name
            vector_size: Vector dimension size
        """
        # PDF parser
        self.pdf_converter = PDFToJSONConverter()

        # LLM client for summarization
        self.llm_client = OpenAI(
            api_key=openai_api_key,
            base_url=openai_base_url
        )
        self.llm_model = openai_model

        # Embedding service config
        self.embedding_url = embedding_url
        self.embedding_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {embedding_api_key}"
        }

        # Qdrant client
        self.qdrant_client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key
        )
        self.collection_name = collection_name
        self.vector_size = vector_size

        # Progress tracking object
        self.progress = VectorizationProgress()

        # Ensure collection exists
        self._ensure_collection()

    def _ensure_collection(self):
        """Ensure Qdrant collection exists, create if not."""
        try:
            collections = self.qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if self.collection_name in collection_names:
                # Collection exists, try to delete and recreate to ensure correct schema
                print(f"Collection {self.collection_name} exists, recreating...")
                try:
                    self.qdrant_client.delete_collection(collection_name=self.collection_name)
                    print(f"✓ Deleted existing collection: {self.collection_name}")
                except:
                    pass

            # Create collection with dual named vectors (summary + content)
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "summary_vector": VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    ),
                    "content_vector": VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                }
            )
            print(f"✓ Created collection with dual vectors: {self.collection_name}")
        except Exception as e:
            raise Exception(f"Failed to ensure collection: {e}")

    def _generate_summary(self, page_content: str, page_number: int) -> str:
        """
        Generate summary for a page using LLM.

        Args:
            page_content: Text content of the page
            page_number: Page number

        Returns:
            Summary text
        """
        try:
            prompt = f"""请为以下PDF第{page_number}页的内容生成一个简洁的摘要（100-200字）。
摘要应该：
1. 提取关键信息和主要观点
2. 保留重要的数据和结论
3. 忽略格式和样式信息
4. 使用简洁的语言

页面内容：
{page_content}

请直接输出摘要，不需要前缀说明。"""

            completion = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "你是一个专业的文档摘要助手。"},
                    {"role": "user", "content": prompt}
                ]
            )

            return completion.choices[0].message.content.strip()
        except Exception as e:
            return f"生成摘要失败: {str(e)}"

    def _get_embedding(self, text: str) -> List[float]:
        """
        Get embedding vector for text using curl-based embedding service.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        try:
            data = {
                "model": "text-embedding",
                "input": text,
                "encoding_format": "float"
            }

            response = requests.post(
                self.embedding_url,
                headers=self.embedding_headers,
                data=json.dumps(data)
            )

            if response.status_code == 200:
                result = response.json()
                return result["data"][0]["embedding"]
            else:
                raise Exception(f"Embedding request failed: {response.status_code}, {response.text}")
        except Exception as e:
            raise Exception(f"Failed to get embedding: {e}")

    def delete_document(self, filename: str, owner: str, verbose: bool = True):
        """
        Delete all pages of a document by filename and owner.
        This is a public method that can be called externally.

        Args:
            filename: Document filename to delete
            owner: Owner of the document
            verbose: Whether to print progress
        """
        try:
            # Use scroll to get all points with matching filename and owner
            scroll_result = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="filename",
                            match=MatchValue(value=filename)
                        ),
                        FieldCondition(
                            key="owner",
                            match=MatchValue(value=owner)
                        )
                    ]
                ),
                limit=1000  # Assume max 1000 pages per document
            )

            points_to_delete = [point.id for point in scroll_result[0]]

            if points_to_delete:
                self.qdrant_client.delete(
                    collection_name=self.collection_name,
                    points_selector=points_to_delete
                )
                if verbose:
                    print(f"✓ Deleted {len(points_to_delete)} existing pages for: {filename} (owner: {owner})")
            else:
                if verbose:
                    print(f"✓ No existing pages found for: {filename} (owner: {owner})")

        except Exception as e:
            if verbose:
                print(f"⚠ Warning: Failed to delete existing pages: {e}")

    def vectorize_pdf(self, pdf_path: str, owner: str, verbose: bool = True) -> Dict:
        """
        Vectorize entire PDF and store in Qdrant.
        Uses dual-vector strategy: summary_vector + content_vector
        Updates self.progress object during processing for real-time tracking.

        Args:
            pdf_path: Path to PDF file
            owner: Owner of the document
            verbose: Whether to print progress

        Returns:
            Dictionary with processing results
        """
        # Reset progress
        self.progress.reset()

        filename = os.path.basename(pdf_path)

        # Update progress: Initialization
        self.progress.update(
            stage="init",
            message=f"开始处理文档: {filename}",
            current_step="初始化",
            progress_percent=0,
            data={"filename": filename, "owner": owner}
        )

        if verbose:
            print(f"\n{'='*60}")
            print(f"Processing PDF: {filename}")
            print(f"Owner: {owner}")
            print(f"{'='*60}\n")

        # Step 0: Delete existing document with same filename and owner
        self.progress.update(
            message="检查并删除已存在的文档",
            current_step="去重处理",
            progress_percent=5
        )

        if verbose:
            print("Step 0: Checking for duplicate documents...")
        self.delete_document(filename, owner, verbose)

        # Step 1: Parse PDF to JSON
        self.progress.update(
            stage="parsing",
            message="正在解析PDF文档...",
            current_step="PDF解析",
            progress_percent=10
        )

        if verbose:
            print("\nStep 1: Parsing PDF...")
        result = self.pdf_converter.convert(pdf_path, analyze_images=False, verbose=False)

        total_pages = result['total_pages']
        self.progress.update(
            total_pages=total_pages,
            message=f"PDF解析完成，共 {total_pages} 页",
            progress_percent=15
        )

        if verbose:
            print(f"✓ Parsed {total_pages} pages\n")

        # Step 2-5: Process each page
        self.progress.update(stage="processing")
        points = []
        point_id = 0

        for page in result['pages']:
            page_number = page['page_number']
            paragraphs = page['paragraphs']

            # Combine all paragraphs into page content
            page_content = "\n\n".join(paragraphs)

            if not page_content.strip():
                if verbose:
                    print(f"Page {page_number}: Empty, skipping...")
                continue

            # Calculate progress (15% - 85% range for processing)
            page_progress = 15 + (page_number / total_pages) * 70

            # Update progress: Processing page
            self.progress.update(
                current_page=page_number,
                message=f"正在处理第 {page_number}/{total_pages} 页",
                current_step="生成摘要",
                progress_percent=page_progress,
                data={"page_number": page_number}
            )

            if verbose:
                print(f"Processing Page {page_number}...")

            # Step 2: Generate summary
            if verbose:
                print(f"  - Generating summary...")
            summary = self._generate_summary(page_content, page_number)

            # Step 3: Get embedding vectors for BOTH summary and content
            self.progress.update(
                current_step="摘要向量化",
                progress_percent=page_progress + (70 / total_pages * 0.3),
                message=f"第 {page_number} 页：摘要向量化"
            )

            if verbose:
                print(f"  - Generating summary vector...")
            summary_embedding = self._get_embedding(summary)

            self.progress.update(
                current_step="内容向量化",
                progress_percent=page_progress + (70 / total_pages * 0.6),
                message=f"第 {page_number} 页：内容向量化"
            )

            if verbose:
                print(f"  - Generating content vector...")
            content_embedding = self._get_embedding(page_content)

            # Step 4: Prepare point with dual vectors
            point = PointStruct(
                id=point_id,
                vector={
                    "summary_vector": summary_embedding,
                    "content_vector": content_embedding
                },
                payload={
                    "owner": owner,
                    "filename": filename,
                    "page_number": page_number,
                    "summary": summary,
                    "content": page_content
                }
            )
            points.append(point)
            point_id += 1

            self.progress.update(
                current_step="页面完成",
                progress_percent=page_progress + (70 / total_pages),
                message=f"第 {page_number} 页处理完成",
                data={
                    "page_number": page_number,
                    "summary_length": len(summary),
                    "content_length": len(page_content)
                }
            )

            if verbose:
                print(f"  ✓ Page {page_number} processed (summary: {len(summary)} chars, content: {len(page_content)} chars)\n")

        # Step 5: Store in Qdrant
        self.progress.update(
            stage="storing",
            current_page=total_pages,
            message=f"正在存储 {len(points)} 个向量到数据库...",
            current_step="数据存储",
            progress_percent=90,
            data={"total_vectors": len(points)}
        )

        if verbose:
            print(f"Storing {len(points)} vectors in Qdrant...")

        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=points
        )

        # Completed
        final_result = {
            "filename": filename,
            "owner": owner,
            "total_pages": total_pages,
            "processed_pages": len(points),
            "collection": self.collection_name
        }

        self.progress.update(
            stage="completed",
            message=f"处理完成！成功存储 {len(points)} 页",
            current_step="完成",
            progress_percent=100,
            data=final_result
        )

        if verbose:
            print(f"✓ Successfully stored {len(points)} pages in Qdrant\n")
            print(f"{'='*60}")
            print(f"Processing complete!")
            print(f"{'='*60}\n")

        return final_result

    def search(
        self,
        query: str,
        limit: int = 5,
        mode: str = "dual",
        verbose: bool = True
    ) -> Dict[str, List[Dict]]:
        """
        Search similar pages by query.

        Args:
            query: Search query
            limit: Number of results to return per path
            mode: Retrieval mode - "dual" (both), "summary" (summary only), "content" (content only)
            verbose: Whether to print results

        Returns:
            Dictionary with keys depending on mode:
            - mode="dual": {"summary_results": [...], "content_results": [...]}
            - mode="summary": {"summary_results": [...]}
            - mode="content": {"content_results": [...]}
        """
        if mode not in ["dual", "summary", "content"]:
            raise ValueError(f"Invalid mode: {mode}. Must be 'dual', 'summary', or 'content'.")

        # Get query embedding
        query_embedding = self._get_embedding(query)

        if verbose:
            print(f"\n{'='*60}")
            print(f"Query: {query}")
            print(f"Mode: {mode.upper()}")
            print(f"{'='*60}\n")

        results = {}

        # Path 1: Search using summary_vector
        if mode in ["dual", "summary"]:
            if verbose:
                print("🔍 Searching via SUMMARY vector...")
            summary_search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=("summary_vector", query_embedding),
                limit=limit
            )

            summary_results = []
            for i, hit in enumerate(summary_search_results, 1):
                result = {
                    "rank": i,
                    "score": hit.score,
                    "filename": hit.payload["filename"],
                    "page_number": hit.payload["page_number"],
                    "summary": hit.payload["summary"],
                    "content": hit.payload["content"],
                    "retrieval_path": "summary"
                }
                summary_results.append(result)

                if verbose:
                    print(f"\n  Result #{i} (Score: {hit.score:.4f})")
                    print(f"  File: {result['filename']}, Page: {result['page_number']}")
                    print(f"  Summary: {result['summary'][:100]}...")

            results["summary_results"] = summary_results

        # Path 2: Search using content_vector
        if mode in ["dual", "content"]:
            if verbose and mode == "dual":
                print(f"\n\n🔍 Searching via CONTENT vector...")
            elif verbose:
                print("🔍 Searching via CONTENT vector...")

            content_search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=("content_vector", query_embedding),
                limit=limit
            )

            content_results = []
            for i, hit in enumerate(content_search_results, 1):
                result = {
                    "rank": i,
                    "score": hit.score,
                    "filename": hit.payload["filename"],
                    "page_number": hit.payload["page_number"],
                    "summary": hit.payload["summary"],
                    "content": hit.payload["content"],
                    "retrieval_path": "content"
                }
                content_results.append(result)

                if verbose:
                    print(f"\n  Result #{i} (Score: {hit.score:.4f})")
                    print(f"  File: {result['filename']}, Page: {result['page_number']}")
                    print(f"  Summary: {result['summary'][:100]}...")

            results["content_results"] = content_results

        if verbose:
            print(f"\n{'='*60}")
            if "summary_results" in results:
                print(f"Summary path: {len(results['summary_results'])} results")
            if "content_results" in results:
                print(f"Content path: {len(results['content_results'])} results")
            print(f"{'='*60}\n")

        return results
