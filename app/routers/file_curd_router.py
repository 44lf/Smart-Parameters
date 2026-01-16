from fastapi import status, UploadFile, File, Form, HTTPException, PATH, Body

from .base_router import BaseRouter
from ..schemas.knowledge_file import KnowledgeFileUpdate
from ..services.knowledge_file_service import KnowledgeFileService
from ..schemas.common import ApiResponse
from ..utils.file_handler import UploadFile as FileUploader
from ..config import settings
from ..exceptions.base_api_exception import (
    DatabaseException,
    ValidationException,
    UnsupportedFileTypeException, NotFoundException
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
        logger.info("Initializing FileHandleRouter")
        super().__init__()
        self.router = self._register_routes()

    def _register_routes(self):
        self.router.post(
        "/uploadFile",
        response_model=ApiResponse,
        status_code=status.HTTP_201_CREATED,
        summary="上传知识文件",
        description="上传文档文件到系统",
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
            description="可只更新表字段；也可携带文件进行替换上传",
            tags=["知识管理"]
        )(self.update_knowledge_file)

        return self.router

    async def upload_knowledge_file(
        self,
        file: UploadFile = File(..., description="待上传的知识文件"),
        collection_name: str = Form(..., description="知识文件所属的集合名称")
    ):
        try:
            if not file:
                raise ValidationException("No file provided")

            file_extension = file.filename.split('.')[-1].lower() if file.filename else ''
            if file_extension not in SUPPORTED_EXTENSIONS:
                raise UnsupportedFileTypeException(f"不支持的文件类型: {file_extension}")

            uploaded_file = FileUploader()
            uploaded_object = await uploaded_file.upload_file_form(file, KB_BUCKET_NAME)

            if not uploaded_object:
                raise DatabaseException("文件上传失败")

            knowledge_file_param = {
                "collection_name": collection_name,
                "file_name": uploaded_object.get('stored_filename'),
                "file_type": file_extension,
                "minio_path": uploaded_object.get('file_url'),
                "chunk_strategy": 'adaptive',
                "status": 'uploaded',
                "created_by": 1
            }

            record = knowledge_file_service.save_knowledge_file_response(knowledge_file_param)
            # 改成这样:
            return ApiResponse(status=200, message="上传成功", data=record.model_dump())

        except (ValidationException, UnsupportedFileTypeException, DatabaseException) as e:
            raise HTTPException(status_code=e.status_code, detail=str(e))
        except Exception as e:
            logger.error(f"上传失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="服务器错误")



    async def find_knowledge_file(
        self,
        id: str = Path(..., description="知识文件ID"),
    ):
        try:
            record = knowledge_file_service.find_file_response(id)
            # 改成这样:
            return ApiResponse(status=200, message="查找成功", data=record.model_dump())
        except ValidationException as e:
            raise HTTPException(status_code=422, detail=str(e))
        except NotFoundException as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"查找失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="服务器错误")



    async def delete_knowledge_file(
        self,
        id: str = Path(..., description="要删除文件的ID"),
    ):


        try:
            result = knowledge_file_service.delete_knowledge_file(id)
            return ApiResponse(status=200, message="删除成功", data=result)
        except ValidationException as e:
            raise HTTPException(status_code=422, detail=str(e))
        except NotFoundException as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"删除失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="服务器错误")



    async def update_knowledge_file(
        self,
        id: str = Path(..., description="知识文件ID"),
        payload: KnowledgeFileUpdate = Body(..., description="要更新的字段")
    ):
        try:
            updated = knowledge_file_service.update_partial(id, payload)
            return ApiResponse(status=200, message="修改成功", data=updated.model_dump())
        except ValidationException as e:
            raise HTTPException(status_code=422, detail=str(e))
        except NotFoundException as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"修改失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="服务器错误")






    async def replace_knowledge_file(
        self,
        id: str = Path(..., description="知识文件ID"),
        file: UploadFile = File(..., description="新的知识文件"),
    ):
        try:
            if not file:
                raise ValidationException("No file provided")

            file_extension = file.filename.split('.')[-1].lower() if file.filename else ''
            if file_extension not in SUPPORTED_EXTENSIONS:
                raise UnsupportedFileTypeException(f"不支持的文件类型: {file_extension}")

            uploaded_file = FileUploader()
            uploaded_object = await uploaded_file.upload_file_form(file, KB_BUCKET_NAME)
            if not uploaded_object:
                raise DatabaseException("文件上传失败")


            patch = KnowledgeFileUpdate(

            updated = knowledge_file_service.update_file_fields(
                id=id,
                file_name=uploaded_object.get("stored_filename"),
                file_type=file_extension,
                minio_path=uploaded_object.get("file_url"),
                status="uploaded",
            )

            return ApiResponse(status=200, message="替换文件成功", data=updated.model_dump())

        except ValidationException as e:
            raise HTTPException(status_code=422, detail=str(e))
        except NotFoundException as e:
            raise HTTPException(status_code=404, detail=str(e))
        except (UnsupportedFileTypeException, DatabaseException) as e:
            raise HTTPException(status_code=e.status_code, detail=str(e))
        except Exception as e:
            logger.error(f"替换文件失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="服务器错误")






