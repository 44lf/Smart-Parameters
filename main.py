# # main.py
from fastapi import FastAPI

from app.routers.file_curd_router import FileHandleRouter
# from app.routers.file_handle_router import FileHandleRouter
from app.routers.chunk_router import ChunkRouter
# from app.routers.chatbot_query_router import ChatBotQueryRouter
# from app.routers.tex2sql_router import Text2SqlRouter
# from app.routers.knowledge_file_router import KnowledgeFileRouter
# from app.routers.agent_router import AgentRouter
# from app.routers.text2echarts_router import Text2EchartsRouter
import logging.config
import uvicorn
from app.utils.database_manager import DatabaseManager
from app.config import settings


#

# 配置logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 移除所有现有的handler
for handler in logger.handlers[:]:
    logger.removeHandler(handler)
#
# 创建新的格式化器和handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# ------------------------------
# 核心修改：使用 lifespan 替代 on_event
# ------------------------------

#
# # 创建 FastAPI 实例并绑定生命周期
app = FastAPI()
# # 创建路由器实例
# text2sql_router = Text2SqlRouter()
# # 注册启动事件
# text2sql_router.register_startup_event(app)
#
# # 挂载路由（确保每个路由模块中定义了 router 实例）
app.include_router(FileHandleRouter().router, prefix="/api/v1/file")
app.include_router(FileHandleRouter().router, prefix="/api/v2/file")


app.include_router(ChunkRouter()._register_routes(), prefix="/api/v1/chunks")
# app.include_router(ChatBotQueryRouter()._register_routes(), prefix="/api/v1/rag")
# app.include_router(KnowledgeFileRouter()._register_routes(), prefix="/api/v1/kb")
# app.include_router(AgentRouter()._register_routes(), prefix="/api/v1/agent")
# app.include_router(Text2EchartsRouter()._register_routes(), prefix="/api/v1/bi")
#
# app.include_router(text2sql_router._register_routes(), prefix="/api/v1/t2s")
# # 健康检查端点

@app.get("/")
async def root():
    return {"message": "Hello World"}




@app.on_event("startup")
async def startup_event():
    db_manager = DatabaseManager(settings.MYSQL_URI)
    db_manager.create_tables()
    logger.info("数据库表初始化完成")
if __name__ == "__main__":

    uvicorn.run("main:app", host="0.0.0.0", port=8019,workers=1, timeout_keep_alive=600 ,reload=True)
