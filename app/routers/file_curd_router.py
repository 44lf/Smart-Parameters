from fastapi import status, UploadFile, File, Form, HTTPException, Path, Body
from typing import Optional

from .base_router import BaseRouter
from ..schemas.knowledge_file import KnowledgeFileUpdate
from ..services.knowledge_file_service import KnowledgeFileService
from ..schemas.common import ApiResponse
from ..utils.file_handler import UploadFile as FileUploader
from ..config import settings
from ..exceptions.base_api_exception import (
    DatabaseException,
    ValidationException,
    UnsupportedFileTypeException,
    NotFoundException
)
import logging

logger = logging.getLogger(__name__)
knowledge_file_service = KnowledgeFileService()

KB_BUCKET_NAME = settings.KB_BUCKET_NAME
SUPPORTED_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'sql', 'json', 'md'
}


class FileHandleRouter(BaseRouter):
    def __init__(self):
        logger.info("Initializing FileHandleRouter (CRUD)")
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

        self.router.get(
            "/files/{id}",
            response_model=ApiResponse,
            status_code=status.HTTP_200_OK,
            summary="查找知识文件",
            tags=["知识管理"]
        )(self.find_knowledge_file)

        self.router.delete(
            "/files/{id}",
            response_model=ApiResponse,
            status_code=status.HTTP_200_OK,
            summary="删除知识文件",
            tags=["知识管理"]
        )(self.delete_knowledge_file)

        self.router.patch(
            "/files/{id}",
            response_model=ApiResponse,
            status_code=status.HTTP_200_OK,
            summary="部分更新知识文件",
            tags=["知识管理"]
        )(self.update_knowledge_file)

        self.router.put(
            "/files/{id}/content",
            response_model=ApiResponse,
            status_code=status.HTTP_200_OK,
            summary="替换知识文件",
            tags=["知识管理"]
        )(self.replace_knowledge_file)

        return self.router

    async def upload_knowledge_file(
        self,
        file: UploadFile = File(...),
        collection_name: str = Form(...)
    ):
        try:
            if not file or not file.filename:
                raise ValidationException("未提供文件")

            ext = file.filename.split('.')[-1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                raise UnsupportedFileTypeException(f"不支持的文件类型: {ext}")

            uploader = FileUploader()
            uploaded = await uploader.upload_file_form(file, KB_BUCKET_NAME)
            if not uploaded:
                raise DatabaseException("文件上传失败")

            param = {
                "collection_name": collection_name,
                "file_name": uploaded.get('stored_filename'),
                "file_type": ext,
                "minio_path": uploaded.get('file_url'),
                "chunk_strategy": 'adaptive',
                "status": 'uploaded',
                "created_by": 1
            }

            record = knowledge_file_service.save_knowledge_file_response(param)
            return ApiResponse(status=200, message="上传成功", data=record.model_dump())

        except (ValidationException, UnsupportedFileTypeException, DatabaseException) as e:
            raise HTTPException(status_code=e.status_code, detail=str(e))
        except Exception as e:
            logger.error(f"上传失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")

    async def find_knowledge_file(self, id: str = Path(...)):
        try:
            record = knowledge_file_service.find_file_response(id)
            return ApiResponse(status=200, message="查找成功", data=record.model_dump())
        except NotFoundException as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"查找失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")

    async def delete_knowledge_file(self, id: str = Path(...)):
        try:
            result = knowledge_file_service.delete_knowledge_file(id)
            return ApiResponse(status=200, message="删除成功", data=result)
        except NotFoundException as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"删除失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")

    async def update_knowledge_file(
        self,
        id: str = Path(...),
        payload: KnowledgeFileUpdate = Body(...)
    ):
        try:
            updated = knowledge_file_service.update_partial(id, payload)
            return ApiResponse(status=200, message="修改成功", data=updated.model_dump())
        except NotFoundException as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ValidationException as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            logger.error(f"修改失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")

    async def replace_knowledge_file(
        self,
        id: str = Path(...),
        file: UploadFile = File(...)
    ):
        try:
            if not file or not file.filename:
                raise ValidationException("未提供文件")

            ext = file.filename.split('.')[-1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                raise UnsupportedFileTypeException(f"不支持的文件类型: {ext}")

            uploader = FileUploader()
            uploaded = await uploader.upload_file_form(file, KB_BUCKET_NAME)
            if not uploaded:
                raise DatabaseException("文件上传失败")

            updated = knowledge_file_service.update_file_fields(
                id=id,
                file_name=uploaded.get("stored_filename"),
                file_type=ext,
                minio_path=uploaded.get("file_url"),
                status="uploaded"
            )

            return ApiResponse(status=200, message="替换成功", data=updated.model_dump())

        except (ValidationException, UnsupportedFileTypeException, DatabaseException, NotFoundException) as e:
            raise HTTPException(status_code=e.status_code, detail=str(e))
        except Exception as e:
            logger.error(f"替换失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")