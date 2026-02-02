from langchain_community.chat_message_histories import ChatMessageHistory
# 初始化记忆
memory = ChatMessageHistory()
# 保存对话（用户→AI）
memory.add_user_message("我叫张三，体重70kg")
memory.add_ai_message("好的，已记录你的信息")
# 加载历史（返回消息列表）
print(memory.messages)
# 输出：[HumanMessage(content='我叫张三，体重70kg'), AIMessage(content='好的，已记录你的信息')]