# test_minio.py
import os
import uuid

from app.test.wrok3 import MinioClient, MinioConfig


def main() -> None:
    # 1) 读取环境变量（按需改成你自己的配置方式）
    cfg = MinioConfig(
        endpoint=os.getenv("MINIO_ENDPOINT", "127.0.0.1:9100"),
        access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
        secure=os.getenv("MINIO_SECURE", "0") == "1",
        public_endpoint=os.getenv("MINIO_PUBLIC_ENDPOINT"),  # 可选：如 "minio.example.com"
    )
    bucket = os.getenv("MINIO_BUCKET", "demo-bucket")
    local_file = os.getenv("MINIO_TEST_FILE", "README.md")  # 改成你本地存在的文件

    mc = MinioClient(cfg)

    # 2) 创建桶（不存在则创建）
    mc.ensure_bucket(bucket)
    print("bucket ok:", bucket)

    # 3) 上传文件
    object_name = f"uploads/{uuid.uuid4().hex}-{os.path.basename(local_file)}"
    mc.upload_file(bucket, object_name, local_file)
    print("uploaded:", object_name)

    # 4) 获取“连接地址”
    # 4.1 推荐：预签名下载链接（无需桶公开）
    url = mc.presigned_get_url(bucket, object_name, expiry_seconds=3600)
    print("presigned url (1h):", url)

    # 4.2 可选：拼直链（仅当桶/对象对外可读或有反代鉴权时才有效）
    public_url = mc.public_object_url(bucket, object_name)
    print("public url (requires public-read):", public_url)


if __name__ == "__main__":
    main()
