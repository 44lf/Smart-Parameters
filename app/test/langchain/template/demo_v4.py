from langchain_core.prompts import ChatPromptTemplate

prompt_template = ChatPromptTemplate.from_messages(
   [
  ("system", "你是一个有帮助的AI机器人，你的名字是{name}。"),
  ("human", "你好，最近怎么样？"),
  ("ai", "我很好，谢谢！"),
  ("human", "{user_input}"),
   ]
)

# 格式化聊天提示词模版中的变量
messages = prompt_template.invoke(
 input={"name":"小明", "user_input":"你叫什么名字？"}
)

print(messages)