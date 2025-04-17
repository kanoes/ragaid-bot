# robot.rag — Retrieval‑Augmented Generation 子包

本目录为 **AIEnhancedRobot** 提供“检索 + 生成”能力。  
核心目标：在机器人遇到障碍或复杂情境时，利用知识库与 LLM 产出 **可执行决策**  
（目前支持 `reroute` 绕行、`wait` 等待、`report_unreachable` 放弃）。

```
┌────────────┐      query / context
│  Robot     │──────────────┐
└────────────┘              │decision
          │                 ▼
          │       ┌───────────────────┐
          └──────►│   RAGModule       │
                  ├───────────────────┤
                  │ Retriever  (FAISS)│
                  │ LLMClient (OpenAI)│
                  │ PromptHelper      │
                  └───────────────────┘
```

---

## 目录一览

| 文件 | 功能 |
|------|------|
| **`llm_client.py`** | OpenAI Embedding / Chat API 二次封装 |
| **`knowledge_base.py`** | 读取 JSON 文档 → 生成向量 → 建立 FAISS 索引 |
| **`retriever.py`** | 基于向量索引检索 `top‑k` 相关文本 |
| **`prompt_helper.py`** | 构造系统 / 用户 Prompt；简化 LLM 输出为固定指令 |
| **`rag_module.py`** | 对外入口：`obstacle_decision()` 返回 `reroute / wait / report_unreachable` |
| **`__init__.py`** | re‑export `RAGModule` 便于 `from robot.rag import RAGModule` |
| **`README.md`** | 当前说明文档 |

---

## 运行依赖

```text
faiss-cpu>=1.7
openai>=1.14
numpy
python-dotenv    # 配置读取 .env
```

> 若只想离线测试检索，可不安装 openai；但 `RAGModule.is_ready()` 会返回 False。

---

## 环境变量

| 变量 | 作用 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | OpenAI 访问令牌 | — |
| `EMBEDDING_MODEL` | 向量化模型 | `text-embedding-ada-002` |
| `COMPLETION_MODEL` | Chat 模型 | `gpt-3.5-turbo` |
| `TEMPERATURE` | 生成温度 | `0.0` |
| `TOP_K` | 检索条数 | `3` |

可在项目根 `.env` 中配置。

---

## 知识库格式

`resources/rag_knowledge/restaurant_rule.json`

```jsonc
{
  "documents": [
    {"id": 1, "content": "如果路径被暂时阻塞，建议等待 10 秒再尝试。"},
    {"id": 2, "content": "当障碍物无法绕开时，报告不可达并返回厨房。"}
  ]
}
```

*若仅为简单文本列表，也可直接用 `["text1", "text2", ...]`。*

---

## 使用示例

```python
from robot.rag import RAGModule

rag = RAGModule(
    api_key="sk-...",
    knowledge_file="resources/rag_knowledge/restaurant_rule.json",
)

decision = rag.obstacle_decision(
    robot_id=1,
    position=(6, 2),
    goal=(2, 5),
    obstacle=(5, 2),
)
print("LLM 决策:", decision)   # reroute / wait / report_unreachable
```

在 `AIEnhancedRobot` 中，此流程被自动调用并映射到具体动作。

---

## 二次开发指南

| 需求 | 修改点 | 建议 |
|------|--------|------|
| **替换 LLM 为本地模型** | `llm_client.py` | 实现新类 `LocalLLMClient`：`embed()` & `chat()`；在 `RAGModule` 初始化时注入即可 |
| **使用向量数据库 (Pinecone, Milvus)** | `knowledge_base.py` & `retriever.py` | 抽象一个 `BaseIndex`；FAISS 实现为本地版，另写 Pinecone 实现 |
| **增加多情境决策** (如桌子选择) | `prompt_helper.py` | 为每种 `situation_type` 写 `build_xxx_query` 与 `simplify_xxx` |
| **在线增量知识** | `KnowledgeBase.add(doc)` | 追加文本 → 生成 embedding → `index.add()` |

---

## 性能提示

* **批量生成 Embedding**：`LLMClient.embed()` 已采用单批 API；大量文档时可分批并行。  
* **索引持久化**：如需加速启动，可调用 `faiss.write_index`/`read_index`，将索引保存到磁盘。  
* **成本控制**：若只想本地检索 + 规则决策，可在 `RAGModule` 里跳过 `chat()`，直接基于检索结果走规则树。

