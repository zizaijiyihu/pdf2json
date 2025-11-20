"""
KS Infrastructure 模块

提供统一的服务工厂方法，用于创建和管理各种基础设施服务实例。
"""

from .services import (
    ks_mysql,
    ks_minio,
    ks_qdrant,
    ks_openai,
    ks_embedding,
    ks_vision,
    KsEmbeddingService,
    KsVisionService,
    clear_instances,
    KsInfrastructureError,
    KsConnectionError,
    KsConfigError,
    KsServiceError,
)

# 默认配置初始化函数
def init_infrastructure(config=None):
    """
    初始化基础设施服务工厂

    Args:
        config (dict, optional): 自定义配置字典
    """
    # 清空现有实例缓存
    clear_instances()

    # 如果提供了配置，则更新默认配置
    if config:
        from .configs import default
        for key, value in config.items():
            if hasattr(default, key):
                setattr(default, key, value)


__all__ = [
    # 工厂函数
    'ks_mysql',
    'ks_minio',
    'ks_qdrant',
    'ks_openai',
    'ks_embedding',
    'ks_vision',
    # 服务类
    'KsEmbeddingService',
    'KsVisionService',
    # 初始化函数
    'init_infrastructure',
    # 异常类
    'KsInfrastructureError',
    'KsConnectionError',
    'KsConfigError',
    'KsServiceError',
]