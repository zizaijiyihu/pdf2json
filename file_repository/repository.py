"""
文件存储仓库服务
基于MinIO提供文件上传和查询接口，并在MySQL中管理文件元数据
"""

import logging
from typing import Optional, BinaryIO
from botocore.exceptions import ClientError

from ks_infrastructure.services.minio_service import ks_minio
from ks_infrastructure.services.exceptions import KsConnectionError
from .db import save_file_metadata, get_owner_files as db_get_owner_files, set_file_public_status as db_set_file_public_status

logger = logging.getLogger(__name__)

DEFAULT_BUCKET = "kms"


def _ensure_bucket_exists(client, bucket_name: str) -> None:
    """
    确保bucket存在，不存在则创建

    Args:
        client: MinIO客户端
        bucket_name: bucket名称
    """
    try:
        # 使用 list_buckets 检查 bucket 是否存在
        response = client.list_buckets()
        existing_buckets = [bucket['Name'] for bucket in response.get('Buckets', [])]

        if bucket_name not in existing_buckets:
            try:
                client.create_bucket(Bucket=bucket_name)
                logger.info(f"Created bucket: {bucket_name}")
            except ClientError as create_error:
                error_code = create_error.response.get('Error', {}).get('Code', '')
                if error_code == 'BucketAlreadyOwnedByYou':
                    # Bucket 已存在，忽略错误
                    logger.info(f"Bucket {bucket_name} already exists")
                else:
                    raise KsConnectionError(f"创建bucket失败: {create_error}")
            except Exception as create_error:
                raise KsConnectionError(f"创建bucket失败: {create_error}")
    except KsConnectionError:
        raise
    except ClientError as e:
        raise KsConnectionError(f"检查bucket失败: {e}")
    except Exception as e:
        raise KsConnectionError(f"检查bucket失败: {e}")


def upload_file(
    username: str,
    filename: str,
    file_data: BinaryIO,
    bucket: str = DEFAULT_BUCKET,
    content_type: Optional[str] = None,
    is_public: int = 0
) -> str:
    """
    上传文件到MinIO，并保存元数据到数据库

    Args:
        username: 用户名
        filename: 原文件名
        file_data: 文件数据（二进制流）
        bucket: bucket名称，默认为'kms'
        content_type: 文件MIME类型
        is_public: 是否公开 (0=非公开, 1=公开)，默认0

    Returns:
        str: 文件在MinIO中的完整路径 (username/filename)

    Raises:
        KsConnectionError: 上传失败时抛出
    """
    client = ks_minio()
    _ensure_bucket_exists(client, bucket)

    object_key = f"{username}/{filename}"

    try:
        # 获取文件大小
        file_data.seek(0, 2)  # 移动到文件末尾
        file_size = file_data.tell()
        file_data.seek(0)  # 重置到开头

        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type

        # 上传到MinIO
        client.upload_fileobj(
            file_data,
            bucket,
            object_key,
            ExtraArgs=extra_args if extra_args else None
        )
        logger.info(f"Uploaded file: {bucket}/{object_key}")

        # 保存元数据到数据库
        save_file_metadata(
            file_path=object_key,
            owner=username,
            filename=filename,
            bucket=bucket,
            is_public=is_public,
            content_type=content_type,
            file_size=file_size
        )

        return object_key
    except Exception as e:
        raise KsConnectionError(f"文件上传失败: {e}")


def get_file(
    username: str,
    filename: str,
    bucket: str = DEFAULT_BUCKET
) -> Optional[bytes]:
    """
    从MinIO获取文件

    Args:
        username: 用户名
        filename: 文件名
        bucket: bucket名称，默认为'kms'

    Returns:
        bytes: 文件内容，文件不存在返回None

    Raises:
        KsConnectionError: 查询失败时抛出
    """
    client = ks_minio()
    object_key = f"{username}/{filename}"

    try:
        response = client.get_object(Bucket=bucket, Key=object_key)
        return response['Body'].read()
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code in ('404', 'NoSuchKey'):
            return None
        raise KsConnectionError(f"文件查询失败: {e}")
    except Exception as e:
        raise KsConnectionError(f"文件查询失败: {e}")


def list_user_files(
    username: str,
    bucket: str = DEFAULT_BUCKET
) -> list[dict]:
    """
    列出用户的所有文件（从MinIO）

    Args:
        username: 用户名
        bucket: bucket名称，默认为'kms'

    Returns:
        list[dict]: 文件列表，每个文件包含key, size, last_modified

    Raises:
        KsConnectionError: 查询失败时抛出
    """
    client = ks_minio()
    prefix = f"{username}/"

    try:
        response = client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        files = []
        for obj in response.get('Contents', []):
            files.append({
                'key': obj['Key'],
                'filename': obj['Key'].replace(prefix, '', 1),
                'size': obj['Size'],
                'last_modified': obj['LastModified']
            })
        return files
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code in ('404', 'NoSuchBucket'):
            return []
        raise KsConnectionError(f"文件列表查询失败: {e}")
    except Exception as e:
        raise KsConnectionError(f"文件列表查询失败: {e}")


def get_owner_file_list(
    owner: str,
    include_public: bool = False
) -> list[dict]:
    """
    获取所有者的文件列表（从数据库）

    Args:
        owner: 文件所有者
        include_public: 是否包含公开文件
                       - False: 只返回所有者的文件
                       - True: 返回所有者的文件 + 所有公开文件(is_public=1)

    Returns:
        list[dict]: 文件列表，包含完整的元数据信息

    Raises:
        KsConnectionError: 查询失败时抛出
    """
    return db_get_owner_files(owner, include_public)


def set_file_public(
    owner: str,
    filename: str,
    is_public: int
) -> bool:
    """
    设置文件的公开状态

    Args:
        owner: 文件所有者
        filename: 文件名
        is_public: 公开状态 (0=非公开, 1=公开)

    Returns:
        bool: 是否成功更新

    Raises:
        KsConnectionError: 更新失败时抛出
    """
    if is_public not in (0, 1):
        raise ValueError("is_public 必须是 0 或 1")

    return db_set_file_public_status(owner, filename, is_public)
