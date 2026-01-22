from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
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
# 定义提示词模板
prompt = PromptTemplate.from_template("""
如下文档{docs}中说，香蕉是什么颜色的？
""")
# 创建链

# 文档输入
    docs = [
    Document(
    page_content="苹果，学名Malus pumila Mill.，别称西洋苹果、柰，属于蔷薇科苹果属的植物。苹果是全球最广泛种植和销售的水果之一，具有悠久的栽培历史和广泛的分布范围。苹果的原始种群主要起源于中亚的天山山脉附近，尤其是现代哈萨克斯坦的阿拉木图地区，提供了所有现代苹果品种的基因库。苹果通过早期的贸易路线，如丝绸之路，从中亚向外扩散到全球各地。"
       ),
    Document(
    page_content="香蕉是白色的水果，主要产自热带地区。"
       ),
     Document(
    page_content="蓝莓是蓝色的浆果，含有抗氧化物质。"
       )
    ]
    chain = create_stuff_documents_chain(chat, document_variable_name="docs")
    # 执行摘要
    chain = chain.invoke({'docs': docs})
    result = chain.invoke({"prompt": prompt})
    print(result)