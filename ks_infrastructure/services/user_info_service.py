"""
HR API用户信息服务
"""

import logging
import requests
from typing import Dict, Any, Optional

from .base import get_instance_key, get_cached_instance, set_cached_instance
from .exceptions import KsServiceError

logger = logging.getLogger(__name__)


class KsUserInfoService:
    """
    HR API用户信息服务封装类

    提供获取用户信息的功能，隐藏底层HTTP请求细节
    """

    def __init__(self, base_url: str, api_token: str):
        """
        初始化用户信息服务

        Args:
            base_url: HR API服务基础URL
            api_token: API访问令牌
        """
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.headers = {
            "Authorization": api_token
        }

    def get_employee_info(self, email_prefix: str) -> Dict[str, Any]:
        """
        根据邮箱前缀获取员工信息

        Args:
            email_prefix: 员工邮箱前缀（如 lihaoze2）

        Returns:
            dict: 包含员工信息的字典，格式如下：
                {
                    "success": bool,
                    "data": {
                        "userId": str,
                        "userName": str,
                        "userNo": str,
                        "deptName": str,
                        "deptFullName": str,
                        "positionName": str,
                        "rank": str,
                        "location": str,
                        "sex": str,
                        "age": str,
                        "birthday": str,
                        "education": str,
                        "graduationInstitution": str,
                        "speciality": str,
                        "joinedDate": str,
                        "workAge": str,
                        "contractExpire": str,
                        ...
                    }
                }

        Raises:
            KsServiceError: 当请求失败或返回错误时抛出
        """
        url = f"{self.base_url}/{email_prefix}"

        try:
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result
                else:
                    raise KsServiceError(
                        f"HR API返回失败: {result}"
                    )
            else:
                raise KsServiceError(
                    f"HR API请求失败: {response.status_code} - {response.text}"
                )
        except requests.RequestException as e:
            raise KsServiceError(f"HR API请求异常: {e}")


    def get_subordinates(self, email_prefix: str) -> Dict[str, Any]:
        """
        根据邮箱前缀获取下属列表

        Args:
            email_prefix: 员工邮箱前缀（如 huxiaoxiao）

        Returns:
            dict: 包含下属信息的字典，格式如下：
                {
                    "success": bool,
                    "data": [
                        {
                            "userId": str,
                            "userName": str,
                            "userNo": str,
                            "deptName": str,
                            ...
                        },
                        ...
                    ]
                }

        Raises:
            KsServiceError: 当请求失败或返回错误时抛出
        """
        # 使用 /api/hr/subordinates/{email_prefix} 端点
        url = f"{self.base_url.replace('/employee', '/subordinates')}/{email_prefix}"

        try:
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result
                else:
                    raise KsServiceError(
                        f"HR API返回失败: {result}"
                    )
            else:
                raise KsServiceError(
                    f"HR API请求失败: {response.status_code} - {response.text}"
                )
        except requests.RequestException as e:
            raise KsServiceError(f"HR API请求异常: {e}")

    def get_attendance(self, email_prefix: str) -> Dict[str, Any]:
        """
        根据邮箱前缀获取考勤记录

        Args:
            email_prefix: 员工邮箱前缀（如 huxiaoxiao）

        Returns:
            dict: 包含考勤记录的字典，格式如下：
                {
                    "success": bool,
                    "data": [
                        {
                            "date": str,
                            "status": str,
                            "checkIn": str,
                            "checkOut": str,
                            ...
                        },
                        ...
                    ]
                }

        Raises:
            KsServiceError: 当请求失败或返回错误时抛出
        """
        # 使用 /api/hr/attendance/{email_prefix} 端点
        url = f"{self.base_url.replace('/employee', '/attendance')}/{email_prefix}"

        try:
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result
                else:
                    raise KsServiceError(
                        f"HR API返回失败: {result}"
                    )
            else:
                raise KsServiceError(
                    f"HR API请求失败: {response.status_code} - {response.text}"
                )
        except requests.RequestException as e:
            raise KsServiceError(f"HR API请求异常: {e}")

    def get_subordinate_employee_info(self, target_email_prefix: str, current_user_email_prefix: Optional[str] = None) -> Dict[str, Any]:
        """
        获取下属的员工信息（带权限验证）

        Args:
            target_email_prefix: 目标员工的邮箱前缀
            current_user_email_prefix: 当前用户的邮箱前缀，如果为None则使用get_current_user()获取

        Returns:
            dict: 包含员工信息的字典，格式如下：
                {
                    "success": bool,
                    "data": {...},
                    "message": str  # 可选，仅在无权限时返回
                }

        Raises:
            KsServiceError: 当请求失败或返回错误时抛出
        """
        # 获取当前用户ID
        if current_user_email_prefix is None:
            current_user_email_prefix = get_current_user()

        logger.info(f"当前用户: {current_user_email_prefix}, 查询目标员工信息: {target_email_prefix}")

        try:
            # 1. 获取当前用户的下属列表
            subordinates_result = self.get_subordinates(current_user_email_prefix)

            if not subordinates_result.get('success'):
                raise KsServiceError("无法获取下属列表")

            subordinates_data = subordinates_result.get('data', [])

            # 2. 检查目标用户是否在下属列表中
            target_user_ids = [sub.get('userId') for sub in subordinates_data]

            logger.info(f"下属列表: {target_user_ids}")

            # 判断目标用户是否在下属中
            is_subordinate = target_email_prefix in target_user_ids

            if not is_subordinate:
                # 无权限访问
                logger.warning(f"用户 {current_user_email_prefix} 无权访问 {target_email_prefix} 的员工信息")
                return {
                    "success": False,
                    "message": f"无权限访问用户 {target_email_prefix} 的员工信息"
                }

            # 3. 有权限，查询员工信息
            logger.info(f"用户 {current_user_email_prefix} 有权访问 {target_email_prefix} 的员工信息")
            employee_info_result = self.get_employee_info(target_email_prefix)

            return employee_info_result

        except KsServiceError as e:
            logger.error(f"获取下属员工信息失败: {e}")
            raise

    def get_subordinate_attendance(self, target_email_prefix: str, current_user_email_prefix: Optional[str] = None) -> Dict[str, Any]:
        """
        获取下属的考勤记录（带权限验证）

        Args:
            target_email_prefix: 目标员工的邮箱前缀
            current_user_email_prefix: 当前用户的邮箱前缀，如果为None则使用get_current_user()获取

        Returns:
            dict: 包含考勤记录的字典，格式如下：
                {
                    "success": bool,
                    "data": [...],
                    "message": str  # 可选，仅在无权限时返回
                }

        Raises:
            KsServiceError: 当请求失败或返回错误时抛出
        """
        # 获取当前用户ID
        if current_user_email_prefix is None:
            current_user_email_prefix = get_current_user()

        logger.info(f"当前用户: {current_user_email_prefix}, 查询目标: {target_email_prefix}")

        try:
            # 1. 获取当前用户的下属列表
            subordinates_result = self.get_subordinates(current_user_email_prefix)

            if not subordinates_result.get('success'):
                raise KsServiceError("无法获取下属列表")

            subordinates_data = subordinates_result.get('data', [])

            # 2. 检查目标用户是否在下属列表中
            target_user_ids = [sub.get('userId') for sub in subordinates_data]

            logger.info(f"下属列表: {target_user_ids}")

            # 判断目标用户是否在下属中
            is_subordinate = target_email_prefix in target_user_ids

            if not is_subordinate:
                # 无权限访问
                logger.warning(f"用户 {current_user_email_prefix} 无权访问 {target_email_prefix} 的考勤记录")
                return {
                    "success": False,
                    "message": f"无权限访问用户 {target_email_prefix} 的考勤记录"
                }

            # 3. 有权限，查询考勤记录
            logger.info(f"用户 {current_user_email_prefix} 有权访问 {target_email_prefix} 的考勤记录")
            attendance_result = self.get_attendance(target_email_prefix)

            return attendance_result

        except KsServiceError as e:
            logger.error(f"获取下属考勤记录失败: {e}")
            raise


def ks_user_info(**kwargs) -> KsUserInfoService:
    """
    用户信息服务工厂函数

    Args:
        **kwargs: 传递给用户信息服务的参数

    Returns:
        KsUserInfoService: 用户信息服务对象
    """
    from ..configs.default import HR_API_CONFIG

    # 合并默认配置和传入参数
    config = {**HR_API_CONFIG, **kwargs}

    instance_key = get_instance_key("user_info", config)

    cached = get_cached_instance(instance_key)
    if cached is not None:
        return cached

    instance = KsUserInfoService(
        base_url=config['base_url'],
        api_token=config['api_token']
    )
    set_cached_instance(instance_key, instance)
    logger.info(f"User info service initialized with URL: {config['base_url']}")
    return instance


def get_current_user() -> str:
    """
    获取当前用户
    
    Returns:
        str: 当前用户名
    """
    # 目前返回默认用户，未来可扩展为从请求头或Token中获取
    return "huxiaoxiao"
