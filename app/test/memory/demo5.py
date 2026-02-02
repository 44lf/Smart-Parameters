from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain.memory import ConversationBufferMemory

# 1. 初始化 SQL 存储（SQLite 示例，支持 PostgreSQL/MySQL）
sql_history = SQLChatMessageHistory(
    session_id="user_zhang3",
    connection_string="sqlite:///chat_history.db"  # SQLite 数据库路径
)

# 2. 结合 BufferMemory 使用
memory = ConversationBufferMemory(
    chat_memory=sql_history,
    memory_key="history"
)

# 3. 保存对话（自动写入数据库）
memory.save_context({"input": "我有糖尿病"}, {"output": "需注意低糖饮食"})
print(memory.load_memory_variables({})["history"])  # 输出：Human: 我有糖尿病\nAI: 需注意低糖饮食