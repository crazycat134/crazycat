"""Cloudflare R2 上传：boto3 + S3 兼容接口。"""
from pathlib import Path

import boto3


def get_r2_client(cfg):
    """创建连接 Cloudflare R2 的 S3 客户端。"""
    return boto3.client(
        "s3",
        endpoint_url=cfg.r2_endpoint_url,
        aws_access_key_id=cfg.r2_access_key_id,
        aws_secret_access_key=cfg.r2_secret_access_key,
        region_name="auto",
    )


def upload_to_r2(cfg, local_path, key) -> str:
    """上传本地文件到 R2 bucket，返回公共 HTTPS URL。"""
    client = get_r2_client(cfg)
    client.upload_file(str(local_path), cfg.r2_bucket, key)
    return f"{cfg.r2_public_base_url}/{key}"


if __name__ == "__main__":
    # 手动测试：python -m app.r2_uploader <本地文件> <key>
    import sys

    from .config import Config

    if len(sys.argv) != 3:
        print("用法: python -m app.r2_uploader <本地文件> <key>")
        sys.exit(1)
    url = upload_to_r2(Config(), Path(sys.argv[1]), sys.argv[2])
    print(url)
