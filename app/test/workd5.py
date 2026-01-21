import os
import time
import glob
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List

# --- 1. 数据结构定义 ---
@dataclass
class Document:
    id: str         # 文件名作为ID
    content: str    # 文件内容
    metadata: dict  # 比如文件大小、修改时间

# --- 2. 辅助函数：读取本地文件 ---
def load_documents_from_folder(folder_path: str) -> List[Document]:
    """读取指定文件夹下的所有 txt/md 文件"""
    docs = []
    # 获取文件夹下所有文件 (这里以 txt 和 md 为例)
    # 如果你想读取所有文件，可以使用 os.listdir
    file_patterns = [f"{folder_path}/*.txt", f"{folder_path}/*.md"]

    files = []
    for pattern in file_patterns:
        files.extend(glob.glob(pattern))

    if not files:
        print(f"⚠️  警告：在 '{folder_path}' 下没有找到 .txt 或 .md 文件！")
        return []

    print(f"📂 发现 {len(files)} 个文件，准备加载...")

    for file_path in files:
        try:
            filename = os.path.basename(file_path)
            # 使用 utf-8 读取，忽略无法解码的字符以防止报错
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # 获取文件大小作为元数据示例
            file_size = os.path.getsize(file_path)

            docs.append(Document(
                id=filename,
                content=content,
                metadata={"size": file_size, "path": file_path}
            ))
        except Exception as e:
            print(f"❌ 读取文件 {file_path} 失败: {e}")

    return docs

# --- 3. 切片核心逻辑 (保持不变) ---
def split_text(text: str, chunk_size: int = 500) -> List[str]:
    """简单的按长度切片"""
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def process_single_document(doc: Document) -> dict:
    """单个文档的处理任务"""
    start_time = time.time()

    # 执行切片
    chunks = split_text(doc.content)

    # 模拟稍微复杂一点的处理（例如清洗数据）
    # time.sleep(0.01)

    return {
        "doc_id": doc.id,
        "chunk_count": len(chunks),
        "file_size": doc.metadata.get("size", 0),
        "time_taken": time.time() - start_time
    }

# --- 4. 并行处理控制器 (保持不变) ---
def process_documents_parallel(docs: List[Document], use_multiprocessing=True):
    results = []
    Executor = ProcessPoolExecutor if use_multiprocessing else ThreadPoolExecutor
    # 自动获取 CPU 核心数，保留 1 个核心给系统
    worker_count = max(1, os.cpu_count() - 1)

    print(f"🚀 开始处理 {len(docs)} 个文档，使用模式: {'多进程' if use_multiprocessing else '多线程'} (Workers: {worker_count})...")

    start_total = time.time()

    with Executor(max_workers=worker_count) as executor:
        future_to_doc = {executor.submit(process_single_document, doc): doc for doc in docs}

        for future in as_completed(future_to_doc):
            try:
                data = future.result()
                results.append(data)
                # 打印进度
                print(f"   ✅ [{data['doc_id']}] 完成: {data['chunk_count']} 个切片 ({data['time_taken']:.4f}s)")
            except Exception as exc:
                print(f"   ❌ 处理异常: {exc}")

    print(f"🏁 全部完成! 总耗时: {time.time() - start_total:.2f}s")
    return results

# --- 5. 运行入口 ---
if __name__ == "__main__":
    # >>>>> 设置：在这里修改你的文件夹路径 <<<<<
    # 建议你在当前代码目录下创建一个叫 test_files 的文件夹，把文件丢进去
    MY_FOLDER_PATH = "docs"

    # 1. 如果文件夹不存在，自动创建，方便你测试
    if not os.path.exists(MY_FOLDER_PATH):
        os.makedirs(MY_FOLDER_PATH)
        print(f"提示：文件夹 '{MY_FOLDER_PATH}' 不存在，已自动创建。请往里面放入 .txt 文件后再次运行。")
        # 创建一个测试文件，防止空跑
        with open(os.path.join(MY_FOLDER_PATH, "demo.txt"), "w", encoding="utf-8") as f:
            f.write("这是一个自动生成的测试文件。" * 100)

    # 2. 加载真实文件
    my_docs = load_documents_from_folder(MY_FOLDER_PATH)

    # 3. 如果有文件，开始运行
    if my_docs:
        # 纯文本切分建议使用 True (多进程)
        process_documents_parallel(my_docs, use_multiprocessing=True)