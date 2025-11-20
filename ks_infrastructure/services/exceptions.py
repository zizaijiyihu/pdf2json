"""
自定义异常类

提供统一的异常处理
"""


class KsInfrastructureError(Exception):
    """KS Infrastructure 基础异常类"""
    pass


class KsConnectionError(KsInfrastructureError):
    """连接错误"""
    pass


class KsConfigError(KsInfrastructureError):
    """配置错误"""
    pass


class KsServiceError(KsInfrastructureError):
    """服务调用错误"""
    pass
