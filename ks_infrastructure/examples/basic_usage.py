"""
KS Infrastructure 模块使用示例
"""

# 方式1: 使用默认配置
from ks_infrastructure import (
    ks_mysql,
    ks_minio,
    ks_qdrant,
    ks_openai,
    ks_embedding,
    ks_vision
)

def example_with_default_config():
    """使用默认配置获取服务实例"""
    print("=== 使用默认配置获取服务实例 ===")
    
    # 获取MySQL连接
    mysql_conn = ks_mysql()
    print(f"MySQL连接状态: {mysql_conn.is_connected()}")
    
    # 获取MinIO客户端
    minio_client = ks_minio()
    print("MinIO客户端创建成功")
    
    # 获取Qdrant客户端
    qdrant_client = ks_qdrant()
    print("Qdrant客户端创建成功")
    
    # 获取OpenAI客户端
    openai_client = ks_openai()
    print("OpenAI客户端创建成功")
    
    # 获取Embedding服务
    embedding_service = ks_embedding()
    print(f"Embedding服务URL: {embedding_service.url}")
    
    # 获取Vision服务
    vision_service = ks_vision()
    print("Vision服务创建成功")

# 方式2: 使用自定义配置
def example_with_custom_config():
    """使用自定义配置初始化服务工厂"""
    print("\n=== 使用自定义配置初始化服务工厂 ===")
    
    # 自定义配置
    custom_config = {
        'MYSQL_CONFIG': {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': 'password',
            'database': 'test'
        },
        'MINIO_CONFIG': {
            'endpoint': 'http://localhost:9000',
            'access_key': 'minioadmin',
            'secret_key': 'minioadmin',
            'region': 'us-east-1'
        }
    }
    
    # 初始化基础设施服务工厂
    from ks_infrastructure import init_infrastructure
    init_infrastructure(custom_config)
    
    # 获取服务实例（将使用自定义配置）
    mysql_conn = ks_mysql()
    print(f"使用自定义配置的MySQL连接状态: {mysql_conn.is_connected()}")

# 方式3: 使用参数覆盖
def example_with_parameter_override():
    """使用参数覆盖获取服务实例"""
    print("\n=== 使用参数覆盖获取服务实例 ===")
    
    # 重新初始化为默认配置
    from ks_infrastructure import init_infrastructure
    init_infrastructure()  # 重置为默认配置
    
    # 使用参数覆盖获取服务实例
    mysql_conn = ks_mysql(charset='utf8mb4', autocommit=True)
    print(f"使用参数覆盖的MySQL连接状态: {mysql_conn.is_connected()}")
    
    minio_client = ks_minio(region_name='us-west-1')
    print("使用参数覆盖的MinIO客户端创建成功")

if __name__ == "__main__":
    example_with_default_config()
    example_with_custom_config()
    example_with_parameter_override()