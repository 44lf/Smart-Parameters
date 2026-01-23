# 1. 导入必要的模块
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI # 记得我们说过，DeepSeek兼容OpenAI协议
from langchain_core.output_parsers import StrOutputParser

# 2. 准备原料 (你的 DeepSeek 配置)
# 这里的 base_url 和 api_key 记得换成你自己的
llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key="sk-ead21e759d0348229c2d57a2710692b6",
    openai_api_base="https://api.deepseek.com"
)

# 3. 定义步骤 (Prompt)
prompt = ChatPromptTemplate.from_template("请给生产{product}的公司起一个很酷的中文名字，只返回名字，不要废话。")

# 4. 定义工具 (把输出转成字符串的解析器，不然大模型返回的是一堆对象)
output_parser = StrOutputParser()

chain = prompt | llm | output_parser

# 5. 运行 Chain
result = chain.invoke({"product": "量子计算机"})

print(f"老师给你的评分：{result}")