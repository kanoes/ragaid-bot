# RAG システム

このモジュールは、レストラン配達ロボットのための検索拡張生成（Retrieval-Augmented Generation）システムを提供します。

## 構成要素

- **知識ベース（KnowledgeBase）**: JSONファイルからのデータ読み込み、FAISSベクトルインデックス作成・管理
- **検索エンジン（Retriever）**: クエリに関連する知識の検索
- **LLMクライアント（LLMClient）**: OpenAI APIとの通信
- **RAGモジュール（RAGModule）**: ロボット制御システムのためのワンストップRAGインターフェース
- **プロンプトヘルパー（PromptHelper）**: プロンプト生成と出力の整形

## 新しいベクトル検索機能

以前のバージョンでは単純なJSONファイルを検索していましたが、このバージョンではFAISSベクトルデータベースを使用した高度なセマンティック検索を実装しています：

1. テキストをベクトル化（OpenAI Embedding API使用）
2. ベクトル間の類似度に基づいて検索
3. 知識ベースの保存と再利用
4. JSONファイルの自動読み込みと更新

## 使用方法

### 基本的な使い方

```python
from robot.rag import RAGModule

# 初期化（APIキーは.envファイルまたは環境変数から読み込まれます）
rag = RAGModule()

# クエリを実行
answer = rag.query_answer("レストランでの注文処理の優先順位は？")
print(answer)
```

### ロボット意思決定への活用

```python
from robot.rag import RAGModule

# RAGモジュールの初期化
rag = RAGModule()

# 障害物回避の決定
decision = rag.make_decision(
    'obstacle',
    robot_id=1,
    position=(10, 20),
    goal=(50, 50), 
    context=(12, 20)  # 障害物の位置
)
print(f"決定された行動: {decision}")
```

## 知識ベースの管理

### 知識ファイルの形式

知識ファイルは `robot/rag/knowledge` ディレクトリに JSON 形式で保存します：

```json
[
  {
    "content": "ロボットは障害物を検出した場合、まず右回りで回避を試みる。",
    "source": "navigation_manual",
    "type": "rule",
    "priority": "high"
  },
  {
    "content": "同じ目的地に向かうロボットが複数ある場合、最も近いロボットが担当する。",
    "source": "efficiency_guidelines",
    "type": "rule",
    "priority": "medium"
  }
]
```

または、シンプルな配列形式も使えます：

```json
[
  "優先処理奇数訂单",
  "3号テーブルの注文は最後に処理する"
]
```

### 知識ベースの更新

知識ファイルを更新した後、ベクトルデータベースを更新するには：

- **スクリプトを使用する方法**:

```bash
python -m robot.rag.update_knowledge
```

オプション：

- `--knowledge-dir` - 知識ディレクトリのパス
- `--vector-db-dir` - ベクトルDBディレクトリのパス
- `--api-key` - OpenAI APIキー
- `-v, --verbose` - 詳細ログを表示

- **プログラム内での更新**:

```python
from robot.rag import RAGModule

rag = RAGModule()
rag.update_knowledge_base()
```

## ベクトルデータベースの保存場所

デフォルトでは、ベクトルデータベースは `robot/rag/knowledge/vector_db` ディレクトリに保存されます。
異なる場所に保存したい場合は、初期化時に `vector_db_dir` パラメータで指定できます：

```python
rag = RAGModule(vector_db_dir="/path/to/vector_db")
```

## 依存関係

- `faiss-cpu`: 高速なベクトル検索
- `openai`: OpenAI API呼び出し
- `numpy`: 数値計算
- `python-dotenv`: 環境変数の読み込み
