from redis_rag_service import  RedisRAGService

def customer_example():
    """电商客服示例（使用Ollama Embeddings）"""
    # 初始化RAG服务
    rag_service = RedisRAGService(
        redis_host="localhost",
        embedding_model="nomic-embed-text",  # 使用Ollama嵌入模型
        ollama_model="qwen3:0.6b"
    )

    # 添加商品知识库
    product_docs = [
        "产品A: 智能手表, 价格299元, 支持心率监测、GPS定位, 续航7天, 支持30天无理由退货, 保修期1年",
        "产品B: 无线耳机, 价格599元, 主动降噪, 续航30小时, 支持7天无理由退货, 保修期2年",
        "产品C: 平板电脑, 价格1299元, 10英寸屏幕, 128GB存储, 保修期1年, 支持教育优惠",
        "配送政策: 全国包邮, 一般3-5天送达, 加急配送需额外支付20元, 1-2天送达",
        "退换货政策: 7天内商品无损坏可无理由退货, 30天内质量问题可换货",
        "支付方式: 支持支付宝、微信支付、信用卡、花呗分期"
    ]

    rag_service.add_documents(product_docs)

    # 用户查询示例
    queries = [
        "产品A的价格是多少？有什么功能？",
        "你们的退货政策是怎样的？",
        "支持哪些支付方式？可以分期吗？",
        "配送需要多长时间？有加急选项吗？"
    ]

    for query in queries:
        print(f"\n用户问题: {query}")
        response = rag_service.rag_pipeline(query)
        print(f"回答: {response['answer']}")
        print(f"参考来源: {len(response['sources'])} 个文档")


# 运行示例
customer_example()