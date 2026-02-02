import logging
from typing import Optional

from fastapi import status
from pydantic import BaseModel

from app.routers.base_router import BaseRouter
from app.schemas.common import ApiResponse
from app.services.nutritionist_agent_service import NutritionistAgentService
from app.config import settings
from app.utils.redis_utils import RedisUtils
logger = logging.getLogger(__name__)

redis_utils = RedisUtils()
# 数据模型
class QueryRequest(BaseModel):
    question: str = None
    user_id: Optional[str] = None
    limit: Optional[int] = 10
    auto_execute: Optional[bool] = True




class AgentRouter(BaseRouter):
    def __init__(self):
        logger.info("Initializing AgentRouter")
        super().__init__()
        self.router = self._register_routes()
        # 移除异步初始化代码

    def _register_routes(self):
        self.router.post(
            "/query",
            response_model=ApiResponse,
            status_code=status.HTTP_200_OK,
            summary="查询问题",
            description="查询健康",
            tags=["多轮对话"]
        )(self.natural_agent_query)

        return self.router


    async def natural_agent_query(self, request: QueryRequest):
        """自然语言查询接口"""
        try:
            user_input = request.question
            logger.info(f"收到查询请求: {user_input}")
            history_key = f"history_{request.user_id}"
            agent = NutritionistAgentService(llm_model=settings.LLM_MODEL,user_id=request.user_id)  # 建议使用1.8b及以上模型确保逻辑严谨
            if redis_utils.isExists_key(history_key):
                history_input = redis_utils.get_str(history_key)
                history_input = history_input.decode("unicode_escape").encode("latin-1")
                history_input = history_input.decode("utf-8").replace("'","")
                logger.info(f"after history_input: {history_input}")
                user_input = f"{history_input},{user_input}"
                logger.info(f"user_input: {user_input}")
            response,res_content = agent.chat(user_input)
            print(f"history_input:{response} \r\n{response['input']}")
            redis_utils.set_params(history_key,response['input'])
            # 保存用户档案
            agent._save_user_profile()
            return ApiResponse(
                status=200,
                message="success",
                data={res_content}
            )

        except Exception as e:
            logger.error(f"查询处理失败: {str(e)}")