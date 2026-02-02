from sqlalchemy import  Column, Integer, String,  DateTime, JSON,  Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
import logging

logger = logging.getLogger("UserProfile")

Base = declarative_base()


class UserProfile(Base):
    """用户档案表 - 长记忆"""
    __tablename__ = 'user_profiles'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID，自增长')
    user_id = Column(String(100), unique=True, nullable=False, index=True, comment='用户唯一标识符')
    basic_info = Column(JSON, comment='用户基本信息，包括年龄、性别、体重、身高等')
    health_conditions = Column(JSON, comment='健康状况信息，包括疾病史、过敏史等')
    diet_preferences = Column(JSON, comment='饮食偏好信息，包括喜欢的食物、忌口等')
    created_at = Column(DateTime, default=datetime.utcnow, comment='记录创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='记录最后更新时间')

    # 定义关系
    # conversations = relationship("ConversationHistory", back_populates="user", cascade="all, delete-orphan")