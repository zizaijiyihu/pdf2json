"""
数据库会话管理器

提供统一的数据库会话上下文管理,自动处理:
- 连接获取和归还
- Cursor 创建和关闭
- 事务提交和回滚
- 异常处理

使用示例:
    # 基本用法
    with db_session() as cursor:
        cursor.execute("SELECT * FROM users")
        return cursor.fetchall()
    
    # 返回字典格式
    with db_session(dictionary=True) as cursor:
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        return cursor.fetchone()
    
    # 手动控制事务
    with db_session(auto_commit=False) as cursor:
        cursor.execute("UPDATE ...")
        # 手动提交
        cursor.connection.commit()
"""

import logging
from contextlib import contextmanager
from typing import Generator, Optional
from mysql.connector.cursor import MySQLCursor

from .services.mysql_service import ks_mysql
from .services.exceptions import KsConnectionError

logger = logging.getLogger(__name__)


@contextmanager
def db_session(
    dictionary: bool = False,
    auto_commit: bool = True
) -> Generator[MySQLCursor, None, None]:
    """
    数据库会话上下文管理器
    
    Args:
        dictionary: 是否返回字典格式的结果(默认False,返回元组)
        auto_commit: 是否自动提交事务(默认True)
    
    Yields:
        MySQLCursor: 数据库游标对象
        
    Raises:
        KsConnectionError: 数据库操作失败时抛出
        
    Example:
        with db_session() as cursor:
            cursor.execute("INSERT INTO users (name) VALUES (%s)", ("Alice",))
            user_id = cursor.lastrowid
    """
    conn = None
    cursor = None
    
    try:
        # 从连接池获取连接
        conn = ks_mysql()
        cursor = conn.cursor(dictionary=dictionary)
        
        yield cursor
        
        # 自动提交事务
        if auto_commit:
            conn.commit()
            
    except Exception as e:
        # 发生异常时回滚
        if conn and auto_commit:
            try:
                conn.rollback()
                logger.warning(f"Transaction rolled back due to error: {e}")
            except Exception as rollback_error:
                logger.error(f"Failed to rollback transaction: {rollback_error}")
        
        # 重新抛出原始异常
        if isinstance(e, KsConnectionError):
            raise
        else:
            raise KsConnectionError(f"Database operation failed: {e}") from e
            
    finally:
        # 清理资源
        if cursor:
            try:
                cursor.close()
            except Exception as e:
                logger.error(f"Failed to close cursor: {e}")
        
        if conn:
            try:
                conn.close()  # 归还连接到池
            except Exception as e:
                logger.error(f"Failed to close connection: {e}")


@contextmanager
def db_transaction() -> Generator[MySQLCursor, None, None]:
    """
    数据库事务上下文管理器(显式事务控制)
    
    与 db_session 的区别:
    - 显式开启事务
    - 必须手动提交或回滚
    - 适合需要精确控制事务边界的场景
    
    Yields:
        MySQLCursor: 数据库游标对象
        
    Example:
        with db_transaction() as cursor:
            cursor.execute("UPDATE accounts SET balance = balance - 100 WHERE id = 1")
            cursor.execute("UPDATE accounts SET balance = balance + 100 WHERE id = 2")
            cursor.connection.commit()  # 手动提交
    """
    conn = None
    cursor = None
    
    try:
        conn = ks_mysql()
        conn.start_transaction()
        cursor = conn.cursor(dictionary=True)
        
        yield cursor
        
    except Exception as e:
        if conn:
            try:
                conn.rollback()
                logger.warning(f"Transaction rolled back: {e}")
            except Exception as rollback_error:
                logger.error(f"Failed to rollback: {rollback_error}")
        raise KsConnectionError(f"Transaction failed: {e}") from e
        
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception as e:
                logger.error(f"Failed to close cursor: {e}")
        
        if conn:
            try:
                conn.close()
            except Exception as e:
                logger.error(f"Failed to close connection: {e}")
