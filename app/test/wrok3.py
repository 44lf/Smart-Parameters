
from __future__ import annotations

import argparse
import math
import random
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from pymilvus import (
    connections,
    utility,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType,
)

# ---------------------------
# 全局配置
# ---------------------------

MILVUS_HOST = "127.0.0.1"
MILVUS_PORT = "19530"
MILVUS_ALIAS = "default"

random.seed(42)
np.random.seed(42)

# ---------------------------
# 简单日志存储（“运行日志接口”的底座）
# ---------------------------

@dataclass
class RunLog:
    run_id: str
    demo: str
    ts: str
    params: Dict[str, Any]
    timings_ms: Dict[str, float]
    result_summary: Dict[str, Any]

LOGS: List[RunLog] = []

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def log_run(demo: str, params: Dict[str, Any], timings_ms: Dict[str, float], result_summary: Dict[str, Any]) -> str:
    run_id = f"{demo}-{int(time.time()*1000)}-{random.randint(1000, 9999)}"
    LOGS.append(
        RunLog(
            run_id=run_id,
            demo=demo,
            ts=_now_iso(),
            params=params,
            timings_ms=timings_ms,
            result_summary=result_summary,
        )
    )
    return run_id

def print_recent_log(run_id: str) -> None:
    r = next((x for x in reversed(LOGS) if x.run_id == run_id), None)
    if not r:
        return
    print(f"\n[LOG] run_id={r.run_id} demo={r.demo} ts={r.ts}")
    print(f"[LOG] params={r.params}")
    print(f"[LOG] timings_ms={r.timings_ms}")
    print(f"[LOG] result_summary={r.result_summary}\n")


# ---------------------------
# Milvus 工具函数
# ---------------------------

def connect_milvus() -> None:
    connections.connect(alias=MILVUS_ALIAS, host=MILVUS_HOST, port=MILVUS_PORT)

def safe_drop_collection(name: str) -> None:
    try:
        if utility.has_collection(name, using=MILVUS_ALIAS):
            Collection(name, using=MILVUS_ALIAS).drop()
            print(f"[CLEAN] dropped collection: {name}")
    except Exception as e:
        print(f"[CLEAN] drop collection failed: {name}, err={e}")

def l2_normalize(v: List[float]) -> List[float]:
    arr = np.array(v, dtype=np.float32)
    n = float(np.linalg.norm(arr))
    if n == 0:
        return v
    return (arr / n).tolist()

def make_noisy(vec: List[float], noise: float) -> List[float]:
    return [x + random.uniform(-noise, noise) for x in vec]

def create_flat_index_and_load(coll: Collection, field: str, metric: str, partitions: Optional[List[str]] = None) -> None:
    # FLAT 不需要 params
    coll.create_index(field_name=field, index_params={"index_type": "FLAT", "metric_type": metric, "params": {}})
    if partitions:
        coll.load(partition_names=partitions)
    else:
        coll.load()

# ---------------------------
# 3a：多分区查询（图文）+ 合并噪声 [-0.06, 0.06] + mock 100 条
# ---------------------------

