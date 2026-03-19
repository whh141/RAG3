# Agentic RAG 问答系统详细设计文档（第二阶段：Schema、API 与工程骨架）

## 1. 文档定位

本文件承接《第一阶段：技术栈审视与逐步开发》。第一阶段已经冻结了技术栈与总体边界；本阶段不再讨论“要不要用某项技术”，而是直接回答下面四个问题：

1. 系统里有哪些核心对象，它们的字段是什么；
2. 前后端如何通信，REST API 与 WebSocket 协议如何定义；
3. LangGraph 的状态图要如何落到工程结构中；
4. 如何在不违背第一性原则的前提下，搭出一个能持续生长到 5000+ 行的项目骨架。

本文档的目标不是“列出很多接口”，而是确保后续编码时每一个接口、每一张表、每一个状态字段都能找到明确职责。

---

## 2. 设计前提与约束

在开始详细设计之前，先重申本项目的固定约束。

### 2.1 目标约束

系统核心目标只有一条：

> 针对用户问题，自主判断应走本地知识检索、外部搜索还是直接生成，并将中间路由状态可视化展示出来。

### 2.2 范围约束

第一版只做：

- 校园规章与通用问答；
- 单用户演示级系统；
- 文本知识库；
- 单轮 / 多轮会话；
- 路由、检索、搜索、生成、引用、评测。

第一版不做：

- 复杂权限体系；
- 多租户；
- 多模态上传；
- 自我反思与自动纠错闭环；
- 复杂工作流编排平台。

### 2.3 技术冻结

- Backend: FastAPI
- Frontend: Vue 3 + TypeScript + Element Plus + Pinia
- Database: SQLite
- Vector Store: ChromaDB
- Agent Runtime: LangChain + LangGraph
- Model Providers: ZhipuAI / OpenAI
- Web Search: Tavily

---

## 3. 核心领域对象建模

这一部分不从“数据库表”出发，而从业务对象出发。这样可以避免一开始就把运行时状态、持久化状态、前端展示状态混为一谈。

## 3.1 文档域（Knowledge Base Domain）

### 3.1.1 Document

表示一个被上传到知识库中的原始文件。

**职责**：

- 标识一个知识源；
- 记录处理状态；
- 记录切片与向量化结果概况；
- 作为 UI 管理与删除的最小单位。

**字段定义**：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | `str(UUID)` | 是 | 文档主键 |
| `filename` | `str` | 是 | 原始文件名 |
| `display_name` | `str` | 是 | 前端展示名，可与文件名一致 |
| `file_ext` | `str` | 是 | 扩展名，如 `pdf` / `txt` / `md` |
| `mime_type` | `str` | 否 | 上传时解析出的 MIME 类型 |
| `storage_path` | `str` | 是 | 文件落盘路径 |
| `file_size` | `int` | 是 | 文件字节数 |
| `status` | `enum` | 是 | `uploaded / parsing / chunking / embedding / completed / failed` |
| `chunk_strategy` | `str` | 是 | 当前采用的切块策略名称 |
| `chunk_count` | `int` | 是 | 生成的切片数量 |
| `token_count` | `int` | 否 | 粗略 token 总量 |
| `error_message` | `str` | 否 | 处理失败时的错误信息 |
| `created_at` | `datetime` | 是 | 上传时间 |
| `updated_at` | `datetime` | 是 | 更新时间 |

### 3.1.2 DocumentChunk

表示文档被切分后的一个知识块。这个对象在逻辑上存在于系统中，但不建议全部落到 SQLite；其核心存储位置是 ChromaDB 元数据层。

**职责**：

- 成为向量检索的最小单位；
- 保留足够的定位信息，便于生成引用。

