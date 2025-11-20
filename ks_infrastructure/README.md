# KS Infrastructure 模块

这是一个独立的基础设施服务模块，提供统一的服务工厂方法，用于创建和管理各种基础设施服务实例。

## 功能特性

- **统一配置管理**: 所有服务配置集中管理
- **工厂模式**: 每个服务只创建一次实例，避免重复连接
- **灵活可配置**: 支持通过参数覆盖默认配置
- **向后兼容**: 保持现有代码的兼容性
- **全面测试**: 所有服务经过完整功能测试，确保可用性
- **统一异常处理**: 提供自定义异常类便于错误处理
- **日志支持**: 内置日志记录便于调试和监控
- **支持的服务**:
  - MySQL 数据库连接
  - MinIO 对象存储
  - Qdrant 向量数据库
  - OpenAI 大语言模型
  - Embedding 文本嵌入服务
  - Vision 图像识别服务

## 目录结构

```
ks_infrastructure/
├── __init__.py                    # 模块入口
├── README.md                      # 文档
├── setup.py                       # 安装配置
├── pyproject.toml                 # 项目配置
├── configs/
│   ├── __init__.py               # 配置模块导出
│   └── default.py                # 默认配置
├── services/
│   ├── __init__.py               # 服务模块导出
│   ├── base.py                   # 基础功能（缓存管理、日志）
│   ├── exceptions.py             # 自定义异常类
│   ├── mysql_service.py          # MySQL 服务
│   ├── minio_service.py          # MinIO 服务
│   ├── qdrant_service.py         # Qdrant 服务
│   ├── openai_service.py         # OpenAI 服务
│   ├── embedding_service.py      # Embedding 服务
│   └── vision_service.py         # Vision 服务
├── examples/
│   └── basic_usage.py            # 使用示例
└── tests/
    └── test_all_services.py      # 测试脚本
```

## 安装依赖

```bash
pip install mysql-connector-python boto3 qdrant-client openai pillow requests
```

## 快速开始

### 1. 使用默认配置

```python
from ks_infrastructure import (
    ks_mysql,
    ks_minio,
    ks_qdrant,
    ks_openai,
    ks_embedding,
    ks_vision
)

# 获取服务实例
mysql_conn = ks_mysql()
minio_client = ks_minio()
qdrant_client = ks_qdrant()
openai_client = ks_openai()
embedding_service = ks_embedding()  # 现在返回封装好的服务对象
vision_service = ks_vision()
```

### 2. 使用自定义配置

```python
from ks_infrastructure import init_infrastructure

# 自定义配置
custom_config = {
    'MYSQL_CONFIG': {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': 'password',
        'database': 'test'
    }
}

# 初始化基础设施服务工厂
init_infrastructure(custom_config)

# 获取服务实例（将使用自定义配置）
mysql_conn = ks_mysql()
```

### 3. 使用参数覆盖

```python
from ks_infrastructure import ks_mysql, ks_minio

# 使用参数覆盖获取服务实例
mysql_conn = ks_mysql(charset='utf8mb4', autocommit=True)
minio_client = ks_minio(region_name='us-west-1')
```

## 服务使用示例

### MySQL 数据库服务

```python
# 获取数据库连接
mysql_conn = ks_mysql()

# 创建游标并执行SQL
cursor = mysql_conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), email VARCHAR(255))")
cursor.execute("INSERT INTO users (name, email) VALUES (%s, %s)", ("张三", "zhangsan@example.com"))
mysql_conn.commit()

# 查询数据
cursor.execute("SELECT * FROM users")
results = cursor.fetchall()
for row in results:
    print(f"ID: {row[0]}, Name: {row[1]}, Email: {row[2]}")

cursor.close()
mysql_conn.close()
```

### MinIO 对象存储服务

```python
# 获取MinIO客户端
minio_client = ks_minio()

# 创建bucket
bucket_name = "my-test-bucket"
minio_client.create_bucket(Bucket=bucket_name)

# 上传文件
with open("test.txt", "w") as f:
    f.write("Hello, World!")

minio_client.upload_file("test.txt", bucket_name, "test-file.txt")

# 下载文件
minio_client.download_file(bucket_name, "test-file.txt", "downloaded_test.txt")

# 删除文件和bucket
minio_client.delete_object(Bucket=bucket_name, Key="test-file.txt")
minio_client.delete_bucket(Bucket=bucket_name)
```

### Qdrant 向量数据库服务

