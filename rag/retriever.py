
from rag.embedding import get_embedding
from rag.vectorstore import collection
from agent.logger import log


def search(query, top_k=5):
    """
    根据问题进行向量检索。

    保持返回值为文本列表，兼容现有 Agent 调用。
    同时输出来源、页码和距离，便于调试检索质量。
    """

    # 1. 问题向量化
    query_embedding = get_embedding(query)

    # 2. 向量数据库搜索
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    documents = results["documents"][0] or []
    metadatas = results["metadatas"][0] or []
    distances = results["distances"][0] or []

    # 3. 整理调试信息
    debug_results = []

    for index, document in enumerate(documents):
        metadata = (
            metadatas[index]
            if index < len(metadatas) and metadatas[index]
            else {}
        )

        distance = (
            distances[index]
            if index < len(distances)
            else None
        )

        debug_results.append({
            "rank": index + 1,
            "source": metadata.get("source", "unknown"),
            "page": metadata.get("page", "unknown"),
            "distance": distance,
            "text": document
        })

    log("RAG检索问题", query)
    log("RAG检索结果详情", debug_results)

    # 4. 仍然只返回文本，保持原有接口不变
    return documents


if __name__ == "__main__":
    question = input("请输入问题：")
    results = search(question)
    log("测试检索结果", results)
