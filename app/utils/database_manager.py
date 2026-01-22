from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.mysql import VARCHAR
from app.models.mysql.knowledge_file import Base,KnowledgeFile
from app.models.mysql.prompt_file import Prompt
from app.models.mysql.prompt_file import Prompt


# 数据库连接和会话管理
class DatabaseManager:
    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def get_session(self):
        return self.SessionLocal()

    def get_prompt(self):
        session = self.get_session()
        try:
            row = (
                session.query(Prompt)
                .filter(Prompt.is_deleted.is_(False))
                .order_by(Prompt.id.asc())
                .first()
            )
            if not row:
                raise RuntimeError("prompts 表没有记录")
            return row.content, row.output_requirement
        finally:
            session.close()