**字段定义**：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | `str(UUID)` | 是 | chunk 主键 |
| `document_id` | `str(UUID)` | 是 | 所属文档 |
| `chunk_index` | `int` | 是 | 在原始文档中的顺序 |
| `content` | `str` | 是 | 文本内容 |
| `title_path` | `str` | 否 | 标题路径，如 `学生管理/转专业/申请条件` |
| `category` | `str` | 否 | 教务 / 宿舍 / 奖学金等 |
| `char_start` | `int` | 否 | 原文起始字符偏移 |
| `char_end` | `int` | 否 | 原文结束字符偏移 |
| `token_count` | `int` | 否 | 切片 token 数 |

### 3.1.3 ChunkStrategyConfig

表示当前使用的切块策略配置。该对象不一定单独建表，但必须在系统中有显式结构定义，否则后续会把切块逻辑写散。

**字段定义**：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `name` | `str` | 策略名称，如 `by_heading_paragraph` |
| `max_tokens` | `int` | 单 chunk 最大 token |
| `overlap_tokens` | `int` | 重叠 token |
| `respect_heading` | `bool` | 是否优先按标题切分 |
| `respect_paragraph` | `bool` | 是否优先按段落切分 |
| `strip_whitespace` | `bool` | 是否清理冗余空白 |
| `merge_short_paragraphs` | `bool` | 是否合并过短段落 |

---

## 3.2 会话域（Conversation Domain）

### 3.2.1 ChatSession

表示一次连续对话会话。

**字段定义**：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | `str(UUID)` | 是 | 会话主键 |
| `title` | `str` | 是 | 会话标题 |
| `description` | `str` | 否 | 会话简述 |
| `model_provider` | `str` | 是 | `zhipuai` / `openai` |
| `agent_mode` | `str` | 是 | `baseline_rag` / `agentic_rag` |
| `created_at` | `datetime` | 是 | 创建时间 |
| `updated_at` | `datetime` | 是 | 更新时间 |
| `last_message_at` | `datetime` | 否 | 最近消息时间 |

### 3.2.2 ChatMessage

表示会话中的一条消息。

**字段定义**：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | `str(UUID)` | 是 | 消息主键 |
| `session_id` | `str(UUID)` | 是 | 所属会话 |
| `role` | `enum` | 是 | `system / user / assistant` |
| `content` | `text` | 是 | 消息内容 |
| `content_format` | `str` | 是 | `plain_text / markdown` |
| `message_status` | `str` | 是 | `completed / streaming / failed` |
| `citations_json` | `json` | 否 | 引用信息 |
| `trace_id` | `str(UUID)` | 否 | 对应一次 agent 运行 |
| `latency_ms` | `int` | 否 | 回答耗时 |
| `created_at` | `datetime` | 是 | 创建时间 |

### 3.2.3 Citation

这是面向展示层和消息层的结构，不建议作为单独主表；更适合作为 JSON 嵌入到 `ChatMessage.citations_json` 中。

**字段定义**：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `source_type` | `str` | `local_document` / `web_search` |
| `source_id` | `str` | 文档或网页来源 ID |
| `source_name` | `str` | 文件名或网页标题 |
| `chunk_id` | `str` | 本地检索时对应 chunk ID |
| `snippet` | `str` | 引用片段摘要 |
| `url` | `str` | 外部搜索时的链接 |
| `score` | `float` | 检索得分 |

---

## 3.3 智能体运行域（Agent Runtime Domain）

这里是本系统最关键的部分。需要明确一点：**LangGraph State 不等于数据库表**。它描述的是单次问答过程中的运行时状态。

### 3.3.1 AgentRunState

建议将 Graph State 设计为结构化对象，而不是零散字典。

