"""
Configuration for App API
"""

# OpenAI/LLM Configuration
OPENAI_CONFIG = {
    "api_key": "85c923cc-9dcf-467a-89d5-285d3798014d",
    "base_url": "https://kspmas.ksyun.com/v1/",
    "model": "DeepSeek-V3.1-Ksyun"
}

# Embedding Service Configuration
EMBEDDING_CONFIG = {
    "url": "http://10.69.86.20/v1/embeddings",
    "api_key": "7c64b222-4988-4e6a-bb26-48594ceda8a9"
}

# Qdrant Vector Database Configuration
QDRANT_CONFIG = {
    "url": "http://120.92.109.164:6333/",
    "api_key": "rsdyxjh"
}

# Collection Configuration
COLLECTION_NAME = "pdf_knowledge_base"
VECTOR_SIZE = 4096

# Default User
DEFAULT_USER = "hu"

# Upload Configuration
UPLOAD_FOLDER = "/tmp/km_agent_uploads"
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

# Flask Configuration
DEBUG = True
HOST = "0.0.0.0"
PORT = 5000
