# 核心修正：从 langchain_classic 导入
from langchain_classic.memory import ConversationBufferMemory
from langchain_ollama import OllamaLLM
from typing import Dict, Any

class CustomKnowledgeGraphMemory:
    def __init__(self, llm):
        self.llm = llm
        self.entities = {}
        self.relationships = []
        self.buffer_memory = ConversationBufferMemory()

    def save_context(self, user_input: str, ai_output: str):
        # 保存到缓冲记忆
        self.buffer_memory.save_context({"input": user_input}, {"output": ai_output})

        # 提取实体和关系（简化示例）
        # 这里可以添加更复杂的实体提取逻辑
        if "我叫" in user_input:
            name = user_input.split("我叫")[1].split("，")[0]
            self.entities["用户"] = name

        if "体重" in user_input and "身高" in user_input:
            weight = user_input.split("体重")[1].split("kg")[0]
            height = user_input.split("身高")[1].split("cm")[0]
            self.entities["体重"] = weight
            self.entities["身高"] = height

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, str]:
        buffer_data = self.buffer_memory.load_memory_variables(inputs)

        # 构建知识图谱描述
        kg_description = "知识图谱包含实体："
        if self.entities:
            kg_description += "、".join([f"{k}={v}" for k, v in self.entities.items()])

        return {
            "history": buffer_data.get("history", ""),
            "knowledge_graph": kg_description
        }


# 使用自定义记忆
llm = OllamaLLM(model="qwen3:0.6b")
memory = CustomKnowledgeGraphMemory(llm=llm)

# 保存上下文
memory.save_context(
    "我叫张三，体重70kg，身高175cm",
    "你的BMI=22.9（正常）"
)

# 加载记忆
memory_data = memory.load_memory_variables({})
print("对话历史:", memory_data["history"])
print("知识图谱:", memory_data["knowledge_graph"])