```python
# 获取Qdrant客户端
qdrant_client = ks_qdrant()

# 创建集合
qdrant_client.recreate_collection(
    collection_name="test_collection",
    vectors_config={
        "size": 4,
        "distance": "Cosine"
    }
)

# 插入向量点
qdrant_client.upsert(
    collection_name="test_collection",
    points=[
        {"id": 1, "vector": [0.1, 0.2, 0.3, 0.4], "payload": {"city": "北京"}},
        {"id": 2, "vector": [0.5, 0.6, 0.7, 0.8], "payload": {"city": "上海"}}
    ]
)

# 搜索相似向量
search_result = qdrant_client.search(
    collection_name="test_collection",
    query_vector=[0.1, 0.2, 0.3, 0.4],
    limit=3
)

# 删除集合
qdrant_client.delete_collection(collection_name="test_collection")
```

### OpenAI 大语言模型服务

```python
# 获取OpenAI客户端
openai_client = ks_openai()

# 发起对话
completion = openai_client.chat.completions.create(
    model="your-model-name",
    messages=[
        {"role": "system", "content": "你是一个乐于助人的助手。"},
        {"role": "user", "content": "写一首关于春天的诗。"}
    ],
    max_tokens=150
)

print(completion.choices[0].message.content)
```

### Embedding 文本嵌入服务

```python
# 获取Embedding服务
embedding_service = ks_embedding()

# 方法1: 获取完整响应
result = embedding_service.create_embedding("这是需要转换为向量的文本")
embedding_vector = result['data'][0]['embedding']
print(f"生成的嵌入向量维度: {len(embedding_vector)}")

# 方法2: 直接获取向量数组
vector = embedding_service.get_embedding_vector("这是需要转换为向量的文本")
print(f"生成的嵌入向量维度: {len(vector)}")
```

### Vision 图像识别服务

```python
# 获取Vision服务
vision_service = ks_vision()

# 读取并编码图像
import base64
with open("image.jpg", "rb") as image_file:
    image_base64 = base64.b64encode(image_file.read()).decode('utf-8')

# 分析图像（支持自定义提示词）
result = vision_service.analyze_image(
    image_base64=image_base64,
    image_format="jpg",
    prompt="请详细描述这张图片的内容"
)

print(result)
```

## 服务说明

### MySQL 数据库服务

```python
# 支持所有 mysql.connector.connect 的参数
mysql_conn = ks_mysql(
    charset='utf8mb4',
    autocommit=True,
    connection_timeout=30
)
```

### MinIO 对象存储服务

```python
# 支持所有 boto3.client 的参数
minio_client = ks_minio(
    region_name='us-west-1',
    endpoint_url='http://localhost:9000'
)
```

### Qdrant 向量数据库服务

```python
# 支持所有 QdrantClient 的参数
qdrant_client = ks_qdrant(
    timeout=30,
    prefer_grpc=True
)
```

### OpenAI 大语言模型服务

```python
# 支持所有 OpenAI 客户端的参数
openai_client = ks_openai(
    timeout=30.0,
    max_retries=2
)
```

### Embedding 文本嵌入服务

```python
# 支持自定义URL和API密钥
embedding_service = ks_embedding(
    url='http://your-embedding-service-url/v1/embeddings',
    api_key='your-api-key'
)

# 使用服务生成嵌入向量
vector = embedding_service.get_embedding_vector("需要转换的文本")
```

### Vision 图像识别服务

```python
# 支持自定义提示词
vision_service = ks_vision()
result = vision_service.analyze_image(
    image_base64_data, 
    "png",
    "请用中文详细描述这张图片"
)
```

## 异常处理

模块提供统一的异常类，便于错误处理：

```python
from ks_infrastructure import (
    KsInfrastructureError,  # 基础异常类
    KsConnectionError,       # 连接错误
    KsConfigError,          # 配置错误
    KsServiceError          # 服务调用错误
)

try:
    mysql_conn = ks_mysql()
except KsConnectionError as e:
    print(f"连接失败: {e}")
except KsInfrastructureError as e:
    print(f"基础设施错误: {e}")
```

## 测试验证

所有服务都经过完整的功能测试，确保实际可用性。测试内容包括：

- MySQL: 表创建、数据插入、查询和删除
- MinIO: bucket创建、文件上传下载、清理
- Qdrant: 集合创建、向量点插入、相似性搜索、删除
- OpenAI: 模型调用、响应获取
- Embedding: 向量生成、维度验证
- Vision: 图像分析、描述获取

运行测试：

```bash
python tests/test_all_services.py
```

测试脚本位于 `tests/test_all_services.py`，可直接运行验证服务功能。

## 配置文件

默认配置文件位于 `configs/default.py`，可以根据需要进行修改或覆盖。

## 许可证

MIT