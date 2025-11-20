"""
Vision视觉识别服务
"""

import os
import logging
from typing import Optional
from openai import OpenAI

from .base import get_instance_key, get_cached_instance, set_cached_instance
from .exceptions import KsServiceError, KsConfigError

logger = logging.getLogger(__name__)


class KsVisionService:
    """
    视觉识别服务封装类

    提供图像分析功能
    """

    def __init__(self, api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 model: Optional[str] = None):
        """
        Initialize the Vision service.

        Args:
            api_key: API key for Qwen Vision model (defaults to DASHSCOPE_API_KEY env var)
            base_url: Base URL for API (defaults to Aliyun DashScope)
            model: Model name to use (defaults to qwen-vl-max)
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.base_url = base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.model = model or "qwen-vl-max"

    def analyze_image(self, image_base64: str, image_format: str = "png",
                     prompt: str = "请描述这张图片的内容") -> str:
        """
        Use Qwen Vision model to analyze image content.

        Args:
            image_base64: Base64 encoded image data
            image_format: Image format (png, jpg, etc.)
            prompt: Analysis prompt (defaults to "请描述这张图片的内容")

        Returns:
            Text description of the image content

        Raises:
            KsConfigError: 当API密钥未配置时抛出
            KsServiceError: 当服务调用失败时抛出
        """
        if not self.api_key:
            raise KsConfigError("Vision服务API密钥未配置")

        try:
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )

            # Construct data URL for the image
            data_url = f"data:image/{image_format};base64,{image_base64}"

            completion = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": data_url}
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            return completion.choices[0].message.content
        except Exception as e:
            raise KsServiceError(f"Vision图像分析失败: {e}")


def ks_vision(**kwargs) -> KsVisionService:
    """
    Vision视觉识别服务工厂函数

    Args:
        **kwargs: 传递给Vision服务的参数

    Returns:
        KsVisionService: Vision服务对象
    """
    from ..configs.default import VISION_CONFIG

    # 合并默认配置和传入参数
    config = {**VISION_CONFIG, **kwargs}

    instance_key = get_instance_key("vision", config)

    cached = get_cached_instance(instance_key)
    if cached is not None:
        return cached

    api_key = config.get('api_key') or os.getenv("DASHSCOPE_API_KEY")
    base_url = config.get('base_url') or "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model = config.get('model') or "qwen-vl-max"

    instance = KsVisionService(
        api_key=api_key,
        base_url=base_url,
        model=model
    )
    set_cached_instance(instance_key, instance)
    logger.info(f"Vision service initialized with model: {model}")
    return instance
