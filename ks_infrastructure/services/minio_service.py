"""
MinIO对象存储服务
"""

import logging
import boto3
from botocore.client import BaseClient

from .base import get_instance_key, get_cached_instance, set_cached_instance
from .exceptions import KsConnectionError

logger = logging.getLogger(__name__)


def ks_minio(**kwargs) -> BaseClient:
    """
    MinIO对象存储服务工厂函数

    Args:
        **kwargs: 传递给boto3.client的参数

    Returns:
        boto3.session.Session.client: MinIO客户端对象

    Raises:
        KsConnectionError: 当连接失败时抛出
    """
    from ..configs.default import MINIO_CONFIG

    # 合并默认配置和传入参数
    config = {
        'endpoint_url': MINIO_CONFIG['endpoint'],
        'aws_access_key_id': MINIO_CONFIG['access_key'],
        'aws_secret_access_key': MINIO_CONFIG['secret_key'],
        'region_name': MINIO_CONFIG['region'],
        'service_name': 's3'
    }
    config.update(kwargs)

    # 分离service_name以便传递给boto3.client
    service_name = config.pop('service_name')
    instance_key = get_instance_key("minio", config)

    cached = get_cached_instance(instance_key)
    if cached is not None:
        return cached

    try:
        instance = boto3.client(service_name, **config)
        set_cached_instance(instance_key, instance)
        logger.info(f"MinIO client connected to {config.get('endpoint_url')}")
        return instance
    except Exception as e:
        raise KsConnectionError(f"MinIO连接失败: {e}")
