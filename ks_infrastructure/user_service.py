"""
User Service - 用户管理服务

提供统一的获取当前用户的方法，替代硬编码的默认用户。
"""

def get_current_user() -> str:
    """
    获取当前用户
    
    Returns:
        str: 当前用户名
    """
    # 目前返回默认用户，未来可扩展为从请求头或Token中获取
    return "huxiaoxiao"
