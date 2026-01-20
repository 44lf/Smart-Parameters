import os
from typing import Optional

from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
class Settings:
    # Ollama配置
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen3:0.6b")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "bge-m3:latest")
    SILICON_FLOW_LLM_MODEL: str = os.getenv("SILICON_FLOW_LLM_MODEL")
    SILICON_FLOW_EMBEDDING_MODEL: str = os.getenv("SILICON_FLOW_EMBEDDING_MODEL")
    # 新增策略配置
    LLM_STRATEGY: str = os.getenv("LLM_STRATEGY")
    EMBEDDING_STRATEGY: str = os.getenv("EMBEDDING_STRATEGY")
    SILICON_FLOW_API_KEY: str = os.getenv("SILICON_FLOW_API_KEY")
    SILICON_FLOW_BASE_URL: str = os.getenv("SILICON_FLOW_BASE_URL")
    # API配置
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_KEY: Optional[str] = os.getenv("API_KEY")



    # MinIO配置
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "vanna-training-data")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "False").lower() == "true"

    KB_BUCKET_NAME: str = os.getenv("KB_BUCKET_NAME", "")

    REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_MAX_CONNECTIONS: int = int(os.getenv("REDIS_MAX_CONNECTIONS",10000))
    REDIS_SOCKET_TIMEOUT: int = int(os.getenv("REDIS_SOCKET_TIMEOUT",30))
    REDIS_SOCKET_CONNECT_TIMEOUT: int = int(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT",5))

    MYSQL_HOST: str = os.getenv("MYSQL_HOST")
    MYSQL_PORT: str = os.getenv("MYSQL_PORT")
    MYSQL_USER: str = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD")
    MYSQL_DB: str = os.getenv("MYSQL_DB")
    MYSQL_URI = os.getenv("MYSQL_URI")

    MILVUS_URI: str = os.getenv("MILVUS_URI")
    MILVUS_HOST: str = os.getenv("MILVUS_HOST")
    MILVUS_PORT: str = os.getenv("MILVUS_PORT")
    MILVUS_DEFAULT_COLLECTION: str = os.getenv("MILVUS_DEFAULT_COLLECTION")
    MILVUS_DEFAULT_ALIAS: str = os.getenv("MILVUS_DEFAULT_ALIAS")
    MILVUS_DEFAULT_DB: str = os.getenv("MILVUS_DEFAULT_DB")
    # 文件上传
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
    FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
    DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB


# 创建配置实例
settings = Settings()