**字段定义**：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `trace_id` | `str(UUID)` | 单次运行 ID |
| `session_id` | `str(UUID)` | 对应会话 ID |
| `query` | `str` | 用户本轮问题 |
| `normalized_query` | `str` | 预处理后的问题 |
| `query_type` | `str` | `campus_rule / factual / timely / reasoning / unknown` |
| `route` | `str` | `direct / local_rag / web_search / hybrid` |
| `route_reason` | `str` | 路由原因摘要 |
| `retrieved_chunks` | `list[RetrievedChunk]` | 本地检索结果 |
| `web_results` | `list[WebSearchResult]` | 联网结果 |
| `selected_evidence` | `list[EvidenceItem]` | 最终进入生成阶段的证据 |
| `compressed_context` | `str` | 压缩后的上下文 |
| `final_answer` | `str` | 最终答案 |
| `citations` | `list[Citation]` | 引用集合 |
| `node_history` | `list[NodeTrace]` | 节点执行历史 |
| `error` | `str | None` | 失败原因 |

### 3.3.2 RetrievedChunk

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `chunk_id` | `str` | chunk ID |
| `document_id` | `str` | 文档 ID |
| `document_name` | `str` | 文件名 |
| `content` | `str` | chunk 内容 |
| `score` | `float` | 初步检索分数 |
| `rerank_score` | `float` | 重排序分数 |
| `chunk_index` | `int` | 块序号 |

### 3.3.3 WebSearchResult

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `result_id` | `str` | 结果 ID |
| `title` | `str` | 页面标题 |
| `url` | `str` | 页面链接 |
| `snippet` | `str` | 摘要 |
| `published_at` | `datetime | None` | 发布时间 |
| `score` | `float` | 搜索相关性得分 |

### 3.3.4 NodeTrace

这是给 WebSocket 可视化与调试面板使用的核心结构。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `node_name` | `str` | 节点名 |
| `status` | `str` | `pending / running / completed / failed / skipped` |
| `summary` | `str` | 节点摘要 |
| `started_at` | `datetime` | 开始时间 |
| `finished_at` | `datetime | None` | 结束时间 |
| `extra` | `dict` | 扩展数据 |

---

## 3.4 评测域（Evaluation Domain）

### 3.4.1 EvalRun

表示一次批量评测任务。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `str(UUID)` | 评测任务 ID |
| `name` | `str` | 评测任务名称 |
| `dataset_name` | `str` | 数据集名 |
| `baseline_mode` | `str` | 基线方案 |
| `agent_mode` | `str` | 智能体方案 |
| `status` | `str` | `pending / running / completed / failed` |
| `question_count` | `int` | 问题总数 |
| `created_at` | `datetime` | 创建时间 |
| `finished_at` | `datetime | None` | 结束时间 |

### 3.4.2 EvalRecord

表示单题评测结果。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `str(UUID)` | 主键 |
| `eval_run_id` | `str(UUID)` | 所属批次 |
| `question` | `text` | 测试问题 |
| `reference_answer` | `text` | 参考答案 |
| `baseline_answer` | `text` | 基线输出 |
| `agent_answer` | `text` | Agent 输出 |
| `baseline_latency_ms` | `int` | 基线耗时 |
| `agent_latency_ms` | `int` | Agent 耗时 |
| `baseline_score` | `float` | 基线得分 |
| `agent_score` | `float` | Agent 得分 |
| `route_expected` | `str` | 预期路径 |
| `route_actual` | `str` | 实际路径 |
| `route_correct` | `bool` | 路由是否正确 |

---

## 4. 持久化设计：SQLite 与 ChromaDB 的职责分解

## 4.1 SQLite 中必须存在的表

建议第一版至少包含以下 5 张核心表：

1. `documents`
2. `chat_sessions`
3. `chat_messages`
4. `eval_runs`
5. `eval_records`

其中：

- `documents` 负责文档元数据；
- `chat_sessions` 与 `chat_messages` 负责会话历史；
- `eval_runs` 与 `eval_records` 负责评测结果；
- 文本 chunk 不强制入 SQLite 明细表，优先放在 ChromaDB 元数据中。

### 为什么不建议第一版把全部 chunk 再存一张重表

原因不是不能存，而是当前目标是最短路径完成：

