
import json
from pathlib import Path

from rag.embedding import get_embedding
from rag.vectorstore import collection
from rag.retriever import _rerank


CANDIDATE_K = 10
TOP_K = 5

# 人工标注文件：保存在项目根目录下的 test 文件夹中
LABEL_FILE = Path(__file__).parent / "reranker_relevance_labels.json"

TEST_CASES = [
    {
        "question": "什么是 RAG？",
        "expected_content": "解释 RAG 的定义，以及检索与生成如何结合。",
    },
    {
        "question": "RAG 的离线建库阶段包括哪些步骤？",
        "expected_content": "解释文档加载、文本切分、向量化和保存索引。",
    },
    {
        "question": "为什么文本切分会影响 RAG 的检索质量？",
        "expected_content": "解释片段过大或过小的影响，以及上下文和信息完整性。",
    },
    {
        "question": "Embedding 模型在 RAG 中负责什么？",
        "expected_content": "解释文本如何转换为向量，以及向量如何支持语义检索。",
    },
]


def retrieve_candidates(question):
    """执行向量召回，返回候选文本及元数据。"""
    count = collection.count()

    if count == 0:
        return []

    query_embedding = get_embedding(question)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(CANDIDATE_K, count),
        include=["documents", "metadatas", "distances"],
    )

    documents = (results.get("documents") or [[]])[0] or []
    metadatas = (results.get("metadatas") or [[]])[0] or []
    distances = (results.get("distances") or [[]])[0] or []

    candidates = []

    for i, document in enumerate(documents):
        if not document:
            continue

        metadata = (
            metadatas[i]
            if i < len(metadatas) and metadatas[i]
            else {}
        )

        candidates.append({
            "source": metadata.get("source", "unknown"),
            "page": metadata.get("page", "unknown"),
            "distance": distances[i] if i < len(distances) else None,
            "text": document,
        })

    return candidates


def load_labels():
    """读取之前保存的人工标注。"""
    if not LABEL_FILE.exists():
        return {}

    try:
        with LABEL_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"读取标注文件失败：{exc}")
        print("将从空标注开始。")
        return {}


def save_labels(labels):
    """保存人工标注。"""
    try:
        with LABEL_FILE.open("w", encoding="utf-8") as file:
            json.dump(
                labels,
                file,
                ensure_ascii=False,
                indent=2,
            )
    except OSError as exc:
        print(f"保存标注文件失败：{exc}")
        raise


def make_label_key(question, item):
    """
    使用问题、来源、页码和文本内容生成标注键。
    文本内容参与标识，避免同一页的不同片段共用一个标签。
    """
    import hashlib

    text_hash = hashlib.sha256(
        item["text"].encode("utf-8")
    ).hexdigest()[:16]

    return (
        f"{question}|{item.get('source', 'unknown')}|"
        f"{item.get('page', 'unknown')}|{text_hash}"
    )


def print_item(rank, item, rerank=False):
    """打印单条候选文本。"""
    if rerank and "rerank_score" in item:
        score = f"Reranker 分数={item['rerank_score']:.4f}"
    else:
        score = f"向量距离={item.get('distance')}"

    text = item["text"].replace("\n", " ")

    print(f"\n排名={rank} | {score}")
    print(
        f"来源={item.get('source', 'unknown')} | "
        f"页码={item.get('page', 'unknown')}"
    )
    print(f"文本：{text[:500]}")
    if len(text) > 500:
        print("……（文本已截断显示）")


def get_relevance_label(question, item, labels):
    """
    获取人工相关性标签：
    1 = 文本确实包含回答问题所需的信息
    0 = 文本只是提到术语，或不能提供足够的回答依据
    """
    key = make_label_key(question, item)

    if key in labels and labels[key] in (0, 1):
        return labels[key]

    while True:
        answer = input(
            "\n请标注相关性 [1=相关，0=不相关，q=退出]："
        ).strip().lower()

        if answer == "q":
            return None

        if answer in ("0", "1"):
            label = int(answer)
            labels[key] = label
            save_labels(labels)
            return label

        print("输入无效，请输入 1、0 或 q。")


