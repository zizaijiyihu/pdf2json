"""
MySQL数据库服务
"""

import logging
import mysql.connector
from mysql.connector.connection import MySQLConnection

from .base import get_instance_key, get_cached_instance, set_cached_instance
from .exceptions import KsConnectionError

logger = logging.getLogger(__name__)


def ks_mysql(**kwargs) -> MySQLConnection:
    """
    MySQL数据库服务工厂函数

    Args:
        **kwargs: 传递给mysql.connector.connect的参数

    Returns:
        mysql.connector.connection.MySQLConnection: MySQL连接对象

    Raises:
        KsConnectionError: 当连接失败时抛出
    """
    from ..configs.default import MYSQL_CONFIG

    # 合并默认配置和传入参数
    config = {**MYSQL_CONFIG, **kwargs}

    instance_key = get_instance_key("mysql", config)

    cached = get_cached_instance(instance_key)
    if cached is not None:
        # 检查连接是否仍然有效
        try:
            if cached.is_connected():
                return cached
            else:
                # 尝试重连
                cached.reconnect()
                logger.info("MySQL connection reconnected")
                return cached
        except Exception:
            # 连接无效，创建新连接
            logger.warning("Cached MySQL connection invalid, creating new one")

    try:
        instance = mysql.connector.connect(**config)
        set_cached_instance(instance_key, instance)
        logger.info(f"MySQL connected to {config.get('host')}:{config.get('port')}")
        return instance
    except mysql.connector.Error as e:
        raise KsConnectionError(f"MySQL连接失败: {e}")
