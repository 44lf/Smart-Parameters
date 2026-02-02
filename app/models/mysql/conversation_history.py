from sqlalchemy import  Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import os
import logging

logger = logging.getLogger("ConversationHistory")

Base = declarative_base()


class ConversationHistory(Base):
    """对话历史表 - 短记忆"""
    __tablename__ = 'conversation_history'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID，自增长')
    user_id = Column(String(100), nullable=False, index=True, comment='用户唯一标识符，关联user_profiles.user_id')
    user_input = Column(Text, nullable=False, comment='用户输入的对话内容')
    agent_response = Column(Text, nullable=False, comment='智能体回复的内容')
    timestamp = Column(DateTime, default=datetime.now(), comment='对话发生的时间')
    # 将metadata重命名为conversation_metadata以避免关键字冲突
    conversation_metadata = Column(JSON, comment='对话元数据，包括提取的实体、情感分析结果等')

    # 定义关系
    # user = relationship("UserProfile", back_populates="conversations")