from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_models import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# 配置模型
chat = ChatOpenAI(
    model='deepseek-chat',
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("BASE_URL"),
    streaming=True,
    temperature=0.7
)

# 定义两个提示模板
template1 = """你是个剧作家。给定剧本的标题,你的工作就是为这个标题写一个大纲。
Title:{title}
"""
prompt1 = PromptTemplate.from_template(template1)

template2 = """你是<<纽约时报>>的剧作家。有了剧本的大纲,你的工作是为剧本写一篇评论。
剧情大纲:
{synopsis}
"""
prompt2 = PromptTemplate.from_template(template2)

# 构建链
parser = StrOutputParser()

# 第一个链:生成大纲
chain1 = prompt1 | chat | parser

# 第二个链:生成评论
chain2 = prompt2 | chat | parser

# 执行
title = "日落海滩上的悲剧"
print(f"=== 处理标题: {title} ===\n")

synopsis = chain1.invoke({"title": title})
print(f"大纲:\n{synopsis}\n")

review = chain2.invoke({"synopsis": synopsis})
print(f"评论:\n{review}")