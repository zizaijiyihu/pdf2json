# 会话管理模块

## 概述

会话管理模块为KM Agent提供对话历史的持久化和检索功能，支持多轮对话的上下文保持和历史查询。

## 架构设计

```
conversation_repository/        # 数据访问层
├── schema.sql                  # 数据库表结构
├── db.py                       # 数据库CRUD操作
├── init_db.py                  # 数据库初始化脚本
└── __init__.py

km_agent/                       # Agent业务层
├── agent.py                    # Agent核心(集成会话管理)
├── conversation_manager.py     # 会话管理器
└── tools.py

app_api/routes/                 # API层
├── chat.py                     # 聊天API(支持会话ID)
└── conversations.py            # 会话管理API
```

## 数据库表结构

### conversations (会话表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 自增主键 |
| conversation_id | VARCHAR(64) | 会话唯一标识(UUID) |
| owner | VARCHAR(100) | 会话所有者 |
| title | VARCHAR(200) | 会话标题 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |
| is_deleted | TINYINT(1) | 软删除标记 |

### conversation_messages (消息表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 自增主键 |
| conversation_id | VARCHAR(64) | 关联的会话ID |
| role | ENUM | 消息角色(system/user/assistant/tool) |
| content | TEXT | 消息内容 |
| tool_calls | JSON | 工具调用信息 |
| tool_call_id | VARCHAR(100) | 工具调用ID |
| message_order | INT | 消息顺序 |
| created_at | TIMESTAMP | 创建时间 |

## 快速开始

### 1. 数据库表自动创建

无需手动运行初始化脚本。当您第一次导入 `conversation_repository` 模块时（例如启动应用或运行测试时），系统会自动检查并创建所需的数据库表。

### 2. 使用会话管理功能

#### 在Agent中启用历史记录

```python
from km_agent import KMAgent

# 创建启用历史记录的Agent
agent = KMAgent(
    owner="user@example.com",
    enable_history=True  # 启用历史记录
)

# 发送消息(自动保存到数据库)
response = agent.chat("你好")
conversation_id = agent.conversation_manager.get_conversation_id()
print(f"会话ID: {conversation_id}")
```

#### 续接已有会话

```python
# 使用已有的conversation_id创建Agent
agent = KMAgent(
    owner="user@example.com",
    conversation_id="existing-uuid",
    enable_history=True
)

# 加载历史记录
history = agent.conversation_manager.load_history()

# 继续对话
response = agent.chat("继续刚才的话题", history=history)
```

### 3. API使用示例

#### 创建新会话

```bash
curl -X POST http://localhost:5000/api/conversations \
  -H "Content-Type: application/json" \
  -d '{"title": "关于居住证的咨询"}'
```

#### 获取会话列表

```bash
curl http://localhost:5000/api/conversations?limit=20&offset=0
```

#### 发送消息(启用历史)

```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "如何办理居住证?",
    "conversation_id": "uuid-from-create",
    "enable_history": true
  }'
```

#### 获取会话历史

```bash
curl http://localhost:5000/api/conversations/{conversation_id}/messages
```

#### 搜索会话

```bash
curl http://localhost:5000/api/conversations/search?q=居住证
```

## API端点

### 会话管理

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/conversations` | 获取会话列表 |
| POST | `/api/conversations` | 创建新会话 |
| GET | `/api/conversations/:id` | 获取会话详情 |
| GET | `/api/conversations/:id/messages` | 获取会话消息 |
| PUT | `/api/conversations/:id` | 更新会话标题 |
| DELETE | `/api/conversations/:id` | 删除会话 |
| GET | `/api/conversations/search` | 搜索会话 |

### 聊天

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/chat` | 发送消息(支持会话ID) |

## 核心功能

### ConversationManager (会话管理器)

位于 `km_agent/conversation_manager.py`

**主要方法：**

- `start_conversation(title)` - 创建新会话
- `save_user_message(content)` - 保存用户消息
- `save_assistant_message(content, tool_calls)` - 保存助手消息
- `save_tool_message(tool_call_id, content)` - 保存工具消息
- `load_history(limit)` - 加载历史记录
- `update_title(title)` - 更新会话标题
- `get_conversation_id()` - 获取会话ID

### 数据访问层

位于 `conversation_repository/db.py`

**会话管理：**
- `create_conversation(owner, title)` - 创建会话
- `get_conversation(conversation_id)` - 获取会话信息
- `list_conversations(owner, limit, offset)` - 列出会话
- `update_conversation_title(conversation_id, title)` - 更新标题
- `delete_conversation(conversation_id)` - 删除会话

**消息管理：**
- `add_message(conversation_id, role, content, ...)` - 添加消息
- `get_conversation_history(conversation_id, limit)` - 获取历史
- `search_conversations(owner, keyword, limit)` - 搜索会话

## 测试

运行测试套件：

```bash
cd /Users/xiaohu/projects/km-agent_2
python test_conversation.py
```

测试包括：
1. 会话管理器基本功能
2. 会话持久化
3. 会话续接
4. 流式响应与历史记录

## 设计特点

### 1. 可选特性
通过 `enable_history` 参数控制是否启用历史记录，不影响现有功能。

### 2. 会话隔离
每个会话有独立的UUID，确保多用户、多会话的数据隔离。

### 3. 自动保存
在 `chat_stream` 方法中自动保存所有消息，无需手动调用。

### 4. 分层设计
- **数据层** (conversation_repository): 纯数据库操作
- **业务层** (km_agent/conversation_manager): Agent特定逻辑
- **应用层** (km_agent/agent): Agent核心功能

### 5. 性能优化
- 使用连接池管理数据库连接
- 支持分页查询
- 消息按顺序索引

## 注意事项

1. **隐私保护**: 敏感对话内容建议加密存储
2. **数据清理**: 定期清理过期会话，避免数据膨胀
3. **并发控制**: 同一会话的并发写入已通过message_order保证顺序
4. **备份策略**: 重要对话数据需要定期备份

## 未来扩展

- [ ] 会话导出功能(导出为Markdown/JSON)
- [ ] 会话分享功能
- [ ] 会话标签和分类
- [ ] 全文搜索优化(使用Elasticsearch)
- [ ] 消息编辑和删除
- [ ] 会话统计和分析

## 相关文档

- [项目架构文档](../ARCHITECTURE.md)
- [数据库连接池重构](../MYSQL_POOL_REFACTORING.md)
