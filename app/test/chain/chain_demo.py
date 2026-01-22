from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_models import ChatOpenAI
from dotenv import load_dotenv
import os
# 加载环境变量
# print(os.getenv("DEEPSEEK_API_KEY"))

# 强制加载指定的 .env 文件

load_dotenv()
print(os.getenv("DEEPSEEK_API_KEY"))
# 配置 DeepSeek 模型
chat = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("BASE_URL"),
    streaming=False,   # 先关掉，排错更直接
    temperature=0.7,
)
print(os.getenv("DEEPSEEK_API_KEY"))

prompt_template = PromptTemplate.from_template(
template="请给我讲一个关于{topic}的笑话"
)

parser = StrOutputParser()

# 情况1：没有使用chain
# prompt_value = prompt_template.format(topic="黑色幽默")
# result = chat.invoke(prompt_value)
# out_put = parser.invoke(result)
# print(out_put)

# 情况2：使用chain
chain = prompt_template | chat | parser
output = chain.invoke({"topic": "黑色幽默"})
print(output)