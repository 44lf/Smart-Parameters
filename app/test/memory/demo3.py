from langchain.memory import ConversationBufferWindowMemory
# 初始化记忆：仅保留最近2轮对话
memory = ConversationBufferWindowMemory(
    k=2,  # 窗口大小：保留最近2轮
    memory_key="history"
)

# 模拟多轮对话
memory.save_context({"input": "我叫张三"}, {"output": "已记录"})
memory.save_context({"input": "体重70kg"}, {"output": "好的"})
memory.save_context({"input": "身高175cm"}, {"output": "收到"})

# 加载历史（仅保留后2轮：体重+身高）
print(memory.load_memory_variables({})["history"])
# 输出：Human: 体重70kg\nAI: 好的\nHuman: 身高175cm\nAI: 收到