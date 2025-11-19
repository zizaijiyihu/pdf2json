# App API - 知识管理 HTTP API 服务

基于 Flask 的 HTTP API 服务，提供知识管理功能的 RESTful 接口。

## 功能特性

- ✅ **聊天接口** - 与 KM Agent 对话，支持多轮连续对话
- ✅ **文档列表** - 获取用户有权访问的文档列表
- ✅ **文件上传** - 上传 PDF 并向量化，支持 SSE 实时进度
- ✅ **文件删除** - 删除指定文档
- ✅ **权限管理** - 修改文档公开/私有状态

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

**Response**:
```json
{
    "success": true,
    "response": "Agent 的回复",
    "tool_calls": [
        {
            "tool": "search_knowledge",
            "arguments": {...},
            "result": {...}
        }
    ],
    "history": [...]  // 更新后的历史，用于下一轮对话
}
```

**示例**:
```bash
# 第一轮对话
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "北京人才网的信息"}'

# 第二轮对话（带历史）
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "详细说明一下", "history": [...]}'
```

---

### 2. 获取文档列表

**Endpoint**: `GET /api/documents`

**功能**: 获取用户有权访问的文档列表（用户的文档 + 公开文档）

**Query Parameters**:
- `owner` (可选): 用户名，默认 "hu"

**Response**:
```json
{
    "success": true,
    "owner": "hu",
    "count": 3,
    "documents": [
        {
            "filename": "document.pdf",
            "owner": "hu",
            "is_public": 0,
            "point_id": 123,
            "page_count": 5
        }
    ]
}
```

**示例**:
```bash
# 获取默认用户的文档列表
curl http://localhost:5000/api/documents

# 获取指定用户的文档列表
curl http://localhost:5000/api/documents?owner=user123
```

---

### 3. 上传并向量化 PDF

**Endpoint**: `POST /api/upload`

**功能**: 上传 PDF 文件并向量化，支持 SSE 实时进度更新

**Content-Type**: `multipart/form-data`

**Form Data**:
- `file`: PDF 文件（必需）
- `owner`: 用户名（可选，默认 "hu"）
- `is_public`: 0=私有，1=公开（可选，默认 0）

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
  -F "owner=hu" \
  -F "is_public=0"

# 上传公开文档
curl -X POST http://localhost:5000/api/upload \
  -F "file=@document.pdf" \
  -F "owner=hu" \
  -F "is_public=1"
```

**JavaScript 示例** (监听 SSE):
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('owner', 'hu');
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

**Query Parameters**:
- `owner` (可选): 用户名，默认 "hu"

**Response**:
```json
{
    "success": true,
    "filename": "document.pdf",
    "owner": "hu",
    "message": "Document deleted successfully"
}
```

**示例**:
```bash
# 删除默认用户的文档
curl -X DELETE http://localhost:5000/api/documents/document.pdf

# 删除指定用户的文档
curl -X DELETE "http://localhost:5000/api/documents/document.pdf?owner=user123"
```

---

### 5. 修改文档可见性

**Endpoint**: `PUT /api/documents/<filename>/visibility`

**功能**: 修改文档为公开/私有

**Query Parameters**:
- `owner` (可选): 用户名，默认 "hu"

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
    "updated_count": 3,
    "filename": "document.pdf",
    "owner": "hu",
    "is_public": 1
}
```

**示例**:
```bash
# 设置为公开
curl -X PUT http://localhost:5000/api/documents/document.pdf/visibility \
  -H "Content-Type: application/json" \
  -d '{"is_public": 1}'

# 设置为私有
curl -X PUT "http://localhost:5000/api/documents/document.pdf/visibility?owner=user123" \
  -H "Content-Type: application/json" \
  -d '{"is_public": 0}'
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

配置文件：`app_api/config.py`

```python
# 默认用户
DEFAULT_USER = "hu"

# 上传配置
UPLOAD_FOLDER = "/tmp/km_agent_uploads"
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

# 服务器配置
DEBUG = True
HOST = "0.0.0.0"
PORT = 5000
```

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

### 测试脚本
见 `test_api/` 目录下的测试脚本。

## 安全注意事项

1. **生产环境配置**
   - 修改 `DEBUG = False`
   - 使用 HTTPS
   - 添加认证和授权
   - 限制文件大小和类型

2. **文件上传**
   - 使用 `secure_filename()` 防止路径遍历
   - 限制文件大小（默认 50MB）
   - 只允许 PDF 文件
   - 上传后自动清理临时文件

3. **CORS**
   - 如需跨域访问，使用 `flask-cors`

## 技术栈

- **Flask**: Web 框架
- **SSE**: Server-Sent Events 用于实时进度推送
- **KM Agent**: 知识管理对话 Agent
- **PDF Vectorizer**: PDF 向量化和知识库管理

## 许可证

MIT License
