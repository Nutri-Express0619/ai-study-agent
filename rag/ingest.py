
import os

from .loader import load_document
from .splitter import split_text
from .embedding import get_embedding
from .vectorstore import add_documents, document_exists


# PDF 存放目录
data_dir = "./data"


def ingest_pdfs():
    if not os.path.isdir(data_dir):
        raise FileNotFoundError(
            f"PDF 目录不存在：{os.path.abspath(data_dir)}"
        )

    # 只处理 PDF，并按文件名排序
    pdf_files = sorted(
        filename
        for filename in os.listdir(data_dir)
        if filename.lower().endswith(".pdf")
    )

    if not pdf_files:
        print(f"目录中没有 PDF 文件：{os.path.abspath(data_dir)}")
        return

    for filename in pdf_files:
        print(f"\n开始检查：{filename}")

        # 已入库的文件直接跳过
        if document_exists(filename):
            print(f"跳过已入库文件：{filename}")
            continue

        pdf_path = os.path.join(data_dir, filename)

        try:
            # 1. 加载 PDF
            documents = load_document(pdf_path)

            # 2. 切分文本
            chunks = split_text(documents)

            if not chunks:
                print(f"没有提取到有效文本，跳过：{filename}")
                continue

            # 3. 生成 Embedding
            embeddings = []

            for chunk in chunks:
                vector = get_embedding(chunk["text"])
                embeddings.append(vector)

            # 4. 保存到 ChromaDB
            add_documents(chunks, embeddings)

            print(
                f"文件处理完成：{filename}，"
                f"共生成 {len(chunks)} 个文本片段"
            )

        except Exception as exc:
            print(f"处理失败：{filename}")
            print(f"错误信息：{exc}")
            raise

    print("\n知识库入库流程结束")


if __name__ == "__main__":
    ingest_pdfs()
