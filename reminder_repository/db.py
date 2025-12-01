"""
Reminder Repository - 数据库操作模块

提供agent_reminders表的CRUD操作，使用统一的db_session管理器
提醒不属于任何用户，是全局可见的自然语言提示
"""

import logging
from typing import List, Dict, Any, Optional
from ks_infrastructure import db_session
from ks_infrastructure.services.exceptions import KsConnectionError

logger = logging.getLogger(__name__)

TABLE_NAME = "agent_reminders"


def _ensure_table_exists():
    """
    确保agent_reminders表存在，不存在则创建
    """
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_created_at (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent提醒表（全局）'
    """
    try:
        with db_session() as cursor:
            cursor.execute(create_table_sql)
        logger.info(f"Table {TABLE_NAME} ensured to exist")
    except Exception as e:
        logger.error(f"Failed to create table {TABLE_NAME}: {e}")
        raise KsConnectionError(f"创建表失败: {e}")


def create_reminder(content: str) -> dict:
    """
    创建新提醒
    
    Args:
        content: 提醒内容（自然语言）
    
    Returns:
        {
            "success": True,
            "reminder_id": 1
        }
    
    Raises:
        ValueError: 内容为空或参数无效
        KsConnectionError: 数据库操作失败
    """
    # 参数验证
    if not content or not content.strip():
        raise ValueError("content不能为空")
    
    _ensure_table_exists()
    
    try:
        with db_session() as cursor:
            sql = f"""
            INSERT INTO {TABLE_NAME} (content)
            VALUES (%s)
            """
            cursor.execute(sql, (content.strip(),))
            
            return {
                "success": True,
                "reminder_id": cursor.lastrowid
            }
    except Exception as e:
        logger.error(f"Failed to create reminder: {e}")
        raise KsConnectionError(f"创建提醒失败: {e}")


def get_all_reminders() -> list:
    """
    获取所有提醒
    
    Returns:
        [
            {
                "id": 1,
                "content": "今天谁比较辛苦",
                "created_at": "2025-12-01 11:00:00",
                "updated_at": "2025-12-01 11:00:00"
            }
        ]
    
    按创建时间降序排序
    """
    _ensure_table_exists()
    
    try:
        with db_session(dictionary=True) as cursor:
            sql = f"""
            SELECT id, content, created_at, updated_at
            FROM {TABLE_NAME}
            ORDER BY created_at DESC
            """
            cursor.execute(sql)
            results = cursor.fetchall()
            
            # 格式化时间
            for result in results:
                if result.get('created_at'):
                    result['created_at'] = result['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                if result.get('updated_at'):
                    result['updated_at'] = result['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            return results
    except Exception as e:
        logger.error(f"Failed to get all reminders: {e}")
        raise KsConnectionError(f"查询提醒失败: {e}")


def get_reminder_by_id(reminder_id: int) -> dict:
    """
    获取单个提醒的详情
    
    Args:
        reminder_id: 提醒ID
    
    Returns:
        {
            "id": 1,
            "content": "今天谁比较辛苦",
            "created_at": "2025-12-01 11:00:00",
            "updated_at": "2025-12-01 11:00:00"
        }
    
    Raises:
        ValueError: 提醒不存在
        KsConnectionError: 数据库操作失败
    """
    _ensure_table_exists()
    
    try:
        with db_session(dictionary=True) as cursor:
            sql = f"""
            SELECT id, content, created_at, updated_at
            FROM {TABLE_NAME}
            WHERE id = %s
            """
            cursor.execute(sql, (reminder_id,))
            result = cursor.fetchone()
            
            if not result:
                raise ValueError("提醒不存在")
            
            # 格式化时间
            if result.get('created_at'):
                result['created_at'] = result['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if result.get('updated_at'):
                result['updated_at'] = result['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            return result
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        logger.error(f"Failed to get reminder by id: {e}")
        raise KsConnectionError(f"查询提醒失败: {e}")


def update_reminder(reminder_id: int, content: str) -> dict:
    """
    更新提醒
    
    Args:
        reminder_id: 提醒ID
        content: 新的提醒内容
    
    Returns:
        {
            "success": True,
            "message": "提醒更新成功"
        }
    
    Raises:
        ValueError: 参数无效或提醒不存在
        KsConnectionError: 数据库操作失败
    """
    # 参数验证
    if not content or not content.strip():
        raise ValueError("content不能为空")
    
    _ensure_table_exists()
    
    try:
        with db_session() as cursor:
            # 验证提醒是否存在
            check_sql = f"SELECT id FROM {TABLE_NAME} WHERE id = %s"
            cursor.execute(check_sql, (reminder_id,))
            if not cursor.fetchone():
                raise ValueError("提醒不存在")
            
            # 更新内容
            sql = f"""
            UPDATE {TABLE_NAME}
            SET content = %s
            WHERE id = %s
            """
            cursor.execute(sql, (content.strip(), reminder_id))
        
        return {
            "success": True,
            "message": "提醒更新成功"
        }
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        logger.error(f"Failed to update reminder: {e}")
        raise KsConnectionError(f"更新提醒失败: {e}")


def delete_reminder(reminder_id: int) -> dict:
    """
    删除提醒
    
    Args:
        reminder_id: 提醒ID
    
    Returns:
        {
            "success": True,
            "message": "提醒删除成功"
        }
    
    Raises:
        ValueError: 提醒不存在
        KsConnectionError: 数据库操作失败
    """
    _ensure_table_exists()
    
    try:
        with db_session() as cursor:
            # 验证并删除
            sql = f"DELETE FROM {TABLE_NAME} WHERE id = %s"
            cursor.execute(sql, (reminder_id,))
            
            if cursor.rowcount == 0:
                raise ValueError("提醒不存在")
        
        return {
            "success": True,
            "message": "提醒删除成功"
        }
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        logger.error(f"Failed to delete reminder: {e}")
        raise KsConnectionError(f"删除提醒失败: {e}")
