"""
Embedding文本嵌入服务
"""

import logging
import requests
from typing import List, Dict, Any

from .base import get_instance_key, get_cached_instance, set_cached_instance
from .exceptions import KsServiceError

logger = logging.getLogger(__name__)


class KsEmbeddingService:
    """
    Embedding服务封装类

    提供简单的文本嵌入功能，隐藏底层HTTP请求细节
    """

    def __init__(self, url: str, api_key: str):
        """
        初始化Embedding服务

        Args:
            url: Embedding服务URL
            api_key: API密钥
        """
        self.url = url
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def create_embedding(self, text: str, model: str = "text-embedding",
                        encoding_format: str = "float") -> Dict[str, Any]:
        """
        为文本创建嵌入向量

        Args:
            text: 需要转换为向量的文本
            model: 模型名称，默认为"text-embedding"
            encoding_format: 编码格式，默认为"float"

        Returns:
            dict: 包含嵌入向量的响应数据

        Raises:
            KsServiceError: 当请求失败时抛出
        """
        data = {
            "model": model,
            "input": text,
            "encoding_format": encoding_format
        }

        try:
            response = requests.post(self.url, headers=self.headers, json=data)

            if response.status_code == 200:
                return response.json()
            else:
                raise KsServiceError(
                    f"Embedding服务请求失败: {response.status_code} - {response.text}"
                )
        except requests.RequestException as e:
            raise KsServiceError(f"Embedding服务请求异常: {e}")

    def get_embedding_vector(self, text: str, model: str = "text-embedding",
                            encoding_format: str = "float") -> List[float]:
        """
        获取文本的嵌入向量（仅返回向量数组）

        Args:
            text: 需要转换为向量的文本
            model: 模型名称，默认为"text-embedding"
            encoding_format: 编码格式，默认为"float"

        Returns:
            list: 文本的嵌入向量

        Raises:
            KsServiceError: 当请求失败时抛出
        """
        result = self.create_embedding(text, model, encoding_format)
        return result['data'][0]['embedding']


def ks_embedding(**kwargs) -> KsEmbeddingService:
    """
    Embedding服务工厂函数

    Args:
        **kwargs: 传递给Embedding服务的参数

    Returns:
        KsEmbeddingService: Embedding服务对象
    """
    from ..configs.default import EMBEDDING_CONFIG

    # 合并默认配置和传入参数
    config = {**EMBEDDING_CONFIG, **kwargs}

    instance_key = get_instance_key("embedding", config)

    cached = get_cached_instance(instance_key)
    if cached is not None:
        return cached

    instance = KsEmbeddingService(
        url=config['url'],
        api_key=config['api_key']
    )
    set_cached_instance(instance_key, instance)
    logger.info(f"Embedding service initialized with URL: {config['url']}")
    return instance
