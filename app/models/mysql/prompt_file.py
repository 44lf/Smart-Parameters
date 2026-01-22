from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base

# 假设 Base 已经在 database_manager.py 里定义了，这里为了演示单独写出来
from app.models.mysql.knowledge_file import Base

class Prompt(Base):
    """
    提示词(Prompt)存储模型
    """
    # 1. 必须定义表名
    __tablename__ = 'prompts'

    # 2. 使用 SQLAlchemy 的 Column 定义字段
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')

    # name = fields.CharField(max_length=50) -> 改为 String
    name = Column(String(50), nullable=False, comment='提示词名称')

    # content = fields.TextField() -> 改为 Text
    content = Column(Text, nullable=False, comment='提示词内容')

    # output_requirement = fields.TextField() -> 改为 Text
    output_requirement = Column(Text, comment='大模型输出要求')

    # is_active = fields.BooleanField() -> 改为 Boolean
    is_active = Column(Boolean, default=False, comment='是否激活')

    # is_deleted = fields.BooleanField() -> 改为 Boolean
    is_deleted = Column(Boolean, default=False, comment='是否软删除')

    # created_at -> 改为 DateTime
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    # 3. 修正初始化方法 (只初始化上面的字段)
    def __init__(self, name, content, output_requirement=None, is_active=False):
        self.name = name
        self.content = content
        self.output_requirement = output_requirement
        self.is_active = is_active
        self.created_at = datetime.now()
        self.is_deleted = False

    # 4. 修正 to_dict (对应真实的字段)
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'content': self.content,
            'output_requirement': self.output_requirement,
            'is_active': self.is_active,
            'created_at': str(self.created_at) if self.created_at else ''
        }