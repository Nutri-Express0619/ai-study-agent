
def split_text(
    documents,
    chunk_size=500,
    overlap=100
):
    """
    将文档切分为文本片段，并保留原始元数据。

    参数：
        documents: load_document() 返回的文档列表
        chunk_size: 每个文本片段的最大字符数
        overlap: 相邻片段之间重叠的字符数

    返回：
        [{"text": ..., "metadata": ...}, ...]
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size 必须大于 0")

    if overlap < 0:
        raise ValueError("overlap 不能小于 0")

    if overlap >= chunk_size:
        raise ValueError("overlap 必须小于 chunk_size")

    chunks = []

    for document in documents:
        text = document.get("text") or ""
        metadata = document["metadata"]

        if not text.strip():
            continue

        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end]

            if chunk_text.strip():
                chunks.append({
                    "text": chunk_text,
                    "metadata": metadata.copy()
                })

            if end >= len(text):
                break

            start = end - overlap

    return chunks