def demo_3a_partitions_merge_noise() -> None:
    t0 = time.time()

    collection_name = "q3a_unified_partitions"
    safe_drop_collection(collection_name)

    dim = 128
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=False),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dim),
        FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=16),
    ]
    schema = CollectionSchema(fields=fields, description="Q3a partitions: img_part/txt_part with merge-noise")
    coll = Collection(name=collection_name, schema=schema, using=MILVUS_ALIAS)

    # partitions
    coll.create_partition(partition_name="img_part")
    coll.create_partition(partition_name="txt_part")

    # mock 100: 50 img + 50 txt
    base_common = [random.random() for _ in range(dim // 2)]
    base_img_unique = [random.random() for _ in range(dim // 2)]
    base_txt_unique = [random.random() for _ in range(dim // 2)]
    base_img = base_common + base_img_unique
    base_txt = base_common + base_txt_unique

    def gen_related(base: List[float], count: int, vec_noise: float = 0.03) -> List[List[float]]:
        return [make_noisy(base, vec_noise) for _ in range(count)]

    img_ids = list(range(1000, 1050))
    txt_ids = list(range(2000, 2050))
    img_vecs = gen_related(base_img, 50, vec_noise=0.03)
    txt_vecs = gen_related(base_txt, 50, vec_noise=0.03)

    coll.insert([img_ids, img_vecs, ["image"] * 50], partition_name="img_part")
    coll.insert([txt_ids, txt_vecs, ["text"] * 50], partition_name="txt_part")
    coll.flush()

    t1 = time.time()
    create_flat_index_and_load(coll, field="vector", metric="L2", partitions=["img_part", "txt_part"])
    t2 = time.time()

    # query：贴近 common + unique 混合
    query = (
        [base_common[i] + random.uniform(-0.05, 0.05) for i in range(dim // 2)]
        + [((base_img_unique[i] + base_txt_unique[i]) / 2) + random.uniform(-0.05, 0.05) for i in range(dim // 2)]
    )

    top_k_each = 20
    final_top_k = 10

    # 分区分别检索
    s0 = time.time()
    res_img = coll.search(
        data=[query],
        anns_field="vector",
        param={"metric_type": "L2", "params": {}},
        limit=top_k_each,
        partition_names=["img_part"],
        output_fields=["category"],
    )
    res_txt = coll.search(
        data=[query],
        anns_field="vector",
        param={"metric_type": "L2", "params": {}},
        limit=top_k_each,
        partition_names=["txt_part"],
        output_fields=["category"],
    )
    s1 = time.time()

    # 应用层合并 + 合并噪声 [-0.06, 0.06]（加在 distance 上）
    merged: List[Dict[str, Any]] = []
    for hit in res_img[0]:
        noise = random.uniform(-0.06, 0.06)
        merged.append(
            {
                "id": hit.id,
                "category": hit.entity.get("category"),
                "distance": float(hit.distance),
                "noise": noise,
                "distance_noisy": float(hit.distance) + noise,
                "partition": "img_part",
            }
        )
    for hit in res_txt[0]:
        noise = random.uniform(-0.06, 0.06)
        merged.append(
            {
                "id": hit.id,
                "category": hit.entity.get("category"),
                "distance": float(hit.distance),
                "noise": noise,
                "distance_noisy": float(hit.distance) + noise,
                "partition": "txt_part",
            }
        )

    # L2：越小越相似，按 distance_noisy 升序
    merged.sort(key=lambda x: x["distance_noisy"])
    final = merged[:final_top_k]
    s2 = time.time()

    print("\n[Q3a] 合并(含噪声) Top10（L2 越小越相似，按 distance_noisy 排序）：")
    for i, item in enumerate(final, 1):
        print(
            f"rank={i} part={item['partition']} id={item['id']} cat={item['category']} "
            f"dist={item['distance']:.4f} noise={item['noise']:.4f} dist_noisy={item['distance_noisy']:.4f}"
        )

    run_id = log_run(
        demo="3a",
        params={
            "collection": collection_name,
            "partitions": ["img_part", "txt_part"],
            "mock_total": 100,
            "dim": dim,
            "metric": "L2",
            "top_k_each": top_k_each,
            "final_top_k": final_top_k,
            "merge_noise_range": [-0.06, 0.06],
        },
        timings_ms={
            "insert_flush": (t1 - t0) * 1000,
            "index_load": (t2 - t1) * 1000,
            "search_partitions": (s1 - s0) * 1000,
            "merge_sort": (s2 - s1) * 1000,
            "total": (time.time() - t0) * 1000,
        },
        result_summary={
            "final_top_ids": [x["id"] for x in final],
            "final_top_partitions": [x["partition"] for x in final],
            "noise_min": min(x["noise"] for x in final) if final else None,
            "noise_max": max(x["noise"] for x in final) if final else None,
        },
    )
    print_recent_log(run_id)

    coll.release()

# ---------------------------
# 3b：多向量检索（dim=16）+ 返回20条 + 权重0.75/0.25 + RRFRanker
# ---------------------------

def rrf_fuse(
    ranked_ids_a: List[int],
    ranked_ids_b: List[int],
    w_a: float = 0.75,
    w_b: float = 0.25,
    k: int = 60,
) -> List[Tuple[int, float]]:
    """
    RRF: score(id) = w_a/(k+rank_a) + w_b/(k+rank_b)
    rank 从 1 开始；不在列表则忽略该项贡献。
    """
    scores: Dict[int, float] = {}
    for rank, _id in enumerate(ranked_ids_a, start=1):
        scores[_id] = scores.get(_id, 0.0) + w_a / (k + rank)
    for rank, _id in enumerate(ranked_ids_b, start=1):
        scores[_id] = scores.get(_id, 0.0) + w_b / (k + rank)
    # 分数越大越好
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

def demo_3b_multi_vector_rrf() -> None:
    t0 = time.time()

    collection_name = "q3b_multi_vector_rrf"
    safe_drop_collection(collection_name)

    dim = 16
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=False),
        FieldSchema(name="vec_a", dtype=DataType.FLOAT_VECTOR, dim=dim),
        FieldSchema(name="vec_b", dtype=DataType.FLOAT_VECTOR, dim=dim),
        FieldSchema(name="tag", dtype=DataType.VARCHAR, max_length=16),
    ]
    schema = CollectionSchema(fields=fields, description="Q3b: two vectors + RRF fusion")
    coll = Collection(name=collection_name, schema=schema, using=MILVUS_ALIAS)

    # mock 数据：让部分样本在 A 更相似，部分在 B 更相似
    n = 200
    base_a = np.random.rand(dim).astype(np.float32).tolist()
    base_b = np.random.rand(dim).astype(np.float32).tolist()

    ids = list(range(1, n + 1))
    vec_a_list: List[List[float]] = []
    vec_b_list: List[List[float]] = []
    tags: List[str] = []

    for i in range(n):
        # 让前 120 条更贴近 A，后 120 条更贴近 B（中间会混）
        if i < 120:
            va = make_noisy(base_a, 0.03)
            vb = make_noisy(np.random.rand(dim).astype(np.float32).tolist(), 0.20)
            tag = "A_like"
        else:
            va = make_noisy(np.random.rand(dim).astype(np.float32).tolist(), 0.20)
            vb = make_noisy(base_b, 0.03)
            tag = "B_like"
        vec_a_list.append(va)
        vec_b_list.append(vb)
        tags.append(tag)

    coll.insert([ids, vec_a_list, vec_b_list, tags])
    coll.flush()

    t1 = time.time()
    # 用 COSINE 更符合“向量相似”，也更常见；为了稳，做归一化更严谨，但这里用 FLAT+COSINE 也能跑
    # 如果你希望更稳，可把插入和 query 都做 l2_normalize。
    create_flat_index_and_load(coll, field="vec_a", metric="COSINE")
    create_flat_index_and_load(coll, field="vec_b", metric="COSINE")
    t2 = time.time()

    # query：分别贴近 base_a/base_b
    q_a = make_noisy(base_a, 0.02)
    q_b = make_noisy(base_b, 0.02)

    top_k_each = 60
    final_top_k = 20
    w_a, w_b = 0.75, 0.25
    rrf_k = 60

    s0 = time.time()
    res_a = coll.search(
        data=[q_a],
        anns_field="vec_a",
        param={"metric_type": "COSINE", "params": {}},
        limit=top_k_each,
        output_fields=["tag"],
    )
    res_b = coll.search(
        data=[q_b],
        anns_field="vec_b",
        param={"metric_type": "COSINE", "params": {}},
        limit=top_k_each,
        output_fields=["tag"],
    )
    s1 = time.time()

    ranked_a = [hit.id for hit in res_a[0]]
    ranked_b = [hit.id for hit in res_b[0]]

    fused = rrf_fuse(ranked_a, ranked_b, w_a=w_a, w_b=w_b, k=rrf_k)
    top20 = fused[:final_top_k]

    print("\n[Q3b] RRF 融合 Top20（score 越大越好）：")
    for i, (_id, score) in enumerate(top20, 1):
        print(f"rank={i} id={_id} rrf_score={score:.6f}")

    run_id = log_run(
        demo="3b",
        params={
            "collection": collection_name,
            "dim": dim,
            "metric": "COSINE",
            "top_k_each": top_k_each,
            "final_top_k": final_top_k,
            "weights": {"vec_a": w_a, "vec_b": w_b},
            "rrf_k": rrf_k,
        },
        timings_ms={
            "insert_flush": (t1 - t0) * 1000,
            "index_load": (t2 - t1) * 1000,
            "search_two_vectors": (s1 - s0) * 1000,
            "rrf_fuse": (time.time() - s1) * 1000,
            "total": (time.time() - t0) * 1000,
        },
        result_summary={
            "top20_ids": [x[0] for x in top20],
            "top20_scores": [round(x[1], 6) for x in top20],
        },
    )
    print_recent_log(run_id)

    coll.release()

# ---------------------------
# 3c：衰减排序器：时间倒序前3天的
# ---------------------------

def demo_3c_time_decay_last_3_days() -> None:
    t0 = time.time()

    collection_name = "q3c_time_decay"
    safe_drop_collection(collection_name)

    dim = 32
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=False),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dim),
        FieldSchema(name="ts", dtype=DataType.INT64),  # epoch seconds
    ]
    schema = CollectionSchema(fields=fields, description="Q3c: vector search + time decay rerank (last 3 days)")
    coll = Collection(name=collection_name, schema=schema, using=MILVUS_ALIAS)

    # mock：生成最近 7 天数据（便于做“最近3天”过滤）
    now = datetime.now(timezone.utc)
    n = 400

    base = np.random.rand(dim).astype(np.float32).tolist()
    ids = list(range(1, n + 1))
    vecs: List[List[float]] = []
    tss: List[int] = []

    for i in range(n):
        # 随机分布在过去 0~7 天
        age_hours = random.uniform(0, 7 * 24)
        ts = int((now - timedelta(hours=age_hours)).timestamp())
        # 向量与 base 有一定相关（噪声可调）
        v = make_noisy(base, 0.10)
        vecs.append(v)
        tss.append(ts)

    coll.insert([ids, vecs, tss])
    coll.flush()

    t1 = time.time()
    create_flat_index_and_load(coll, field="vector", metric="L2")
    t2 = time.time()

    # 查询向量：贴近 base
    query = make_noisy(base, 0.05)

    # 先向量检索取候选，再做“最近3天 + 衰减 rerank”
    candidate_k = 120
    final_top_k = 20

    s0 = time.time()
    res = coll.search(
        data=[query],
        anns_field="vector",
        param={"metric_type": "L2", "params": {}},
        limit=candidate_k,
        output_fields=["ts"],
    )
    s1 = time.time()

    # 最近 3 天窗口
    window_start = now - timedelta(days=3)
    window_start_ts = int(window_start.timestamp())

    # 衰减：按“年龄(小时)”指数衰减；lambda 越大越偏新
    decay_lambda_per_hour = 0.08  # 可调；约 12.5 小时衰减 e^-1
    def sim_from_l2(dist: float) -> float:
        # 把 L2 distance 转成 (0,1] 相似度，便于乘衰减
        return 1.0 / (1.0 + dist)

    reranked: List[Dict[str, Any]] = []
    for hit in res[0]:
        ts = int(hit.entity.get("ts"))
        if ts < window_start_ts:
            continue  # 只保留最近3天
        age_h = max(0.0, (now.timestamp() - ts) / 3600.0)
        decay = math.exp(-decay_lambda_per_hour * age_h)
        sim = sim_from_l2(float(hit.distance))
        final_score = sim * decay

        reranked.append(
            {
                "id": hit.id,
                "ts": ts,
                "age_hours": age_h,
                "distance": float(hit.distance),
                "sim": sim,
                "decay": decay,
                "final_score": final_score,
            }
        )

    # final_score 越大越好
    reranked.sort(key=lambda x: x["final_score"], reverse=True)
    top = reranked[:final_top_k]
    s2 = time.time()

    print("\n[Q3c] 最近3天 + 衰减排序 Top20（final_score 越大越好）：")
    for i, item in enumerate(top, 1):
        dt = datetime.fromtimestamp(item["ts"], tz=timezone.utc).isoformat()
        print(
            f"rank={i} id={item['id']} ts={dt} age_h={item['age_hours']:.1f} "
            f"dist={item['distance']:.4f} sim={item['sim']:.4f} "
            f"decay={item['decay']:.4f} final={item['final_score']:.6f}"
        )

    run_id = log_run(
        demo="3c",
        params={
            "collection": collection_name,
            "dim": dim,
            "metric": "L2",
            "candidate_k": candidate_k,
            "final_top_k": final_top_k,
            "time_window_days": 3,
            "decay_lambda_per_hour": decay_lambda_per_hour,
        },
        timings_ms={
            "insert_flush": (t1 - t0) * 1000,
            "index_load": (t2 - t1) * 1000,
            "search_candidates": (s1 - s0) * 1000,
            "filter_decay_sort": (s2 - s1) * 1000,
            "total": (time.time() - t0) * 1000,
        },
        result_summary={
            "window_start_utc": window_start.isoformat(),
            "returned": len(top),
            "top_ids": [x["id"] for x in top],
        },
    )
    print_recent_log(run_id)

    coll.release()

# ---------------------------
# 可选：FastAPI 日志接口
# ---------------------------

def serve_logs_api(host: str = "127.0.0.1", port: int = 8001) -> None:
    try:
        from fastapi import FastAPI
        import uvicorn
    except Exception:
        raise SystemExit("缺少 fastapi/uvicorn：pip install fastapi uvicorn")

    app = FastAPI(title="Milvus Q3 Logs")

    @app.get("/logs")
    def get_logs() -> List[Dict[str, Any]]:
        return [asdict(x) for x in LOGS]

    @app.get("/logs/{run_id}")
    def get_log(run_id: str) -> Dict[str, Any]:
        r = next((x for x in LOGS if x.run_id == run_id), None)
        return asdict(r) if r else {"error": "not found", "run_id": run_id}

    uvicorn.run(app, host=host, port=port, log_level="info")


# ---------------------------
# main
# ---------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", choices=["3a", "3b", "3c", "all"], default="all")
    parser.add_argument("--serve", action="store_true", help="start FastAPI logs server on :8001")
    args = parser.parse_args()

    connect_milvus()

    if args.demo in ("3a", "all"):
        demo_3a_partitions_merge_noise()
    if args.demo in ("3b", "all"):
        demo_3b_multi_vector_rrf()
    if args.demo in ("3c", "all"):
        demo_3c_time_decay_last_3_days()

    if args.serve:
        serve_logs_api()

    connections.disconnect(MILVUS_ALIAS)

if __name__ == "__main__":
    main()