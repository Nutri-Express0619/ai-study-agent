
import os
import hashlib

from rag.loader import load_document
from rag.splitter import split_text
from rag.embedding import get_embedding
from rag.vectorstore import collection
from agent.logger import log


def rebuild_document(filename):
    """重新构建指定 PDF 的向量记录，尽量降低更新失败风险。"""

    pdf_path = os.path.join("./data", filename)

    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(
            f"PDF 文件不存在：{os.path.abspath(pdf_path)}"
        )

    # 1. 读取、切分文档
    documents = load_document(pdf_path)
    chunks = split_text(documents)

    if not chunks:
        raise ValueError(f"{filename} 没有有效文本片段，取消更新")

    # 2. 生成新向量
    embeddings = []

    for index, chunk in enumerate(chunks, start=1):
        log("生成 Embedding", {
            "文件": filename,
            "进度": f"{index}/{len(chunks)}"
        })
        embeddings.append(get_embedding(chunk["text"]))

    if len(chunks) != len(embeddings):
        raise ValueError("文本片段与向量数量不一致")

    dimensions = {len(vector) for vector in embeddings}
    if len(dimensions) != 1:
        raise ValueError(f"新向量维度不一致：{dimensions}")

    # 3. 保存旧记录，供发生异常时恢复
    old_data = collection.get(
        where={"source": filename},
        include=["documents", "metadatas", "embeddings"]
    )

    old_ids = old_data["ids"]
    old_documents = old_data["documents"] or []
    old_metadatas = old_data["metadatas"] or []
    old_embeddings = old_data["embeddings"]

    if old_ids and old_embeddings is None:
        raise RuntimeError("无法读取旧向量，取消更新以保护现有数据")

    # 4. 为新片段生成稳定 ID
    new_ids = []

    for chunk in chunks:
        metadata = chunk["metadata"]
        unique_text = (
            f"{metadata.get('source', 'unknown')}|"
            f"{metadata.get('page', 0)}|"
            f"{chunk['text']}"
        )
        new_ids.append(
            hashlib.sha256(unique_text.encode("utf-8")).hexdigest()
        )

    if len(new_ids) != len(set(new_ids)):
        raise RuntimeError("新片段出现重复 ID，取消更新")

    # 5. 检查 ID 是否属于其他文件
    existing = collection.get(
        ids=new_ids,
        include=["metadatas"]
    )

    for existing_id, metadata in zip(
        existing["ids"], existing["metadatas"] or []
    ):
        if metadata.get("source") != filename:
            raise RuntimeError(
                f"新片段 ID 与其他文件冲突：{existing_id}"
            )

    # 新旧 ID 有重合时，先保存其旧内容；若失败可恢复
    old_by_id = {
        item_id: {
            "document": old_documents[i],
            "metadata": old_metadatas[i],
            "embedding": old_embeddings[i].tolist()
        }
        for i, item_id in enumerate(old_ids)
    }

    # 6. 写入新片段
    collection.upsert(
        ids=new_ids,
        documents=[chunk["text"] for chunk in chunks],
        metadatas=[chunk["metadata"] for chunk in chunks],
        embeddings=embeddings
    )

    # 7. 验证每个新 ID、文本和元数据
    verified = collection.get(
        ids=new_ids,
        include=["documents", "metadatas"]
    )

    verified_by_id = {
        item_id: (document, metadata)
        for item_id, document, metadata in zip(
            verified["ids"],
            verified["documents"] or [],
            verified["metadatas"] or []
        )
    }

    expected_by_id = {
        item_id: (chunk["text"], chunk["metadata"])
        for item_id, chunk in zip(new_ids, chunks)
    }

    if verified_by_id != expected_by_id:
        # 恢复新写入覆盖的旧 ID
        for item_id in set(new_ids) & set(old_ids):
            old = old_by_id[item_id]
            collection.upsert(
                ids=[item_id],
                documents=[old["document"]],
                metadatas=[old["metadata"]],
                embeddings=[old["embedding"]]
            )

        # 删除本次新增、原先不存在的 ID
        added_ids = list(set(new_ids) - set(old_ids))
        if added_ids:
            collection.delete(ids=added_ids)

        raise RuntimeError("新片段验证失败，已尝试回滚")

    # 8. 删除不再使用的旧 ID
    obsolete_ids = list(set(old_ids) - set(new_ids))

    try:
        if obsolete_ids:
            collection.delete(ids=obsolete_ids)
    except Exception:
        # 恢复旧记录
        collection.upsert(
            ids=old_ids,
            documents=old_documents,
            metadatas=old_metadatas,
            embeddings=old_embeddings.tolist()
        )

        # 删除本次新增的 ID
        added_ids = list(set(new_ids) - set(old_ids))
        if added_ids:
            collection.delete(ids=added_ids)

        raise

    # 9. 输出结果
    final_data = collection.get(
        where={"source": filename},
        include=["metadatas"]
    )

    print(f"\n文件更新完成：{filename}")
    print(f"旧片段数量：{len(old_ids)}")
    print(f"新片段数量：{len(final_data['ids'])}")
    print(f"清理旧记录数量：{len(obsolete_ids)}")


if __name__ == "__main__":
    rebuild_document("rag_learning_notes.pdf")
