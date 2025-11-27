"""
清空file_repository相关的数据库数据

功能：
- 清空MySQL中的file_metadata表的所有数据
- 清空MinIO中的kms bucket的所有文件
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ks_infrastructure import db_session
from ks_infrastructure.services.minio_service import ks_minio
from ks_infrastructure.services.exceptions import KsConnectionError
from botocore.exceptions import ClientError


DEFAULT_BUCKET = "kms"
TABLE_NAME = "file_metadata"


def clear_mysql_table():
    """
    清空MySQL中的file_metadata表的所有数据
    """
    print(f"\n{'='*60}")
    print(f"清空MySQL表: {TABLE_NAME}")
    print(f"{'='*60}\n")

    try:
        # 查询记录数
        with db_session() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
            count = cursor.fetchone()[0]

        print(f"找到 {count} 条记录")

        if count == 0:
            print("✓ 表已经是空的")
            return

        # 确认删除
        confirm = input(f"\n⚠️  确定要删除 {count} 条记录吗？(yes/no): ")
        if confirm.lower() != 'yes':
            print("✗ 操作已取消")
            return

        # 清空表
        with db_session() as cursor:
            cursor.execute(f"TRUNCATE TABLE {TABLE_NAME}")

        print(f"✓ 成功清空表 '{TABLE_NAME}'")

        # 验证清空结果
        with db_session() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
            count_after = cursor.fetchone()[0]
        
        print(f"✓ 当前记录数: {count_after}")

    except Exception as e:
        print(f"✗ 清空MySQL表失败: {e}")
        raise


def clear_minio_bucket(bucket: str = DEFAULT_BUCKET):
    """
    清空MinIO bucket中的所有文件

    Args:
        bucket: bucket名称，默认为'kms'
    """
    print(f"\n{'='*60}")
    print(f"清空MinIO Bucket: {bucket}")
    print(f"{'='*60}\n")

    try:
        client = ks_minio()

        # 检查bucket是否存在
        try:
            response = client.list_buckets()
            existing_buckets = [b['Name'] for b in response.get('Buckets', [])]

            if bucket not in existing_buckets:
                print(f"⚠ Bucket '{bucket}' 不存在，无需清空")
                return
        except Exception as e:
            print(f"✗ 检查bucket失败: {e}")
            raise

        # 列出所有对象
        try:
            response = client.list_objects_v2(Bucket=bucket)
            objects = response.get('Contents', [])
            object_count = len(objects)

            print(f"找到 {object_count} 个文件")

            if object_count == 0:
                print("✓ Bucket已经是空的")
                return

            # 确认删除
            confirm = input(f"\n⚠️  确定要删除 {object_count} 个文件吗？(yes/no): ")
            if confirm.lower() != 'yes':
                print("✗ 操作已取消")
                return

            # 批量删除对象
            deleted_count = 0
            for obj in objects:
                try:
                    client.delete_object(Bucket=bucket, Key=obj['Key'])
                    deleted_count += 1
                    print(f"  删除: {obj['Key']}")
                except Exception as e:
                    print(f"  ✗ 删除失败 {obj['Key']}: {e}")

            print(f"✓ 成功删除 {deleted_count}/{object_count} 个文件")

            # 验证清空结果
            response_after = client.list_objects_v2(Bucket=bucket)
            remaining = len(response_after.get('Contents', []))
            print(f"✓ 剩余文件数: {remaining}")

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code in ('404', 'NoSuchBucket'):
                print(f"⚠ Bucket '{bucket}' 不存在")
            else:
                raise KsConnectionError(f"列出对象失败: {e}")

    except Exception as e:
        print(f"✗ 清空MinIO bucket失败: {e}")
        raise


def main():
    """主函数"""
    print("\n" + "="*60)
    print("File Repository 数据库清空工具")
    print("="*60)
    print("\n此脚本将清空以下数据：")
    print(f"  - MySQL: {TABLE_NAME} 表")
    print(f"  - MinIO: {DEFAULT_BUCKET} bucket")
    print("\n" + "="*60 + "\n")

    try:
        # 清空MySQL表
        clear_mysql_table()

        # 清空MinIO bucket
        clear_minio_bucket()

        print("\n" + "="*60)
        print("✓ 数据清空完成")
        print("="*60 + "\n")

    except Exception as e:
        print("\n" + "="*60)
        print(f"✗ 数据清空失败: {e}")
        print("="*60 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
