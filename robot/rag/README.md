# robot.rag — 検索と生成 (RAG) サブパッケージ

このサブパッケージは `AIEnhancedRobot` に検索 + 生成機能を提供し、障害物や特殊なシーンに遭遇した際に知識ベースとLLMに基づいて**実行可能な決定**（`reroute`/`wait`/`report_unreachable`）を行うために使用されます。
大まかなフロー図は以下の通りです：

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

## ディレクトリ構造

```text
robot/rag/
├─ knowledge/           # デフォルト知識ベースディレクトリ
│  └─ restaurant_rule.json
├─ llm_client.py        # OpenAI Embedding & Chat ラッパー
├─ knowledge_base.py    # 知識ベースのロードとFAISS索引
├─ retriever.py         # ベクトル検索コンポーネント
├─ prompt_helper.py     # Promptの構築 & 簡略化
├─ rag_module.py        # `RAGModule` コアクラス
└─ README.md            # この説明ドキュメント
```

---

## 環境変数

- `OPENAI_API_KEY`：OpenAI アクセストークン（必須）
- `EMBEDDING_MODEL`：ベクトル化モデル、デフォルト `text-embedding-ada-002`
- `COMPLETION_MODEL`：対話モデル、デフォルト `gpt-4o`
- `TEMPERATURE`：生成温度、デフォルト `0.4`（未使用）
- `TOP_K`：検索件数、デフォルト `3`（未使用）

プロジェクトのルートディレクトリに `.env` ファイルを作成して設定できます。

---

## クイックテスト

- Dockerをインストールして起動:

```bash
docker compose up --build
```

- アクセス先：[http://localhost:8501]

- アプリケーションでテスト

## 改善提案

- 現時点ではまだテスト版RAGであり、検索が本当に統合されていません。
- `retriever.py` で知識ベースと埋め込みインデックスの増分更新をサポートし、実行時に新しいルールを迅速にロードできるようにし、`prompt_helper.py` で複数回の対話コンテキスト管理を追加して、決定の精度を向上させる。
