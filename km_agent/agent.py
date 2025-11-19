"""
KM Agent - Knowledge Management Agent
Intelligent agent for knowledge base query and management
"""

import json
import sys
import os
from typing import List, Dict, Optional, Any
from openai import OpenAI

# Import PDFVectorizer
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pdf_vectorizer import PDFVectorizer


class KMAgent:
    """
    Knowledge Management Agent

    Features:
    - Query knowledge base using semantic search
    - Retrieve complete knowledge by fetching subsequent pages
    - Provide accurate answers based on knowledge base
    - Never fabricate information
    """

    SYSTEM_PROMPT = """你是金山知识管理agent，可以根据用户需求查询相关知识库，并且根据知识库返回的内容，给用户准确答案。

注意事项：
1. 如果某个知识切片的内容不完全，你可以继续查询出他后续的切片，以保证知识完全
2. 如果用户想要新增知识库，你需要提醒用户"点击输入框的知识标识，可以上传您的知识"
3. 如果知识库查询之后看不到匹配的答案，告诉用户知识库目前还没有此类信息
4. 你的结果可以是没有信息，但是一定不要自己编造信息
5. 回答时要基于知识库内容，引用具体的文档和页码

你有以下工具可以使用：
- search_knowledge: 搜索知识库，返回相关的知识切片
- get_pages: 根据文件名和页码获取完整的知识内容
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
        vector_size: int = 4096,
        verbose: bool = False
    ):
        """
        Initialize KM Agent

        Args:
            openai_api_key: OpenAI API key for LLM
            openai_base_url: OpenAI base URL
            openai_model: Model name for chat
            embedding_url: Embedding service URL
            embedding_api_key: Embedding service API key
            qdrant_url: Qdrant server URL
            qdrant_api_key: Qdrant API key
            collection_name: Qdrant collection name
            vector_size: Vector dimension size
            verbose: Whether to print debug information
        """
        self.verbose = verbose

        # LLM client
        self.llm_client = OpenAI(
            api_key=openai_api_key,
            base_url=openai_base_url
        )
        self.llm_model = openai_model

        # Vectorizer for knowledge base operations
        self.vectorizer = PDFVectorizer(
            openai_api_key=openai_api_key,
            openai_base_url=openai_base_url,
            openai_model=openai_model,
            embedding_url=embedding_url,
            embedding_api_key=embedding_api_key,
            qdrant_url=qdrant_url,
            qdrant_api_key=qdrant_api_key,
            collection_name=collection_name,
            vector_size=vector_size
        )

        # Tool definitions for function calling
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_knowledge",
                    "description": "搜索知识库，返回与查询相关的知识切片。使用语义搜索找到最相关的文档页面。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索查询内容"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "返回结果数量，默认5",
                                "default": 5
                            },
                            "mode": {
                                "type": "string",
                                "enum": ["content"],
                                "description": "搜索模式：只使用content(内容)召回",
                                "default": "content"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_pages",
                    "description": "根据文件名和页码获取完整的知识内容。当需要查看完整内容或后续页面时使用。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "文档文件名"
                            },
                            "page_numbers": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "description": "要获取的页码列表，例如 [1, 2, 3]"
                            },
                            "fields": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "要返回的字段列表，可选值：filename, page_number, content, owner。默认返回 filename, page_number, content。"
                            }
                        },
                        "required": ["filename", "page_numbers"]
                    }
                }
            }
        ]

    def _search_knowledge(self, query: str, limit: int = 5, mode: str = "content") -> Dict:
        """
        Search knowledge base

        Args:
            query: Search query
            limit: Number of results
            mode: Search mode (dual/summary/content)

        Returns:
            Search results
        """
        if self.verbose:
            print(f"\n[Tool] search_knowledge: query='{query}', limit={limit}, mode={mode}")

        results = self.vectorizer.search(query, limit=limit, mode=mode, verbose=False)

        # Format results for LLM - only return content, no summary
        formatted_results = []

        if "content_results" in results:
            for result in results["content_results"]:
                formatted_results.append({
                    "filename": result["filename"],
                    "page_number": result["page_number"],
                    "score": result["score"],
                    "content": result["content"]  # Return full content, not preview
                })

        if self.verbose:
            print(f"[Tool] Found {len(formatted_results)} results")

        return {
            "success": True,
            "total_results": len(formatted_results),
            "results": formatted_results
        }

    def _get_pages(self, filename: str, page_numbers: List[int], fields: Optional[List[str]] = None) -> Dict:
        """
        Get specific pages from knowledge base

        Args:
            filename: Document filename
            page_numbers: List of page numbers to retrieve
            fields: Optional list of fields to return (default: filename, page_number, content)

        Returns:
            Page data
        """
        # Default fields: only content-related fields, no summary
        if fields is None:
            fields = ["filename", "page_number", "content"]

        if self.verbose:
            print(f"\n[Tool] get_pages: filename='{filename}', page_numbers={page_numbers}, fields={fields}")

        pages = self.vectorizer.get_pages(
            filename=filename,
            page_numbers=page_numbers,
            fields=fields,
            verbose=False
        )

        if self.verbose:
            print(f"[Tool] Retrieved {len(pages)} pages")

        return {
            "success": True,
            "total_pages": len(pages),
            "pages": pages
        }

    def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """
        Execute a tool function

        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments for the tool

        Returns:
            JSON string of tool result
        """
        try:
            if tool_name == "search_knowledge":
                result = self._search_knowledge(**tool_args)
            elif tool_name == "get_pages":
                result = self._get_pages(**tool_args)
            else:
                result = {"success": False, "error": f"Unknown tool: {tool_name}"}

            return json.dumps(result, ensure_ascii=False)

        except Exception as e:
            error_result = {"success": False, "error": str(e)}
            return json.dumps(error_result, ensure_ascii=False)

    def chat(self, user_message: str, history: Optional[List[Dict]] = None) -> Dict:
        """
        Chat with the agent

        Args:
            user_message: User's message
            history: Optional conversation history

        Returns:
            Dictionary containing:
            - response: Agent's response text
            - tool_calls: List of tool calls made (if any)
            - history: Updated conversation history
        """
        if history is None:
            history = []

        # Add system prompt if this is the first message
        if not history:
            messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        else:
            messages = history.copy()

        # Add user message
        messages.append({"role": "user", "content": user_message})

        tool_calls_made = []
        max_iterations = 5  # Prevent infinite loops
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            if self.verbose:
                print(f"\n[Iteration {iteration}] Calling LLM...")

            # Call LLM
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )

            assistant_message = response.choices[0].message

            # Add assistant message to history
            messages.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in (assistant_message.tool_calls or [])
                ] if assistant_message.tool_calls else None
            })

            # If no tool calls, we're done
            if not assistant_message.tool_calls:
                if self.verbose:
                    print(f"[Iteration {iteration}] No tool calls, finishing")
                break

            # Execute tool calls
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                if self.verbose:
                    print(f"[Iteration {iteration}] Executing tool: {tool_name}")

                # Execute tool
                tool_result = self._execute_tool(tool_name, tool_args)

                # Record tool call
                tool_calls_made.append({
                    "tool": tool_name,
                    "arguments": tool_args,
                    "result": json.loads(tool_result)
                })

                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })

        # Get final response
        final_response = messages[-1]["content"] if messages[-1]["role"] == "assistant" else "抱歉，我无法处理您的请求。"

        return {
            "response": final_response,
            "tool_calls": tool_calls_made,
            "history": messages
        }

    def run(self):
        """
        Run interactive chat session
        """
        print("="*80)
        print("金山知识管理 Agent")
        print("="*80)
        print("提示：输入 'quit' 或 'exit' 退出")
        print("="*80)

        history = None

        while True:
            try:
                user_input = input("\n用户: ").strip()

                if user_input.lower() in ['quit', 'exit', '退出']:
                    print("\n再见！")
                    break

                if not user_input:
                    continue

                print("\nAgent: ", end="", flush=True)

                result = self.chat(user_input, history)
                print(result["response"])

                history = result["history"]

                if self.verbose and result["tool_calls"]:
                    print(f"\n[Debug] Tool calls: {len(result['tool_calls'])}")
                    for i, tc in enumerate(result["tool_calls"], 1):
                        print(f"  {i}. {tc['tool']}: {tc['arguments']}")

            except KeyboardInterrupt:
                print("\n\n再见！")
                break
            except Exception as e:
                print(f"\n错误: {e}")
                if self.verbose:
                    import traceback
                    traceback.print_exc()
