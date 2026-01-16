from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class KnowledgeFileBase(BaseModel):
    collection_name: Optional[str] = Field(None, max_length=256, description="集合名称")
    file_name: Optional[str] = Field(None, max_length=255, description="文件名称")
    file_type: Optional[str] = Field(None, max_length=20, description="文件类型")
    minio_path: Optional[str] = Field(None, max_length=1000, description="MinIO中的存储路径")
    chunk_strategy: Optional[str] = Field(None, max_length=20, description="分片策略")
    description: Optional[str] = Field(None, max_length=255, description="文件描述")
    status: Optional[str] = Field(None, max_length=20, description="文件状态")
    version_no: Optional[int] = Field(None, description="版本号")


class KnowledgeFileCreate(KnowledgeFileBase):
    collection_name: str = Field(..., max_length=256, description="集合名称")
    created_by: int = Field(..., description="创建者")


class KnowledgeFileUpdate(KnowledgeFileBase):
    """部分更新模型,所有字段可选"""
    updated_by: Optional[int] = Field(None, description="更新者")

    def to_update_dict(self) -> dict:
        """返回非None字段的字典"""
        return {k: v for k, v in self.model_dump(exclude_none=True).items() if k != 'id'}


class KnowledgeFileDelete(BaseModel):
    id: str = Field(..., description="文件ID")


class KnowledgeFileInDB(KnowledgeFileBase):
    id: str
    created_time: datetime = Field(..., description="创建时间")
    updated_time: Optional[datetime] = Field(None, description="更新时间")
    created_by: int = Field(..., description="创建者")
    updated_by: Optional[int] = Field(None, description="更新者")

    model_config = {"from_attributes": True}


class KnowledgeFileResponse(BaseModel):
    id: str
    collection_name: str
    file_name: str
    file_type: str
    minio_path: str
    chunk_strategy: str
    description: str = ''
    status: str
    created_by: int
    updated_by: int = 0
    created_time: str = ''
    updated_time: str = ''
    version_no: int = 0

    @field_validator('updated_by', 'version_no', mode='before')
    @classmethod
    def set_default_int(cls, v):
        return 0 if v is None else v

    @field_validator('created_time', 'updated_time', 'description', mode='before')
    @classmethod
    def set_default_str(cls, v):
        return '' if v is None else str(v)

    model_config = {
        "from_attributes": True,
        "extra": "ignore"
    }