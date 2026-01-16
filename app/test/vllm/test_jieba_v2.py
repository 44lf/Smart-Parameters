from test_jieba_v1 import init_jieba
import logging

logger = logging.getLogger("test_jieba_v2")# 创建自定义词典示例
def create_custom_dict(terms, output_path):
    """创建自定义词典"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for term in terms:
            f.write(f"{term} 10 n\n")  # 格式: 词语 词频 词性

    logger.info(f"已创建自定义词典: {output_path}")


# 专业术语示例
ai_terms = ["深度学习", "神经网络", "自然语言处理", "计算机视觉", "强化学习"]
create_custom_dict(ai_terms, "ai_terms_dict.txt")

# 使用自定义词典
init_jieba('default', user_dict_path="ai_terms_dict.txt")