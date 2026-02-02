from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from app.config import settings  # 从配置文件获取数据库连接信息
import logging

# 初始化日志（跟踪数据库连接状态）
logger = logging.getLogger("app.utils.db")

# ------------------------------
# 1. 全局引擎与会话工厂（单例模式，避免重复创建连接）
# ------------------------------
# 数据库引擎配置（适配 MySQL，支持连接池优化）
engine = create_engine(
    url=settings.MYSQL_URI,  # 格式：mysql+pymysql://user:password@host:port/db_name
    echo=False,  # 调试模式下打印 SQL 语句（生产环境设为 False）
    pool_size=5,  # 连接池默认大小（根据并发量调整，建议 5-20）
    max_overflow=10,  # 连接池最大溢出连接数（临时并发时自动扩容）
    pool_recycle=3600,  # 连接自动回收时间（秒，避免长时间闲置被数据库断开）
    pool_pre_ping=True,  # 每次获取连接前检查连通性（防止死连接）
    connect_args={
        "charset": "utf8mb4",  # 支持 emoji 等特殊字符
        "connect_timeout": 10  # 连接超时时间（秒，避免无限阻塞）
    }
)

# 会话工厂（绑定引擎，配置会话默认行为）
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,  # 关闭自动提交（需手动调用 session.commit() 提交事务）
    autoflush=False,  # 关闭自动刷新（避免未提交数据被自动同步到数据库）
    expire_on_commit=False  # 提交后不失效会话中的对象（方便后续读取已提交数据）
)


# ------------------------------
# 2. 会话获取函数（核心接口）
# ------------------------------
def get_db_session() -> Session:
    """
    获取 SQLAlchemy 数据库会话实例

    功能特性：
    - 自动创建会话并绑定到全局引擎
    - 异常时自动回滚未提交事务
    - 确保会话最终被关闭（避免资源泄漏）

    返回：
        Session: SQLAlchemy 会话对象，用于执行数据库 CRUD 操作

    示例：
        with get_db_session() as db:
            user = db.query(UserProfile).filter_by(user_id="test123").first()
            db.commit()
    """
    db = None
    try:
        # 创建新会话
        db = SessionLocal()
        logger.debug(f"成功创建数据库会话（ID: {id(db)}）")

        #  yield 会话（支持 with 语句自动管理生命周期）
        yield db

        # with 块正常结束时，提交事务（若用户未手动提交）
        if not db.in_transaction():
            db.commit()
            logger.debug(f"会话（ID: {id(db)}）自动提交事务")

    except SQLAlchemyError as e:
        # 数据库异常时回滚事务
        if db and db.in_transaction():
            db.rollback()
            logger.error(f"会话（ID: {id(db)}）事务回滚，原因：{str(e)}", exc_info=True)
        raise  # 重新抛出异常，让调用方处理

    finally:
        # 确保会话最终关闭（释放连接到连接池）
        if db:
            db.close()
            logger.debug(f"会话（ID: {id(db)}）已关闭，连接释放")


# ------------------------------
# 3. 辅助函数（可选，用于初始化数据库表）
# ------------------------------
def init_db():
    """
    初始化数据库表结构（基于 SQLAlchemy 模型）
    首次启动项目时调用，自动创建所有模型对应的表
    """
    try:
        from app.models.mysql.conversation_history import ConversationHistory
        from app.models.mysql.user_profile import UserProfile  # 导入所有 MySQL 模型
        # 基于模型创建表（若表已存在则不重复创建）
        from sqlalchemy.ext.declarative import declarative_base as Base  # 导入你的 Base 类（declarative_base() 实例）
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表结构初始化成功（已存在的表将跳过）")
    except Exception as e:
        logger.error(f"数据库表结构初始化失败：{str(e)}", exc_info=True)
        raise