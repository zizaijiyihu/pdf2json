"""
PDF Vectorizer

Converts PDF files to vectors and stores them in Qdrant database.
"""

import os
import sys
from typing import Dict, List, Optional
from qdrant_client.models import Distance, VectorParams, PointStruct, NamedVector, Filter, FieldCondition, MatchValue

# Import pdf_to_json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pdf_to_json import PDFToJSONConverter

# Import ks_infrastructure services
from ks_infrastructure import ks_openai, ks_embedding, ks_qdrant


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
        collection_name: str = "pdf_knowledge_base",
        vector_size: int = 4096
    ):
        """
        Initialize PDFVectorizer.

        Args:
            collection_name: Qdrant collection name
            vector_size: Vector dimension size

        Note:
            OpenAI model is automatically configured from ks_infrastructure.
            Default model: DeepSeek-V3.1-Ksyun (configured in ks_infrastructure/configs/default.py)
        """
        # PDF parser
        self.pdf_converter = PDFToJSONConverter()

        # LLM client for summarization (using ks_infrastructure)
        self.llm_client = ks_openai()

        # Get model from ks_infrastructure config
        from ks_infrastructure.configs.default import OPENAI_CONFIG
        self.llm_model = OPENAI_CONFIG.get("model", "DeepSeek-V3.1-Ksyun")

        # Embedding service (using ks_infrastructure)
        self.embedding_service = ks_embedding()

        # Qdrant client (using ks_infrastructure)
        self.qdrant_client = ks_qdrant()
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
                # Collection exists, use it directly
                print(f"✓ Collection {self.collection_name} already exists, using it")
                return

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
        Get embedding vector for text using ks_infrastructure embedding service.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        try:
            return self.embedding_service.get_embedding_vector(text)
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

    def vectorize_pdf(self, pdf_path: str, owner: str, display_filename: str = None, verbose: bool = True) -> Dict:
        """
        Vectorize entire PDF and store in Qdrant.
        Uses dual-vector strategy: summary_vector + content_vector
        Updates self.progress object during processing for real-time tracking.

        Args:
            pdf_path: Path to PDF file
            owner: Owner of the document
            display_filename: Optional display filename to use in database (useful for preserving original names with special characters)
            verbose: Whether to print progress

        Returns:
            Dictionary with processing results
        """
        # Reset progress
        self.progress.reset()

        # Use display_filename if provided, otherwise extract from path
        filename = display_filename if display_filename else os.path.basename(pdf_path)

        try:
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
            result = self.pdf_converter.convert(pdf_path, analyze_images=True, verbose=False)

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

            # Get the maximum point_id from existing data to avoid ID conflicts
            try:
                collection_info = self.qdrant_client.get_collection(self.collection_name)
                if collection_info.points_count > 0:
                    # Scroll through all points to find max ID
                    scroll_result = self.qdrant_client.scroll(
                        collection_name=self.collection_name,
                        limit=10000,
                        with_payload=False,
                        with_vectors=False
                    )
                    existing_ids = [point.id for point in scroll_result[0]]
                    point_id = max(existing_ids) + 1 if existing_ids else 0
                else:
                    point_id = 0
            except Exception as e:
                if verbose:
                    print(f"⚠ Warning: Could not get max point_id, starting from 0: {e}")
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
        except Exception as e:
            error_msg = f"向量化失败: {str(e)}"
            if verbose:
                print(f"\n{'='*60}")
                print(f"ERROR: {error_msg}")
                print(f"{'='*60}\n")
            
            # 更新进度状态为错误
            self.progress.update(
                stage="error",
                message=error_msg,
                error=str(e),
                progress_percent=0
            )
            
            # 向上抛出异常,让调用者知道失败了
            raise

    def search(
        self,
        query: str,
        limit: int = 5,
        mode: str = "dual",
        owner: Optional[str] = None,
        verbose: bool = True
    ) -> Dict[str, List[Dict]]:
        """
        Search similar pages by query.

        Args:
            query: Search query
            limit: Number of results to return per path
            mode: Retrieval mode - "dual" (both), "summary" (summary only), "content" (content only)
            owner: Optional owner filter. If provided, only returns documents owned by this user
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

        # Build filter: owner=specified_owner (if provided)
        search_filter = None
        if owner is not None:
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="owner",
                        match=MatchValue(value=owner)
                    )
                ]
            )

        if verbose:
            print(f"\n{'='*60}")
            print(f"Query: {query}")
            print(f"Mode: {mode.upper()}")
            if owner:
                print(f"Owner filter: {owner}")
            print(f"{'='*60}\n")

        results = {}

        # Path 1: Search using summary_vector
        if mode in ["dual", "summary"]:
            if verbose:
                print("🔍 Searching via SUMMARY vector...")
            summary_search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=("summary_vector", query_embedding),
                limit=limit,
                query_filter=search_filter
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
                limit=limit,
                query_filter=search_filter
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

    def get_pages(
        self,
        filename: str,
        page_numbers: List[int],
        fields: Optional[List[str]] = None,
        owner: Optional[str] = None,
        verbose: bool = False
    ) -> List[Dict]:
        """
        Get page slices by filename and page numbers.

        Args:
            filename: Document filename
            page_numbers: List of page numbers to retrieve
            fields: List of fields to return. If None, returns all fields.
                   Available fields: "filename", "page_number", "summary", "content", "owner"
            owner: Optional owner filter. If provided, only returns pages for this owner.
            verbose: Whether to print progress

        Returns:
            List of dictionaries containing requested fields for each page.
            Pages are returned in the same order as page_numbers.
            If a page is not found, it will not be included in the results.

        Example:
            # Get summary and content for pages 1, 3, 5
            results = vectorizer.get_pages(
                filename="document.pdf",
                page_numbers=[1, 3, 5],
                fields=["page_number", "summary", "content"]
            )
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"Retrieving pages from: {filename}")
            print(f"Page numbers: {page_numbers}")
            print(f"Fields: {fields or 'all'}")
            if owner:
                print(f"Owner filter: {owner}")
            print(f"{'='*60}\n")

        # Available fields in payload
        available_fields = {"filename", "page_number", "summary", "content", "owner"}

        # If no fields specified, return all
        if fields is None:
            fields = list(available_fields)
        else:
            # Validate requested fields
            invalid_fields = set(fields) - available_fields
            if invalid_fields:
                raise ValueError(f"Invalid fields: {invalid_fields}. Available fields: {available_fields}")

        results = []

        # Query each page number
        for page_num in page_numbers:
            try:
                # Build filter conditions
                filter_conditions = [
                    FieldCondition(
                        key="filename",
                        match=MatchValue(value=filename)
                    ),
                    FieldCondition(
                        key="page_number",
                        match=MatchValue(value=page_num)
                    )
                ]

                # Add owner filter if provided
                if owner:
                    filter_conditions.append(
                        FieldCondition(
                            key="owner",
                            match=MatchValue(value=owner)
                        )
                    )

                # Search for this specific page
                scroll_result = self.qdrant_client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=Filter(must=filter_conditions),
                    limit=1
                )

                # If page found, extract requested fields
                if scroll_result[0]:
                    point = scroll_result[0][0]
                    page_data = {}

                    for field in fields:
                        if field in point.payload:
                            page_data[field] = point.payload[field]

                    results.append(page_data)

                    if verbose:
                        print(f"✓ Found page {page_num}")
                else:
                    if verbose:
                        print(f"✗ Page {page_num} not found")

            except Exception as e:
                if verbose:
                    print(f"✗ Error retrieving page {page_num}: {e}")
                continue

        if verbose:
            print(f"\n{'='*60}")
            print(f"Retrieved {len(results)} out of {len(page_numbers)} requested pages")
            print(f"{'='*60}\n")

        return results