- SQLite 主职责是管理业务元数据；
- ChromaDB 已经能承载 chunk 及其 metadata；
- 如果第一版再额外造 `document_chunks` 关系表，会增加同步与删除复杂度；
- 这部分复杂度对答辩亮点贡献有限。

因此，第一版建议：

- **SQLite 管文档级元数据**；
- **ChromaDB 管 chunk 级内容与索引**。

## 4.2 ChromaDB Collection 设计

建议至少维护一个主 collection：

- `campus_rules_collection`

每条记录的 metadata 建议包含：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `document_id` | `str` | 文档 ID |
| `document_name` | `str` | 文件名 |
| `chunk_id` | `str` | chunk ID |
| `chunk_index` | `int` | 序号 |
| `category` | `str` | 类别 |
| `title_path` | `str` | 标题路径 |
| `token_count` | `int` | token 数 |

---

## 5. Pydantic Schema 建议

这一层的作用是：让 FastAPI 输入输出协议稳定下来，避免路由函数里直接操作裸字典。

## 5.1 知识库相关 Schema

### UploadDocumentResponse

```python
class UploadDocumentResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    message: str
```

### DocumentListItem

```python
class DocumentListItem(BaseModel):
    id: str
    filename: str
    display_name: str
    status: str
    chunk_strategy: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime
```

## 5.2 会话相关 Schema

### CreateSessionRequest

```python
class CreateSessionRequest(BaseModel):
    title: str | None = None
    model_provider: Literal["zhipuai", "openai"] = "zhipuai"
    agent_mode: Literal["baseline_rag", "agentic_rag"] = "agentic_rag"
```

### CreateSessionResponse

```python
class CreateSessionResponse(BaseModel):
    session_id: str
    title: str
    created_at: datetime
```

### MessageDTO

```python
class MessageDTO(BaseModel):
    id: str
    role: Literal["system", "user", "assistant"]
    content: str
    content_format: str
    message_status: str
    citations: list[dict] = []
    created_at: datetime
```

## 5.3 评测相关 Schema

### StartEvalRequest

```python
class StartEvalRequest(BaseModel):
    name: str
    dataset_name: str
    question_count: int = 100
    model_provider: Literal["zhipuai", "openai"] = "zhipuai"
```

### EvalRunDTO

```python
class EvalRunDTO(BaseModel):
    id: str
    name: str
    status: str
    question_count: int
    created_at: datetime
    finished_at: datetime | None = None
```

---

## 6. REST API 设计

这一部分只定义第一版必须存在的接口，不添加花哨能力。

## 6.1 知识库接口

### 6.1.1 `POST /api/kb/upload`

**用途**：上传文档并触发异步处理。

**请求**：

- `multipart/form-data`
- 字段：
  - `file`: 文件本体
  - `chunk_strategy`: 可选，默认 `by_heading_paragraph`

**响应示例**：

```json
{
  "document_id": "9ab2...",
  "filename": "山东大学学生管理规定.pdf",
  "status": "uploaded",
  "message": "上传成功，后台处理中"
}
```

### 6.1.2 `GET /api/kb/list`

**用途**：获取知识库文件列表。

**响应示例**：

```json
[
  {
    "id": "9ab2...",
    "filename": "山东大学学生管理规定.pdf",
    "display_name": "山东大学学生管理规定",
    "status": "completed",
    "chunk_strategy": "by_heading_paragraph",
    "chunk_count": 42,
    "created_at": "2026-03-18T10:00:00Z",
    "updated_at": "2026-03-18T10:02:12Z"
  }
]
```

### 6.1.3 `GET /api/kb/{document_id}`

**用途**：查看单个文档的处理详情。

**说明**：该接口很有必要，因为前端管理页面不仅要展示列表，还要在详情抽屉中查看处理状态、错误信息、切块策略。

### 6.1.4 `DELETE /api/kb/{document_id}`

**用途**：删除文档及其向量数据。

**全链路要求**：

