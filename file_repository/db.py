"""
文件元数据数据库管理
"""

import logging
from typing import Optional
from datetime import datetime

from ks_infrastructure.services.mysql_service import ks_mysql
from ks_infrastructure.services.exceptions import KsConnectionError

logger = logging.getLogger(__name__)

# 表名
TABLE_NAME = "file_metadata"


def _ensure_table_exists() -> None:
    """
    确保文件元数据表存在，不存在则创建
    """
    conn = ks_mysql()
    cursor = conn.cursor()

    try:
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        cursor.execute(create_table_sql)
        conn.commit()
        logger.info(f"Table {TABLE_NAME} ensured")
    except Exception as e:
        conn.rollback()
        raise KsConnectionError(f"创建表失败: {e}")
    finally:
        cursor.close()


def save_file_metadata(
    file_path: str,
    owner: str,
    filename: str,
    bucket: str,
    is_public: int = 0,
    content_type: Optional[str] = None,
    file_size: Optional[int] = None
) -> int:
    """
    保存文件元数据到数据库

    Args:
        file_path: 文件在MinIO中的路径 (owner/filename)
        owner: 文件所有者
        filename: 文件名
        bucket: bucket名称
        is_public: 是否公开 (0=非公开, 1=公开)
        content_type: 文件MIME类型
        file_size: 文件大小（字节）

    Returns:
        int: 插入的记录ID

    Raises:
        KsConnectionError: 保存失败时抛出
    """
    _ensure_table_exists()
    conn = ks_mysql()
    cursor = conn.cursor()

    try:
        # 使用 INSERT ... ON DUPLICATE KEY UPDATE 实现覆盖
        sql = f"""
        INSERT INTO {TABLE_NAME}
            (file_path, owner, filename, bucket, is_public, content_type, file_size)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            owner = VALUES(owner),
            filename = VALUES(filename),
            bucket = VALUES(bucket),
            is_public = VALUES(is_public),
            content_type = VALUES(content_type),
            file_size = VALUES(file_size),
            updated_at = CURRENT_TIMESTAMP
        """
        cursor.execute(sql, (file_path, owner, filename, bucket, is_public, content_type, file_size))
        conn.commit()

        # 获取插入或更新的ID
        record_id = cursor.lastrowid
        logger.info(f"Saved file metadata: {file_path} (id={record_id})")
        return record_id
    except Exception as e:
        conn.rollback()
        raise KsConnectionError(f"保存文件元数据失败: {e}")
    finally:
        cursor.close()


def get_owner_files(
    owner: str,
    include_public: bool = False
) -> list[dict]:
    """
    获取所有者的文件列表

    Args:
        owner: 文件所有者
        include_public: 是否包含公开文件 (is_public=1)
                       - False: 只返回所有者的文件
                       - True: 返回所有者的文件 + 所有公开文件

    Returns:
        list[dict]: 文件列表，每个文件包含所有字段

    Raises:
        KsConnectionError: 查询失败时抛出
    """
    _ensure_table_exists()
    conn = ks_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        if include_public:
            # 查询所有者的文件 + 所有公开文件
            sql = f"""
            SELECT * FROM {TABLE_NAME}
            WHERE owner = %s OR is_public = 1
            ORDER BY created_at DESC
            """
            cursor.execute(sql, (owner,))
        else:
            # 只查询所有者的文件
            sql = f"""
            SELECT * FROM {TABLE_NAME}
            WHERE owner = %s
            ORDER BY created_at DESC
            """
            cursor.execute(sql, (owner,))

        results = cursor.fetchall()
        return results
    except Exception as e:
        raise KsConnectionError(f"查询文件列表失败: {e}")
    finally:
        cursor.close()


def set_file_public_status(
    owner: str,
    filename: str,
    is_public: int
) -> bool:
    """
    设置文件的公开状态

    Args:
        owner: 文件所有者
        filename: 文件名
        is_public: 公开状态 (0=非公开, 1=公开)

    Returns:
        bool: 是否成功更新

    Raises:
        KsConnectionError: 更新失败时抛出
    """
    _ensure_table_exists()
    conn = ks_mysql()
    cursor = conn.cursor()

    try:
        file_path = f"{owner}/{filename}"
        sql = f"""
        UPDATE {TABLE_NAME}
        SET is_public = %s, updated_at = CURRENT_TIMESTAMP
        WHERE file_path = %s AND owner = %s
        """
        cursor.execute(sql, (is_public, file_path, owner))
        conn.commit()

        affected_rows = cursor.rowcount
        if affected_rows > 0:
            logger.info(f"Updated file public status: {file_path} -> is_public={is_public}")
            return True
        else:
            logger.warning(f"File not found or no permission: {file_path}")
            return False
    except Exception as e:
        conn.rollback()
        raise KsConnectionError(f"更新文件公开状态失败: {e}")
    finally:
        cursor.close()


def get_file_metadata(file_path: str) -> Optional[dict]:
    """
    获取文件元数据

    Args:
        file_path: 文件路径 (owner/filename)

    Returns:
        dict: 文件元数据，不存在返回None

    Raises:
        KsConnectionError: 查询失败时抛出
    """
    _ensure_table_exists()
    conn = ks_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        sql = f"""
        SELECT * FROM {TABLE_NAME}
        WHERE file_path = %s
        """
        cursor.execute(sql, (file_path,))
        result = cursor.fetchone()
        return result
    except Exception as e:
        raise KsConnectionError(f"查询文件元数据失败: {e}")
    finally:
        cursor.close()
