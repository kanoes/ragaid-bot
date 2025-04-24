# robot.rag — 检索与生成 (RAG) 子包

本子包为 `AIEnhancedRobot` 提供检索 + 生成能力，用于在遇到障碍或特殊场景时基于知识库与 LLM 作出**可执行决策**（`reroute`/`wait`/`report_unreachable`）。
大致流程图如下：

```text
┌────────────┐      query              ┌───────────────────┐
│  Robot     │ ──────────────────────▶ │   RAGModule       │
└────────────┘                         ├───────────────────┤
     ▲                                 │ Retriever (FAISS) │
     │      decision                   │ LLMClient (OpenAI)│
     └───────────────────────────────  │ PromptHelper      │
                                       └───────────────────┘
```

---

## 目录结构

```text
robot/rag/
├─ knowledge/           # 默认知识库目录
│  └─ restaurant_rule.json
├─ llm_client.py        # OpenAI Embedding & Chat 封装
├─ knowledge_base.py    # 知识库加载与 FAISS 索引
├─ retriever.py         # 向量检索组件
├─ prompt_helper.py     # 构造 & 简化 Prompt
├─ rag_module.py        # `RAGModule` 核心类
└─ README.md            # 本说明文档
```

---

## 环境变量

- `OPENAI_API_KEY`：OpenAI 访问令牌（必需）
- `EMBEDDING_MODEL`：向量化模型，默认 `text-embedding-ada-002`
- `COMPLETION_MODEL`：对话模型，默认 `gpt-4o`
- `TEMPERATURE`：生成温度，默认 `0.4`(未使用)
- `TOP_K`：检索条数，默认 `3`(未使用)

可在项目根目录创建 `.env` 文件配置。

## 改进建议

- 目前还只是测试版RAG，尚未真正集成检索。
- 在 `retriever.py` 中支持增量更新知识库和嵌入索引，以便在运行时快速加载新的规则，并在 `prompt_helper.py` 中加入对多轮对话上下文的管理，以提升决策准确度。
