# PDF Vectorizer Module

将PDF文档向量化并存储到Qdrant向量数据库的Python模块，支持实时进度跟踪。

## 🔥 最新改造 (2025-01)

### 改造说明

`PDFVectorizer` 已经重构为使用 `ks_infrastructure` 基础设施服务模块，不再需要手动传递各种服务的连接参数。

### 改造前后对比

**改造前（旧版本）**：
```python
from pdf_vectorizer import PDFVectorizer

vectorizer = PDFVectorizer(
    openai_api_key="your-api-key",
    openai_base_url="https://api.openai.com",
    openai_model="gpt-3.5-turbo",
    embedding_url="http://embedding-service/v1/embeddings",
    embedding_api_key="embedding-key",
    qdrant_url="http://qdrant:6333",
    qdrant_api_key="qdrant-key",
    collection_name="pdf_knowledge_base",
    vector_size=4096
)
```

**改造后（新版本）**：
```python
from pdf_vectorizer import PDFVectorizer

# 简化的初始化 - 所有服务配置自动从 ks_infrastructure 获取
vectorizer = PDFVectorizer(
    collection_name="pdf_knowledge_base",  # 可选，默认值
    vector_size=4096  # 可选，默认值
)

# 或者使用完全默认配置
vectorizer = PDFVectorizer()
```

### 主要改进

1. ✅ **极度简化初始化**: 不再需要传递繁琐的连接参数（9个参数减少到2个可选参数）
2. ✅ **统一配置管理**: 所有服务配置（包括 OpenAI model）统一在 `ks_infrastructure/configs/default.py` 中管理
3. ✅ **自动模型配置**: OpenAI 模型自动从 ks_infrastructure 配置读取（默认：DeepSeek-V3.1-Ksyun）
4. ✅ **自动连接池**: 利用 `ks_infrastructure` 的连接池和缓存机制，提高性能
5. ✅ **业务逻辑不变**: 所有对外接口保持完全兼容，无需修改现有调用代码
6. ✅ **更易维护**: 配置与业务逻辑完全分离，修改配置无需修改代码

### 内部实现改动

- **OpenAI服务**: 使用 `ks_openai()` 替代直接创建 `OpenAI` 客户端
- **Embedding服务**: 使用 `ks_embedding()` 替代直接发送HTTP请求
- **Qdrant服务**: 使用 `ks_qdrant()` 替代直接创建 `QdrantClient`

### 配置说明

所有服务配置位于 `ks_infrastructure/configs/default.py`：
```python
# OpenAI配置（包括默认模型）
OPENAI_CONFIG = {
    "api_key": "...",
    "base_url": "...",
    "model": "DeepSeek-V3.1-Ksyun"  # 默认模型
}

# Embedding配置
EMBEDDING_CONFIG = {
    "url": "...",
    "api_key": "..."
}

# Qdrant配置
QDRANT_CONFIG = {
    "url": "...",
    "api_key": "..."
}
```

**注意**: OpenAI 的 `model` 参数会被自动应用于所有 PDF 摘要生成操作。

### 测试验证

运行测试套件验证改造：
```bash
python pdf_vectorizer/test/test_vectorizer_refactor.py
```

---

## 功能特性

- ✅ **PDF解析**：使用 `pdf_to_json` 将PDF解析为结构化JSON
- ✅ **智能摘要**：使用LLM为每页内容生成摘要
- ✅ **双路向量化**：同时对摘要和全文内容生成向量
- ✅ **双路召回**：支持摘要向量、内容向量、双路召回三种模式
- ✅ **向量存储**：存储到Qdrant数据库，支持语义搜索
- ✅ **所有者管理**：支持多用户文档隔离
- ✅ **自动去重**：按文件名+所有者自动删除重复文档
- ✅ **实时进度**：提供进度对象，应用层可轮询或yield推送
- ✅ **页面查询**：根据文件名和页码快速获取切片信息
- ✅ **可见性控制**：支持公开/私有文档，可动态修改可见性

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

### 基本用法（新版本）

```python
from pdf_vectorizer import PDFVectorizer

# 最简单的方式：使用完全默认配置
vectorizer = PDFVectorizer()

# 或自定义 collection 和 vector size
vectorizer = PDFVectorizer(
    collection_name="my_knowledge_base",  # 可选
    vector_size=4096  # 可选
)

# 注意：OpenAI 模型自动从 ks_infrastructure 配置读取（DeepSeek-V3.1-Ksyun）

# 向量化PDF（默认为私有文档）
result = vectorizer.vectorize_pdf("document.pdf", owner="user123")
print(f"处理完成：{result['processed_pages']} 页")

# 向量化PDF为公开文档
result = vectorizer.vectorize_pdf("document.pdf", owner="user123", is_public=1)

# 搜索
results = vectorizer.search("查询内容", mode="dual", limit=5)

# 根据页码获取内容
pages = vectorizer.get_pages(
    filename="document.pdf",
    page_numbers=[1, 2, 3],
    fields=["page_number", "summary", "content"]
)

# 修改文档可见性
result = vectorizer.update_document_visibility(
    filename="document.pdf",
    owner="user123",
    is_public=1  # 设置为公开
)
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

### 4. 根据页码获取切片信息

快速获取指定页面的内容，无需重新解析PDF。

```python
# 获取所有字段
pages = vectorizer.get_pages(
    filename="document.pdf",
    page_numbers=[1, 2, 3]
)

