from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain.memory import ConversationBufferMemory

# 1. 初始化 Redis 存储（session_id 唯一标识一个会话）
redis_history = RedisChatMessageHistory(
    session_id="user_zhang3",  # 用户唯一ID
    url="redis://localhost:5379/0"  # Redis 地址
)

# 2. 结合 BufferMemory 使用
memory = ConversationBufferMemory(
    chat_memory=redis_history,  # 用 Redis 作为底层存储
    memory_key="history"
)

# 3. 保存/加载对话（跨进程/跨服务可见）
memory.save_context({"input": "我叫张三"}, {"output": "已记录"})
print(memory.load_memory_variables({})["history"])  # 输出：Human: 我叫张三\nAI: 已记录