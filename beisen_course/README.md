# 北森课程模块

北森课程模块提供与北森学习系统的集成，用于获取和管理课程信息。

## 功能特性

- 获取北森系统课程列表
- 支持分页查询
- 自动处理访问令牌认证
- 完善的错误处理和日志记录

## 安装依赖

```bash
pip install requests
```

## 使用方法

### 基本用法

```python
from beisen_course import get_course_list

# 获取第一页课程（默认10条）
result = get_course_list()

if result['success']:
    courses = result['data']
    print(f"共 {result['total']} 门课程")
    for course in courses:
        print(f"- {course['title']}")
else:
    print(f"获取失败: {result['error']}")
```

### 自定义分页

```python
# 获取第2页，每页20条
result = get_course_list(page_index=2, page_size=20)
```

## API 说明

### get_course_list(page_index=1, page_size=10)

获取北森系统课程列表。

**参数：**
- `page_index` (int): 页码，必须从 1 开始，默认 1
- `page_size` (int): 每页数量，默认 10，最大 300

**返回值：**
返回一个字典，包含以下字段：
- `success` (bool): 是否成功
- `data` (list): 课程列表（成功时）
  - 每个课程对象包含：title（标题）、courseId（课程ID）、description（描述）等字段
- `total` (int): 课程总数（成功时）
- `page_index` (int): 当前页码（成功时）
- `page_size` (int): 每页数量（成功时）
- `error` (str): 错误信息（失败时）

**示例返回：**
```python
{
    "success": True,
    "data": [
        {
            "title": "Python 入门",
            "courseId": "12345",
            "description": "Python 编程基础课程",
            ...
        },
        ...
    ],
    "total": 100,
    "page_index": 1,
    "page_size": 10
}
```

## 配置

北森系统的访问配置在 `course_service.py` 中：

```python
BEISEN_BASE_URL = "http://10.69.80.179:8888"
BEISEN_APP_KEY = "您的 APP_KEY"
BEISEN_APP_SECRET = "您的 APP_SECRET"
```

## 在 KM Agent 中使用

该模块已集成到 KM Agent 中，作为 `get_course_list` 工具可供 Agent 调用：

```python
from km_agent import KMAgent

agent = KMAgent(verbose=True)

# Agent 可以通过自然语言查询课程
for chunk in agent.chat_stream("帮我查询一下有哪些课程"):
    if chunk["type"] == "content":
        print(chunk["data"], end="", flush=True)
```

## 错误处理

模块会处理以下错误情况：
- 访问令牌获取失败
- API 请求超时
- 网络连接错误
- API 返回错误状态码
- 数据格式异常

所有错误都会通过返回值中的 `error` 字段返回，并记录到日志中。

## 日志

模块使用 Python 标准 logging 模块记录日志：

```python
import logging

# 配置日志级别
logging.basicConfig(level=logging.INFO)
```

## 技术细节

### 认证流程

1. 使用 APP_KEY 和 APP_SECRET 获取 access_token
2. 使用 access_token 调用课程列表 API
3. 自动处理令牌刷新

### API 端点

- 获取令牌：`POST /token`
- 获取课程列表：`POST /Learning/api/v1/course/GetCourseList`

## 注意事项

- 页码必须从 1 开始
- 最大页容量为 300
- 访问令牌有效期由北森系统控制
- 请求包含 10 秒超时设置
