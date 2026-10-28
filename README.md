# AI Study Agent

基于本地大语言模型 **Ollama** 构建的个人 AI 学习助手，集成长期记忆、RAG 知识库、Tool Calling、LangGraph、MCP 和 FastAPI，并通过 Docker 实现容器化运行。

项目以 Python 为主要开发语言，采用循序渐进的工程实践方式，从基础 LLM 调用逐步构建具备任务规划、工具执行、知识检索和记忆管理能力的 AI Agent。

## 1. 项目目标

本项目旨在构建一个可持续扩展的 AI 学习助手，重点实践 AI 应用开发中的核心技术。

- 掌握大语言模型 API 调用与 Prompt 设计。
- 实现短期对话记忆和长期用户记忆。
- 构建基于 PDF 文档的 RAG 知识库。
- 实现 Tool Calling 和 Agent 自主决策。
- 使用 LangGraph 管理 Agent 状态和执行流程。
- 使用 MCP 接入标准化工具与外部能力。
- 使用 FastAPI 提供 HTTP 接口。
- 使用 Docker 实现容器化部署。
- 为后续前端开发、GitHub 展示和简历项目包装打下基础。

## 2. 技术栈

| 技术 | 主要用途 |
|---|---|
| Python | 核心开发语言 |
| Ollama | 本地大模型服务 |
| Qwen2 7B | 对话、推理和工具决策 |
| nomic-embed-text | 文本向量化 |
| Requests / HTTP API | 与模型服务通信 |
| JSON | 长期记忆持久化 |
| ChromaDB | 向量数据库 |
| RAG | 外部知识检索与增强生成 |
| Tool Calling | 根据任务选择并调用工具 |
| LangGraph | Agent 状态图与流程控制 |
| MCP | 标准化工具发现与调用 |
| FastAPI | HTTP API 服务 |
| Uvicorn | ASGI 服务运行 |
| Docker | 应用容器化 |
| Docker Compose | 容器配置与生命周期管理 |

## 3. 学习路线与总体进度

```text
Python 基础
    ↓
LLM API 调用                         ✅
    ↓
短期 Memory / 长期 Memory            ✅
    ↓
System Prompt                       ✅
    ↓
Tool Calling                        ✅
    ↓
RAG 知识库                           ✅
    ↓
Agent 基础架构                       ✅
    ↓
LangGraph 状态图                     ✅
    ↓
MCP 工具集成                         ✅
    ↓
Planner 多步骤任务规划                ✅
    ↓
FastAPI 服务化                       ✅
    ↓
Docker 容器化运行                     ✅
    ↓
工程化完善 / 前端 / GitHub 项目包装   🔄
```

> 当前进度说明：以上状态依据目前已经完成的开发和测试记录整理。部分高级工程能力仍需要进一步测试和完善，不能仅凭基础功能运行成功就认定全部达到生产环境要求。

---

## 4. Phase 1：LLM 基础调用 ✅

### 学习内容

- Ollama 本地大模型部署与调用。
- Python HTTP 请求。
- LLM API 请求与响应流程。
- JSON 数据解析。
- `.env` 环境变量配置。

### 已实现功能

- Python 连接 Ollama。
- 调用 `qwen2:7b-instruct-q4_K_S`。
- 接收用户输入。
- 获取并输出模型回答。

### 核心流程

```text
用户输入
   ↓
Python
   ↓
Ollama API
   ↓
本地大语言模型
   ↓
返回模型回答
```

### 核心理解

大语言模型并不是直接接收 Python 变量，而是通过 API 接收请求，再返回结构化响应。应用程序负责请求构造、参数配置和结果处理。

---

## 5. Phase 2：Memory 记忆系统 ✅

### 5.1 短期记忆

#### 学习内容

- LLM 的无状态特性。
- `system`、`user` 和 `assistant` 消息角色。
- 多轮对话上下文管理。

#### 已实现能力

- 保存聊天历史。
- 进行多轮对话。
- 将历史消息重新传递给模型。

#### 核心原理

