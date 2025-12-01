"""
KM Agent - Knowledge Management Agent
Intelligent agent for knowledge base query and management
"""

import json
import sys
import os
from typing import List, Dict, Optional, Any

# Import PDFVectorizer
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pdf_vectorizer import PDFVectorizer

# Import ks_infrastructure services
from ks_infrastructure import ks_openai, ks_user_info
from ks_infrastructure.configs.default import OPENAI_CONFIG
from ks_infrastructure import get_current_user

# Import agent tools
from km_agent.tools import AgentTools


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
5. **回答格式要求**：
   - 使用 Markdown 格式组织回答，严禁使用HTML标签
   - 使用标题、列表、粗体等格式使内容更清晰
   
6. **引用文档规则（极其重要，必须严格遵守）**：
   - **只有在search_knowledge 或 get_pages 工具中获得了目标知识，才能添加"引用文档"部分**
   - **如果没有匹配的答案，绝对不要显示"引用文档"部分**
   - **引用的文档名和页码必须完全来自工具返回的结果，禁止自己编造或猜测**
   - **引用文档必须使用Markdown链接语法，不能使用HTML <a>标签**
   - **引用格式（仅在有工具结果时使用）**：

     **引用文档：**
     - 📄 [居住证办理.pdf:2](http://pdf/居住证办理.pdf:2)
     - 📄 [另一个文档.pdf:3](http://pdf/另一个文档.pdf:3)

   - **Markdown链接格式规则**：
     * 显示文本格式：`文档名.pdf:页码`
     * 链接地址格式：`http://pdf/文档名.pdf:页码`
     * 完整示例：`[居住证办理.pdf:2](http://pdf/居住证办理.pdf:2)` ✓
     * 错误示例：
       - `[居住证办理.pdf:2](居住证办理.pdf:2)` ✗ 链接地址缺少 http://pdf/ 前缀
       - `[居住证办理.pdf:2]()` ✗ 链接地址为空
       - `<a href="">居住证办理.pdf:2</a>` ✗ 禁止使用HTML
   - **关键**：链接地址必须是 `http://pdf/文档名.pdf:页码` 格式！
   - **再次强调**：没有调用工具或工具无结果时，不要显示任何引用！

你有以下工具可以使用：
- search_knowledge: 搜索知识库，返回相关的知识切片
- get_pages: 根据文件名和页码获取完整的知识内容
- get_subordinate_attendance: 获取下属的考勤记录（需要权限验证）
- get_manager_style: 获取管理者的管理风格类型
- get_current_time: 获取当前时间
- get_subordinates: 获取指定用户的下属列表（不指定则获取当前用户的下属）
- get_subordinate_employee_info: 获取下属的员工信息（需要权限验证）
"""

    def __init__(
        self,
        verbose: bool = False,
        owner: str = None,
        conversation_id: str = None,
        enable_history: bool = False
    ):
        """
        Initialize KM Agent

        Args:
            verbose: Whether to print debug information
            owner: User identifier for loading custom instructions
            conversation_id: Conversation ID for history persistence (optional)
            enable_history: Whether to enable conversation history persistence

        Note:
            All configuration (OpenAI, embedding, Qdrant) is automatically loaded
            from ks_infrastructure services. No need to pass any parameters.
        """
        self.verbose = verbose
        self.owner = owner if owner else get_current_user()

        # LLM client (using ks_infrastructure)
        self.llm_client = ks_openai()
        self.llm_model = OPENAI_CONFIG.get("model", "DeepSeek-V3.1-Ksyun")

        # Vectorizer for knowledge base operations (using ks_infrastructure)
        # collection_name, vector_size are defaults in PDFVectorizer
        self.vectorizer = PDFVectorizer()

        # User info service for HR operations
        self.user_info_service = ks_user_info()

        # Initialize agent tools
        self.agent_tools = AgentTools(
            vectorizer=self.vectorizer,
            user_info_service=self.user_info_service,
            verbose=self.verbose
        )

        # Get tool definitions from agent tools
        self.tools = self.agent_tools.get_tool_definitions()

        # Load user custom instructions
        self.custom_instructions = self._load_instructions()

        # Build effective system prompt with custom instructions
        self.effective_system_prompt = self._build_system_prompt()
        
        # Conversation manager (optional)
        self.conversation_manager = None
        if enable_history:
            from km_agent.conversation_manager import ConversationManager
            self.conversation_manager = ConversationManager(
                owner=self.owner,
                conversation_id=conversation_id,
                verbose=self.verbose
            )
            # If no conversation_id provided, create a new conversation
            if not conversation_id:
                self.conversation_manager.start_conversation()
            
            if self.verbose:
                print(f"[ConversationManager] Enabled with conversation_id: {self.conversation_manager.get_conversation_id()}")

    def _load_instructions(self) -> list:
        """
        Load user's custom instructions from database
        
        Returns:
            List of active instructions ordered by priority
        """
        try:
            from instruction_repository import get_active_instructions
            return get_active_instructions(self.owner)
        except Exception as e:
            if self.verbose:
                print(f"Warning: Failed to load custom instructions: {e}")
            return []
    
    def _build_system_prompt(self) -> str:
        """
        Build effective system prompt by combining base prompt with custom instructions
        
        Returns:
            Complete system prompt string
        """
        base_prompt = self.SYSTEM_PROMPT
        
        if not self.custom_instructions:
            return base_prompt
        
        # Format custom instructions
        instructions_text = "\n".join([
            f"{i+1}. {inst['content']}" 
            for i, inst in enumerate(self.custom_instructions)
        ])
        
        # Append custom instructions to base prompt
        return f"""{base_prompt}

**用户自定义指示**（请严格遵守以下要求）：
{instructions_text}
"""
    
    def reload_instructions(self):
        """
        Reload custom instructions from database
        
        Useful when instructions are updated during agent lifecycle
        """
        self.custom_instructions = self._load_instructions()
        self.effective_system_prompt = self._build_system_prompt()
        if self.verbose:
            print(f"Reloaded {len(self.custom_instructions)} custom instructions")

    def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """
        Execute a tool function

        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments for the tool

        Returns:
            JSON string of tool result
        """
        return self.agent_tools.execute_tool(tool_name, tool_args, current_user=self.owner)

    def chat_stream(self, user_message: str, history: Optional[List[Dict]] = None):
        """
        Chat with the agent using streaming response

        Args:
            user_message: User's message
            history: Optional conversation history

        Yields:
            Dictionary chunks containing:
            - type: 'tool_call' | 'content' | 'done'
            - data: Tool call info or content chunk
        """
        if history is None:
            history = []

        # Always use the latest system prompt (important for dynamic instruction updates)
        if not history:
            messages = [{"role": "system", "content": self.effective_system_prompt}]
            # Save system message if conversation manager is enabled
            if self.conversation_manager:
                self.conversation_manager.save_system_message(self.effective_system_prompt)
        else:
            # Copy history but update the system prompt to reflect latest instructions
            messages = history.copy()
            # Replace the first system message with the updated prompt
            if messages and messages[0]["role"] == "system":
                messages[0] = {"role": "system", "content": self.effective_system_prompt}
                if self.verbose:
                    print(f"\n[DEBUG] Updated system prompt in history")
                    print(f"[DEBUG] Custom instructions count: {len(self.custom_instructions)}")

        # Add user message
        messages.append({"role": "user", "content": user_message})
        
        # Save user message to database
        if self.conversation_manager:
            self.conversation_manager.save_user_message(user_message)

        tool_calls_made = []
        max_iterations = 5
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            if self.verbose:
                print(f"\n[Iteration {iteration}] Calling LLM with streaming...")
                # Debug: Print full prompt
                print("-" * 20 + " Full Prompt " + "-" * 20)
                print(json.dumps(messages, ensure_ascii=False, indent=2))
                print("-" * 50)

            # Call LLM with streaming
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                stream=True
            )

            # Collect streaming response
            collected_content = ""
            collected_tool_calls = []
            current_tool_call = None

            for chunk in response:
                # Check if choices is empty (final chunk in stream)
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta

                # Handle content streaming
                if delta.content:
                    collected_content += delta.content
                    # Yield content chunk immediately for streaming experience
                    yield {
                        "type": "content",
                        "data": delta.content
                    }

                # Handle tool calls
                if delta.tool_calls:
                    for tc_chunk in delta.tool_calls:
                        if tc_chunk.index is not None:
                            # New tool call
                            while len(collected_tool_calls) <= tc_chunk.index:
                                collected_tool_calls.append({
                                    "id": "",
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""}
                                })
                            current_tool_call = collected_tool_calls[tc_chunk.index]

                        if tc_chunk.id:
                            current_tool_call["id"] = tc_chunk.id
                        if tc_chunk.function:
                            if tc_chunk.function.name:
                                current_tool_call["function"]["name"] = tc_chunk.function.name
                            if tc_chunk.function.arguments:
                                current_tool_call["function"]["arguments"] += tc_chunk.function.arguments

            # Add assistant message to history (in-memory)
            messages.append({
                "role": "assistant",
                "content": collected_content,
                "tool_calls": collected_tool_calls if collected_tool_calls else None
            })
            
            # Only save assistant message to database if it's the final answer (no tool calls)
            if not collected_tool_calls:
                if self.conversation_manager:
                    self.conversation_manager.save_assistant_message(
                        content=collected_content,
                        tool_calls=None
                    )
                
                # Get clean history (consistent with DB) for the frontend
                # Filter out intermediate tool calls and tool results from the returned history
                clean_history = []
                for msg in messages:
                    # Keep user and system messages
                    if msg['role'] in ['user', 'system']:
                        clean_history.append(msg)
                    # Keep assistant messages ONLY if they don't have tool_calls
                    elif msg['role'] == 'assistant' and not msg.get('tool_calls'):
                        clean_history.append(msg)
                    # Skip tool messages (role='tool')
                
                yield {
                    "type": "done",
                    "data": {
                        "tool_calls": tool_calls_made,
                        "history": clean_history,
                        "conversation_id": self.conversation_manager.get_conversation_id() if self.conversation_manager else None
                    }
                }
                break

            # Execute tool calls
            for tool_call in collected_tool_calls:
                tool_name = tool_call["function"]["name"]
                tool_args = json.loads(tool_call["function"]["arguments"])

                if self.verbose:
                    print(f"[Iteration {iteration}] Executing tool: {tool_name}")

                # Yield tool call notification (optional, frontend logs it but doesn't show in chat bubble)
                yield {
                    "type": "tool_call",
                    "data": {
                        "tool": tool_name,
                        "arguments": tool_args
                    }
                }

                # Execute tool
                tool_result = self._execute_tool(tool_name, tool_args)

                # Record tool call
                tool_calls_made.append({
                    "tool": tool_name,
                    "arguments": tool_args,
                    "result": json.loads(tool_result)
                })

                # Add tool result to messages (in-memory)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": tool_result
                })
                
                # Do NOT save tool message to database (as per user requirement)

    def run(self):
        """
        Run interactive chat session using streaming
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

                # Use chat_stream instead of chat
                tool_calls_made = []
                final_history = None

                for chunk in self.chat_stream(user_input, history):
                    if chunk["type"] == "content":
                        print(chunk["data"], end="", flush=True)
                    elif chunk["type"] == "tool_call":
                        tool_calls_made.append(chunk["data"])
                    elif chunk["type"] == "done":
                        final_history = chunk["data"]["history"]
                        tool_calls_made = chunk["data"]["tool_calls"]

                print()  # New line after response
                history = final_history

                if self.verbose and tool_calls_made:
                    print(f"\n[Debug] Tool calls: {len(tool_calls_made)}")
                    for i, tc in enumerate(tool_calls_made, 1):
                        print(f"  {i}. {tc['tool']}: {tc['arguments']}")

            except KeyboardInterrupt:
                print("\n\n再见！")
                break
            except Exception as e:
                print(f"\n错误: {e}")
                if self.verbose:
                    import traceback
                    traceback.print_exc()