- 删除 SQLite 文档记录；
- 删除 ChromaDB 对应 chunk；
- 删除本地原始文件；
- 若删除失败，返回明确错误。

---

## 6.2 会话接口

### 6.2.1 `POST /api/chat/session`

**用途**：创建新会话。

**请求示例**：

```json
{
  "title": "转专业咨询",
  "model_provider": "zhipuai",
  "agent_mode": "agentic_rag"
}
```

**响应示例**：

```json
{
  "session_id": "a1b2...",
  "title": "转专业咨询",
  "created_at": "2026-03-18T10:10:00Z"
}
```

### 6.2.2 `GET /api/chat/sessions`

**用途**：获取会话列表。

### 6.2.3 `GET /api/chat/{session_id}/history`

**用途**：获取会话历史消息。

### 6.2.4 `DELETE /api/chat/{session_id}`

**用途**：删除一个会话及其消息。

---

## 6.3 评测接口

### 6.3.1 `POST /api/eval/run`

**用途**：启动批量评测。

### 6.3.2 `GET /api/eval/runs`

**用途**：查看评测任务列表。

### 6.3.3 `GET /api/eval/run/{eval_run_id}`

**用途**：查看单次评测的汇总结果。

### 6.3.4 `GET /api/eval/run/{eval_run_id}/records`

**用途**：查看单题结果列表。

---

## 7. WebSocket 事件协议设计

这是系统最关键的实时链路。必须在编码前把事件类型定义清楚，否则前后端一定会在联调时混乱。

## 7.1 连接定义

### `WS /ws/chat/{session_id}`

建立问答双向通道：

- 前端发送用户问题；
- 后端回传节点状态、流式文本、引用、结束事件；
- 一个连接对应一个会话，但一次连接中可以连续提问多轮。

## 7.2 前端发送事件

### AskEvent

```json
{
  "action": "ask",
  "request_id": "req-001",
  "query": "学校关于本科生转专业的规定是什么？",
  "model_provider": "zhipuai",
  "agent_mode": "agentic_rag"
}
```

### PingEvent

```json
{
  "action": "ping"
}
```

## 7.3 后端推送事件

### 7.3.1 AgentStateEvent

用于展示节点流转。

```json
{
  "type": "agent_state",
  "request_id": "req-001",
  "trace_id": "trace-001",
  "node": "router",
  "status": "completed",
  "summary": "问题被判定为校园规章查询，路由到本地知识库检索",
  "extra": {
    "query_type": "campus_rule",
    "route": "local_rag"
  },
  "timestamp": "2026-03-18T10:10:01Z"
}
```

### 7.3.2 RetrievalEvent

用于展示命中文档与重排序结果。

```json
{
  "type": "retrieval",
  "request_id": "req-001",
  "trace_id": "trace-001",
  "items": [
    {
      "source_name": "学籍管理规定.pdf",
      "chunk_id": "chunk-01",
      "score": 0.88,
      "rerank_score": 0.93
    }
  ]
}
```

### 7.3.3 ChunkEvent

用于流式答案文本输出。

```json
{
  "type": "chunk",
  "request_id": "req-001",
  "trace_id": "trace-001",
  "content": "根据《山东大学本科生学籍管理规定》，本科生申请转专业通常需要满足..."
}
```

### 7.3.4 DoneEvent

表示本轮执行完成。

```json
{
  "type": "done",
  "request_id": "req-001",
  "trace_id": "trace-001",
  "answer": "根据学校规定，本科生申请转专业需要满足以下条件...",
  "citations": [
    {
      "source_type": "local_document",
      "source_name": "学籍管理规定.pdf",
      "chunk_id": "chunk-01",
      "score": 0.93
    }
  ],
  "latency_ms": 1842
}
```

### 7.3.5 ErrorEvent

```json
{
  "type": "error",
  "request_id": "req-001",
  "trace_id": "trace-001",
  "message": "知识库检索失败",
  "code": "RETRIEVAL_ERROR"
}
```

