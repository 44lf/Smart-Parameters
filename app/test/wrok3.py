# minio_client.py
# pip install minio
from __future__ import annotations

import os
import mimetypes
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from minio import Minio
from minio.error import S3Error


@dataclass(frozen=True)
class MinioConfig:
    endpoint: str                 # e.g. "127.0.0.1:9100"
    access_key: str
    secret_key: str
    secure: bool = False          # True => https
    public_endpoint: Optional[str] = None
    # public_endpoint 用于拼“可直接访问的公开地址”，例如：
    # - 反代后域名: "minio.example.com"
    # - 或同 endpoint: "127.0.0.1:9000"


class MinioClient:
    def __init__(self, cfg: MinioConfig) -> None:
        self.cfg = cfg
        self.client = Minio(
            endpoint=cfg.endpoint,
            access_key=cfg.access_key,
            secret_key=cfg.secret_key,
            secure=cfg.secure,
        )

    def ensure_bucket(self, bucket: str) -> None:
        """不存在则创建桶"""
        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)

    def upload_file(self, bucket: str, object_name: str, file_path: str, content_type: Optional[str] = None) -> str:
        """上传本地文件（fput_object）。返回 object_name。"""
        if content_type is None:
            content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        self.client.fput_object(bucket, object_name, file_path, content_type=content_type)
        return object_name

    def presigned_get_url(self, bucket: str, object_name: str, expiry_seconds: int = 3600) -> str:
        """生成临时下载链接（推荐：不要求桶公开）。"""
        return self.client.presigned_get_object(
            bucket,
            object_name,
            expires=timedelta(seconds=expiry_seconds),
        )

    def public_object_url(self, bucket: str, object_name: str) -> str:
        """
        拼一个“直链”（仅当桶/对象对外可读或你有反代鉴权时才可用）。
        更稳的是用 presigned_get_url。
        """
        host = (self.cfg.public_endpoint or self.cfg.endpoint).rstrip("/")
        scheme = "https" if self.cfg.secure else "http"
        # MinIO 默认 path-style: http(s)://host/bucket/object
        return f"{scheme}://{host}/{bucket}/{object_name}"
