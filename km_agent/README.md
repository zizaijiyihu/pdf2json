# KM Agent - 知识管理智能代理

金山知识管理智能代理，能够根据用户需求查询知识库并提供准确答案。

## 功能特性

- ✅ **智能问答**：基于知识库内容提供准确答案
- ✅ **语义搜索**：使用向量搜索找到最相关的知识
- ✅ **完整知识获取**：自动获取后续页面以保证知识完整性
- ✅ **多轮对话**：支持上下文连续对话
- ✅ **工具调用**：自动调用 search_knowledge 和 get_pages 工具
- ✅ **准确可靠**：不会编造信息，只基于知识库回答
- ✅ **友好提示**：引导用户上传新知识

## 核心原则

1. **如果知识切片不完整** → 自动查询后续切片
2. **如果用户想上传知识** → 提醒"点击输入框的知识标识，可以上传您的知识"
3. **如果知识库无匹配内容** → 明确告知，不编造信息
4. **所有回答** → 必须基于知识库内容，引用文档和页码

## 快速开始

### 安装依赖

```bash
pip install openai requests qdrant-client PyMuPDF
```

### 基本用法

```python
from km_agent import KMAgent

# 初始化 Agent
agent = KMAgent(
    openai_api_key="your-api-key",
    openai_base_url="https://api.openai.com/v1",
    openai_model="gpt-4",
    embedding_url="http://embedding-service/v1/embeddings",
    embedding_api_key="your-embedding-key",
    qdrant_url="http://localhost:6333",
    qdrant_api_key="your-qdrant-key",
    collection_name="pdf_knowledge_base"
)

# 单次查询
result = agent.chat("关于北京人才网的信息")
print(result["response"])

# 多轮对话
history = None
result1 = agent.chat("查询第一页内容", history)
history = result1["history"]

result2 = agent.chat("总结一下", history)
print(result2["response"])

# 交互式模式
agent.run()
```

## 工作原理

```
用户问题 → LLM分析 → 调用工具 → 获取知识 → 生成答案
              ↓
        [工具选择]
              ↓
    ┌─────────┴─────────┐
    ↓                   ↓
search_knowledge    get_pages
(语义搜索)         (精确获取)
    ↓                   ↓
 返回相关切片      返回完整内容
    └─────────┬─────────┘
              ↓
        整合知识并回答
```

## 可用工具

### 1. search_knowledge

搜索知识库，返回与查询相关的知识切片。**只召回正文内容，不召回摘要**。

**参数**：
- `query` (string): 搜索查询内容
- `limit` (integer): 返回结果数量，默认 5
- `mode` (string): 搜索模式，固定为 `content`（内容召回）

**返回**：
```json
{
  "success": true,
  "total_results": 5,
  "results": [
    {
      "filename": "document.pdf",
      "page_number": 1,
      "score": 0.95,
      "content": "完整的页面内容..."
    }
  ]
}
```

### 2. get_pages

根据文件名和页码获取完整的知识内容。**默认只返回正文，不返回摘要**。

**参数**：
- `filename` (string): 文档文件名
- `page_numbers` (array): 页码列表，如 [1, 2, 3]
- `fields` (array, optional): 返回的字段列表，默认为 `["filename", "page_number", "content"]`

**返回**：
```json
{
  "success": true,
  "total_pages": 3,
  "pages": [
    {
      "filename": "document.pdf",
      "page_number": 1,
      "content": "完整内容..."
    }
  ]
}
```

## API 文档

### KMAgent

**初始化参数**：

- `openai_api_key`: OpenAI API key
- `openai_base_url`: OpenAI base URL
- `openai_model`: LLM 模型名称
- `embedding_url`: 向量化服务 URL
- `embedding_api_key`: 向量化服务 API key
- `qdrant_url`: Qdrant 服务器 URL
- `qdrant_api_key`: Qdrant API key
- `collection_name`: Qdrant 集合名称（默认 "pdf_knowledge_base"）
- `vector_size`: 向量维度（默认 4096）
- `verbose`: 是否打印调试信息（默认 False）

**主要方法**：

#### `chat(user_message, history=None)`

与 Agent 对话。

**参数**：
- `user_message` (str): 用户消息
- `history` (list, optional): 对话历史

**返回**：
```python
{
    "response": "Agent 的回复文本",
    "tool_calls": [
        {
            "tool": "search_knowledge",
            "arguments": {"query": "...", "limit": 5},
            "result": {...}
        }
    ],
    "history": [...]  # 更新后的对话历史
}
```

#### `run()`

启动交互式对话模式。

用户可以在终端中直接与 Agent 对话，输入 `quit` 或 `exit` 退出。

## 使用示例

### 示例 1: 知识查询

```python
agent = KMAgent(...)
result = agent.chat("北京人才网的具体信息是什么？")
print(result["response"])
```

Agent 会：
1. 调用 `search_knowledge` 搜索相关内容
2. 如果发现内容不完整，调用 `get_pages` 获取后续页面
3. 基于知识库内容给出准确答案，并引用文档和页码

### 示例 2: 多轮对话

```python
agent = KMAgent(...)

# 第一轮
result1 = agent.chat("查询第一页的内容")
history = result1["history"]

# 第二轮（带历史）
result2 = agent.chat("请详细说明一下", history)
print(result2["response"])
```

### 示例 3: 无匹配知识

```python
agent = KMAgent(...)
result = agent.chat("量子计算机的原理是什么？")
print(result["response"])
# 输出: "知识库目前还没有关于量子计算机的信息"
```

### 示例 4: 上传提醒

```python
agent = KMAgent(...)
result = agent.chat("我想添加一些新的文档")
print(result["response"])
# 输出: "点击输入框的知识标识，可以上传您的知识"
```

## 测试

运行测试脚本：

```bash
python test_km_agent.py
```

测试包括：
1. 单次查询知识库
2. 多轮对话
3. 知识库无匹配内容的情况
4. 上传知识提醒
5. 交互式对话模式

## 系统提示词

Agent 使用以下系统提示词：

```
你是金山知识管理agent，可以根据用户需求查询相关知识库，并且根据知识库返回的内容，给用户准确答案。

注意事项：
1. 如果某个知识切片的内容不完全，你可以继续查询出他后续的切片，以保证知识完全
2. 如果用户想要新增知识库，你需要提醒用户"点击输入框的知识标识，可以上传您的知识"
3. 如果知识库查询之后看不到匹配的答案，告诉用户知识库目前还没有此类信息
4. 你的结果可以是没有信息，但是一定不要自己编造信息
5. 回答时要基于知识库内容，引用具体的文档和页码
```

## 依赖模块

- `pdf_vectorizer`: PDF 向量化和知识库管理
- `openai`: LLM 调用和 Function Calling
- `qdrant-client`: 向量数据库客户端

## 许可证

MIT License
