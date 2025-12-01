"""
会话管理数据库操作层
提供对话历史的CRUD操作
"""

import uuid
import json
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from ks_infrastructure.db_session import db_session
from ks_infrastructure.services.exceptions import KsConnectionError

logger = logging.getLogger(__name__)


def _ensure_tables_exist():
    """
    确保会话管理相关的表存在，不存在则自动创建
    """
    # 会话表
    create_conversations_sql = """
    CREATE TABLE IF NOT EXISTS conversations (
        id INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
        conversation_id VARCHAR(64) UNIQUE NOT NULL COMMENT '会话唯一标识(UUID)',
        owner VARCHAR(100) NOT NULL COMMENT '会话所有者(用户标识)',
        title VARCHAR(200) DEFAULT NULL COMMENT '会话标题',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        is_deleted TINYINT(1) DEFAULT 0 COMMENT '软删除标记(0:未删除, 1:已删除)',
        INDEX idx_owner (owner),
        INDEX idx_created_at (created_at),
        INDEX idx_conversation_id (conversation_id),
        INDEX idx_owner_created (owner, created_at DESC)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会话表'
    """
    
    # 消息表
    create_messages_sql = """
    CREATE TABLE IF NOT EXISTS conversation_messages (
        id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
        conversation_id VARCHAR(64) NOT NULL COMMENT '关联的会话ID',
        role ENUM('system', 'user', 'assistant', 'tool') NOT NULL COMMENT '消息角色',
        content TEXT COMMENT '消息内容',
        tool_calls JSON DEFAULT NULL COMMENT '工具调用信息(JSON格式)',
        tool_call_id VARCHAR(100) DEFAULT NULL COMMENT '工具调用ID',
        message_order INT NOT NULL COMMENT '消息在会话中的顺序',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        INDEX idx_conversation_id (conversation_id),
        INDEX idx_created_at (created_at),
        INDEX idx_conversation_order (conversation_id, message_order)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会话消息表'
    """
    
    try:
        with db_session() as cursor:
            # 创建会话表
            cursor.execute(create_conversations_sql)
            logger.info("Table 'conversations' ensured to exist")
            
            # 创建消息表
            cursor.execute(create_messages_sql)
            logger.info("Table 'conversation_messages' ensured to exist")
            
    except Exception as e:
        logger.error(f"Failed to create conversation tables: {e}")
        raise KsConnectionError(f"Failed to create conversation tables: {e}")


# 确保模块导入时检查表是否存在
_ensure_tables_exist()


# ==================== 会话管理 ====================

def create_conversation(owner: str, title: str = None) -> str:
    """
    创建新会话

    Args:
        owner: 会话所有者
        title: 会话标题(可选)

    Returns:
        str: 会话ID (UUID格式)
    """
    logger.debug(f"→ 调用 conversation_repository.db.create_conversation(owner={owner}, title={title})")
    conversation_id = str(uuid.uuid4())

    sql = """
        INSERT INTO conversations (conversation_id, owner, title)
        VALUES (%s, %s, %s)
    """
    logger.debug(f"  执行SQL: {sql}")
    logger.debug(f"  参数: ({conversation_id}, {owner}, {title})")

    with db_session() as cursor:
        cursor.execute(sql, (conversation_id, owner, title))

    logger.info(f"← 创建会话成功 conversation_id={conversation_id}, owner={owner}")
    return conversation_id


def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """
    获取会话信息

    Args:
        conversation_id: 会话ID

    Returns:
        Dict: 会话信息，如果不存在返回None
    """
    logger.debug(f"→ 调用 conversation_repository.db.get_conversation(conversation_id={conversation_id})")

    sql = """
        SELECT id, conversation_id, owner, title, created_at, updated_at
        FROM conversations
        WHERE conversation_id = %s AND is_deleted = 0
    """
    logger.debug(f"  执行SQL: {sql}")
    logger.debug(f"  参数: ({conversation_id},)")

    with db_session(dictionary=True) as cursor:
        cursor.execute(sql, (conversation_id,))
        result = cursor.fetchone()

    logger.debug(f"← 返回: {result}")
    return result


