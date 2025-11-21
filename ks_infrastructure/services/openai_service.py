"""
OpenAI大语言模型服务
"""

import logging
from openai import OpenAI

from .base import get_instance_key, get_cached_instance, set_cached_instance
from .exceptions import KsConnectionError

logger = logging.getLogger(__name__)


def ks_openai(**kwargs) -> OpenAI:
    """
    OpenAI大语言模型服务工厂函数

    Args:
        **kwargs: 传递给OpenAI的参数

    Returns:
        OpenAI: OpenAI客户端对象

    Raises:
        KsConnectionError: 当连接失败时抛出
    """
    from ..configs.default import OPENAI_CONFIG

    # 合并默认配置和传入参数
    config = {**OPENAI_CONFIG, **kwargs}

    # 移除 'model' 参数，因为它不是 OpenAI 客户端初始化参数
    # 'model' 应该在调用 API 时传递（如 chat.completions.create 时）
    config.pop('model', None)

    instance_key = get_instance_key("openai", config)

    cached = get_cached_instance(instance_key)
    if cached is not None:
        return cached

    try:
        instance = OpenAI(**config)
        set_cached_instance(instance_key, instance)
        logger.info(f"OpenAI client connected to {config.get('base_url')}")
        return instance
    except Exception as e:
        raise KsConnectionError(f"OpenAI客户端创建失败: {e}")
