from langchain_core.prompts import ChatPromptTemplate

#参数类型这里使用的是tuple构成的list
prompt_template = ChatPromptTemplate(
   [
# 字符串 role + 字符串 content
    ("system", "你是一个AI开发工程师，你的名字是{name}"),
    ("human", "你能开发哪些应用?"),
    ("ai", "我能开发很多AI应用, 比如聊天机器人, 图像识别, 自然语言处理等."),
    ("human", "{user_input}")
   ]
)
#调用方法，返回字符串
prompt = prompt_template.invoke(
    input={"name": "沃林AI机器人", "user_input": "你能帮我做些什么?"}
)

print(prompt)