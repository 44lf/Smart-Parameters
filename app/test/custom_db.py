from pymilvus import (
        connections,

        Collection,
        db,
        utility
    )


# 配置
milvus_alias = "similarity_demo"
db_name = "custom_db"
collection_name = "custom_collection"
dim = 64  # 向量维度


def setup_milvus():
    """初始化Milvus连接和环境"""
    # 连接服务
    connections.connect(
        alias=milvus_alias,
        host='localhost',
        port='19530'
    )

    # 清理旧环境
    if db_name in db.list_database(using=milvus_alias):
        db.using_database(db_name, using=milvus_alias)
        db.using_database("default", using=milvus_alias)
        for coll in utility.list_collections(using=milvus_alias):
            Collection(coll, using=milvus_alias).drop()
        db.drop_database(db_name, using=milvus_alias)

    # 创建新数据库
    db.create_database(db_name, using=milvus_alias)
    db.using_database(db_name, using=milvus_alias)

    return True