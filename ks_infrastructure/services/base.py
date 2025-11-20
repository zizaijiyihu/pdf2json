"""
基础服务模块

包含服务工厂的公共功能
"""

import json
import logging
from typing import Any, Dict

# 配置日志
logger = logging.getLogger(__name__)

# 全局实例缓存
_instances: Dict[str, Any] = {}


def get_instance_key(service_name: str, config: dict) -> str:
    """
    生成稳定的实例缓存键

    Args:
        service_name: 服务名称
        config: 配置字典

    Returns:
        str: 稳定的缓存键
    """
    # 使用 json.dumps 生成稳定的键，sort_keys 确保顺序一致
    config_str = json.dumps(config, sort_keys=True, default=str)
    return f"{service_name}_{config_str}"


def get_cached_instance(key: str) -> Any:
    """获取缓存的实例"""
    return _instances.get(key)


def set_cached_instance(key: str, instance: Any) -> None:
    """设置缓存的实例"""
    _instances[key] = instance
    logger.debug(f"Cached instance for key: {key}")


def clear_instances() -> None:
    """清空所有缓存的实例"""
    _instances.clear()
    logger.debug("Cleared all cached instances")
