from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_models import ChatOpenAI
from dotenv import load_dotenv
import os
# 加载环境变量
current_dir = os.path.dirname(os.path.abspath(__file__))
# 拼接出同级目录下 .env 的路径
env_path = os.path.join(current_dir, '.env')

# 强制加载指定的 .env 文件
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path, override=True) # override=True 确保覆盖掉系统变量
    print(f"✅ 已加载环境配置: {env_path}")
else:
    print("❌ 未找到同级目录下的 .env 文件，尝试默认加载...")
    load_dotenv()
# 配置 DeepSeek 模型
chat = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("BASE_URL"),
    streaming=False,   # 先关掉，排错更直接
    temperature=0.7,
)


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