FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 安装 Python 依赖
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r /app/requirements.txt

# 复制项目代码
COPY agent/ /app/agent/
COPY rag/ /app/rag/
COPY mcp_demo/ /app/mcp_demo/
COPY tools/ /app/tools/
COPY config.py /app/config.py
COPY fastapi_app.py /app/fastapi_app.py
COPY llm.py /app/llm.py
COPY memory.py /app/memory.py
COPY long_memory.py /app/long_memory.py

# 创建运行时数据目录
RUN mkdir -p /app/chroma_db /app/storage

EXPOSE 8000

CMD ["uvicorn", "fastapi_app:app", "--host", "0.0.0.0", "--port", "8000"]
