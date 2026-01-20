from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Document:
    page_content: str
    metadata: Dict


class ChunkingStrategy(ABC):
    """ABC：运行时强约束。子类不实现抽象方法 -> 不能实例化"""

    @abstractmethod
    def split_document(self, docs: List[Document], doc_path: str, minio_metadata: Dict) -> List[Document]:
        """子类必须实现"""
        raise NotImplementedError


class JiebaLikeChunkingStrategy(ChunkingStrategy):
    """一个具体实现：按固定窗口切分（不依赖 jieba/langchain，保证可跑通）"""

    def __init__(self, chunk_size: int = 20, chunk_overlap: int = 5):
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



def main() -> None:
    docs = [Document(page_content="这是一个用于演示 ABC 的测试文本。我们将它切成多个块。", metadata={"lang": "zh"})]

    print("1) Instantiate concrete implementation (should succeed)")
    s = JiebaLikeChunkingStrategy(chunk_size=10, chunk_overlap=3)
    out = s.split_document(docs, doc_path="demo.txt", minio_metadata={"bucket": "x"})
    print("chunks:", len(out))
    for i, d in enumerate(out[:5]):
        print(i, repr(d.page_content), d.metadata)

    print("\n2) Instantiate BrokenChunker (should fail)")



if __name__ == "__main__":
    main()
