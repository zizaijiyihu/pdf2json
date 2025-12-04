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
        is_public TINYINT DEFAULT 1 COMMENT '是否公开: 1=公开, 0=私有',
        user_id VARCHAR(255) DEFAULT NULL COMMENT '用户ID（私有提醒时使用）',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_created_at (created_at),
        INDEX idx_user_id (user_id),
        INDEX idx_is_public (is_public)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent提醒表（支持公开/私有）'
    """
    try:
        with db_session() as cursor:
            cursor.execute(create_table_sql)
            
            # Add columns if they don't exist (for existing tables)
            # MySQL doesn't support IF NOT EXISTS for ALTER TABLE ADD COLUMN
            alter_sqls = [
                f"ALTER TABLE {TABLE_NAME} ADD COLUMN is_public TINYINT DEFAULT 1 COMMENT '是否公开: 1=公开, 0=私有'",
                f"ALTER TABLE {TABLE_NAME} ADD COLUMN user_id VARCHAR(255) DEFAULT NULL COMMENT '用户ID（私有提醒时使用）'",
                f"ALTER TABLE {TABLE_NAME} ADD INDEX idx_user_id (user_id)",
                f"ALTER TABLE {TABLE_NAME} ADD INDEX idx_is_public (is_public)"
            ]
            
            for alter_sql in alter_sqls:
                try:
                    cursor.execute(alter_sql)
                    logger.info(f"Successfully executed: {alter_sql}")
                except Exception as e:
                    # Ignore errors if column/index already exists
                    error_msg = str(e)
                    if "Duplicate column name" in error_msg or "Duplicate key name" in error_msg:
                        logger.debug(f"Column/Index already exists, skipping: {alter_sql}")
                    else:
                        logger.warning(f"Failed to alter table: {e}")
            
        logger.info(f"Table {TABLE_NAME} ensured to exist")
    except Exception as e:
        logger.error(f"Failed to create table {TABLE_NAME}: {e}")
        raise KsConnectionError(f"创建表失败: {e}")


def create_reminder(content: str, is_public: bool = True, user_id: Optional[str] = None) -> dict:
    """
    创建新提醒
    
    Args:
        content: 提醒内容（自然语言）
        is_public: 是否公开（默认True）
        user_id: 用户ID（私有提醒时必填）
    
    Returns:
        {
            "success": True,
            "reminder_id": 1
        }
    
    Raises:
        ValueError: 内容为空、参数无效或超出限制
        KsConnectionError: 数据库操作失败
    """
    # 参数验证
    if not content or not content.strip():
        raise ValueError("content不能为空")
    
    if not is_public and not user_id:
        raise ValueError("私有提醒必须指定user_id")
    
    _ensure_table_exists()
    
    try:
        with db_session() as cursor:
            # 检查数量限制
            if is_public:
                # 公开提醒最多10个
                cursor.execute(f"SELECT COUNT(*) as count FROM {TABLE_NAME} WHERE is_public = 1")
                count = cursor.fetchone()[0]
                if count >= 10:
                    raise ValueError("公开提醒已达上限（最多10个）")
            else:
                # 私有提醒每个用户最多5个
                cursor.execute(f"SELECT COUNT(*) as count FROM {TABLE_NAME} WHERE is_public = 0 AND user_id = %s", (user_id,))
                count = cursor.fetchone()[0]
                if count >= 5:
                    raise ValueError(f"用户 {user_id} 的私有提醒已达上限（最多5个）")
            
            sql = f"""
            INSERT INTO {TABLE_NAME} (content, is_public, user_id)
            VALUES (%s, %s, %s)
            """
            cursor.execute(sql, (content.strip(), 1 if is_public else 0, user_id))
            
            return {
                "success": True,
                "reminder_id": cursor.lastrowid
            }
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        logger.error(f"Failed to create reminder: {e}")
        raise KsConnectionError(f"创建提醒失败: {e}")


def get_all_reminders(user_id: Optional[str] = None) -> list:
    """
    获取提醒列表
    
    Args:
        user_id: 用户ID（如果提供，返回所有公开提醒+该用户的私有提醒）
    
    Returns:
        [
            {
                "id": 1,
                "content": "今天谁比较辛苦",
                "is_public": 1,
                "user_id": None,
                "created_at": "2025-12-01 11:00:00",
                "updated_at": "2025-12-01 11:00:00"
            }
        ]
    
    按创建时间降序排序
    """
    _ensure_table_exists()
    
    try:
        with db_session(dictionary=True) as cursor:
            if user_id:
                # 返回所有公开提醒 + 该用户的私有提醒
                sql = f"""
                SELECT id, content, is_public, user_id, created_at, updated_at
                FROM {TABLE_NAME}
                WHERE is_public = 1 OR (is_public = 0 AND user_id = %s)
                ORDER BY created_at DESC
                """
                cursor.execute(sql, (user_id,))
            else:
                # 只返回所有公开提醒
                sql = f"""
                SELECT id, content, is_public, user_id, created_at, updated_at
                FROM {TABLE_NAME}
                WHERE is_public = 1
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
            "is_public": 1,
            "user_id": None,
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
            SELECT id, content, is_public, user_id, created_at, updated_at
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