---

## 8. LangGraph 工作流详细建议

第一版图工作流不应过于复杂，建议固定为下面几个节点。

## 8.1 节点列表

1. `prepare_query`
2. `router`
3. `local_retriever`
4. `web_searcher`
5. `context_compressor`
6. `generator`
7. `finalizer`

## 8.2 节点职责

### `prepare_query`

- 清洗用户输入；
- 提取规范化 query；
- 初始化状态对象；
- 推送第一个 `agent_state` 事件。

### `router`

- 判断问题类型；
- 选择 `direct / local_rag / web_search / hybrid` 路径；
- 记录 `route_reason`；
- 将状态推送给前端。

### `local_retriever`

- 调用 ChromaDB 检索 Top-K；
- 结合重排序模型或 LLM 重排；
- 输出检索命中；
- 写入 `retrieved_chunks`。

### `web_searcher`

- 调用 Tavily；
- 过滤低质量结果；
- 写入 `web_results`。

### `context_compressor`

- 从本地 chunk 或网页摘要中抽取生成所需核心证据；
- 合并为压缩上下文；
- 避免直接把冗长全文送进生成阶段。

### `generator`

- 基于 `compressed_context` 生成最终答案；
- 流式推送 `chunk`；
- 累积 `final_answer`。

### `finalizer`

- 汇总 citations；
- 计算 latency；
- 持久化消息记录；
- 推送 `done` 事件。

## 8.3 条件边建议

```text
prepare_query -> router
router -> local_retriever      [route == local_rag]
router -> web_searcher         [route == web_search]
router -> local_retriever      [route == hybrid]
local_retriever -> context_compressor
web_searcher -> context_compressor
context_compressor -> generator
generator -> finalizer
```

### 为什么不建议第一版引入更多节点

因为当前目标是“路由正确 + 过程可展示 + 结果可评测”。如果继续增加：

- query rewrite 节点；
- self-check 节点；
- critique 节点；
- tool planner 节点；

会直接把重点从“自主路由”转移到“复杂 agent 框架”，这不符合你的课题中心。

---

## 9. 工程目录结构建议

建议使用 monorepo，目录如下：

```text
agentic-rag-qa/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── kb.py
│   │   │   │   ├── chat.py
│   │   │   │   ├── eval.py
│   │   │   │   └── ws_chat.py
│   │   │   └── deps.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── logging.py
│   │   │   └── websocket.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   ├── models/
│   │   │   │   ├── document.py
│   │   │   │   ├── chat.py
│   │   │   │   └── evaluation.py
│   │   │   └── repositories/
│   │   ├── schemas/
│   │   │   ├── document.py
│   │   │   ├── chat.py
│   │   │   ├── evaluation.py
│   │   │   └── ws_events.py
│   │   ├── services/
│   │   │   ├── document_service.py
│   │   │   ├── chunking_service.py
│   │   │   ├── embedding_service.py
│   │   │   ├── retrieval_service.py
│   │   │   ├── model_service.py
│   │   │   └── evaluation_service.py
│   │   ├── agent/
│   │   │   ├── state.py
│   │   │   ├── nodes/
│   │   │   │   ├── prepare_query.py
│   │   │   │   ├── router.py
│   │   │   │   ├── local_retriever.py
│   │   │   │   ├── web_searcher.py
│   │   │   │   ├── context_compressor.py
│   │   │   │   ├── generator.py
│   │   │   │   └── finalizer.py
│   │   │   └── graph.py
│   │   ├── integrations/
│   │   │   ├── zhipu_client.py
│   │   │   ├── openai_client.py
│   │   │   ├── tavily_client.py
│   │   │   └── chroma_client.py
│   │   ├── utils/
│   │   │   ├── ids.py
│   │   │   ├── time.py
│   │   │   └── markdown.py
│   │   └── main.py
│   ├── tests/
│   ├── scripts/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── kb.ts
│   │   │   ├── chat.ts
│   │   │   ├── eval.ts
│   │   │   └── ws.ts
│   │   ├── stores/
│   │   │   ├── chat.ts
│   │   │   ├── kb.ts
│   │   │   └── eval.ts
│   │   ├── types/
│   │   │   ├── chat.ts
│   │   │   ├── kb.ts
│   │   │   ├── eval.ts
│   │   │   └── ws.ts
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   ├── cot/
│   │   │   ├── kb/
│   │   │   └── eval/
│   │   ├── views/
│   │   │   ├── ChatView.vue
│   │   │   ├── KnowledgeBaseView.vue
│   │   │   ├── EvaluationView.vue
│   │   │   └── SessionHistoryView.vue
│   │   ├── router/
│   │   ├── App.vue
│   │   └── main.ts
│   ├── public/
│   └── package.json
└── docs/
    ├── development-plan.md
    └── system-spec.md
```

