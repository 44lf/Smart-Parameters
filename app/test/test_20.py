from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math


# -----------------------------
# 数据结构：一条候选 chunk
# -----------------------------
@dataclass
class Candidate:
    chunk_id: str
    text: str
    scores: Dict[str, float] = field(default_factory=dict)  # 各路原始分数：{"vector":..., "bm25":..., "rule":...}
    meta: Dict[str, object] = field(default_factory=dict)   # 可放 doc_id、file_id 等


# -----------------------------
# 归一化：min-max（本批次 topK 内重标定）
# - 对每个通道单独做：把分数压到 [0,1]
# - 支持 "higher_is_better" 和 "lower_is_better"(比如距离)
# -----------------------------
def minmax_normalize(
    values: List[float],
    higher_is_better: bool = True,
    eps: float = 1e-12
) -> List[float]:
    if not values:
        return []

    vmin, vmax = min(values), max(values)
    if abs(vmax - vmin) < eps:
        # 全一样：给全 1.0（或全 0.0 都行，取决于你希望“全相等时是否保留贡献”）
        return [1.0 for _ in values]

    out = []
    for v in values:
        n = (v - vmin) / (vmax - vmin)
        if not higher_is_better:
            n = 1.0 - n  # 距离越小越好 -> 反转
        out.append(n)
    return out


# -----------------------------
# 融合：归一化 + 加权求和
# - channel_cfg：定义每路是相似度还是距离、以及默认缺失分数
# - weights：各路权重（可先都设 1.0）
# -----------------------------
def normalize_and_fuse(
    pool: List[Candidate],
    channel_cfg: Dict[str, Dict[str, object]],
    weights: Dict[str, float],
    missing_value: float = 0.0
) -> List[Tuple[Candidate, float, Dict[str, float]]]:
    """
    返回：[(candidate, fused_score, per_channel_norm_scores), ...] 按 fused_score 降序
    """
    # 1) 收集每个通道的分数列表（按 pool 顺序对齐）
    channel_raw: Dict[str, List[float]] = {}
    for ch in channel_cfg.keys():
        channel_raw[ch] = []
        for c in pool:
            channel_raw[ch].append(float(c.scores.get(ch, missing_value)))

    # 2) 各通道分别归一化
    channel_norm: Dict[str, List[float]] = {}
    for ch, vals in channel_raw.items():
        higher_is_better = bool(channel_cfg[ch].get("higher_is_better", True))
        channel_norm[ch] = minmax_normalize(vals, higher_is_better=higher_is_better)

    # 3) 加权融合
    fused: List[Tuple[Candidate, float, Dict[str, float]]] = []
    for i, c in enumerate(pool):
        per_ch = {ch: channel_norm[ch][i] for ch in channel_cfg.keys()}
        score = 0.0
        for ch, s_norm in per_ch.items():
            w = float(weights.get(ch, 1.0))
            score += w * s_norm
        fused.append((c, score, per_ch))

    # 4) 排序（粗排）
    fused.sort(key=lambda x: x[1], reverse=True)
    return fused


# -----------------------------
# 示例：3 路召回合并后的候选池
# - vector：假设是“距离”（越小越好）
# - bm25：分数越大越好
# - rule：规则命中给 1.0，不命中缺失
# -----------------------------
if __name__ == "__main__":
    pool = [
        Candidate(chunk_id="c1", text="Milvus using 参数用于指定连接别名", scores={"vector": 0.21, "bm25": 7.2, "rule": 1.0}),
        Candidate(chunk_id="c2", text="connections.connect 的 alias 与 using 的关系", scores={"vector": 0.18, "bm25": 3.1}),
        Candidate(chunk_id="c3", text="Milvus database / collection / partition 基础概念", scores={"vector": 0.35, "bm25": 8.5}),
        Candidate(chunk_id="c4", text="FastAPI lifespan 用法", scores={"bm25": 6.0}),  # 没有向量路命中（或被过滤掉）
        Candidate(chunk_id="c5", text="Milvus 过滤 expr 写法示例", scores={"vector": 0.24, "rule": 1.0}),
    ]

    # 每路分数的“方向”
    channel_cfg = {
        "vector": {"higher_is_better": False},  # 距离越小越好
        "bm25": {"higher_is_better": True},
        "rule": {"higher_is_better": True},
    }

    # 权重：起步可都 1.0；也可以让语义召回更重要
    weights = {
        "vector": 1.2,
        "bm25": 1.0,
        "rule": 0.4,
    }

    fused = normalize_and_fuse(pool, channel_cfg=channel_cfg, weights=weights)

    # 打印 topN（粗排结果）
    top_n = 5
    for rank, (c, score, per_ch) in enumerate(fused[:top_n], start=1):
        print(
            f"#{rank} chunk_id={c.chunk_id} fused={score:.4f} "
            f"norm={ {k: round(v, 3) for k, v in per_ch.items()} } "
            f"text={c.text}"
        )
