# robot — ロボットのコアロジック

`robot` パッケージは、レストラン配達ロボットの中核機能を担当します。
全体は三層アーキテクチャに従って設計されています：

```text
┌─────────────────┐     ┌───────────────┐     ┌──────────────────┐
│ スケジューリング層 │ --> │ 計画層         │ --> │ 実行層            │
│ Robot      　　　│     │ PathPlanner   │     │ MotionController │
│ AIEnhanced 　　　│     │ OrderManager  │     │ + RAGModule      │
└─────────────────┘     └───────────────┘     └──────────────────┘
```

- **スケジューリング層**：`Robot` / `AIEnhancedRobot` が注文の割り当て、経路計画、実行を管理します
- **計画層**：`PathPlanner` (A*) および `OrderManager` / `Order` により注文のライフサイクルを制御
- **実行層**：`MotionController` がステップ移動や障害物対応を担当し、オプションで `RAGModule` によるインテリジェントな意思決定も可能です

---

## ディレクトリ構成

```text
robot/
├─ robot.py                # `Robot` および `AIEnhancedRobot`
├─ motion_controller.py    # 実行層
├─ plan.py                 # `PathPlanner` 実装
├─ order.py                # `Order`, `OrderStatus`, `OrderManager`
├─ rag/                    # RAGサブパッケージ (検索 + 推論)
│  ├─ knowledge/           # デフォルトナレッジベース
│  │  └─ restaurant_rule.json
│  ├─ llm_client.py        # LLMクライアントラッパー
│  ├─ knowledge_base.py    # ナレッジベースのロードとインデックス化
│  ├─ retriever.py         # ベクトル検索コンポーネント
│  ├─ prompt_helper.py     # プロンプト作成と解析
│  ├─ rag_module.py        # `RAGModule` コアクラス
│  └─ README.md            # 本ドキュメント
└─ __init__.py
```

---

## 主なコンポーネント

- **Robot** / **AIEnhancedRobot**：スケジューリング層インターフェース。注文、経路、実行の管理を担当
- **PathPlanner**：A* アルゴリズム実装、拡張型サーチ戦略にも対応
- **Order** & **OrderManager**：注文エンティティとキュー管理
- **MotionController**：単ステップ移動と障害物回避ロジック
- **RAGModule**：ナレッジベース＋LLMを組み合わせたスマート推論モジュール

---

## 改善提案

- `plan.py` にて、Dijkstra法や遺伝的アルゴリズムなど複数の経路計画アルゴリズムをプラグイン形式でサポート
- `motion_controller.py` にバッテリー消費や高度な障害物回避戦略のシミュレーションを追加
- `restaurant` サイドの多様な突発イベント対応にあわせ、テストケース・テストデータを拡充することを推奨
