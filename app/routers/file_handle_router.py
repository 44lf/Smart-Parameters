from fastapi import status, UploadFile, File, Form
from .base_router import BaseRouter
from app.services.knowledge_file_service import KnowledgeFileService
from app.schemas.common import ApiResponse
from app.utils.file_handler import UploadFile as FileUploader
from app.config import settings
from app.exceptions.base_api_exception import ValidationException, UnsupportedFileTypeException, DatabaseException

import logging
logger = logging.getLogger(__name__)

knowledge_file_service = KnowledgeFileService()
KB_BUCKET_NAME = settings.KB_BUCKET_NAME
SUPPORTED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'sql', 'json', 'md'}

class FileHandleRouter(BaseRouter):
    def __init__(self):
        super().__init__()
        self.router = self._register_routes()

    def _register_routes(self):
        self.router.post(
            "/uploadFile",
            response_model=ApiResponse,
            status_code=status.HTTP_201_CREATED,
            summary="上传知识文件",
            tags=["知识管理"]
        )(self.upload_knowledge_file)
        return self.router

    async def upload_knowledge_file(
        self,
        file: UploadFile = File(..., description="待上传的知识文件"),
        collection_name: str = Form(..., description="知识文件所属的集合名称")
    ):
        if not file or not file.filename:
            raise ValidationException("No file provided")

        ext = file.filename.split(".")[-1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise UnsupportedFileTypeException(f"不支持的文件类型: {ext}")

        uploader = FileUploader()
        uploaded = await uploader.upload_file_form(file, KB_BUCKET_NAME)
        if not uploaded:
            raise DatabaseException("文件上传失败")

        param = {
            "collection_name": collection_name,
            "file_name": uploaded.get("stored_filename"),
            "file_type": ext,
            "minio_path": uploaded.get("file_url"),
            "chunk_strategy": "adaptive",
            "status": "uploaded",
            "created_by": 1,
        }
        record = knowledge_file_service.save_knowledge_file_response(param)
        return ApiResponse(status=201, message="上传成功", data=record.model_dump())
