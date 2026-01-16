from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType
import random

random.seed(42)

connections.connect(alias="default", host="127.0.0.1", port="19530")

collection_name = "unified_collection"

# drop old
try:
    Collection(collection_name).drop()
    print(f"已删除旧集合 {collection_name}")
except Exception:
    pass

dim = 128
schema = CollectionSchema(fields=[
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=False),
    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dim),
    FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=50),
])

collection = Collection(name=collection_name, schema=schema)
print(f"已创建新集合 {collection_name}")

# create partitions (Milvus 2.x)
partition_image = collection.create_partition(partition_name="image_partition")
partition_text = collection.create_partition(partition_name="text_partition")
print(f"已创建分区: {partition_image.name}, {partition_text.name}")

def generate_related_vectors(base, count, noise=0.05):
    return [[x + random.uniform(-noise, noise) for x in base] for _ in range(count)]

base_common = [random.random() for _ in range(dim // 2)]
base_image_unique = [random.random() for _ in range(dim // 2)]
base_text_unique = [random.random() for _ in range(dim // 2)]

base_image_vector = base_common + base_image_unique
base_text_vector = base_common + base_text_unique

# insert into partitions by partition_name
image_data = [
    [i for i in range(1000, 1010)],
    generate_related_vectors(base_image_vector, 10),
    ["image"] * 10,
]
collection.insert(image_data, partition_name="image_partition")

text_data = [
    [i for i in range(2000, 2010)],
    generate_related_vectors(base_text_vector, 10),
    ["text"] * 10,
]
collection.insert(text_data, partition_name="text_partition")

collection.flush()

print(f"总数据量: {collection.num_entities} 条（预期20条）")

# create index
index_params = {"index_type": "FLAT", "metric_type": "L2", "params": {}}
collection.create_index(field_name="vector", index_params=index_params)

# load (choose one)
# 方案A：加载整个 collection（最稳）
# collection.load()

# 方案B：只加载指定分区（节省内存，注意用 partition_names 关键字）
collection.load(partition_names=["image_partition", "text_partition"])

print("索引创建完成，已加载")

# 7.1 search in single partition
query_image_vector = [base_image_vector[i] + random.uniform(-0.05, 0.05) for i in range(dim)]
results_image = collection.search(
    data=[query_image_vector],
    anns_field="vector",
    param={"metric_type": "L2", "params": {}},
    limit=5,
    partition_names=["image_partition"],
    output_fields=["id", "category"],
)
print("\n在 'image_partition' 分区中的搜索结果:")
for hit in results_image[0]:
    print(f"ID: {hit.entity.get('id')}, Category: {hit.entity.get('category')}, 距离: {hit.distance:.4f}")

# 7.2 combined search across all loaded partitions (no partition_names -> search all)
query_combined_vector = (
    [base_common[i] + random.uniform(-0.05, 0.05) for i in range(dim // 2)] +
    [((base_image_unique[i] + base_text_unique[i]) / 2) + random.uniform(-0.05, 0.05) for i in range(dim // 2)]
)

results_combined = collection.search(
    data=[query_combined_vector],
    anns_field="vector",
    param={"metric_type": "L2", "params": {}},
    limit=10,
    output_fields=["id", "category"],
)

print("\n在所有已加载分区中的合并搜索结果:")
if results_combined and len(results_combined[0]) > 0:
    for hit in results_combined[0]:
        print(f"ID: {hit.entity.get('id')}, Category: {hit.entity.get('category')}, 距离: {hit.distance:.4f}")
else:
    print("  未找到匹配结果（检查是否 load 成功、是否插入成功）")

collection.release()