短期记忆主要依靠保存对话历史，并在后续请求中提供相关上下文。

### 5.2 长期记忆

#### 学习内容

- 长期用户信息提取。
- Memory Extractor 设计。
- 用户画像管理。
- JSON 文件持久化。

#### 已实现能力

- 新增记忆。
- 更新记忆。
- 删除记忆。
- 查询用户记忆。
- 将用户偏好、兴趣和学习目标保存在本地文件中。

#### 存储方式

```text
storage/
├── __init__.py
├── manager.py
└── user_memory.json
```

#### 核心流程

```text
用户消息
   ↓
Memory Extractor
   ↓
判断是否需要保存记忆
   ↓
Memory Save
   ↓
JSON 文件持久化
```

### 核心理解

短期记忆关注当前对话上下文，长期记忆关注跨对话保留的用户信息。二者需要通过 Agent 流程协同使用。

---

## 6. Phase 3：System Prompt ✅

### 学习内容

- System Prompt 的作用。
- Prompt 结构与设计。
- 对模型行为进行约束。
- 指定输出格式与回答边界。

### 已实现能力

- 定义 AI 助手身份。
- 设置回答规则。
- 约束输出格式。
- 限制无关回答。

### 核心理解

System Prompt 用于引导模型遵循指定的行为规则，但它不能保证模型始终正确，也不能代替程序层面的校验。

---

## 7. Phase 4：Tool Calling 工具调用 ✅

### 学习内容

- Function Calling 原理。
- 工具注册与参数定义。
- LLM 生成工具调用请求。
- Python 执行实际业务逻辑。

### 已实现工具

- `calculator`：计算工具。

项目后续还通过 MCP 接入了其他工具能力，详见 MCP 章节。

### 工具调用流程

```text
用户提出问题
     ↓
LLM 判断是否需要工具
     ↓
生成工具名称和参数
     ↓
Python 执行对应函数
     ↓
返回执行结果
     ↓
LLM 组织最终回答
```

### 核心理解

LLM 负责理解需求、选择工具和生成参数；程序负责执行真实逻辑、处理异常并返回结果。

**Tool Calling 是 Agent 的一项能力，但 Tool Calling 本身不等于完整的 Agent。**

---

## 8. Phase 5：RAG 知识库 ✅

### 学习内容

- PDF 文档加载。
- 文本提取与切分。
- Embedding 向量化。
- ChromaDB 持久化存储。
- Retriever 检索。
- 基于检索结果生成回答。

### 已实现组件

```text
rag/
├── loader.py
├── splitter.py
├── embedding.py
├── vectorstore.py
├── ingest.py
├── retriever.py
├── rag_chain.py
└── test_vectorstore.py
```

### RAG 工作流程

#### 离线建库

```text
PDF 文档
   ↓
加载与文本提取
   ↓
文本切分 Chunking
   ↓
Embedding 向量化
   ↓
ChromaDB 持久化存储
```

#### 在线问答

```text
用户问题
   ↓
问题向量化
   ↓
向量数据库检索
   ↓
获取相关文本片段
   ↓
构造上下文 Prompt
   ↓
LLM 生成回答
```

### 已实现能力

- PDF 知识库。
- 文本切分。
- 文本向量化。
- 持久化向量数据库。
- 知识库检索。
- RAG 问答链路。
- 通过 MCP 工具调用知识库检索能力。

### 数据存储

```text
chroma_db/
└── ChromaDB 持久化数据
```

### 后续优化方向

- 检索相关性与距离度量校准。
- 相似度阈值和检索质量评估。
- 无相关结果时的处理。
- 降低知识库外内容带来的幻觉。
- 文档增量更新。
- 检索结果与最终回答的可追溯性。

### 核心理解

RAG 通过检索外部资料，为 LLM 提供与当前问题有关的上下文。最终答案的质量取决于检索质量、上下文完整性以及模型是否忠实使用检索结果。

---

## 9. Phase 6：Agent 基础架构 ✅

### 学习内容

- Agent 的核心思想。
- Think–Act–Observe 循环。
- Brain 决策。
- Executor 执行。
- Router 流程控制。
- 多步骤执行与终止条件。

