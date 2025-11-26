# App API - 知识管理 HTTP API 服务

基于 Flask 的 HTTP API 服务，提供知识管理功能的 RESTful 接口。

## 功能特性

- ✅ **聊天接口** - 与 KM Agent 对话，支持 SSE 流式响应
- ✅ **文档列表** - 获取用户有权访问的文档列表（MinIO + MySQL）
- ✅ **文件上传** - 上传 PDF 到 MinIO 并向量化到 Qdrant，支持 SSE 实时进度
- ✅ **文件下载** - 从 MinIO 获取文档内容
- ✅ **文件删除** - 删除文档（MinIO + MySQL + Qdrant）
- ✅ **权限管理** - 修改文档公开/私有状态
- ✅ **图片分析** - 上传图片到临时存储并使用视觉服务分析

## 安装依赖

```bash
pip install flask werkzeug
```

## 快速开始

### 启动服务

```bash
python -m app_api.api
```

或

```bash
cd app_api
python api.py
```

服务将在 `http://0.0.0.0:5000` 启动

## API 接口文档

### 1. 聊天接口

**Endpoint**: `POST /api/chat`

**功能**: 与 KM Agent 对话，支持多轮连续对话

**Request Body**:
```json
{
    "message": "用户问题",
    "history": [...]  // 可选，上一轮的对话历史
}
```

**Response**: Server-Sent Events (SSE) 流

**Event Types**:
```
data: {"type": "content", "data": "流式内容片段"}
data: {"type": "tool_call", "data": {"tool_name": "search_knowledge"}}
data: {"type": "done", "data": {"history": [...]}}
data: {"type": "error", "data": {"error": "错误信息"}}
```

**示例**:
```bash
# 发起对话
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "居住证办理需要什么材料？"}'

# 带历史的对话
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "详细说明一下", "history": [...]}'
```

---

### 2. 获取文档列表

**Endpoint**: `GET /api/documents`

**功能**: 获取用户有权访问的文档列表（用户的文档 + 公开文档）

**注意**: 用户身份由服务器端通过 `get_current_user()` 自动获取

**Response**:
```json
{
    "success": true,
    "owner": "huxiaoxiao",
    "count": 3,
    "documents": [
        {
            "filename": "document.pdf",
            "owner": "huxiaoxiao",
            "is_public": 0,
            "file_size": 123456,
            "created_at": "2025-01-01T12:00:00",
            "content_type": "application/pdf"
        }
    ]
}
```

**示例**:
```bash
# 获取当前用户的文档列表
curl http://localhost:5000/api/documents
```

---

### 3. 上传并向量化 PDF

**Endpoint**: `POST /api/upload`

**功能**: 上传 PDF 到 MinIO，保存元数据到 MySQL，并向量化到 Qdrant，支持 SSE 实时进度更新

**Content-Type**: `multipart/form-data`

**Form Data**:
- `file`: PDF 文件（必需）
- `is_public`: 0=私有，1=公开（可选，默认 0）

**注意**: 用户身份由服务器端通过 `get_current_user()` 自动获取

**Response**: Server-Sent Events (SSE) 流

**Progress Events**:
```
data: {"stage": "init", "progress_percent": 0, "message": "开始处理..."}
data: {"stage": "parsing", "progress_percent": 10, "message": "解析PDF..."}
data: {"stage": "processing", "progress_percent": 50, "current_page": 5}
data: {"stage": "completed", "progress_percent": 100, "data": {...}}
```

**示例**:
```bash
# 上传私有文档
curl -X POST http://localhost:5000/api/upload \
  -F "file=@document.pdf" \
  -F "is_public=0"

# 上传公开文档
curl -X POST http://localhost:5000/api/upload \
  -F "file=@document.pdf" \
  -F "is_public=1"
```

**JavaScript 示例** (监听 SSE):
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('is_public', '0');

fetch('http://localhost:5000/api/upload', {
    method: 'POST',
    body: formData
}).then(response => {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    function read() {
        reader.read().then(({done, value}) => {
            if (done) return;

            const text = decoder.decode(value);
            const lines = text.split('\n');

            lines.forEach(line => {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.substring(6));
                    console.log('Progress:', data.progress_percent + '%', data.message);
                }
            });

            read();
        });
    }

    read();
});
```

---

### 4. 删除文档

**Endpoint**: `DELETE /api/documents/<filename>`

**功能**: 删除指定文档

**注意**: 用户身份由服务器端通过 `get_current_user()` 自动获取

**Response**:
```json
{
    "success": true,
    "filename": "document.pdf",
    "owner": "huxiaoxiao",
    "message": "Document deleted successfully"
}
```

**示例**:
```bash
# 删除文档
curl -X DELETE http://localhost:5000/api/documents/document.pdf
```

---

### 5. 修改文档可见性

**Endpoint**: `PUT /api/documents/<filename>/visibility`

**功能**: 修改文档为公开/私有

**注意**: 用户身份由服务器端通过 `get_current_user()` 自动获取

**Request Body**:
```json
{
    "is_public": 1  // 0=私有, 1=公开
}
```

**Response**:
```json
{
    "success": true,
    "filename": "document.pdf",
    "owner": "huxiaoxiao",
    "is_public": 1,
    "message": "Visibility updated successfully"
}
```

**示例**:
```bash
# 设置为公开
curl -X PUT http://localhost:5000/api/documents/document.pdf/visibility \
  -H "Content-Type: application/json" \
  -d '{"is_public": 1}'

