from typing import Optional, Any
from pydantic import BaseModel, Field

class ApiResponse(BaseModel):
    status: int = Field(..., description="状态码：200表示成功，非200表示错误")
    message: str = Field(..., description="响应信息：成功/错误描述")
    data: Optional[Any] = Field(None, description="业务数据：成功时返回具体数据，错误时可为None")
    page: Optional[Any] = Field(None, description="分页信息")

    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True,
    }
