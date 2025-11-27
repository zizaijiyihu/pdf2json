"""
Quote Repository - 语录数据库操作模块

提供ks_quotes表的CRUD操作,使用统一的db_session管理器
"""

import logging
from typing import List, Dict, Any, Optional
from ks_infrastructure import db_session
from ks_infrastructure.services.exceptions import KsConnectionError

logger = logging.getLogger(__name__)

TABLE_NAME = "ks_quotes"


def _ensure_table_exists():
    """
    确保ks_quotes表存在,不存在则创建
    """
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        content TEXT NOT NULL COMMENT '语录内容',
        is_fixed TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否固定:1是,0否',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_is_fixed (is_fixed),
        INDEX idx_created_at (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    try:
        with db_session() as cursor:
            cursor.execute(create_table_sql)
        logger.info(f"Table {TABLE_NAME} ensured to exist")
    except Exception as e:
        logger.error(f"Failed to create table {TABLE_NAME}: {e}")
        raise KsConnectionError(f"Failed to create table {TABLE_NAME}: {e}")


# 确保模块导入时检查表是否存在
_ensure_table_exists()


def create_quote(content: str, is_fixed: int = 0) -> Dict[str, Any]:
    """
    创建新语录

    Args:
        content: 语录内容
        is_fixed: 是否固定(0或1)

    Returns:
        Dict: 创建成功的语录信息
    """
    if not content:
        raise ValueError("Content cannot be empty")
    
    is_fixed = 1 if is_fixed else 0

    try:
        with db_session() as cursor:
            # 如果设置为固定,先将其他所有语录设为非固定
            if is_fixed == 1:
                cursor.execute(f"UPDATE {TABLE_NAME} SET is_fixed = 0 WHERE is_fixed = 1")
            
            # 插入新语录
            sql = f"INSERT INTO {TABLE_NAME} (content, is_fixed) VALUES (%s, %s)"
            cursor.execute(sql, (content, is_fixed))
            quote_id = cursor.lastrowid
        
        return {
            "id": quote_id,
            "content": content,
            "is_fixed": is_fixed,
            "success": True
        }
    except Exception as e:
        logger.error(f"Failed to create quote: {e}")
        raise KsConnectionError(f"Failed to create quote: {e}")


def update_quote(quote_id: int, content: Optional[str] = None, is_fixed: Optional[int] = None) -> Dict[str, Any]:
    """
    更新语录

    Args:
        quote_id: 语录ID
        content: 新内容(可选)
        is_fixed: 是否固定(可选)

    Returns:
        Dict: 更新结果
    """
    if content is not None and not content:
        raise ValueError("Content cannot be empty")

    try:
        with db_session() as cursor:
            # 检查记录是否存在
            check_sql = f"SELECT id FROM {TABLE_NAME} WHERE id = %s"
            cursor.execute(check_sql, (quote_id,))
            if not cursor.fetchone():
                raise ValueError(f"Quote with id {quote_id} not found")

            updates = []
            params = []
            
            if content is not None:
                updates.append("content = %s")
                params.append(content)
            
            if is_fixed is not None:
                is_fixed_val = 1 if is_fixed else 0
                # 如果要设为固定,先重置其他的
                if is_fixed_val == 1:
                    cursor.execute(f"UPDATE {TABLE_NAME} SET is_fixed = 0 WHERE is_fixed = 1")
                
                updates.append("is_fixed = %s")
                params.append(is_fixed_val)
            
            if not updates:
                return {"success": True, "message": "No changes made"}
                
            params.append(quote_id)
            sql = f"UPDATE {TABLE_NAME} SET {', '.join(updates)} WHERE id = %s"
            cursor.execute(sql, tuple(params))
        
        return {"success": True, "message": "Quote updated successfully"}
    except ValueError as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to update quote {quote_id}: {e}")
        raise KsConnectionError(f"Failed to update quote {quote_id}: {e}")


def delete_quote(quote_id: int) -> Dict[str, Any]:
    """
    删除语录

    Args:
        quote_id: 语录ID

    Returns:
        Dict: 删除结果
    """
    try:
        with db_session() as cursor:
            sql = f"DELETE FROM {TABLE_NAME} WHERE id = %s"
            cursor.execute(sql, (quote_id,))
            if cursor.rowcount == 0:
                raise ValueError(f"Quote with id {quote_id} not found")
        
        return {"success": True, "message": "Quote deleted successfully"}
    except ValueError as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to delete quote {quote_id}: {e}")
        raise KsConnectionError(f"Failed to delete quote {quote_id}: {e}")


def get_quotes(page: int = 1, page_size: int = 10) -> Dict[str, Any]:
    """
    分页获取语录列表

    Args:
        page: 页码,从1开始
        page_size: 每页数量

    Returns:
        Dict: 包含列表和分页信息
    """
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 10
        
    offset = (page - 1) * page_size
    
    try:
        with db_session(dictionary=True) as cursor:
            # 获取总数
            count_sql = f"SELECT COUNT(*) as total FROM {TABLE_NAME}"
            cursor.execute(count_sql)
            total = cursor.fetchone()['total']
            
            # 获取列表,优先显示固定的,然后按创建时间倒序
            sql = f"""
                SELECT id, content, is_fixed, created_at, updated_at 
                FROM {TABLE_NAME} 
                ORDER BY is_fixed DESC, created_at DESC 
                LIMIT %s OFFSET %s
            """
            cursor.execute(sql, (page_size, offset))
            items = cursor.fetchall()
            
            # 处理datetime对象以便JSON序列化
            for item in items:
                if item['created_at']:
                    item['created_at'] = item['created_at'].isoformat()
                if item['updated_at']:
                    item['updated_at'] = item['updated_at'].isoformat()
            
            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
    except Exception as e:
        logger.error(f"Failed to get quotes: {e}")
        raise KsConnectionError(f"Failed to get quotes: {e}")
