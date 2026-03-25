"""Aliyun OSS Service for file upload"""
import os
import tempfile
from typing import Optional
from datetime import datetime

import oss2
from app.config import get_settings
import structlog

logger = structlog.get_logger()


class OSSService:
    """阿里云 OSS 服务"""

    def __init__(self):
        settings = get_settings()
        self.access_key = settings.ALIYUN_ACCESS_KEY
        self.secret_key = settings.ALIYUN_SECRET_KEY
        self.bucket_name = settings.ALIYUN_OSS_BUCKET
        self.endpoint = getattr(settings, "ALIYUN_OSS_ENDPOINT", "oss-cn-hangzhou.aliyuncs.com")

        # 初始化 OSS 认证和 Bucket
        if self.access_key and self.secret_key and self.bucket_name:
            self.auth = oss2.Auth(self.access_key, self.secret_key)
            self.bucket = oss2.Bucket(self.auth, self.endpoint, self.bucket_name)
            self.enabled = True
        else:
            self.enabled = False
            logger.warning("OSS not configured, uploads will be saved locally")

    async def upload_file(
        self,
        file_data: bytes,
        filename: str,
        folder: str = "interviews"
    ) -> dict:
        """
        上传文件到 OSS 或本地存储

        Args:
            file_data: 文件二进制数据
            filename: 原始文件名
            folder: OSS 中的文件夹

        Returns:
            dict: 包含 file_url, oss_url, local_path 等信息
        """
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{folder}/{timestamp}_{filename}"

        if self.enabled:
            # 上传到 OSS
            try:
                result = self.bucket.put_object(unique_filename, file_data)
                if result.status == 200:
                    # 构建 URL
                    file_url = f"https://{self.bucket_name}.{self.endpoint}/{unique_filename}"
                    logger.info(
                        "File uploaded to OSS",
                        filename=unique_filename,
                        size=len(file_data),
                        url=file_url
                    )
                    return {
                        "file_url": file_url,
                        "oss_url": file_url,
                        "local_path": None,
                        "filename": unique_filename,
                        "size": len(file_data)
                    }
                else:
                    raise Exception(f"OSS upload failed with status {result.status}")
            except Exception as e:
                logger.error("OSS upload failed, falling back to local", error=str(e))
                return await self._save_local(file_data, unique_filename)
        else:
            # 本地存储
            return await self._save_local(file_data, unique_filename)

    async def _save_local(self, file_data: bytes, filename: str) -> dict:
        """保存文件到本地"""
        # 使用临时目录或项目目录
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        upload_dir = os.path.join(base_dir, "uploads", "interviews")
        os.makedirs(upload_dir, exist_ok=True)

        local_path = os.path.join(upload_dir, os.path.basename(filename))

        with open(local_path, "wb") as f:
            f.write(file_data)

        logger.info(
            "File saved locally",
            filename=filename,
            local_path=local_path,
            size=len(file_data)
        )

        return {
            "file_url": f"file://{local_path}",
            "oss_url": None,
            "local_path": local_path,
            "filename": filename,
            "size": len(file_data)
        }

    def delete_file(self, oss_url: str) -> bool:
        """从 OSS 删除文件"""
        if not self.enabled:
            return False

        try:
            # 从 URL 中提取 key
            key = oss_url.split(f"{self.bucket_name}.{self.endpoint}/")[-1]
            self.bucket.delete_object(key)
            logger.info("File deleted from OSS", key=key)
            return True
        except Exception as e:
            logger.error("Failed to delete file from OSS", error=str(e), url=oss_url)
            return False


# Singleton instance
_oss_service: Optional[OSSService] = None


def get_oss_service() -> OSSService:
    """获取 OSS 服务单例"""
    global _oss_service
    if _oss_service is None:
        _oss_service = OSSService()
    return _oss_service