def update_reminder(reminder_id: int, content: Optional[str] = None, is_public: Optional[bool] = None, user_id: Optional[str] = None) -> dict:
    """
    更新提醒
    
    Args:
        reminder_id: 提醒ID
        content: 新的提醒内容（可选）
        is_public: 是否公开（可选）
        user_id: 用户ID（可选，切换为私有时需要）
    
    Returns:
        {
            "success": True,
            "message": "提醒更新成功"
        }
    
    Raises:
        ValueError: 参数无效、提醒不存在或超出限制
        KsConnectionError: 数据库操作失败
    """
    # 参数验证
    if content is not None and (not content or not content.strip()):
        raise ValueError("content不能为空")
    
    if is_public is False and not user_id:
        raise ValueError("切换为私有提醒时必须指定user_id")
    
    _ensure_table_exists()
    
    try:
        with db_session(dictionary=True) as cursor:
            # 获取当前提醒信息
            check_sql = f"SELECT id, is_public, user_id FROM {TABLE_NAME} WHERE id = %s"
            cursor.execute(check_sql, (reminder_id,))
            current = cursor.fetchone()
            if not current:
                raise ValueError("提醒不存在")
            
            # 检查数量限制（如果要切换公开/私有状态）
            if is_public is not None and is_public != current['is_public']:
                if is_public:
                    # 切换为公开，检查公开提醒数量
                    cursor.execute(f"SELECT COUNT(*) as count FROM {TABLE_NAME} WHERE is_public = 1")
                    count = cursor.fetchone()['count']
                    if count >= 10:
                        raise ValueError("公开提醒已达上限（最多10个）")
                else:
                    # 切换为私有，检查该用户的私有提醒数量
                    cursor.execute(f"SELECT COUNT(*) as count FROM {TABLE_NAME} WHERE is_public = 0 AND user_id = %s", (user_id,))
                    count = cursor.fetchone()['count']
                    if count >= 5:
                        raise ValueError(f"用户 {user_id} 的私有提醒已达上限（最多5个）")
            
            # 构建更新SQL
            update_fields = []
            params = []
            
            if content is not None:
                update_fields.append("content = %s")
                params.append(content.strip())
            
            if is_public is not None:
                update_fields.append("is_public = %s")
                params.append(1 if is_public else 0)
            
            if is_public is False and user_id is not None:
                update_fields.append("user_id = %s")
                params.append(user_id)
            elif is_public is True:
                # 切换为公开时清空user_id
                update_fields.append("user_id = NULL")
            
            if not update_fields:
                raise ValueError("没有需要更新的字段")
            
            params.append(reminder_id)
            sql = f"UPDATE {TABLE_NAME} SET {', '.join(update_fields)} WHERE id = %s"
            cursor.execute(sql, params)
        
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
