
import hashlib

import chromadb


# 创建持久化 Chroma 客户端
client = chromadb.PersistentClient(
    path="./chroma_db"
)

# 获取或创建知识库
collection = client.get_or_create_collection(
    name="study_notes"
)


def add_documents(chunks, embeddings):
    """
    将文本片段、向量和元数据写入 ChromaDB。
    使用稳定 ID，避免不同 PDF 的 chunk ID 冲突。
    """

    if len(chunks) != len(embeddings):
        raise ValueError(
            "chunks 数量必须与 embeddings 数量一致"
        )

    if not chunks:
        print("没有可写入的文本片段")
        return

    documents = []
    metadatas = []
    ids = []

    for chunk in chunks:
        text = chunk["text"]
        metadata = chunk["metadata"]

        documents.append(text)
        metadatas.append(metadata)

        source = metadata.get("source", "unknown")
        page = metadata.get("page", 0)
        unique_text = f"{source}|{page}|{text}"

        chunk_id = hashlib.sha256(
            unique_text.encode("utf-8")
        ).hexdigest()

        ids.append(chunk_id)

    collection.upsert(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )

    print(f"本次写入或更新 {len(ids)} 个文本片段")


def document_exists(filename):
    """
    检查指定 PDF 是否已经存在于知识库中。
    """

    result = collection.get(
        where={"source": filename},
        limit=1
    )

    return len(result["ids"]) > 0