### 已实现能力

Agent 可以根据问题选择不同的行动：

- `rag`：知识库检索。
- `tool`：工具调用。
- `mcp`：MCP 工具执行。
- `memory`：记忆相关操作。
- `chat`：普通对话。
- `final`：结束执行并输出最终答案。

具体可用行动取决于当前节点和路由配置。

### 核心流程

```text
用户问题
   ↓
Memory Extractor
   ↓
Brain 决策
   ↓
选择 Action
   ↓
Executor 执行
   ↓
Observation 执行结果
   ↓
Brain 再次决策
   ↓
继续执行或输出最终答案
```

### 核心理解

Agent 不只是接收问题并生成回答，而是可以根据目标选择行动、获取执行结果，并据此决定下一步操作。

---

## 10. Phase 7：LangGraph Agent 流程控制 ✅

### 学习内容

- State。
- Node。
- Edge。
- Conditional Edge。
- StateGraph。
- START 与 END。
- Checkpoint。
- 状态路由和节点协作。

### 已实现组件

#### State

使用 `TypedDict` 管理 Agent 状态，包括：

- `question`
- `thought`
- `action`
- `observation`
- `answer`
- `step`
- `source`
- `long_memory`
- `new_memory`
- `memory_saved`
- `has_error`
- `error`
- `retry_count`
- `tool_history`
- `plan`
- `current_plan_step`
- `current_task`

具体字段以项目当前 `agent/state.py` 为准。

#### Node

已实现或接入的节点包括：

- `memory_extractor_node`
- `memory_save_node`
- `brain_node`
- `executor_node`
- `planner_node`
- `plan_progress_node`
- `plan_step_judge_node`
- `error_handler_node`

部分节点的职责和调用关系可能随代码迭代继续调整。

#### Router

- Memory Router：判断是否需要保存新记忆。
- Agent Router：根据当前行动决定下一步执行节点。
- 计划推进路由：根据任务执行状态判断是否进入下一步。
- 错误处理相关路由：配合异常状态和重试逻辑。

#### Checkpoint

使用 `MemorySaver` 保存图执行过程中的状态，并支持基于 Thread 的状态管理和流程恢复。

需要注意，内存型 Checkpoint 不等同于跨进程的永久持久化存储。

### 当前 Graph 的主要流程

```text
START
  ↓
Memory Extractor
  ↓
Memory Router
  ├── 需要保存 → Memory Save
  └── 无需保存 ─────┐
                    ↓
                  Planner
                    ↓
                   Brain
                    ↓
                  Router
                    ↓
                  Executor
                    ↓
               观察执行结果
                    ↓
               计划进度判断
                    ↓
          继续执行 / 下一计划步骤
                    ↓
             最终答案或结束
                    ↓
                   END
```

该图为逻辑示意，具体边连接以 `agent/graph.py` 和 `agent/router.py` 中的实际实现为准。

---

## 11. Phase 8：MCP 工具集成 ✅

### 学习内容

- Model Context Protocol。
- MCP Server 与 MCP Client。
- 工具发现与工具调用。
- Tool Schema 与参数传递。
- Resource 相关机制。
- 将知识库能力接入 MCP。

### 项目结构

```text
mcp_demo/
├── mcp_server.py
├── mcp_test.py
└── mcp_agent_demo.py
```

### 已接入工具

- `add`：加法计算。
- `get_weather`：天气查询演示工具。
- `search_notes`：笔记检索。
- `search_knowledge_base`：RAG 知识库检索。

这些工具的具体数据来源和可用性以当前 Server 实现为准；演示工具不应被当作真实实时服务的保证。

### 工具发现与调用流程

```text
MCP Client
    ↓
list_tools()
    ↓
获取工具名称、描述和参数结构
    ↓
将可用工具信息提供给 LLM
    ↓
LLM 选择工具并生成参数
    ↓
MCP Client 发起调用
    ↓
MCP Server 执行工具
    ↓
返回工具结果
```

### 已验证内容

