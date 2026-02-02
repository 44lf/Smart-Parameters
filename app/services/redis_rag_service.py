import redis
import json
import hashlib
import requests
import numpy as np
from typing import List, Dict, Any, Union
from langchain.schema import Document

# 尝试不同的导入方式
try:
    # 首先尝试新的官方推荐方式
    from langchain_redis import RedisVectorStore

    REDIS_BACKEND = "redis_vector_store"
    print("✓ 使用 langchain_redis.RedisVectorStore")
except ImportError as e:
    print(f"langchain_redis 导入失败: {e}")
    try:
        # 回退到社区版
        from langchain_community.vectorstores import Redis

        REDIS_BACKEND = "community_redis"
        print("✓ 使用 langchain_community.vectorstores.Redis")
    except ImportError as e:
        print(f"langchain_community 导入失败: {e}")
        try:
            # 最后尝试旧版本方式
            from langchain.vectorstores import Redis

            REDIS_BACKEND = "legacy_redis"
            print("✓ 使用 langchain.vectorstores.Redis")
        except ImportError as e:
            print(f"所有Redis向量存储导入都失败: {e}")
            REDIS_BACKEND = "none"
            Redis = None


class OllamaEmbeddingsWrapper:
    """Ollama Embeddings 包装器"""

    def __init__(self, model_name: str = "nomic-embed-text", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """为文档列表生成嵌入向量"""
        embeddings = []
        for text in texts:
            try:
                response = requests.post(
                    f"{self.base_url}/api/embeddings",
                    json={
                        "model": self.model_name,
                        "prompt": text
                    },
                    timeout=300
                )
                response.raise_for_status()
                embedding = response.json()["embedding"]
                embeddings.append(embedding)
                print(f"✓ 为文档生成嵌入向量成功，维度: {len(embedding)}")
            except Exception as e:
                print(f"✗ 为文档生成嵌入时出错: {e}")
                # 返回默认嵌入向量 (nomic-embed-text 是 768 维)
                embeddings.append([0.0] * 768)
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """为查询文本生成嵌入向量"""
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model_name,
                    "prompt": text
                },
                timeout=300
            )
            response.raise_for_status()
            embedding = response.json()["embedding"]
            print(f"✓ 为查询生成嵌入向量成功，维度: {len(embedding)}")
            return embedding
        except Exception as e:
            print(f"✗ 为查询生成嵌入时出错: {e}")
            return [0.0] * 768


