from typing import List, Dict, Any
from langchain_ollama import OllamaLLM
import re
import json


class OllamaExtractionPipeline:
    """基于 Ollama 的复杂信息提取管道"""

    def __init__(self, model_name: str = "qwen3:0.6b"):
        self.llm = OllamaLLM(model=model_name)

    def extract_entities(self, text: str, entity_types: List[str]) -> Dict[str, List[str]]:
        """提取命名实体"""

        prompt = f"""请从以下文本中提取以下类型的实体：{', '.join(entity_types)}

文本：{text}

请按以下格式返回：
实体类型1: 实体1, 实体2, ...
实体类型2: 实体1, 实体2, ...
...

只返回实体列表，不要有其他解释。"""

        response = self.llm.invoke(prompt)
        return self._parse_entity_response(response, entity_types)

    def extract_relations(self, text: str) -> List[Dict[str, str]]:
        """提取关系信息"""

        prompt = f"""请从以下文本中提取人物-属性关系：

文本：{text}

请按JSON格式返回：
[
    {{"人物": "姓名", "属性": "属性名", "值": "属性值"}},
    ...
]

只返回JSON数组，不要有其他内容。"""

        response = self.llm.invoke(prompt)
        return self._parse_json_response(response)

    def _parse_entity_response(self, response: str, entity_types: List[str]) -> Dict[str, List[str]]:
        """解析实体提取响应"""
        entities = {}
        for line in response.strip().split('\n'):
            for entity_type in entity_types:
                if line.startswith(entity_type + ':'):
                    entities[entity_type] = [e.strip() for e in line.split(':', 1)[1].split(',')]
                    break
        return entities

    def _parse_json_response(self, response: str) -> List[Dict[str, str]]:
        """解析JSON响应"""
        try:
            # 清理响应中的代码块标记
            cleaned = re.sub(r'```json|```', '', response.strip())
            return json.loads(cleaned)
        except json.JSONDecodeError:
            print(f"JSON解析错误: {response}")
            return []


# 使用高级提取管道
pipeline = OllamaExtractionPipeline()

# 提取实体
text = "张三今年25岁，在ABC公司工作，邮箱是zhangsan@email.com。李四30岁，在XYZ公司工作。"
entities = pipeline.extract_entities(text, ["人名", "年龄", "公司", "邮箱"])
print("实体提取:", entities)

# 提取关系
relations = pipeline.extract_relations(text)
print("关系提取:", relations)