- MCP Server 启动。
- MCP Client 连接与工具发现。
- 加法工具调用。
- 天气演示工具调用。
- RAG 知识库检索工具调用。
- 通过 Agent 流程使用 MCP 工具。

### 核心理解

MCP 提供了标准化的上下文和工具交互方式，使应用可以通过统一协议发现并调用外部能力，而不必为每个工具都设计完全独立的通信机制。

---

## 12. Phase 9：Planner 多步骤任务规划 ✅

### 学习内容

- 将复杂任务拆分为多个子任务。
- 根据当前计划执行任务。
- 保存当前计划步骤与执行状态。
- 根据执行结果推进计划。

### 已实现能力

- `planner_node`：生成任务计划。
- `plan_progress_node`：推进计划步骤。
- `plan_step_judge_node`：判断步骤完成情况。
- 将 `current_task` 传递给执行逻辑。
- 将当前任务用于指导 RAG 检索等操作。
- 结合 Agent 状态控制多步骤执行。

### 已完成的端到端测试

测试问题：

> 请先查询知识库中关于 RAG 的资料，再根据查询结果总结 RAG 的工作原理。

Planner 将任务拆分为多个步骤，Agent 随后逐步执行任务，并在计划步骤完成后推进到后续步骤，最终输出 RAG 工作原理的总结。

测试同时暴露了可继续优化的方向：不同计划步骤的检索结果不一定都足够相关，步骤完成也需要更严格的结果校验。

### 核心理解

Planner 负责把目标拆分为可执行任务，Agent 则负责执行这些任务、观察结果并推进整体流程。

**需要区分：** 已经跑通多步骤规划，并不意味着计划质量、任务完成判定和所有异常场景都已经达到成熟水平。

---

## 13. Phase 10：Agent 工程化优化 🔄

### 已实现或已接入的能力

- 最大执行循环次数相关控制。
- 工具调用历史 `tool_history`。
- 错误状态记录。
- 重试次数相关控制。
- 错误处理节点。
- Planner 与 Agent 执行流程结合。
- 计划步骤推进。
- 工具执行结果传递。

### 后续优化方向

- 统一异常类型与错误信息。
- 完善工具失败后的恢复策略。
- 验证重试次数和终止条件是否覆盖边界情况。
- 避免同一工具被无意义地重复调用。
- 规范日志输出与调试开关。
- 增加单元测试和端到端测试。
- 改善检索相关性及计划步骤完成判定。
- 统一 API 错误响应格式。

这些内容中，部分已实现基础逻辑，部分仍需通过专门测试确认，不能一概视为已完成。

---

## 14. Phase 11：FastAPI 服务化 ✅

### 学习内容

- 使用 FastAPI 构建 HTTP API。
- 使用 Uvicorn 运行 ASGI 服务。
- 接收 JSON 请求。
- 将 Agent 能力封装为服务接口。
- 通过 Swagger UI 测试接口。

### 主要文件

```text
fastapi_app.py
```

### 已验证接口

#### 健康检查

```http
GET /
```

已验证返回服务运行状态、项目名称等信息。

#### Agent 问答

```http
POST /chat
Content-Type: application/json
```

请求示例：

```json
{
  "question": "请查询知识库，告诉我 RAG 是什么。"
}
```

已验证 `/chat` 能够返回成功响应及 AI 回答。

### 接口文档

本地服务运行时，可以通过以下地址访问 Swagger UI：

```text
http://localhost:8000/docs
```

### 后续优化方向

- 请求与响应模型规范化。
- 参数校验。
- 统一异常处理。
- 日志与请求追踪。
- 超时和并发控制。
- 用户会话隔离。
- API 认证与访问控制。

---

## 15. Phase 12：Docker 容器化部署 ✅

### 学习内容

- Docker 镜像构建。
- Dockerfile 编写。
- `.dockerignore` 配置。
- Docker Compose 管理容器。
- 环境变量注入。
- 数据目录挂载。
- 容器运行与日志排查。

### Docker 相关文件