# 只获取特定字段
pages = vectorizer.get_pages(
    filename="document.pdf",
    page_numbers=[1, 3, 5, 7],
    fields=["page_number", "summary", "content"]
)

# 使用owner过滤
pages = vectorizer.get_pages(
    filename="document.pdf",
    page_numbers=[1, 2],
    fields=["page_number", "summary"],
    owner="user123"
)

# 返回结果
for page in pages:
    print(f"Page {page['page_number']}: {page['summary']}")
```

**支持的字段**：
- `filename`: 文件名
- `page_number`: 页码
- `summary`: LLM生成的摘要
- `content`: 页面完整内容
- `owner`: 文档所有者
- `is_public`: 可见性（0=私有，1=公开）

**特性**：
- 支持一次获取多页
- 支持选择性返回字段（减少数据传输）
- 支持owner过滤
- 返回顺序与请求顺序一致
- 页面不存在时自动跳过

## API文档

### PDFVectorizer

**主要方法**：

1. `vectorize_pdf(pdf_path, owner, is_public=0, verbose=True)` - 向量化PDF文档
   - `is_public`: 0=私有（默认），1=公开
2. `search(query, limit=5, mode="dual", owner=None, verbose=True)` - 语义搜索
   - `owner`: 指定owner时，返回owner的文档+公开文档
3. `get_pages(filename, page_numbers, fields=None, owner=None, verbose=False)` - 获取指定页面
4. `get_document_list(owner, verbose=True)` - 获取文档列表
   - 返回owner的文档+公开文档（去重）
5. `delete_document(filename, owner, verbose=True)` - 删除文档
6. `update_document_visibility(filename, owner, is_public, verbose=True)` - 修改文档可见性
   - `is_public`: 1=公开，0=私有

详见完整文档或代码注释。

### 5. 文档可见性管理

支持公开/私有文档管理，控制知识切片的访问权限。

```python
# 上传私有文档（默认）
vectorizer.vectorize_pdf("private_doc.pdf", owner="user123")

# 上传公开文档
vectorizer.vectorize_pdf("public_doc.pdf", owner="user123", is_public=1)

# 将私有文档设置为公开
result = vectorizer.update_document_visibility(
    filename="private_doc.pdf",
    owner="user123",
    is_public=1
)
print(f"已更新 {result['updated_count']} 页为公开")

# 将公开文档设置为私有
result = vectorizer.update_document_visibility(
    filename="public_doc.pdf",
    owner="user123",
    is_public=0
)
print(f"已更新 {result['updated_count']} 页为私有")
```

**is_public 字段说明**：
- `0`: 私有文档（默认），只有 owner 可以访问
- `1`: 公开文档，所有用户都可以访问

**使用场景**：
- 个人笔记、私密文档 → `is_public=0`
- 公司知识库、共享文档 → `is_public=1`
- 动态权限管理 → 使用 `update_document_visibility` 修改

### 6. 权限过滤搜索

搜索时支持 owner 过滤，返回用户有权访问的文档。

```python
# 不指定owner，搜索所有文档
results = vectorizer.search("关键词", limit=5)

# 指定owner，返回：owner的文档 + 公开文档
results = vectorizer.search("关键词", limit=5, owner="user123")
```

**权限逻辑**：
- 未指定 `owner`: 返回所有文档
- 指定 `owner`: 返回 `owner=user123` OR `is_public=1` 的文档

### 7. 获取文档列表

获取用户有权访问的所有文档列表。

```python
# 获取user123的文档列表（包括公开文档）
document_list = vectorizer.get_document_list(owner="user123")

for doc in document_list:
    print(f"文件名: {doc['filename']}")
    print(f"所有者: {doc['owner']}")
    print(f"可见性: {'公开' if doc['is_public'] == 1 else '私有'}")
    print(f"页数: {doc['page_count']}")
    print(f"Point ID: {doc['point_id']}")
```

**返回内容**：
- `filename`: 文件名
- `owner`: 文档所有者
- `is_public`: 可见性（0=私有，1=公开）
- `point_id`: 第一个页面的 point ID
- `page_count`: 文档总页数

**特点**：
- 自动去重（按filename）
- 不包含内容和摘要，只有元数据
- 返回 owner 的文档 + 所有公开文档
- 按文件名排序

## 许可证

MIT License