# 设置为私有
curl -X PUT http://localhost:5000/api/documents/document.pdf/visibility \
  -H "Content-Type: application/json" \
  -d '{"is_public": 0}'
```

---

### 6. 获取文档内容

**Endpoint**: `GET /api/documents/<filename>/content`

**功能**: 从 MinIO 获取 PDF 文件内容用于查看

**注意**: 用户身份由服务器端通过 `get_current_user()` 自动获取

**Response**: PDF 文件二进制内容

**示例**:
```bash
# 获取文档内容
curl http://localhost:5000/api/documents/document.pdf/content -o document.pdf
```

---

### 7. 图片上传与分析

**Endpoint**: `POST /api/analyze-image`

**功能**: 上传图片到临时存储并使用视觉服务分析

**Content-Type**: `multipart/form-data`

**Form Data**:
- `file`: 图片文件（必需，支持 png, jpg, jpeg, gif, bmp, webp）
- `username`: 用户名（可选，默认 "system"）
- `prompt`: 分析提示词（可选，使用默认提示词）

**Response**:
```json
{
    "success": true,
    "image_url": "http://...",
    "analysis": "图片分析结果"
}
```

**示例**:
```bash
# 上传并分析图片
curl -X POST http://localhost:5000/api/analyze-image \
  -F "file=@image.png" \
  -F "username=user123" \
  -F "prompt=请描述这张图片"
```

---

### 健康检查

**Endpoint**: `GET /api/health`

**功能**: 检查服务状态

**Response**:
```json
{
    "status": "healthy",
    "services": {
        "km_agent": true,
        "vectorizer": true
    }
}
```

**示例**:
```bash
curl http://localhost:5000/api/health
```

## 配置

实际配置文件：`ks_infrastructure/configs/default.py`

```python
# MySQL数据库配置
MYSQL_CONFIG = {
    "host": "120.92.109.164",
    "port": 8306,
    "user": "admin",
    "password": "rsdyxjh",
    "database": "yanzhi"
}

# MinIO对象存储配置
MINIO_CONFIG = {
    "endpoint": "http://120.92.109.164:9000",  # S3 API服务端口
    "access_key": "admin",
    "secret_key": "rsdyxjh110!",
    "region": "us-east-1"
}

# Qdrant向量数据库配置
QDRANT_CONFIG = {
    "url": "http://120.92.109.164:6333",
    "api_key": "rsdyxjh"
}

# OpenAI大语言模型配置
OPENAI_CONFIG = {
    "api_key": "85c923cc-9dcf-467a-89d5-285d3798014d",
    "base_url": "https://kspmas.ksyun.com/v1/",
    "model": "DeepSeek-V3.1-Ksyun"
}

# Embedding服务配置
EMBEDDING_CONFIG = {
    "url": "http://10.69.86.20/v1/embeddings",
    "api_key": "7c64b222-4988-4e6a-bb26-48594ceda8a9"
}

# Vision视觉识别服务配置
VISION_CONFIG = {
    "api_key": "sk-412a5b410f664d60a29327fdfa28ac6e",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "model": "qwen-vl-max"
}
```

**注意**: 实际的服务配置在 `ks_infrastructure/configs/default.py` 文件中管理，`app_api/config.py` 中的配置主要用于向后兼容和默认值设置。

## 错误处理

所有 API 在出错时返回:
```json
{
    "success": false,
    "error": "错误信息"
}
```

HTTP 状态码:
- `200`: 成功
- `400`: 请求参数错误
- `500`: 服务器内部错误

## 开发和测试

### 运行服务
```bash
python -m app_api.api
```

### 运行测试
```bash
# 设置API地址并运行测试
API_BASE_URL=http://localhost:5000 python3 app_api/test/test_api.py
```

测试将自动执行以下场景：
1. 健康检查
2. 获取文档列表
3. 上传并向量化 PDF
4. 与 Agent 对话
5. 修改文档可见性
6. 获取文档内容
7. 删除文档

## 安全注意事项

1. **生产环境配置**
   - 修改 `DEBUG = False`
   - 使用 HTTPS
   - 添加认证和授权
   - 限制文件大小和类型

2. **文件上传**
   - 文件存储在 MinIO 对象存储中
   - 元数据保存在 MySQL 数据库
   - 限制文件大小（默认 50MB）
   - 只允许 PDF 文件
   - 向量化处理使用临时文件，处理完自动清理

3. **CORS**
   - 如需跨域访问，使用 `flask-cors`

## 技术栈

- **Flask**: Web 框架
- **SSE**: Server-Sent Events 用于流式响应和实时进度推送
- **KM Agent**: 知识管理对话 Agent
- **PDF Vectorizer**: PDF 向量化和知识库管理
- **file_repository**: 文件存储模块（MinIO + MySQL）
- **ks_infrastructure**: 基础设施服务模块（LLM、Embedding、Qdrant等）

## 许可证

MIT License
