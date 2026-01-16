import jieba
import jieba.posseg as pseg  # 用于词性标注
import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jieba_init")

def init_jieba():
    """
    初始化 Jieba 中文分词工具
    设置用户词典和停用词路径（如果存在）
    """
    # 设置 Jieba 词典路径（如果有自定义需求）
    dict_path = os.getenv("JIEBA_DICT_PATH", None)
    if dict_path and os.path.exists(dict_path):
        jieba.set_dictionary(dict_path)
        logger.info(f"已加载自定义词典: {dict_path}")

    # 加载用户自定义词典（如果存在）
    user_dict_path = os.getenv("JIEBA_USER_DICT", str(Path.home() / "jieba_user_dict.txt"))
    if os.path.exists(user_dict_path):
        jieba.load_userdict(user_dict_path)
        logger.info(f"已加载用户自定义词典: {user_dict_path}")
    else:
        logger.info("未找到用户自定义词典，使用默认配置")

    # 设置停用词文件路径（如果有）
    stopwords_path = os.getenv("JIEBA_STOPWORDS_PATH", None)

    logger.info("Jieba 初始化完成，可用于中文文本预处理")
    return {
        "stopwords_path": stopwords_path,
        "user_dict_path": user_dict_path
    }

def tokenize_chinese_text(text, use_stopwords=False, config=None):
    """
    使用 Jieba 进行中文分词

    Args:
        text: 要分词的中文文本
        use_stopwords: 是否使用停用词过滤
        config: 初始化函数返回的配置字典

    Returns:
        分词后的词语列表
    """
    # 精确模式分词
    words = jieba.cut(text, cut_all=False)

    # 如果需要停用词过滤
    if use_stopwords and config and config.get("stopwords_path"):
        try:
            with open(config["stopwords_path"], 'r', encoding='utf-8') as f:
                stopwords = set([line.strip() for line in f])
            words = [word for word in words if word not in stopwords and word.strip()]
        except Exception as e:
            logger.warning(f"加载停用词失败: {e}")

    return list(words)

def pos_tag_chinese_text(text):
    """
    对中文文本进行词性标注

    Args:
        text: 要处理的中文文本

    Returns:
        带词性标注的词语列表 [(word, pos), ...]
    """
    # 使用 jieba.posseg 进行词性标注
    words = pseg.cut(text)
    return [(word, flag) for word, flag in words]

# 使用示例
if __name__ == "__main__":
    # 初始化 Jieba
    config = init_jieba()

    # 示例文本
    sample_text = "自然语言处理是人工智能领域的一个重要方向"

    # 分词
    tokens = tokenize_chinese_text(sample_text)
    logger.info(f"分词结果: {tokens}")

    # 词性标注
    pos_tags = pos_tag_chinese_text(sample_text)
    logger.info(f"词性标注: {pos_tags}")

    # 使用停用词过滤的分词
    # 注意：需要先准备好停用词文件并设置 JIEBA_STOPWORDS_PATH 环境变量
    # tokens_filtered = tokenize_chinese_text(sample_text, use_stopwords=True, config=config)
    # logger.info(f"过滤停用词后的分词结果: {tokens_filtered}")