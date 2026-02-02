from datetime import datetime
from typing import Dict, Any, List
from langchain.agents import initialize_agent, AgentType
from langchain.tools import BaseTool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage

from app.chat.nutritionist_tools import NutritionistTools
from app.manager.memory_manager import MemoryManager
from langchain_ollama import ChatOllama
from app.config import settings
import logging

logger = logging.getLogger("NutritionistAgentService")


class NutritionistAgentService:
    def __init__(self, llm_model=settings.LLM_MODEL, user_id=None):
        # 1. 初始化LLM
        self.llm = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=llm_model,
            temperature=0.1
        )

        # 2. 确保用户ID存在（关键：所有数据关联的基础）
        self.user_id = user_id or f"user_{int(datetime.now().timestamp())}"
        logger.info(f"用户ID确认: {self.user_id}")

        # 3. 初始化记忆管理器（传递user_id！！！）
        self.memory_manager = MemoryManager(user_id=self.user_id)  # 关键修复

        # 4. 初始化记忆和工具
        self.memory = self.memory_manager.short_term_memory
        self.tools = self._create_tools()
        self.agent_executor = self._initialize_agent()

        logger.info(f"营养师智能体已初始化 - 用户ID: {self.user_id}")

    def _create_tools(self) -> List[BaseTool]:
        return NutritionistTools.get_tools()

    def _initialize_agent(self):
        try:
            system_message = SystemMessage(content="""你是专业营养师，需：
               1. 理解用户需求（体重、饮食、健康问题等）
               2. 必要时使用工具计算（BMI、热量等）
               3. 结合用户历史信息提供个性化建议
               4. 保持专业友好""")

            prompt = ChatPromptTemplate.from_messages([
                system_message,
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad")
            ])

            return initialize_agent(
                tools=self.tools,
                llm=self.llm,
                agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
                prompt=prompt,
                memory=self.memory,
                verbose=True,
                handle_parsing_errors=True
            )
        except Exception as e:
            logger.error(f"初始化智能体失败: {e}", exc_info=True)
            raise

    def _save_user_profile(self):
        """保存用户档案（必须与路由中调用的方法名完全一致）"""
        try:
            # 从记忆管理器中获取提取的实体
            extracted_entities = self.memory_manager.extracted_entities
            if not extracted_entities:
                logger.info(f"未提取到用户实体，无需更新档案 - 用户ID: {self.user_id}")
                return

            # 调用记忆管理器的方法更新用户档案
            self.memory_manager.update_user_profile(basic_info=extracted_entities)
            logger.info(f"用户档案保存完成 - 用户ID: {self.user_id}")
        except Exception as e:
            logger.error(f"保存用户档案失败 - 用户ID: {self.user_id}: {str(e)}", exc_info=True)
            # 此处不抛出异常，避免影响主流程，仅记录错误

    def chat(self, user_input: str) :
        try:
            # 1. 调用智能体获取响应
            response = self.agent_executor.invoke({"input": user_input})
            logger.info(f"response:{response}")
            response_text = response.get("output", str(response))
            # self.memory.ad(response=response_text)
            # print(self.memory.load_memory_variables({})['history'])
            # 2. 提取实体（确保关键信息被捕获）
            extracted_entities = self.memory_manager.extract_entities_from_conversation(
                user_input
            )

            # 3. 强制保存对话（即使无实体也保存）
            self.memory_manager.save_conversation(
                user_input=user_input,
                agent_response=response_text,
                entities=extracted_entities
            )

            # self.memory_manager.load_conversation_history_to_memory()

            # 4. 有实体则更新用户档案
            if extracted_entities:
                self.memory_manager.update_user_profile(basic_info=extracted_entities)
            else:
                logger.info("未提取到实体，不更新用户档案")

            return response,response_text
        except Exception as e:
            logger.error(f"智能体执行错误: {e}", exc_info=True)
            return f"抱歉，处理请求时出错：{str(e)}"

    # 其他方法保持不变...
    def get_user_profile(self) -> Dict[str, Any]:
        profile = self.memory_manager.get_user_profile(self.user_id)
        if profile:
            return {
                "basic_info": profile.basic_info or {},
                "health_conditions": profile.health_conditions or {},
                "diet_preferences": profile.diet_preferences or {},
                "created_at": profile.created_at.isoformat() if profile.created_at else None,
                "updated_at": profile.updated_at.isoformat() if profile.updated_at else None
            }
        return {}

    def close(self):
        self.memory_manager.close()
        logger.info(f"营养师智能体已关闭 - 用户ID: {self.user_id}")