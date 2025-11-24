# Instruction Repository - Agent指示管理模块

Agent用户自定义指示的存储和管理模块。

## 功能概述

允许用户创建、编辑、删除自定义指示（≤200字），这些指示会自动加载到KMAgent的系统提示中，影响AI的回答风格和行为。

## 核心功能

### 1. 创建指示

```python
from instruction_repository import create_instruction

result = create_instruction(
    owner="user123",
    content="回答要简洁明了，不要啰嗦",
    priority=10
)
# Returns: {"success": True, "instruction_id": 1}
```

### 2. 获取激活的指示

```python
from instruction_repository import get_active_instructions

instructions = get_active_instructions(owner="user123")
# Returns: [{"id": 1, "content": "...", "priority": 10, "created_at": "..."}]
```

### 3. 获取所有指示

```python
from instruction_repository import get_all_instructions

# 只获取激活的
instructions = get_all_instructions(owner="user123")

# 包含禁用的
all_instructions = get_all_instructions(owner="user123", include_inactive=True)
```

### 4. 更新指示

```python
from instruction_repository import update_instruction

result = update_instruction(
    instruction_id=1,
    owner="user123",
    content="回答要更详细一些",  # 可选
    is_active=1,                # 可选
    priority=5                  # 可选
)
```

### 5. 删除指示

```python
from instruction_repository import delete_instruction

result = delete_instruction(instruction_id=1, owner="user123")
```

## 数据库结构

```sql
CREATE TABLE agent_instructions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    owner VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    is_active TINYINT DEFAULT 1,
    priority INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_owner (owner),
    INDEX idx_owner_active (owner, is_active)
);
```

## 参数说明

- **owner**: 所有者用户名，用于多用户隔离
- **content**: 指示内容，限制≤200字
- **is_active**: 是否启用（1=启用，0=禁用）
- **priority**: 优先级，数字越大越优先显示

## 安全特性

- ✅ 所有操作验证 `owner` 权限
- ✅ 参数化查询防止SQL注入
- ✅ 内容长度验证（≤200字）
- ✅ 自动建表机制

## 使用示例

### 示例1：为用户设置简洁回答风格

```python
create_instruction(
    owner="alice",
    content="每次回答都要简洁明了，控制在3句话以内",
    priority=10
)
```

### 示例2：设置专业领域偏好

```python
create_instruction(
    owner="bob",
    content="回答技术问题时要详细解释原理，回答业务问题时要简明扼要",
    priority=5
)
```

### 示例3：临时禁用指示

```python
update_instruction(
    instruction_id=1,
    owner="alice",
    is_active=0  # 禁用但不删除
)
```

## 注意事项

1. **字数限制**: 指示内容必须≤400字符（中文按字符计数）
2. **优先级**: 多条指示按priority降序排列，数字越大越优先
3. **权限隔离**: 用户只能操作自己的指示
4. **自动建表**: 首次使用时会自动创建表，无需手动初始化

## 测试

运行单元测试：
```bash
python instruction_repository/test/test_instruction.py
```

## 错误处理

```python
try:
    create_instruction(owner="user", content="x" * 201)
except ValueError as e:
    print(e)  # "指示内容超过200字限制（当前201字）"

try:
    delete_instruction(instruction_id=999, owner="user")
except ValueError as e:
    print(e)  # "指示不存在或无权限删除"
```

## 许可证

MIT License
