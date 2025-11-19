# PDF Vectorizer Module

将PDF文档向量化并存储到Qdrant向量数据库的Python模块，支持实时进度跟踪。

## 功能特性

- ✅ **PDF解析**：使用 `pdf_to_json` 将PDF解析为结构化JSON
- ✅ **智能摘要**：使用LLM为每页内容生成摘要
- ✅ **双路向量化**：同时对摘要和全文内容生成向量
- ✅ **双路召回**：支持摘要向量、内容向量、双路召回三种模式
- ✅ **向量存储**：存储到Qdrant数据库，支持语义搜索
- ✅ **所有者管理**：支持多用户文档隔离
- ✅ **自动去重**：按文件名+所有者自动删除重复文档
- ✅ **实时进度**：提供进度对象，应用层可轮询或yield推送

## 工作流程

```
PDF文件 → 解析为JSON(按页) → 生成摘要 → 双路向量化 → 存入Qdrant
         [pdf2json]      [LLM]    [Summary+Content]  [向量数据库]
                                       ↓
                                   实时更新进度对象
```

## 安装依赖

```bash
pip install PyMuPDF openai requests qdrant-client
```

## 快速开始

### 基本用法

```python
from pdf_vectorizer import PDFVectorizer

# 创建向量化器
vectorizer = PDFVectorizer(
    openai_api_key="your-api-key",
    openai_base_url="https://api.openai.com/v1",
    openai_model="gpt-4",
    embedding_url="http://embedding-service/v1/embeddings",
    embedding_api_key="your-embedding-key",
    qdrant_url="http://localhost:6333",
    qdrant_api_key="your-qdrant-key"
)

# 向量化PDF（必须指定owner）
result = vectorizer.vectorize_pdf("document.pdf", owner="user123")
print(f"处理完成：{result['processed_pages']} 页")

# 搜索
results = vectorizer.search("查询内容", mode="dual", limit=5)
```

## 核心功能

### 1. 双路向量化

每页生成两个向量：摘要向量和内容向量。

### 2. 三种召回模式

- `mode="dual"`: 双路召回（默认）
- `mode="summary"`: 仅摘要召回
- `mode="content"`: 仅内容召回

### 3. 实时进度跟踪

```python
import threading

# 后台处理
thread = threading.Thread(target=lambda: vectorizer.vectorize_pdf("doc.pdf", "user123"))
thread.start()

# 轮询进度
while not vectorizer.progress.is_completed:
    progress = vectorizer.progress.get()
    print(f"{progress['progress_percent']:.1f}% - {progress['message']}")
    time.sleep(0.5)
```

## API文档

详见完整文档或代码注释。

## 许可证

MIT License
