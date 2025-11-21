"""
默认配置文件

包含各个基础设施服务的默认配置信息
"""

# MySQL数据库配置
MYSQL_CONFIG = {
    "host": "120.92.109.164",
    "port": 8306,
    "user": "admin",
    "password": "rsdyxjh",
    "database": "yanzhi"
}

# MinIO对象存储配置
MINIO_CONFIG = {
    "endpoint": "http://120.92.109.164:9000",  # S3 API服务端口
    "access_key": "admin",
    "secret_key": "rsdyxjh110!",
    "region": "us-east-1"
}

# Qdrant向量数据库配置
QDRANT_CONFIG = {
    "url": "http://120.92.109.164:6333",
    "api_key": "rsdyxjh"
}

# OpenAI大语言模型配置
OPENAI_CONFIG = {
    "api_key": "85c923cc-9dcf-467a-89d5-285d3798014d",
    "base_url": "https://kspmas.ksyun.com/v1/",
    "model": "DeepSeek-V3.1-Ksyun"
}

# Embedding服务配置
EMBEDDING_CONFIG = {
    "url": "http://10.69.86.20/v1/embeddings",
    "api_key": "7c64b222-4988-4e6a-bb26-48594ceda8a9"
}

# Vision视觉识别服务配置
VISION_CONFIG = {
    "api_key": "sk-412a5b410f664d60a29327fdfa28ac6e",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "model": "qwen-vl-max"
}