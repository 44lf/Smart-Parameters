from langchain_core.prompts import PromptTemplate

prompt_template = PromptTemplate.from_template(
    "请给我一个关于{topic}的{type}解释。"
)
#传入模板中的变量名
prompt = prompt_template.format(
 type="详细",
 topic="量子力学"
)
prompt = prompt_template.invoke({"type":"详细", "topic":"量子力学"})
print(prompt)
print(type(prompt))