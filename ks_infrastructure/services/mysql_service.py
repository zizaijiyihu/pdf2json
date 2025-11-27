"""
MySQL数据库服务
"""

import logging
import mysql.connector
from mysql.connector import pooling
from mysql.connector.connection import MySQLConnection

from .exceptions import KsConnectionError

logger = logging.getLogger(__name__)

# 全局连接池实例
_connection_pool = None


def get_mysql_pool() -> pooling.MySQLConnectionPool:
    """
    获取MySQL连接池实例(单例模式)
    
    Returns:
        pooling.MySQLConnectionPool: MySQL连接池
    """
    global _connection_pool
    
    if _connection_pool is None:
        from ..configs.default import MYSQL_CONFIG
        
        try:
            _connection_pool = pooling.MySQLConnectionPool(
                pool_name="ks_mysql_pool",
                pool_size=10,  # 连接池大小,可根据并发需求调整
                pool_reset_session=True,  # 归还连接时重置会话状态
                **MYSQL_CONFIG
            )
            logger.info(f"MySQL connection pool created: {MYSQL_CONFIG.get('host')}:{MYSQL_CONFIG.get('port')}, pool_size=10")
        except mysql.connector.Error as e:
            raise KsConnectionError(f"Failed to create MySQL connection pool: {e}")
    
    return _connection_pool


def ks_mysql(**kwargs) -> MySQLConnection:
    """
    从连接池获取MySQL连接
    
    Args:
        **kwargs: 传递给连接的额外参数(通常不需要)
    
    Returns:
        mysql.connector.connection.MySQLConnection: MySQL连接对象
        
    Raises:
        KsConnectionError: 当获取连接失败时抛出
        
    Note:
        使用完连接后必须调用 conn.close() 将连接归还到池中
        建议使用 db_session 上下文管理器来自动管理连接
    """
    try:
        pool = get_mysql_pool()
        conn = pool.get_connection()
        
        # 如果有额外参数,记录警告(连接池模式下通常不应该有)
        if kwargs:
            logger.warning(f"Extra kwargs passed to ks_mysql (ignored in pool mode): {kwargs}")
        
        return conn
    except mysql.connector.Error as e:
        raise KsConnectionError(f"Failed to get connection from pool: {e}")


def close_mysql_pool():
    """
    关闭连接池(用于应用关闭时清理资源)
    """
    global _connection_pool
    if _connection_pool is not None:
        # 连接池没有直接的close方法,但会在程序退出时自动清理
        logger.info("MySQL connection pool will be cleaned up on exit")
        _connection_pool = None
