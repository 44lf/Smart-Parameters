from langchain_core.prompts import PromptTemplate

# 定义模板：描述主题的应用
template = PromptTemplate(
 template="请简要描述{topic}的应用。",
 input_variables=["topic"]
)
print(template)

# 使用模板生成提示词
prompt_1 = template.format(topic="python")
prompt_2 = template.format(topic="自然语言处理")

print("提示词1:", prompt_1)
print("提示词2:", prompt_2)

# 定义多个变量的模版
template = PromptTemplate(
template="请评价{product}的优缺点，包括{aspect1}和{aspect2}。",
input_variables=["product", "aspect1", "aspect2"]
)
#使用模板生成提示词
prompt_1 = template.format(
product="智能手机",
aspect1="电池续航",
aspect2="拍照质量"
)
prompt_2 = template.format(
 product="笔记本电脑",
 aspect1="处理速度",
 aspect2="便携性"
)

print("提示词1:",prompt_1)
print("提示词2:",prompt_2)