"""
会话管理数据访问层

提供对话历史的数据库操作接口
"""

from .db import (
    # 会话管理
    create_conversation,
    get_conversation,
    list_conversations,
    count_conversations,
    update_conversation_title,
    delete_conversation,
    
    # 消息管理
    add_message,
    get_conversation_history,
    get_messages_by_time_range,
    search_conversations,
    clear_conversation_messages,
)

__all__ = [
    # 会话管理
    'create_conversation',
    'get_conversation',
    'list_conversations',
    'count_conversations',
    'update_conversation_title',
    'delete_conversation',
    
    # 消息管理
    'add_message',
    'get_conversation_history',
    'get_messages_by_time_range',
    'search_conversations',
    'clear_conversation_messages',
]
