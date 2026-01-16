import uuid
import logging
from typing import Dict, Any

from app.config import settings
from app.exceptions.base_api_exception import ValidationException, NotFoundException
from app.dao.knowledge_file_dao import KnowledgeFileDAO
from app.schemas.knowledge_file import KnowledgeFileUpdate, KnowledgeFileResponse
from app.utils.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

db_manager = DatabaseManager(settings.MYSQL_URI)
file_dao = KnowledgeFileDAO(db_manager)

class KnowledgeFileService:
    def save_knowledge_file(self, model_param: Dict[str, Any]):
        model_param["id"] = str(uuid.uuid4())
        record = file_dao.create_file(model_param)
        return record

    def get_file_by_id(self, file_id: str):
        if not file_id:
            raise ValidationException("No id provided")
        record = file_dao.get_file_by_id(file_id)
        if not record:
            raise NotFoundException("Knowledge file not found")
        return record

    def save_knowledge_file_response(self, model_param: Dict[str, Any]) -> KnowledgeFileResponse:
        record = self.save_knowledge_file(model_param)
        record = self.get_file_by_id(record.id)
        return KnowledgeFileResponse.model_validate(record)

    def find_file_response(self, file_id: str) -> KnowledgeFileResponse:
        record = self.get_file_by_id(file_id)
        return KnowledgeFileResponse.model_validate(record)

    def delete_knowledge_file(self, file_id: str) -> Dict[str, Any]:
        _ = self.get_file_by_id(file_id)
        ok = file_dao.delete_file(file_id)
        if not ok:
            raise NotFoundException("Knowledge file not found")
        return {"id": file_id}

    def update_partial(self, file_id: str, payload: KnowledgeFileUpdate) -> KnowledgeFileResponse:
        if not file_id:
            raise ValidationException("No id provided")

        data = payload.to_update_dict()
        if not data:
            raise ValidationException("没有任何要修改的字段")

        _ = self.get_file_by_id(file_id)
        updated = file_dao.update_file(file_id, data)
        if not updated:
            raise NotFoundException("Knowledge file not found")

        record = self.get_file_by_id(file_id)
        return KnowledgeFileResponse.model_validate(record)

    # --- 新增的方法 ---
    def update_file_fields(self, id: str, file_name: str, file_type: str, minio_path: str, status: str) -> KnowledgeFileResponse:
        """
        专门用于替换文件时更新核心字段
        """
        if not id:
            raise ValidationException("No id provided")

        # 确保文件存在
        _ = self.get_file_by_id(id)

        # 构造更新字典
        update_data = {
            "file_name": file_name,
            "file_type": file_type,
            "minio_path": minio_path,
            "status": status,
            "updated_by": 1  # 保持与 create 一致，或者从 context 获取当前用户
        }

        updated = file_dao.update_file(id, update_data)
        if not updated:
            raise NotFoundException("Knowledge file not found")

        record = self.get_file_by_id(id)
        return KnowledgeFileResponse.model_validate(record)