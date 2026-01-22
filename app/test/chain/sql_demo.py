from langchain_community.utilities import SQLDatabase

# 连接 MySQL 数据库
db_user = "root"
db_password = "123456" #根据自己的密码填写
db_host = "127.0.0.1"
db_port = "3306"
db_name = "test_db"
# mysql+pymysql://用户名:密码@ip地址:端口号/数据库名
db = SQLDatabase.from_uri(f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")
print("哪种数据库：", db.dialect)
print("获取数据表：", db.get_usable_table_names())
# 执行查询
res = db.run("SELECT count(*) FROM conversation_history;")
print("查询结果：", res)
# 连接MySQL数据库
from langchain_community.utilities import SQLDatabase
from langchain.chains.sql_database.query import create_sql_query_chain
from langchain_community.chat_models import ChatOpenAI
from dotenv import load_dotenv
import os

# 过滤警告
# warnings.filterwarnings("ignore", category=UserWarning, module=".*ChatOpenAI.*")
print('-------------------------------------------------------------------------------')
# 加载环境变量
load_dotenv()

# 配置 DeepSeek 模型
chat = ChatOpenAI(
model='deepseek-chat',
openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
openai_api_base=os.getenv("BASE_URL"),
streaming=True,
temperature=0.7
)

# 调用Chain
chain = create_sql_query_chain(llm=chat, db=db)

response = chain.invoke({"question": "数据表conversation_history中时间最晚的id是多少？"})
print(response)

# response = chain.invoke({"question": "数据表processing_logs中处理明细中包含失败的信息有多少条"})
# print(response)