```text
ai-study-agent/
├── Dockerfile  # 如果项目根目录不存在此文件，则不适用
├── .dockerignore
├── docker-compose.yml
└── docker/
    └── Dockerfile
```

项目实际使用的 Dockerfile 位于 `docker/Dockerfile`；上面的根目录 `Dockerfile` 仅用于说明不同项目可能采用的布局，不要求额外创建。

### 已完成的部署配置

- 使用 `python:3.12-slim` 作为基础镜像。
- 安装 Python 项目依赖。
- 将 Agent、RAG、MCP、Tools 和应用模块复制到镜像。
- 使用 Uvicorn 启动 FastAPI。
- 暴露容器端口 `8000`。
- 通过 `.env` 注入运行配置。
- 将 `chroma_db/` 和 `storage/` 挂载到容器。
- 使用 Docker Compose 启动和管理服务。

### 构建镜像

```bash
docker build -f docker/Dockerfile -t ai-study-agent .
```

### 启动容器

```bash
docker-compose up -d
```

### 查看容器状态

```bash
docker ps
```

### 查看日志

```bash
docker-compose logs --tail=100
```

持续查看日志：

```bash
docker-compose logs -f
```

### 重启服务

```bash
docker-compose restart
```

### 停止并移除 Compose 创建的容器

```bash
docker-compose down
```

注意：`docker-compose down` 会移除 Compose 创建的容器和网络，但普通绑定挂载的宿主机数据目录不会因此自动删除。

### 已完成的部署验证

| 验证项目 | 结果 |
|---|---|
| Docker 镜像构建 | ✅ |
| 容器启动 | ✅ |
| FastAPI 服务运行 | ✅ |
| `/` 健康检查接口 | ✅ |
| `/chat` 问答接口 | ✅ |
| 容器连接 Ollama | ✅ |
| 容器内 RAG 检索 | ✅ |
| 容器内长期记忆读取 | ✅ |
| 容器重启后读取 RAG 数据 | ✅ |
| 容器重启后读取长期记忆 | ✅ |

### 当前部署架构

```text
用户 / 浏览器
      ↓
FastAPI
      ↓
LangGraph Agent
      ├── Memory
      ├── Planner
      ├── RAG / ChromaDB
      ├── Tool Calling
      └── MCP
              ↓
          Ollama API
              ↓
        本地大语言模型
```

部署时，FastAPI、Agent 代码和 Python 依赖运行在 Docker 容器中；Ollama 运行在容器外部，并通过配置的 API 地址访问。

ChromaDB 和长期记忆文件通过宿主机目录挂载保存，容器重启后已验证能够读取原有数据。

### 需要继续确认的部署事项

- 删除并重新创建容器后的数据保留测试。
- 在另一台机器上复现部署。
- Ollama 模型的安装与启动说明。
- `.env` 示例文件与安全配置说明。
- 服务启动失败时的排查步骤。
- 生产环境中的认证、网络隔离和密钥管理。

---

## 16. 项目目录结构

以下为主要模块的逻辑结构，实际文件以仓库当前内容为准。

```text
ai-study-agent/
├── agent/
│   ├── brain.py
│   ├── executor.py
│   ├── graph.py
│   ├── logger.py
│   ├── mcp_client.py
│   ├── memory_extractor.py
│   ├── memory_writer.py
│   ├── nodes.py
│   ├── router.py
│   └── state.py
├── rag/
│   ├── loader.py
│   ├── splitter.py
│   ├── embedding.py
│   ├── vectorstore.py
│   ├── ingest.py
│   ├── retriever.py
│   └── rag_chain.py
├── mcp_demo/
│   ├── mcp_server.py
│   ├── mcp_test.py
│   └── mcp_agent_demo.py
├── storage/
│   ├── manager.py
│   └── user_memory.json
├── tools/
├── data/
├── chroma_db/
├── docker/
│   └── Dockerfile
├── fastapi_app.py
├── llm.py
├── memory.py
├── long_memory.py
├── config.py
├── requirements.txt
├── .env.example
├── .dockerignore
├── docker-compose.yml
└── README.md
```

