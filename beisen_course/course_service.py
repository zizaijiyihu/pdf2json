"""
北森课程服务
提供课程列表获取功能
"""

import requests
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# 北森系统配置
BEISEN_BASE_URL = "http://10.69.80.179:8888"
BEISEN_APP_KEY = "DDE762E6C9F141F0B9F2432F063171B6"
BEISEN_APP_SECRET = "B6F8BA8D587D4893AFF9EDE75B3A3EC50454F849BE8D4265A6575C10CFDB4FF3"


def _get_access_token() -> Optional[str]:
    """
    获取北森系统access_token

    Returns:
        access_token 或 None（如果获取失败）
    """
    url = f"{BEISEN_BASE_URL}/token"

    payload = {
        "grant_type": "client_credentials",
        "app_key": BEISEN_APP_KEY,
        "app_secret": BEISEN_APP_SECRET
    }

    headers = {
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)

        if response.status_code == 200:
            result = response.json()
            access_token = result.get('access_token')
            if access_token:
                logger.info("成功获取北森系统 access_token")
                return access_token
            else:
                logger.error("北森系统返回的数据中没有 access_token")
                return None
        else:
            logger.error(f"获取 access_token 失败，状态码: {response.status_code}")
            logger.error(f"错误信息: {response.text}")
            return None
    except Exception as e:
        logger.error(f"获取 access_token 时发生异常: {str(e)}")
        return None


def get_course_list(page_index: int = 1, page_size: int = 10) -> Dict:
    """
    获取北森系统课程列表

    Args:
        page_index: 页码，必须从1开始，默认 1
        page_size: 页容量，默认 10，最大 300

    Returns:
        包含课程列表的字典，格式：
        {
            "success": True/False,
            "data": [
                {
                    "title": "课程标题",
                    "courseId": "课程ID",
                    "description": "课程描述",
                    ...
                }
            ],
            "total": 总数,
            "error": "错误信息"（仅在失败时）
        }
    """
    try:
        # 先获取 access_token
        access_token = _get_access_token()

        if not access_token:
            logger.error("无法获取 access_token，无法获取课程列表")
            return {
                "success": False,
                "error": "无法获取访问令牌"
            }

        # 获取课程列表
        url = f"{BEISEN_BASE_URL}/Learning/api/v1/course/GetCourseList"

        payload = {
            "pageIndex": page_index,
            "pageSize": page_size
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)

        if response.status_code == 200:
            result = response.json()

            # 检查返回数据结构
            if not result or 'data' not in result:
                logger.error("北森系统返回的数据格式不正确")
                return {
                    "success": False,
                    "error": "返回数据格式不正确"
                }

            items = result.get('data', {}).get('items', [])
            total_count = result.get('data', {}).get('totalCount', 0)

            logger.info(f"成功获取课程列表：第 {page_index} 页，共 {len(items)} 条，总数 {total_count}")

            return {
                "success": True,
                "data": items,
                "total": total_count,
                "page_index": page_index,
                "page_size": page_size
            }
        else:
            logger.error(f"获取课程列表失败，状态码: {response.status_code}")
            logger.error(f"错误信息: {response.text}")
            return {
                "success": False,
                "error": f"API 请求失败，状态码: {response.status_code}"
            }
    except Exception as e:
        logger.error(f"获取课程列表时发生异常: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
