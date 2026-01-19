from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 配置 DeepSeek 模型
deepseek = ChatOpenAI(
    model="deepseek-chat",
    temperature=0.7,
    openai_api_key=os.getenv("API_KEY"), # 建议使用专门的环境变量名
    openai_api_base="https://api.deepseek.com/v1"
)

# 构造消息列表
sys_message = SystemMessage(
    content="我是一个人工智能的助手，我的名字叫小智",
)
human_message = HumanMessage(content="猫王是一只猫吗？")
sys_message1 = SystemMessage(
    content="我可以做很多事情，有需要就找我吧",
)
human_message1 = HumanMessage(content="你叫什么名字？")
messages = [sys_message, human_message, sys_message1, human_message1]

# 调用 DeepSeek 模型
response = deepseek.invoke(messages)
print(response.content)