def list_conversations(owner: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    """
    获取用户的会话列表(分页)

    Args:
        owner: 用户标识
        limit: 每页数量
        offset: 偏移量

    Returns:
        List[Dict]: 会话列表
    """
    logger.debug(f"→ 调用 conversation_repository.db.list_conversations(owner={owner}, limit={limit}, offset={offset})")

    sql = """
        SELECT
            c.id,
            c.conversation_id,
            c.owner,
            c.title,
            c.created_at,
            c.updated_at,
            COUNT(m.id) as message_count
        FROM conversations c
        LEFT JOIN conversation_messages m ON c.conversation_id = m.conversation_id
        WHERE c.owner = %s AND c.is_deleted = 0
        GROUP BY c.id
        ORDER BY c.updated_at DESC
        LIMIT %s OFFSET %s
    """
    logger.debug(f"  执行SQL查询 (参数: owner={owner}, limit={limit}, offset={offset})")

    with db_session(dictionary=True) as cursor:
        cursor.execute(sql, (owner, limit, offset))
        result = cursor.fetchall()

    logger.debug(f"← 返回 {len(result)} 条会话记录")
    return result


def count_conversations(owner: str) -> int:
    """
    统计用户的会话总数

    Args:
        owner: 用户标识

    Returns:
        int: 会话总数
    """
    logger.debug(f"→ 调用 conversation_repository.db.count_conversations(owner={owner})")

    sql = """
        SELECT COUNT(*) FROM conversations
        WHERE owner = %s AND is_deleted = 0
    """
    logger.debug(f"  执行SQL: {sql}")

    with db_session() as cursor:
        cursor.execute(sql, (owner,))
        result = cursor.fetchone()
        count = result[0] if result else 0

    logger.debug(f"← 返回 count={count}")
    return count


def update_conversation_title(conversation_id: str, title: str) -> bool:
    """
    更新会话标题
    
    Args:
        conversation_id: 会话ID
        title: 新标题
    
    Returns:
        bool: 是否更新成功
    """
    with db_session() as cursor:
        cursor.execute(
            """
            UPDATE conversations
            SET title = %s
            WHERE conversation_id = %s AND is_deleted = 0
            """,
            (title, conversation_id)
        )
        success = cursor.rowcount > 0
    
    if success:
        logger.info(f"Updated conversation {conversation_id} title to: {title}")
    return success


def delete_conversation(conversation_id: str) -> bool:
    """
    软删除会话
    
    Args:
        conversation_id: 会话ID
    
    Returns:
        bool: 是否删除成功
    """
    with db_session() as cursor:
        cursor.execute(
            """
            UPDATE conversations
            SET is_deleted = 1
            WHERE conversation_id = %s
            """,
            (conversation_id,)
        )
        success = cursor.rowcount > 0
    
    if success:
        logger.info(f"Deleted conversation {conversation_id}")
    return success


# ==================== 消息管理 ====================

def add_message(
    conversation_id: str,
    role: str,
    content: str = None,
    tool_calls: List[Dict] = None,
    tool_call_id: str = None
) -> int:
    """
    添加消息到会话

    Args:
        conversation_id: 会话ID
        role: 消息角色 ('system', 'user', 'assistant', 'tool')
        content: 消息内容
        tool_calls: 工具调用信息(列表)
        tool_call_id: 工具调用ID

    Returns:
        int: 消息ID
    """
    logger.debug(f"→ 调用 conversation_repository.db.add_message(conversation_id={conversation_id}, role={role}, content_len={len(content) if content else 0})")

    # 获取当前消息顺序
    with db_session() as cursor:
        cursor.execute(
            """
            SELECT COALESCE(MAX(message_order), 0) + 1
            FROM conversation_messages
            WHERE conversation_id = %s
            """,
            (conversation_id,)
        )
        message_order = cursor.fetchone()[0]

    logger.debug(f"  计算消息顺序: message_order={message_order}")

    # 转换tool_calls为JSON字符串
    tool_calls_json = json.dumps(tool_calls) if tool_calls else None

    sql = """
        INSERT INTO conversation_messages
        (conversation_id, role, content, tool_calls, tool_call_id, message_order)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    logger.debug(f"  执行SQL插入消息")

    with db_session() as cursor:
        cursor.execute(sql, (conversation_id, role, content, tool_calls_json, tool_call_id, message_order))
        message_id = cursor.lastrowid

    logger.debug(f"← 添加消息成功 message_id={message_id}, role={role}")
    return message_id


def get_conversation_history(
    conversation_id: str,
    limit: int = None
) -> List[Dict[str, Any]]:
    """
    获取会话的消息历史

    Args:
        conversation_id: 会话ID
        limit: 限制返回的消息数量(可选)

    Returns:
        List[Dict]: 消息列表，按时间顺序排序
    """
    logger.debug(f"→ 调用 conversation_repository.db.get_conversation_history(conversation_id={conversation_id}, limit={limit})")

    with db_session(dictionary=True) as cursor:
        if limit:
            # 获取最近的N条消息
            sql = """
                SELECT id, conversation_id, role, content, tool_calls, tool_call_id,
                       message_order, created_at
                FROM conversation_messages
                WHERE conversation_id = %s
                ORDER BY message_order DESC
                LIMIT %s
            """
            logger.debug(f"  执行SQL查询 (带limit={limit})")
            cursor.execute(sql, (conversation_id, limit))
            messages = cursor.fetchall()
            # 反转顺序，使其按时间正序
            messages.reverse()
        else:
            sql = """
                SELECT id, conversation_id, role, content, tool_calls, tool_call_id,
                       message_order, created_at
                FROM conversation_messages
                WHERE conversation_id = %s
                ORDER BY message_order ASC
            """
            logger.debug(f"  执行SQL查询 (无limit)")
            cursor.execute(sql, (conversation_id,))
            messages = cursor.fetchall()

    # 解析tool_calls JSON
    for msg in messages:
        if msg.get('tool_calls'):
            try:
                msg['tool_calls'] = json.loads(msg['tool_calls'])
            except json.JSONDecodeError:
                msg['tool_calls'] = None

    logger.debug(f"← 返回 {len(messages)} 条消息")
    return messages


def get_messages_by_time_range(
    owner: str,
    start_time: datetime,
    end_time: datetime
) -> List[Dict[str, Any]]:
    """
    按时间范围查询用户的消息
    
    Args:
        owner: 用户标识
        start_time: 开始时间
        end_time: 结束时间
    
    Returns:
        List[Dict]: 消息列表
    """
    with db_session(dictionary=True) as cursor:
        cursor.execute(
            """
            SELECT m.id, m.conversation_id, m.role, m.content, m.tool_calls,
                   m.tool_call_id, m.message_order, m.created_at,
                   c.title as conversation_title
            FROM conversation_messages m
            JOIN conversations c ON m.conversation_id = c.conversation_id
            WHERE c.owner = %s 
              AND c.is_deleted = 0
              AND m.created_at BETWEEN %s AND %s
            ORDER BY m.created_at ASC
            """,
            (owner, start_time, end_time)
        )
        messages = cursor.fetchall()
    
    # 解析tool_calls JSON
    for msg in messages:
        if msg.get('tool_calls'):
            try:
                msg['tool_calls'] = json.loads(msg['tool_calls'])
            except json.JSONDecodeError:
                msg['tool_calls'] = None
    
    return messages


def search_conversations(owner: str, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    搜索包含关键词的会话
    
    Args:
        owner: 用户标识
        keyword: 搜索关键词
        limit: 返回结果数量限制
    
    Returns:
        List[Dict]: 匹配的会话列表
    """
    search_pattern = f"%{keyword}%"
    
    with db_session(dictionary=True) as cursor:
        cursor.execute(
            """
            SELECT DISTINCT c.id, c.conversation_id, c.owner, c.title, 
                   c.created_at, c.updated_at
            FROM conversations c
            LEFT JOIN conversation_messages m ON c.conversation_id = m.conversation_id
            WHERE c.owner = %s 
              AND c.is_deleted = 0
              AND (c.title LIKE %s OR m.content LIKE %s)
            ORDER BY c.updated_at DESC
            LIMIT %s
            """,
            (owner, search_pattern, search_pattern, limit)
        )
        return cursor.fetchall()


def clear_conversation_messages(conversation_id: str) -> int:
    """
    清空会话的所有消息(保留会话本身)
    
    Args:
        conversation_id: 会话ID
    
    Returns:
        int: 删除的消息数量
    """
    with db_session() as cursor:
        cursor.execute(
            """
            DELETE FROM conversation_messages
            WHERE conversation_id = %s
            """,
            (conversation_id,)
        )
        deleted_count = cursor.rowcount
    
    logger.info(f"Cleared {deleted_count} messages from conversation {conversation_id}")
    return deleted_count