说明：

- `agent/`：Agent 决策、状态、路由、执行与流程编排。
- `rag/`：知识库加载、切分、向量化、存储和检索。
- `mcp_demo/`：MCP Server、Client 和测试代码。
- `storage/`：长期记忆管理与持久化文件。
- `data/`：原始学习资料。
- `chroma_db/`：向量数据库持久化数据。
- `docker/`：Docker 镜像构建配置。
- `fastapi_app.py`：HTTP API 服务入口。
- `config.py`：应用配置。
- `.env.example`：环境变量模板，不存放真实密钥。

## 17. 本地运行与环境配置

### 17.1 环境要求

- Python 3.12（Docker 环境已使用该版本）。
- Ollama。
- 项目依赖。
- 已下载并配置需要使用的模型。

### 17.2 配置环境变量

参考 `.env.example` 创建本地 `.env` 文件：

```env
OLLAMA_BASE_URL=http://YOUR_OLLAMA_HOST:11434
OLLAMA_MODEL=qwen2:7b-instruct-q4_K_S
```

请将示例地址替换为实际可访问的 Ollama 地址。Docker 容器内使用的地址必须能从容器网络访问。

### 17.3 安装依赖

```bash
pip install -r requirements.txt
```

### 17.4 启动 API

```bash
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000
```

然后访问：

```text
http://localhost:8000/docs
```

以上为通用启动方式；若实际代码还有额外环境要求，应以项目当前配置为准。

## 18. 当前能力总结

目前 AI Study Agent 已经具备以下主要能力：

- [x] Ollama 本地大模型调用
- [x] 多轮对话
- [x] 长期用户记忆
- [x] System Prompt 控制
- [x] 基础 Tool Calling
- [x] PDF 知识库 RAG
- [x] ChromaDB 持久化
- [x] Agent 自主决策
- [x] LangGraph 状态图
- [x] Checkpoint 状态管理
- [x] MCP 工具发现与调用
- [x] RAG 检索工具接入 MCP
- [x] Planner 多步骤任务规划
- [x] FastAPI HTTP 服务
- [x] Docker 镜像构建
- [x] Docker 容器运行
- [x] 容器内 RAG 与长期记忆读取
- [x] 容器重启后的数据读取验证

## 19. 后续开发计划

### 第一阶段：完善工程质量

- [ ] 完善异常处理和恢复策略。
- [ ] 验证最大循环次数与重试边界。
- [ ] 改进 Planner 的任务分解和完成判定。
- [ ] 优化 RAG 检索质量。
- [ ] 增加自动化测试。
- [ ] 完善日志和配置管理。

### 第二阶段：完善部署

- [ ] 验证删除并重新创建容器后的数据持久性。
- [ ] 整理 Docker 部署文档。
- [ ] 完善环境变量模板。
- [ ] 增加部署故障排查指南。
- [ ] 验证全新环境部署流程。

### 第三阶段：应用完善

- [ ] 开发前端交互界面。
- [ ] 完善会话管理。
- [ ] 优化 API 返回结构。
- [ ] 增加用户访问控制。
- [ ] 改善运行状态与错误提示。

### 第四阶段：GitHub 与求职准备

- [ ] 整理 GitHub 仓库。
- [ ] 补充架构图与核心流程图。
- [ ] 编写项目演示说明。
- [ ] 整理技术难点和解决方案。
- [ ] 准备简历项目描述和面试讲解材料。

## 20. 最终目标

将 AI Study Agent 打造成一个具备完整工程结构的个人 AI 应用项目，能够展示：

- LLM 应用开发能力。
- RAG 知识库构建能力。
- Agent 架构设计能力。
- LangGraph 流程编排能力。
- MCP 工具集成能力。
- FastAPI 服务化能力。
- Docker 容器化部署能力。
- 调试、测试与工程化优化能力。

项目最终目标是形成一个可运行、可展示、可复现、可持续扩展的 AI 应用开发作品，为 GitHub 展示、简历项目经历和 AI 应用开发岗位面试提供支撑。
