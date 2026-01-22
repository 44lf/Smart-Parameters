# test_query.py

# 1. 导入必要的工具
from app.utils.database_manager import DatabaseManager  # 你的数据库管家
from app.models.mysql.prompt_file import Prompt         # 你的 Prompt 模型表

def get_prompt_content_by_name(target_name):
    # 第一步：找管家要一个“会话窗口” (Session)
    session = DatabaseManager.get_session()

    try:
        # 第二步：写查询语句 (这一行是核心！)
        # 翻译成 SQL 就是: SELECT * FROM prompts WHERE name = target_name LIMIT 1;
        result = session.query(Prompt).filter(Prompt.name == target_name).first()

        # 第三步：拿到字段的值
        if result:


            return result.content  # 把具体的值返回出去给别人用
        else:
            print("❌ 没找到这条数据")
            return None

    except Exception as e:
        print(f"查询出错了: {e}")
    finally:
        # 第四步：用完记得关窗口 (好习惯)
        session.close()

