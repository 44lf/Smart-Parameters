from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.chat_models import ChatOpenAI
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 配置 DeepSeek 模型
chat = ChatOpenAI(
model='deepseek-chat',
openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
openai_api_base=os.getenv("BASE_URL"),
streaming=True,
temperature=0.7
)


def chat_with_model(question):

    prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个助手，请根据用户问题给出回答"),
    ("human", "{question}")
    ])

# 创建初始提示模板
    chain = prompt | chat

    current_question = question
    while True:


        response = chain.invoke({"question": current_question})
        print(f'模型的回答：{response.content}')

    # 询问用户是否还有其它问题
        user_input = input("是否还有其它问题？(输入'退出'结束对话): ").strip()

    # 设置退出条件
        if user_input == '退出':
            break

    # 更新问题并重新创建提示模板
        current_question = user_input


if __name__ == "__main__":
    chat_with_model("你好！")

