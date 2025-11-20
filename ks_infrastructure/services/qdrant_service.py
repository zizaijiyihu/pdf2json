"""
Qdrant向量数据库服务
"""

import logging
from qdrant_client import QdrantClient

from .base import get_instance_key, get_cached_instance, set_cached_instance
from .exceptions import KsConnectionError

logger = logging.getLogger(__name__)


def ks_qdrant(**kwargs) -> QdrantClient:
    """
    Qdrant向量数据库服务工厂函数

    Args:
        **kwargs: 传递给QdrantClient的参数

    Returns:
        QdrantClient: Qdrant客户端对象

    Raises:
        KsConnectionError: 当连接失败时抛出
    """
    from ..configs.default import QDRANT_CONFIG

    # 合并默认配置和传入参数
    config = {**QDRANT_CONFIG, **kwargs}

    instance_key = get_instance_key("qdrant", config)

    cached = get_cached_instance(instance_key)
    if cached is not None:
        return cached

    try:
        instance = QdrantClient(**config)
        set_cached_instance(instance_key, instance)
        logger.info(f"Qdrant client connected to {config.get('url')}")
        return instance
    except Exception as e:
        raise KsConnectionError(f"Qdrant连接失败: {e}")
