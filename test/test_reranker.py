
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

MODEL_DIR = "/mnt/d/model_cache/modelscope/bge-reranker-base"

# 加载分词器和 ONNX 模型
tokenizer = Tokenizer.from_file(f"{MODEL_DIR}/tokenizer.json")
session = ort.InferenceSession(
    f"{MODEL_DIR}/onnx/model.onnx",
    providers=["CPUExecutionProvider"],
)

def score(query: str, document: str) -> float:
    """计算问题与候选文本的相关性分数。"""
    encoded = tokenizer.encode(
        query,
        pair=document,
    )

    input_ids = np.array([encoded.ids], dtype=np.int64)
    attention_mask = np.array(
        [encoded.attention_mask],
        dtype=np.int64,
    )

    outputs = session.run(
        ["logits"],
        {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
        },
    )

    return float(outputs[0][0][0])


if __name__ == "__main__":
    query = "RAG 的工作原理是什么？"

    documents = [
        "RAG 先从外部知识库检索相关文档，再将检索结果提供给大语言模型生成回答。",
        "Python 是一种广泛使用的编程语言，支持面向对象和函数式编程。",
    ]

    for document in documents:
        print(f"\n候选文本：{document}")
        print(f"相关性原始分数：{score(query, document):.6f}")