class RedisRAGService:
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 5379,
                 redis_password: str = None, index_name: str = "rag_documents",
                 embedding_model: str = "nomic-embed-text",
                 ollama_model: str = "qwen3:0.6b",
                 ollama_base_url: str = "http://localhost:11434"):
        """
        修复版的Redis RAG服务 - 兼容最新LangChain版本
        """
        # 初始化Redis连接
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                db=0,
                decode_responses=True,
                socket_connect_timeout=10,
                socket_keepalive=True
            )
        except Exception as e:
            print(f"✗ Redis连接初始化失败: {e}")
            raise

        # 初始化Ollama Embeddings
        self.embeddings = OllamaEmbeddingsWrapper(
            model_name=embedding_model,
            base_url=ollama_base_url,
        )

        self.ollama_base_url = ollama_base_url
        self.ollama_model = ollama_model
        self.index_name = index_name
        self.vectorstore = None

        # 缓存配置
        self.cache_config = {
            "vector_cache_ttl": 3600,
            "query_cache_ttl": 300,
        }

        print(f"使用的Redis后端: {REDIS_BACKEND}")
        self._test_connections()

    def _test_connections(self):
        """测试连接"""
        try:
            self.redis_client.ping()
            print("✓ Redis连接成功")
        except Exception as e:
            print(f"✗ Redis连接失败: {e}")
            raise

        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=10)
            response.raise_for_status()
            print("✓ Ollama连接成功")

            # 检查模型是否存在
            models = response.json().get("models", [])
            model_names = [model["name"] for model in models]
            required_models = [self.embeddings.model_name, self.ollama_model]

            for model in required_models:
                if f"{model}:latest" not in model_names:
                    print(f"⚠ 警告: 模型 '{model}' 未找到，请使用 'ollama pull {model}' 下载")
                else:
                    print(f"✓ 模型 '{model}' 已安装")

        except Exception as e:
            print(f"✗ Ollama连接失败: {e}")
            raise

    def _initialize_vectorstore(self, documents: List[Document] = None):
        """初始化向量存储 - 兼容多种版本"""
        redis_url = f"redis://{self.redis_client.connection_pool.connection_kwargs['host']}:{self.redis_client.connection_pool.connection_kwargs['port']}"

        try:
            if REDIS_BACKEND == "redis_vector_store":
                # 使用新的RedisVectorStore
                if documents is not None:
                    self.vectorstore = RedisVectorStore.from_documents(
                        documents=documents,
                        embedding=self.embeddings,
                        redis_url=redis_url,
                        index_name=self.index_name,
                    )
                    print(f"✓ 使用RedisVectorStore.from_documents成功创建索引: {self.index_name}")
                else:
                    self.vectorstore = RedisVectorStore(
                        redis_url=redis_url,
                        index_name=self.index_name,
                        embedding=self.embeddings
                    )
                    print(f"✓ 使用RedisVectorStore成功连接到索引: {self.index_name}")

            elif REDIS_BACKEND in ["community_redis", "legacy_redis"] and Redis is not None:
                # 使用社区版或旧版本
                if documents is not None:
                    self.vectorstore = Redis.from_documents(
                        documents=documents,
                        embedding=self.embeddings,
                        redis_url=redis_url,
                        index_name=self.index_name,
                    )
                    print(f"✓ 使用{Redis.__name__}.from_documents成功创建索引: {self.index_name}")
                else:
                    self.vectorstore = Redis(
                        redis_url=redis_url,
                        index_name=self.index_name,
                        embedding=self.embeddings
                    )
                    print(f"✓ 使用{Redis.__name__}成功连接到索引: {self.index_name}")
            else:
                raise ImportError("没有可用的Redis向量存储后端")

        except Exception as e:
            print(f"✗ 初始化向量存储失败: {e}")
            # 尝试备选方法
            try:
                if Redis is not None and hasattr(Redis, 'from_existing_index'):
                    self.vectorstore = Redis.from_existing_index(
                        embedding=self.embeddings,
                        index_name=self.index_name,
                        redis_url=redis_url
                    )
                    print("✓ 使用备选方法from_existing_index初始化向量存储成功")
                else:
                    raise Exception("备选方法不可用")
            except Exception as e2:
                print(f"✗ 备选初始化方法也失败: {e2}")
                self.vectorstore = None

    def add_documents(self, documents: Union[List[Document], List[str]]) -> bool:
        """添加文档到知识库"""
        if len(documents) == 0:
            print("✗ 文档列表为空")
            return False

        if isinstance(documents[0], str):
            documents = [Document(page_content=doc) for doc in documents]

        try:
            # 初始化向量存储
            self._initialize_vectorstore(documents)

            if self.vectorstore is not None:
                print(f"✓ 成功添加 {len(documents)} 个文档到知识库")
                return True
            else:
                print("✗ 向量存储初始化失败，无法添加文档")
                return False

        except Exception as e:
            print(f"✗ 添加文档时出错: {e}")
            return False

    def search_similar(self, query: str, k: int = 3) -> List[Document]:
        """检索相似内容"""
        if self.vectorstore is None:
            print("✗ 向量存储未初始化")
            return []

        cache_key = f"rag_vector:{hashlib.md5(query.encode()).hexdigest()}"
        cached_result = self.redis_client.get(cache_key)

        if cached_result:
            print("✓ 从缓存中获取向量搜索结果")
            try:
                cached_docs = json.loads(cached_result)
                return [Document(page_content=doc) for doc in cached_docs]
            except json.JSONDecodeError:
                print("✗ 缓存数据解析失败")

        try:
            # 使用 similarity_search 方法
            print(f"正在搜索相似内容: {query}")
            results = self.vectorstore.similarity_search(query, k=k)
            print(f"✓ 找到 {len(results)} 个相关文档")

            # 缓存结果
            doc_contents = [doc.page_content for doc in results]
            self.redis_client.setex(
                cache_key,
                self.cache_config["vector_cache_ttl"],
                json.dumps(doc_contents)
            )

            return results
        except Exception as e:
            print(f"✗ 向量搜索时出错: {e}")
            return []

    def generate_answer(self, query: str, context: str) -> str:
        """使用Ollama生成回答"""
        prompt = f"""基于以下上下文信息回答问题。如果上下文不足以回答问题，请说明这一点。

上下文信息：
{context}

问题：{query}

请提供准确、有用的回答："""

        try:
            print("正在生成回答...")
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                },
                timeout=60
            )
            response.raise_for_status()
            answer = response.json()["response"]
            print("✓ 回答生成成功")
            return answer
        except Exception as e:
            print(f"✗ 生成回答时出错: {e}")
            return "抱歉，生成回答时出现错误。"

    def rag_pipeline(self, query: str, k: int = 3) -> Dict[str, Any]:
        """完整的RAG流程"""
        print(f"\n开始处理查询: {query}")

        cache_key = f"rag_query:{hashlib.md5(query.encode()).hexdigest()}"
        cached_response = self.redis_client.get(cache_key)

        if cached_response:
            print("✓ 从缓存中获取完整回答")
            try:
                response = json.loads(cached_response)
                response["cached"] = True
                return response
            except json.JSONDecodeError:
                print("✗ 缓存数据解析失败，继续正常流程")

        # 1. 检索相关文档
        relevant_docs = self.search_similar(query, k=k)

        if not relevant_docs:
            print("✗ 未找到相关文档")
            return {
                "answer": "未找到相关信息。",
                "sources": [],
                "cached": False
            }

        # 提取上下文
        context = "\n".join([doc.page_content for doc in relevant_docs])
        print(f"✓ 构建上下文，长度: {len(context)} 字符")

        # 2. 生成回答
        answer = self.generate_answer(query, context)

        response = {
            "answer": answer,
            "sources": [doc.page_content for doc in relevant_docs],
            "cached": False
        }

        # 缓存响应
        try:
            self.redis_client.setex(
                cache_key,
                self.cache_config["query_cache_ttl"],
                json.dumps(response)
            )
            print("✓ 响应已缓存")
        except Exception as e:
            print(f"✗ 缓存响应失败: {e}")

        return response

    def get_index_info(self):
        """获取索引信息"""
        try:
            # 检查索引是否存在
            info = self.redis_client.execute_command("FT.INFO", self.index_name)
            return info
        except Exception as e:
            print(f"获取索引信息失败: {e}")
            return None

    def clear_cache(self, cache_type: str = "all"):
        """清除缓存"""
        cache_types = []
        if cache_type in ["all", "query"]:
            cache_types.append("query")
        if cache_type in ["all", "vector"]:
            cache_types.append("vector")

        for ctype in cache_types:
            pattern = f"rag_{ctype}:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                print(f"✓ 已清除 {len(keys)} 个{ctype}缓存")
            else:
                print(f"✓ 没有找到{ctype}缓存需要清除")


# 使用示例
def main():
    """主函数示例"""
    try:
        # 初始化RAG服务
        rag_service = RedisRAGService(
            redis_host="localhost",
            embedding_model="nomic-embed-text",
            ollama_model="qwen3:0.6b"
        )

        # 添加示例文档
        documents = [
            "Python是一种高级编程语言，以简洁易读著称",
            "机器学习是人工智能的一个分支，专注于算法开发",
            "Redis是一种内存数据结构存储，用作数据库、缓存和消息代理",
            "Ollama是一个本地运行大型语言模型的工具"
        ]

        # 添加文档到知识库
        success = rag_service.add_documents(documents)

        if success:
            # 测试查询
            test_queries = [
                "Python有什么特点？",
                "什么是机器学习？",
                "Redis有什么用途？"
            ]

            for query in test_queries:
                print("\n" + "=" * 60)
                response = rag_service.rag_pipeline(query)
                print(f"问题: {query}")
                print(f"回答: {response['answer']}")
                if response['sources']:
                    print(f"参考来源: {len(response['sources'])} 个文档")
        else:
            print("文档添加失败，请检查服务状态")

    except Exception as e:
        print(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()