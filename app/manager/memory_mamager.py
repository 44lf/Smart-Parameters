from datetime import datetime
from typing import Dict, List, Any
import re
import logging
from langchain.memory import ConversationBufferMemory
from app.models.mysql.conversation_history import ConversationHistory
from app.models.mysql.user_profile import UserProfile  # 确保导入用户档案模型
from app.utils.db import get_db_session  # 导入会话生成器

logger = logging.getLogger("MemoryManager")


class MemoryManager:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.db_session = None  # 初始化会话变量
        self.extracted_entities = {}  # 存储提取的用户实体（供更新档案用）

        try:
            # 关键：通过 next() 触发生成器，获取实际的 Session 实例
            self.db_session = next(get_db_session())
            logger.info(f"MySQL会话初始化成功 - 用户ID: {self.user_id}, 数据库: test_db")

            # 初始化LangChain短记忆（解决之前的 deprecation warning 可加 return_messages=True）
            self.short_term_memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                # 适配ChatPromptTemplate的Message格式
                output_key="output"  # 与Agent输出键对齐
            )
            # self.load_conversation_history_to_memory()
        except Exception as e:
            logger.error(f"MySQL会话初始化失败 - 用户ID: {self.user_id}: {str(e)}", exc_info=True)
            raise

    def load_conversation_history_to_memory(self):
        """从数据库加载最近的历史对话到短期记忆"""
        try:
            # 获取最近10条对话历史（可根据需要调整数量）
            history_records = (self.db_session.query(ConversationHistory)
                               .filter_by(user_id=self.user_id)
                               .limit(10)
                               .all())

            # 按时间顺序排序（从早到晚）
            history_records.reverse()

            # 将历史对话添加到短期记忆
            for record in history_records:
                self.short_term_memory.chat_memory.add_user_message(record.user_input)
                self.short_term_memory.chat_memory.add_ai_message(record.agent_response)

            logger.info(f"加载历史对话到短期记忆成功 - 用户ID: {self.user_id}, 记录数: {len(history_records)}")

        except Exception as e:
            logger.error(f"加载历史对话到短期记忆失败 - 用户ID: {self.user_id}: {str(e)}")
    def extract_entities_from_conversation(self, user_input: str) -> Dict[str, Any]:
        """提取对话中的用户实体（体重、身高、健康状况等）"""
        entities = {}
        # 1. 提取体重（kg）
        weight_match = re.search(r"体重(\d+(?:\.\d+)?)kg", user_input)
        if weight_match:
            entities["weight_kg"] = float(weight_match.group(1))
        # 2. 提取身高（cm）
        height_match = re.search(r"身高(\d+(?:\.\d+)?)cm", user_input)
        if height_match:
            entities["height_cm"] = float(height_match.group(1))
        # 3. 提取体重下降比例
        weight_loss_match = re.search(r"体重下降了(\d+(?:\.\d+)?)%", user_input)
        if weight_loss_match:
            entities["weight_loss_pct"] = float(weight_loss_match.group(1))

        # 保存到实例属性（供后续更新用户档案）
        self.extracted_entities = entities
        logger.info(f"提取到用户实体 - 用户ID: {self.user_id}, 实体: {entities}")
        return entities

    def save_context_to_memory(self, user_input: str, agent_response: str):
        """将当前对话保存到短期记忆"""
        try:
            self.short_term_memory.save_context(
                {"input": user_input},
                {"output": agent_response}
            )
            logger.debug(f"短期记忆保存成功 - 用户ID: {self.user_id}")
        except Exception as e:
            logger.error(f"短期记忆保存失败 - 用户ID: {self.user_id}: {str(e)}")
    def save_conversation(self, user_input: str, agent_response: str, entities: Dict[str, Any] = None):
        """保存对话到 conversation_history 表（确保会话是Session实例）"""
        if not self.db_session:
            raise ValueError(f"数据库会话未初始化 - 用户ID: {self.user_id}")

        try:
            # 1. 保存到短期记忆
            # self.save_context_to_memory(user_input, agent_response)
            #
            # # 2. 提取实体（如果未提供）
            # if entities is None:
            #     entities = self.extract_entities_from_conversation(user_input, agent_response)

            # 创建对话记录对象
            conversation = ConversationHistory(
                user_id=self.user_id,
                user_input=user_input,
                agent_response=agent_response,
                timestamp=datetime.now(),
                conversation_metadata=entities or {}  # 对应重命名后的字段
            )
            # 插入数据库（此时 self.db_session 是Session实例，有add方法）
            self.db_session.add(conversation)
            self.db_session.commit()  # 提交事务
            logger.info(f"对话保存成功 - 用户ID: {self.user_id}, 对话ID: {conversation.id}")
        except Exception as e:
            # 出错时回滚事务（避免数据不一致）
            if self.db_session.in_transaction():
                self.db_session.rollback()
            logger.error(f"对话保存失败 - 用户ID: {self.user_id}: {str(e)}", exc_info=True)
            raise

    def update_user_profile(self, basic_info: Dict[str, Any]):
        """更新/创建用户档案到 user_profile 表"""
        if not self.db_session:
            raise ValueError(f"数据库会话未初始化 - 用户ID: {self.user_id}")

        try:
            # 1. 查询用户是否已有档案
            profile = self.db_session.query(UserProfile).filter_by(user_id=self.user_id).first()
            logger.info(f"profile:{profile},user_id:{self.user_id}")
            if profile:
                # 2. 已有档案：合并新数据（避免覆盖原有信息）
                profile.basic_info = {**profile.basic_info, **basic_info}
                profile.updated_at = datetime.now()
                logger.info(f"用户档案更新成功 - 用户ID: {self.user_id}")
            else:
                # 3. 无档案：创建新档案
                profile = UserProfile(
                    user_id=self.user_id,
                    basic_info=basic_info,
                    health_conditions={},  # 初始化为空字典
                    diet_preferences={},  # 初始化为空字典
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                self.db_session.add(profile)
                self.db_session.commit()
                logger.info(f"用户档案创建成功 - 用户ID: {self.user_id}")

        except Exception as e:
            if self.db_session.in_transaction():
                self.db_session.rollback()
            logger.error(f"用户档案更新失败 - 用户ID: {self.user_id}: {str(e)}", exc_info=True)
            raise

    def close(self):
        """关闭数据库会话（释放资源，避免连接泄漏）"""
        if self.db_session:
            self.db_session.close()
            logger.info(f"MySQL会话已关闭 - 用户ID: {self.user_id}")