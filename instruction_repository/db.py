"""
Instruction Repository - 数据库操作模块

提供agent_instructions表的CRUD操作,使用统一的db_session管理器
"""

import logging
from typing import List, Dict, Any, Optional
from ks_infrastructure import db_session
from ks_infrastructure.services.exceptions import KsConnectionError

logger = logging.getLogger(__name__)

TABLE_NAME = "agent_instructions"


def _ensure_table_exists():
    """
    确保agent_instructions表存在,不存在则创建
    """
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        owner VARCHAR(255) NOT NULL,
        content TEXT NOT NULL,
        is_active TINYINT DEFAULT 1,
        priority INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_owner (owner),
        INDEX idx_owner_active (owner, is_active)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent用户指示表'
    """
    try:
        with db_session() as cursor:
            cursor.execute(create_table_sql)
        logger.info(f"Table {TABLE_NAME} ensured to exist")
    except Exception as e:
        logger.error(f"Failed to create table {TABLE_NAME}: {e}")
        raise KsConnectionError(f"创建表失败: {e}")


def create_instruction(owner: str, content: str, priority: int = 0) -> dict:
    """
    创建新指示
    
    Args:
        owner: 所有者用户名
        content: 指示内容(≤400字符)
        priority: 优先级,数字越大越优先(默认0)
    
    Returns:
        {
            "success": True,
            "instruction_id": 1
        }
    
    Raises:
        ValueError: 内容超过400字或参数无效
        KsConnectionError: 数据库操作失败
    """
    # 参数验证
    if not owner or not owner.strip():
        raise ValueError("owner不能为空")
    
    if not content or not content.strip():
        raise ValueError("content不能为空")
    
    if len(content) > 400:
        raise ValueError(f"指示内容超过400字符限制(当前{len(content)}字符)")
    
    _ensure_table_exists()
    
    try:
        with db_session() as cursor:
            sql = f"""
            INSERT INTO {TABLE_NAME} (owner, content, priority)
            VALUES (%s, %s, %s)
            """
            cursor.execute(sql, (owner.strip(), content.strip(), priority))
            
            return {
                "success": True,
                "instruction_id": cursor.lastrowid
            }
    except Exception as e:
        logger.error(f"Failed to create instruction: {e}")
        raise KsConnectionError(f"创建指示失败: {e}")


def get_active_instructions(owner: str) -> list:
    """
    获取用户的所有激活指示
    
    Args:
        owner: 所有者用户名
    
    Returns:
        [
            {
                "id": 1,
                "content": "回答要简洁明了",
                "priority": 10,
                "created_at": "2025-11-24 18:00:00"
            }
        ]
    
    按优先级降序、创建时间升序排序
    """
    _ensure_table_exists()
    
    try:
        with db_session(dictionary=True) as cursor:
            sql = f"""
            SELECT id, content, priority, created_at
            FROM {TABLE_NAME}
            WHERE owner = %s AND is_active = 1
            ORDER BY priority DESC, created_at ASC
            """
            cursor.execute(sql, (owner,))
            results = cursor.fetchall()
            
            # 格式化时间
            for result in results:
                if result.get('created_at'):
                    result['created_at'] = result['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            return results
    except Exception as e:
        logger.error(f"Failed to get active instructions: {e}")
        raise KsConnectionError(f"查询指示失败: {e}")


def get_all_instructions(owner: str, include_inactive: bool = False) -> list:
    """
    获取用户的所有指示
    
    Args:
        owner: 所有者用户名
        include_inactive: 是否包含禁用的指示(默认False)
    
    Returns:
        [
            {
                "id": 1,
                "content": "回答要简洁明了",
                "is_active": 1,
                "priority": 10,
                "created_at": "2025-11-24 18:00:00",
                "updated_at": "2025-11-24 18:00:00"
            }
        ]
    """
    _ensure_table_exists()
    
    try:
        with db_session(dictionary=True) as cursor:
            if include_inactive:
                sql = f"""
                SELECT id, content, is_active, priority, created_at, updated_at
                FROM {TABLE_NAME}
                WHERE owner = %s
                ORDER BY priority DESC, created_at ASC
                """
            else:
                sql = f"""
                SELECT id, content, is_active, priority, created_at, updated_at
                FROM {TABLE_NAME}
                WHERE owner = %s AND is_active = 1
                ORDER BY priority DESC, created_at ASC
                """
            
            cursor.execute(sql, (owner,))
            results = cursor.fetchall()
            
            # 格式化时间
            for result in results:
                if result.get('created_at'):
                    result['created_at'] = result['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                if result.get('updated_at'):
                    result['updated_at'] = result['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            return results
    except Exception as e:
        logger.error(f"Failed to get all instructions: {e}")
        raise KsConnectionError(f"查询指示失败: {e}")


def get_instruction_by_id(instruction_id: int, owner: str) -> dict:
    """
    获取单个指示的详情
    
    Args:
        instruction_id: 指示ID
        owner: 所有者用户名(用于权限验证)
    
    Returns:
        {
            "id": 1,
            "content": "回答要简洁明了",
            "is_active": 1,
            "priority": 10,
            "created_at": "2025-11-24 18:00:00",
            "updated_at": "2025-11-24 18:00:00"
        }
    
    Raises:
        ValueError: 指示不存在或无权限查看
        KsConnectionError: 数据库操作失败
    """
    _ensure_table_exists()
    
    try:
        with db_session(dictionary=True) as cursor:
            sql = f"""
            SELECT id, content, is_active, priority, created_at, updated_at
            FROM {TABLE_NAME}
            WHERE id = %s AND owner = %s
            """
            cursor.execute(sql, (instruction_id, owner))
            result = cursor.fetchone()
            
            if not result:
                raise ValueError("指示不存在或无权限查看")
            
            # 格式化时间
            if result.get('created_at'):
                result['created_at'] = result['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if result.get('updated_at'):
                result['updated_at'] = result['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            return result
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Failed to get instruction by id: {e}")
        raise KsConnectionError(f"查询指示失败: {e}")


def update_instruction(
    instruction_id: int,
    owner: str,
    content: str = None,
    is_active: int = None,
    priority: int = None
) -> dict:
    """
    更新指示
    
    Args:
        instruction_id: 指示ID
        owner: 所有者用户名(用于权限验证)
        content: 新的指示内容(可选,≤400字符)
        is_active: 是否启用(可选,0或1)
        priority: 优先级(可选)
    
    Returns:
        {
            "success": True,
            "message": "指示更新成功"
        }
    
    Raises:
        ValueError: 参数无效或权限不足
        KsConnectionError: 数据库操作失败
    """
    # 参数验证
    if content is not None and len(content) > 400:
        raise ValueError(f"指示内容超过400字符限制(当前{len(content)}字符)")
    
    if is_active is not None and is_active not in (0, 1):
        raise ValueError("is_active必须为0或1")
    
    _ensure_table_exists()
    
    try:
        with db_session() as cursor:
            # 验证指示是否属于该用户
            check_sql = f"SELECT id FROM {TABLE_NAME} WHERE id = %s AND owner = %s"
            cursor.execute(check_sql, (instruction_id, owner))
            if not cursor.fetchone():
                raise ValueError("指示不存在或无权限修改")
            
            # 构建更新语句
            update_fields = []
            params = []
            
            if content is not None:
                update_fields.append("content = %s")
                params.append(content.strip())
            
            if is_active is not None:
                update_fields.append("is_active = %s")
                params.append(is_active)
            
            if priority is not None:
                update_fields.append("priority = %s")
                params.append(priority)
            
            if not update_fields:
                return {"success": True, "message": "无更新内容"}
            
            params.extend([instruction_id, owner])
            
            sql = f"""
            UPDATE {TABLE_NAME}
            SET {', '.join(update_fields)}
            WHERE id = %s AND owner = %s
            """
            cursor.execute(sql, params)
        
        return {
            "success": True,
            "message": "指示更新成功"
        }
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Failed to update instruction: {e}")
        raise KsConnectionError(f"更新指示失败: {e}")


def delete_instruction(instruction_id: int, owner: str) -> dict:
    """
    删除指示
    
    Args:
        instruction_id: 指示ID
        owner: 所有者用户名(用于权限验证)
    
    Returns:
        {
            "success": True,
            "message": "指示删除成功"
        }
    
    Raises:
        ValueError: 权限不足
        KsConnectionError: 数据库操作失败
    """
    _ensure_table_exists()
    
    try:
        with db_session() as cursor:
            # 验证并删除
            sql = f"DELETE FROM {TABLE_NAME} WHERE id = %s AND owner = %s"
            cursor.execute(sql, (instruction_id, owner))
            
            if cursor.rowcount == 0:
                raise ValueError("指示不存在或无权限删除")
        
        return {
            "success": True,
            "message": "指示删除成功"
        }
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Failed to delete instruction: {e}")
        raise KsConnectionError(f"删除指示失败: {e}")