### 目录设计原则

- `schemas/` 与 `db/models/` 分开，避免把 API 协议和数据库实体混成一层；
- `services/` 负责具体业务逻辑；
- `agent/` 只负责运行态状态图，不承载数据库逻辑；
- `integrations/` 封装第三方依赖；
- 前端 `types/` 独立，确保 WebSocket 与 REST 的类型定义统一。

---

## 10. 全链路逻辑验证

为了满足“方案必须经过全链路逻辑验证”的要求，这里用三个问题场景走查一次设计。

## 10.1 场景 A：校园规章问题

**问题**：学校关于本科生转专业的规定是什么？

**预期链路**：

1. 前端通过 `ws/chat/{session_id}` 发送 `ask`；
2. `prepare_query` 规范化问题；
3. `router` 判定为 `campus_rule`；
4. 路由到 `local_rag`；
5. `local_retriever` 从 ChromaDB 获取相关 chunk；
6. `context_compressor` 提炼核心条款；
7. `generator` 基于证据生成答案；
8. `finalizer` 返回 `done + citations`；
9. 后端把用户消息和 assistant 消息写入 SQLite。

**验证结果**：链路闭合，且每一步都能被 WebSocket 可视化。

## 10.2 场景 B：时效性问题

**问题**：今天学校官网发布了什么关于奖学金申请的新通知？

**预期链路**：

1. `router` 判断为 `timely`；
2. 路由到 `web_search`；
3. `web_searcher` 调 Tavily；
4. `context_compressor` 抽取有效网页摘要；
5. `generator` 生成答案；
6. `done` 事件中返回外部引用链接。

**验证结果**：链路闭合，没有强行走本地知识库。

## 10.3 场景 C：普通非校园常识问题

**问题**：什么是 RAG？

**预期链路**：

- 可以走 `direct` 或 `web_search`，但第一版建议默认仍经过 `router -> context_compressor -> generator` 的统一主链；
- 如果没有本地知识需求，也可以不检索文档。

**验证结果**：结构上成立，且不会破坏单一主链路原则。

---

## 11. 本阶段交付结论

在进入真正编码前，本阶段已经完成以下冻结：

1. 冻结了核心业务对象与字段；
2. 冻结了 SQLite / ChromaDB / LangGraph State 的职责边界；
3. 冻结了第一版 REST API 范围；
4. 冻结了 WebSocket 事件协议；
5. 冻结了 LangGraph 节点与条件边；
6. 冻结了前后端工程目录骨架；
7. 通过三个场景走查验证了全链路逻辑闭环。

因此，下一步已经不应该再写“泛泛而谈的方案文档”，而应该直接开始：

- 初始化 monorepo 目录；
- 编写后端 SQLAlchemy 模型与 Pydantic schema；
- 编写前端 TypeScript 类型；
- 打通第一批 API 与 WebSocket 框架。

至此，第二阶段文档完成。
