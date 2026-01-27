import logging
import os
import time
from pathlib import Path
from vanna.ollama.ollama import Ollama
from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
import pymysql
from app.config import settings

logger = logging.getLogger(__name__)


class HealthRiskVanna(ChromaDB_VectorStore, Ollama):
    def __init__(self, config=None):
        if config is None:
            config = {}

        # 使用绝对路径避免相对路径问题
        base_dir = Path(__file__).parent.parent
        chroma_path = config.get('chroma_db_path', str(base_dir / 'chromadb'))

        # 确保路径是绝对路径
        chroma_path = os.path.abspath(chroma_path)
        os.makedirs(chroma_path, exist_ok=True)
        config['chroma_db_path'] = chroma_path

        logger.info(f"初始化 ChromaDB，路径: {chroma_path}")

        # 添加超时机制
        max_retries = 1
        for attempt in range(max_retries):
            try:
                ChromaDB_VectorStore.__init__(self, config=config)
                Ollama.__init__(self, config=config)
                logger.info("ChromaDB 初始化成功")
                break
            except Exception as e:
                logger.warning(f"ChromaDB 初始化尝试 {attempt + 1} 失败: {str(e)}")
                if attempt == max_retries - 1:
                    logger.error("ChromaDB 初始化完全失败，使用内存模式")
                    # 使用内存模式作为备选
                    config['chroma_db_path'] = None
                    ChromaDB_VectorStore.__init__(self, config=config)
                    Ollama.__init__(self, config=config)
                else:
                    time.sleep(2)  # 等待2秒后重试

        self.db_config = {
            'host': settings.MYSQL_HOST,
            'port': int(settings.MYSQL_PORT),
            'user': settings.MYSQL_USER,
            'password': settings.MYSQL_PASSWORD,
            'database': settings.MYSQL_DB,
            'charset': 'utf8mb4'
        }

        # 延迟连接数据库，避免启动时阻塞
        self.connection = None

    def connect_to_mysql(self):
        """连接MySQL数据库"""
        try:
            if self.connection is None or not self.connection.open:
                self.connection = pymysql.connect(**self.db_config)
                logger.info("成功连接到MySQL数据库")
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            return False

    def execute_sql(self, sql: str):
        """执行SQL查询"""
        try:
            # 确保连接存在
            if self.connection is None or not self.connection.open:
                self.connect_to_mysql()

            with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                return result
        except Exception as e:
            logger.error(f"SQL执行失败: {str(e)}")
            # 重新连接并重试一次
            try:
                self.connect_to_mysql()
                with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(sql)
                    result = cursor.fetchall()
                    return result
            except Exception as retry_error:
                logger.error(f"SQL重试执行失败: {str(retry_error)}")
                raise retry_error

    def train_health_risk_tables(self):
        """训练健康风险表结构 - 异步执行避免阻塞"""
        try:
            # 用户健康风险测评记录表的DDL
            ddl = """
            CREATE TABLE IF NOT EXISTS user_health_risk_assessment (
                id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
                user_id VARCHAR(64) NOT NULL COMMENT '用户唯一标识',
                user_name VARCHAR(100) NOT NULL COMMENT '用户姓名',
                sex ENUM('男', '女', '其他') NOT NULL COMMENT '性别',
                age TINYINT UNSIGNED NOT NULL COMMENT '年龄',
                assessment_time DATETIME NOT NULL COMMENT '测评时间',
                assessment_count INT DEFAULT 1 COMMENT '测试次数',
                total_score TINYINT UNSIGNED NOT NULL COMMENT '总分',
                nutritional_impairment_score TINYINT UNSIGNED NOT NULL COMMENT '营养受损分',
                disease_severity_score TINYINT UNSIGNED NOT NULL COMMENT '疾病严重度分',
                age_score TINYINT UNSIGNED NOT NULL COMMENT '年龄分',
                assessment_basis TEXT COMMENT '评分依据说明',
                risk_level ENUM('无风险', '低风险', '中风险', '高风险') NOT NULL COMMENT '风险等级',
                bmi DECIMAL(4,2) COMMENT 'BMI指数',
                weight_change VARCHAR(100) COMMENT '体重变化情况',
                disease_condition TEXT COMMENT '疾病状况描述',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户健康风险测评记录表';
            """

            # 训练DDL
            self.train(ddl=ddl)

            # 训练业务文档
            documentation = """
            用户健康风险测评记录表包含NRS2002营养风险筛查的完整评分数据。
            重要字段说明：
            - total_score: 总分(0-7分)，分数越高风险越大
            - nutritional_impairment_score: 营养受损评分(0-3分)
            - disease_severity_score: 疾病严重度评分(0-3分)  
            - age_score: 年龄评分(0-1分)，70岁以上为1分
            - risk_level: 风险等级，根据总分自动计算
            - assessment_count: 测评次数，反映用户测评频率

            常用查询模式：
            1. 查询高风险患者：WHERE risk_level = '高风险'
            2. 按时间范围查询：WHERE assessment_time BETWEEN '开始时间' AND '结束时间'
            3. 统计各风险等级人数：GROUP BY risk_level
            4. 查询用户历史测评记录：WHERE user_id is not null
            """
            self.train(documentation=documentation)

            # 训练示例SQL查询
            example_sqls = [
                "SELECT user_name, age, total_score, risk_level FROM user_health_risk_assessment WHERE risk_level = '高风险' ORDER BY total_score DESC LIMIT 10",
                "SELECT risk_level, COUNT(*) as count FROM user_health_risk_assessment GROUP BY risk_level ORDER BY count DESC",
                "SELECT user_name, assessment_time, total_score FROM user_health_risk_assessment WHERE user_id = 'USER001' ORDER BY assessment_time DESC",
                "SELECT AVG(total_score) as avg_score, AVG(age) as avg_age FROM user_health_risk_assessment WHERE sex = '男'",
                "SELECT DATE(assessment_time) as date, COUNT(*) as daily_count FROM user_health_risk_assessment GROUP BY DATE(assessment_time) ORDER BY date DESC LIMIT 7"
            ]

            for sql in example_sqls:
                self.train(sql=sql)

            logger.info("健康风险表结构训练完成")
        except Exception as e:
            logger.error(f"训练过程出现错误: {str(e)}")
            # 不抛出异常，避免影响服务启动


# 初始化Vanna实例 - 使用绝对路径
base_dir = Path(__file__).parent
chroma_db_path = base_dir / 'chromadb'

vanna_config = {
    'model': settings.LLM_MODEL,
    'ollama_host': settings.OLLAMA_BASE_URL,
    'chroma_db_path': str(chroma_db_path)
}

vn = HealthRiskVanna(config=vanna_config)