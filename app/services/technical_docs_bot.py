from redis_rag_service import  RedisRAGService

def technical_docs_example():
    """技术文档问答示例"""
    rag_service = RedisRAGService(
        redis_host="localhost",
        ollama_model="qwen3:0.6b"  # 使用代码专用模型
    )

    # 添加API文档
    api_docs = [
        "用户登录API: POST /api/v1/auth/login, 参数: {username: string, password: string}, 返回: {token: string, expires_in: 3600}",
        "用户注册API: POST /api/v1/auth/register, 参数: {username: string, password: string, email: string}, 返回: {user_id: number}",
        "订单查询API: GET /api/v1/orders/{order_id}, 需要认证头: Authorization: Bearer {token}, 返回订单详情",
        "商品列表API: GET /api/v1/products?page=1&limit=10, 支持分页参数, 返回商品数组",
        "错误码400: 请求参数错误, 请检查输入数据",
        "错误码401: 未授权访问, 需要有效的认证token",
        "错误码404: 资源不存在, 请检查请求路径",
        "错误码500: 服务器内部错误, 请联系管理员",
        "数据库配置: 使用MySQL 8.0, 连接池大小20, 超时时间30秒",
        "缓存策略: 使用Redis缓存热点数据, TTL设置为1小时"
    ]

    rag_service.add_documents(api_docs)

    # 开发者查询
    queries = [
        "如何实现用户登录？需要调用哪个API？",
        "获取商品列表的API是什么？支持分页吗？",
        "遇到401错误应该怎么处理？",
        "系统的缓存策略是怎样的？"
    ]

    for query in queries:
        print(f"\n开发者问题: {query}")
        response = rag_service.rag_pipeline(query)
        print(f"回答: {response['answer']}")
        print("参考文档:")
        for i, source in enumerate(response['sources'], 1):
            print(f"  {i}. {source}")


# 运行技术文档示例
technical_docs_example()