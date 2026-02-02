from langchain.memory import ConversationBufferMemory
from langchain_ollama import OllamaLLM
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate

# 1. 初始化记忆（返回格式：字符串）
memory = ConversationBufferMemory(
    return_messages=False,  # False：返回字符串；True：返回消息对象列表
    memory_key="history"    # 上下文变量名，需与 Prompt 中的变量对应
)

# 2. 初始化 LLM 和 Prompt
llm = OllamaLLM(model="qwen3:4b",base_url="http://127.0.0.1:11434")
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是助手，需参考历史对话回答：{history}"),
    ("user", "{input}")
])

# 3. 构建对话链
chain = LLMChain(llm=llm, prompt=prompt, memory=memory)

# 4. 多轮对话（自动保存/加载上下文）
print(chain.invoke({"input": "我叫张三，体重70kg"}))  # AI：好的，已记录你的信息
print(chain.invoke({"input": "我刚才说我叫什么？"}))   # AI：你刚才说你叫张三
