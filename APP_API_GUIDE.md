# App API 快速使用指南

## 📦 已创建的内容

```
app_api/
├── __init__.py          # 模块初始化
├── config.py            # 配置文件
├── api.py               # Flask API 实现
└── README.md            # 详细文档

测试脚本:
├── test_api_chat.py     # 测试聊天接口
└── test_api_documents.py # 测试文档接口
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install flask werkzeug requests
```

### 2. 启动服务

```bash
python -m app_api.api
```

服务将在 `http://localhost:5000` 启动

### 3. 测试接口

```bash
# 健康检查
curl http://localhost:5000/api/health

# 获取文档列表
curl http://localhost:5000/api/documents

# 聊天
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "北京人才网的信息"}'
```

## 📋 5个HTTP接口

### 1. **聊天接口** - POST /api/chat

支持多轮连续对话

```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "用户问题"}'
```

### 2. **文档列表** - GET /api/documents

获取用户的文档 + 公开文档

```bash
curl "http://localhost:5000/api/documents?owner=hu"
```

### 3. **上传文件** - POST /api/upload

上传PDF并向量化（SSE实时进度）

```bash
curl -X POST http://localhost:5000/api/upload \
  -F "file=@document.pdf" \
  -F "owner=hu" \
  -F "is_public=0"
```

### 4. **删除文件** - DELETE /api/documents/{filename}

```bash
curl -X DELETE "http://localhost:5000/api/documents/document.pdf?owner=hu"
```

### 5. **修改可见性** - PUT /api/documents/{filename}/visibility

```bash
curl -X PUT http://localhost:5000/api/documents/document.pdf/visibility \
  -H "Content-Type: application/json" \
  -d '{"is_public": 1}'
```

## 🧪 运行测试

```bash
# 测试聊天接口
python test_api_chat.py

# 测试文档接口
python test_api_documents.py
```

## ⚙️ 配置

配置文件：`app_api/config.py`

```python
# 默认用户
DEFAULT_USER = "hu"

# OpenAI/LLM配置
OPENAI_CONFIG = {
    "api_key": "85c923cc-9dcf-467a-89d5-285d3798014d",
    "base_url": "https://kspmas.ksyun.com/v1/",
    "model": "DeepSeek-V3.1-Ksyun"
}

# Embedding配置
EMBEDDING_CONFIG = {
    "url": "http://10.69.86.20/v1/embeddings",
    "api_key": "7c64b222-4988-4e6a-bb26-48594ceda8a9"
}

# Qdrant配置
QDRANT_CONFIG = {
    "url": "http://120.92.109.164:6333/",
    "api_key": "rsdyxjh"
}
```

## 📡 SSE 实时进度示例

上传文件时，服务器通过 SSE 推送进度：

```
data: {"stage": "init", "progress_percent": 0, "message": "开始处理文档..."}
data: {"stage": "parsing", "progress_percent": 10, "message": "正在解析PDF文档..."}
data: {"stage": "processing", "progress_percent": 50, "current_page": 5, "total_pages": 10}
data: {"stage": "storing", "progress_percent": 90, "message": "正在存储向量..."}
data: {"stage": "completed", "progress_percent": 100, "data": {...}}
```

## 🔒 安全注意事项

当前是**开发模式**，生产环境需要：

1. ✅ 设置 `DEBUG = False`
2. ✅ 使用 HTTPS
3. ✅ 添加用户认证
4. ✅ 添加请求限流
5. ✅ 启用 CORS（如需前端调用）

## 💡 使用场景

### 场景1：网页聊天机器人

```javascript
// 前端调用聊天接口
fetch('http://localhost:5000/api/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({message: userInput})
})
.then(res => res.json())
.then(data => {
    console.log(data.response);
    // 保存history用于下一轮对话
    conversationHistory = data.history;
});
```

### 场景2：文件上传进度条

```javascript
// 监听SSE进度事件
const formData = new FormData();
formData.append('file', fileInput.files[0]);

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
            // 解析进度并更新UI
            updateProgressBar(progress);
            read();
        });
    }
    read();
});
```

### 场景3：文档管理界面

```javascript
// 获取文档列表
fetch('http://localhost:5000/api/documents?owner=user123')
    .then(res => res.json())
    .then(data => {
        displayDocuments(data.documents);
    });

// 修改可见性
function toggleVisibility(filename, isPublic) {
    fetch(`http://localhost:5000/api/documents/${filename}/visibility`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({is_public: isPublic ? 1 : 0})
    });
}
```

## 📚 更多文档

详细的 API 文档请查看：[app_api/README.md](app_api/README.md)

## ⚡ 常见问题

**Q: 如何修改端口？**
A: 编辑 `app_api/config.py`，修改 `PORT = 5000`

**Q: 如何支持跨域？**
A: 安装 `flask-cors` 并在 `api.py` 中添加：
```python
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
```

**Q: 上传文件大小限制？**
A: 默认 50MB，修改 `config.py` 中的 `MAX_CONTENT_LENGTH`

**Q: 如何添加认证？**
A: 使用 `flask-login` 或 `flask-jwt-extended` 添加认证中间件
