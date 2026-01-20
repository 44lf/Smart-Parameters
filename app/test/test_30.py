from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Protocol


@dataclass
class Document:
    page_content: str
    metadata: Dict


class ChunkingStrategy(Protocol):
    """Protocol：结构化约束（鸭子类型）。不要求继承，只要方法“长得一样”即可。"""

    def split_document(self, docs: List[Document], doc_path: str, minio_metadata: Dict) -> List[Document]:
        ...


class FixedWindowChunker:
    """不继承 ChunkingStrategy，但因为方法签名匹配，所以可以当作 ChunkingStrategy 用。"""

    def __init__(self, chunk_size: int = 10, chunk_overlap: int = 3):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be >=0 and < chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_document(self, docs: List[Document], doc_path: str, minio_metadata: Dict) -> List[Document]:
        if not docs:
            raise ValueError(f"empty docs: {doc_path}")
        text = docs[0].page_content or ""
        meta = dict(docs[0].metadata or {})
        meta.update({"source": doc_path, "minio": minio_metadata})

        chunks: List[Document] = []
        start = 0
        n = len(text)
        while start < n:
            end = min(start + self.chunk_size, n)
            chunk_text = text[start:end]
            chunk_meta = dict(meta)
            chunk_meta.update({"start": start, "end": end})
            chunks.append(Document(page_content=chunk_text, metadata=chunk_meta))
            if end == n:
                break
            start = max(0, end - self.chunk_overlap)
        return chunks


def run_pipeline(strategy: ChunkingStrategy, docs: List[Document]) -> None:
    out = strategy.split_document(docs, doc_path="demo.txt", minio_metadata={"bucket": "x"})
    print("chunks:", len(out))
    for i, d in enumerate(out[:5]):
        print(i, repr(d.page_content), d.metadata)


def main() -> None:
    docs = [Document(page_content="这是一个用于演示 Protocol 的测试文本。我们将它切成多个块。", metadata={"lang": "zh"})]

    # 注意：FixedWindowChunker 没有继承 ChunkingStrategy，但依然能被 run_pipeline 接收并运行
    print("Protocol pipeline run (should succeed):")
    run_pipeline(FixedWindowChunker(chunk_size=10, chunk_overlap=3), docs)


if __name__ == "__main__":
    main()