def evaluate_ranked_results(question, results, labels, rerank=False):
    """逐条人工标注 Top 5，并计算 Hit@5、MRR@5。"""
    top_results = results[:TOP_K]
    relevance = []

    title = "Reranker 重排" if rerank else "向量检索"

    print(f"\n--- {title}：人工相关性标注 ---")

    for rank, item in enumerate(top_results, start=1):
        print_item(rank, item, rerank=rerank)

        label = get_relevance_label(question, item, labels)

        if label is None:
            print("用户选择退出，本次评估提前结束。")
            return None

        relevance.append(label)

    relevant_ranks = [
        rank
        for rank, label in enumerate(relevance, start=1)
        if label == 1
    ]

    hit_at_k = 1 if relevant_ranks else 0
    mrr = 1 / relevant_ranks[0] if relevant_ranks else 0.0

    return {
        "hit_at_k": hit_at_k,
        "mrr": mrr,
        "relevant_ranks": relevant_ranks,
        "labels": relevance,
    }


def main():
    if collection.count() == 0:
        print("知识库为空，请先完成文档入库。")
        return

    labels = load_labels()
    print(f"已加载 {len(labels)} 条人工标注。")
    print("标注标准：")
    print("  1 = 文本确实包含回答问题所需的信息")
    print("  0 = 只提到术语，或没有提供足够的回答依据")
    print("  q = 退出，已保存的标注不会丢失")

    vector_hit_total = 0
    rerank_hit_total = 0
    vector_mrr_total = 0.0
    rerank_mrr_total = 0.0
    valid_cases = 0

    for index, case in enumerate(TEST_CASES, start=1):
        question = case["question"]

        print("\n" + "=" * 80)
        print(f"测试 {index}/{len(TEST_CASES)}：{question}")
        print(f"相关性标准：{case['expected_content']}")

        candidates = retrieve_candidates(question)

        if not candidates:
            print("没有召回候选文本，跳过本题。")
            continue

        vector_results = candidates[:TOP_K]
        rerank_results = _rerank(question, candidates)[:TOP_K]

        vector_eval = evaluate_ranked_results(
            question,
            vector_results,
            labels,
            rerank=False,
        )
        if vector_eval is None:
            break

        rerank_eval = evaluate_ranked_results(
            question,
            rerank_results,
            labels,
            rerank=True,
        )
        if rerank_eval is None:
            break

        vector_hit_total += vector_eval["hit_at_k"]
        rerank_hit_total += rerank_eval["hit_at_k"]
        vector_mrr_total += vector_eval["mrr"]
        rerank_mrr_total += rerank_eval["mrr"]
        valid_cases += 1

        print("\n本题评估结果：")
        print(
            f"向量检索：Hit@5={vector_eval['hit_at_k']} | "
            f"MRR@5={vector_eval['mrr']:.3f} | "
            f"相关排名={vector_eval['relevant_ranks']}"
        )
        print(
            f"Reranker：Hit@5={rerank_eval['hit_at_k']} | "
            f"MRR@5={rerank_eval['mrr']:.3f} | "
            f"相关排名={rerank_eval['relevant_ranks']}"
        )

    print("\n" + "=" * 80)
    print("评估汇总")

    if valid_cases == 0:
        print("没有完成的测试题。")
        return

    print(f"已完成测试题数：{valid_cases}")
    print(
        f"向量检索 Hit@5：{vector_hit_total}/{valid_cases} "
        f"({vector_hit_total / valid_cases:.1%})"
    )
    print(
        f"Reranker Hit@5：{rerank_hit_total}/{valid_cases} "
        f"({rerank_hit_total / valid_cases:.1%})"
    )
    print(
        f"向量检索平均 MRR@5："
        f"{vector_mrr_total / valid_cases:.3f}"
    )
    print(
        f"Reranker 平均 MRR@5："
        f"{rerank_mrr_total / valid_cases:.3f}"
    )
    print(f"人工标注文件：{LABEL_FILE}")


if __name__ == "__main__":
    main()
