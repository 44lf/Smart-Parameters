from pymilvus import MilvusClient

client = MilvusClient("milvus_demo.db")

if client.has_collection('demo-collection'):
    client.drop_collection("demo-collection")
client.create_collection(
    collection_name="demo_collection",
    demension=768
)

data = [
    {"id": i, "vector": [0.1] * 768, "color": "red" if i % 2 == 0 else "blue"}
    for i in range(10)
]
res = client.insert(collection_name="demo_collection", data=data)
print(res)

search_res = client.search(
    collection_name="demo_collection",
    data=[[0.1] * 768], # 查询向量
    filter="color == 'red'", # 过滤条件
    limit=3,
    output_fields=["color"]
)
print(search_res)

