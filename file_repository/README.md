# File Repository 模块

基于 MinIO 提供文件上传和查询的存储仓库服务，使用 MySQL 管理文件元数据。

## 功能特性

- 文件上传到 MinIO 对象存储
- 文件元数据存储到 MySQL 数据库
- 文件查询和下载
- 列出用户所有文件
- 支持多个 bucket（默认 `kms` 和 `tmp`）
- 自动创建不存在的 bucket
- 重复上传自动覆盖
- 文件公开/私有状态管理
- 跨用户访问公开文件

## 接口说明

### upload_file

上传文件到 MinIO 并保存元数据到数据库

```python
from file_repository import upload_file

with open('example.pdf', 'rb') as f:
    object_key = upload_file(
        username='user123',
        filename='example.pdf',
        file_data=f,
        bucket='kms',  # 可选，默认 'kms'
        content_type='application/pdf',  # 可选
        is_public=0  # 可选，默认 0（私有）
    )
# 返回: 'user123/example.pdf'
```

**参数：**
- `username` (str): 用户名
- `filename` (str): 原文件名
- `file_data` (BinaryIO): 文件二进制流
- `bucket` (str): bucket 名称，默认 'kms'
- `content_type` (str): 文件 MIME 类型，可选
- `is_public` (int): 是否公开 (0=私有, 1=公开)，默认 0

**返回：** 文件在 MinIO 中的路径 (`username/filename`)

### get_file

从 MinIO 获取文件

```python
from file_repository import get_file

content = get_file(
    username='user123',
    filename='example.pdf',
    bucket='kms'  # 可选，默认 'kms'
)

if content:
    # 处理文件内容
    with open('downloaded.pdf', 'wb') as f:
        f.write(content)
else:
    print('文件不存在')
```

**参数：**
- `username` (str): 用户名
- `filename` (str): 文件名
- `bucket` (str): bucket 名称，默认 'kms'

**返回：** 文件内容 (bytes)，文件不存在返回 None

### list_user_files

列出用户的所有文件

```python
from file_repository import list_user_files

files = list_user_files(
    username='user123',
    bucket='kms'  # 可选，默认 'kms'
)

for file_info in files:
    print(f"{file_info['filename']}: {file_info['size']} bytes")
```

**参数：**
- `username` (str): 用户名
- `bucket` (str): bucket 名称，默认 'kms'

**返回：** 文件列表，每个元素包含：
- `key` (str): 完整路径
- `filename` (str): 文件名
- `size` (int): 文件大小（字节）
- `last_modified` (datetime): 最后修改时间

### get_owner_file_list

获取所有者的文件列表（从数据库查询）

```python
from file_repository import get_owner_file_list

# 只获取所有者自己的文件
files = get_owner_file_list(
    owner='user123',
    include_public=False  # 可选，默认 False
)

# 获取所有者的文件 + 所有公开文件
all_files = get_owner_file_list(
    owner='user123',
    include_public=True
)

for file_info in files:
    print(f"{file_info['owner']}/{file_info['filename']}: {file_info['is_public']}")
```

**参数：**
- `owner` (str): 文件所有者
- `include_public` (bool): 是否包含公开文件
  - `False`: 只返回所有者的文件
  - `True`: 返回所有者的文件 + 所有 is_public=1 的文件

**返回：** 文件列表，每个元素包含完整的数据库字段：
- `id` (int): 记录ID
- `file_path` (str): 文件路径
- `owner` (str): 文件所有者
- `filename` (str): 文件名
- `bucket` (str): bucket 名称
- `is_public` (int): 是否公开 (0=私有, 1=公开)
- `content_type` (str): 文件类型
- `file_size` (int): 文件大小
- `created_at` (datetime): 创建时间
- `updated_at` (datetime): 更新时间

### set_file_public

设置文件的公开状态

```python
from file_repository import set_file_public

# 设置为公开
success = set_file_public(
    owner='user123',
    filename='example.pdf',
    is_public=1  # 0=私有, 1=公开
)

if success:
    print("设置成功")
else:
    print("文件不存在或无权限")
```

**参数：**
- `owner` (str): 文件所有者
- `filename` (str): 文件名
- `is_public` (int): 公开状态 (0=私有, 1=公开)

**返回：** bool，是否成功更新

## 数据库结构

### file_metadata 表

```sql
CREATE TABLE file_metadata (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_path VARCHAR(512) NOT NULL UNIQUE,
    owner VARCHAR(255) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    bucket VARCHAR(255) NOT NULL,
    is_public TINYINT DEFAULT 0,
    content_type VARCHAR(128),
    file_size BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_owner (owner),
    INDEX idx_is_public (is_public),
    INDEX idx_owner_public (owner, is_public)
);
```

## Bucket 说明

### 默认 Buckets
- **kms** (Knowledge Management System): 主要存储 bucket，用于长期保存文件
- **tmp**: 临时存储 bucket，用于临时文件

### 命名规则
- Bucket 名称必须至少 3 个字符
- 只能包含小写字母、数字和连字符
- 符合 S3/MinIO 命名规范

## 文件路径结构

文件在 MinIO 中的存储路径格式：`{username}/{filename}`

例如：
- 用户 `alice` 上传 `report.pdf` → 存储路径: `alice/report.pdf`
- 用户 `bob` 上传 `data.csv` → 存储路径: `bob/data.csv`

## 依赖

- `ks_infrastructure.services.minio_service` - MinIO 连接服务
- `ks_infrastructure.services.mysql_service` - MySQL 连接服务
- `boto3` - AWS S3 SDK（用于 MinIO）
- `mysql-connector-python` - MySQL 驱动

## 测试

### 基础功能测试

```bash
python file_repository/tests/test_repository.py
```

测试覆盖：
1. 上传和获取文件（kms 和 tmp bucket）
2. 重复上传覆盖功能
3. 列出用户文件
4. 获取不存在的文件

### 数据库集成测试

```bash
python file_repository/tests/test_db_integration.py
```

测试覆盖：
1. 上传文件并保存元数据
2. 获取所有者文件列表（包含/不包含公开文件）
3. 设置文件公开状态
4. 跨所有者文件可见性

## 异常处理

所有接口在失败时抛出 `KsConnectionError` 异常，包含详细错误信息。

```python
from ks_infrastructure.services.exceptions import KsConnectionError

try:
    upload_file('user', 'file.pdf', file_data)
except KsConnectionError as e:
    print(f"上传失败: {e}")
```
