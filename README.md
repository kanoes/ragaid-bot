# ragaid-bot

このプロジェクトは、Pythonベースの2D配送ロボットシミュレーションフレームワークを構築し、従来の規則ベースロボットとRAG（Retrieval-Augmented Generation）強化ロボットの経路効率、成功率、意思決定などのさまざまなパフォーマンスを比較することを目的としています。

---

## 一、実験内容

1. **基本実験（通常のロボットの経路探索方法）**
   - ロボットが注文を受ける
   - ロボットが経路を計画する
   - ロボットが行動する
   - レストランの作成
2. **RAG（Retrieval-Augmented Generation）の構築**：
   - 知識ベースの作成（ベクトルデータベース）
   - リトリーバー
   - LLMリクエスト
3. **RAG（Retrieval-Augmented Generation）ロボットの構築**：
   - RAGを通常のロボットに接続する

## 二、実験データ

- **現在のデータ**：
  - 配送総時間、配送総距離、注文平均待ち時間
- **拡張可能なデータ**：
  - 障害物
  - 突発的な状況
  - その他

---

## ディレクトリ構造

```text
ragaid-bot/
├─ app/                       # Streamlit Webアプリケーション
│  ├─ constants.py            # 定数定義
│  ├─ handlers.py             # UIイベント処理
│  ├─ main.py                 # アプリケーションのメインロジック
│  ├─ simulation.py           # シミュレーションエンジン
│  ├─ state.py                # 状態管理
│  ├─ ui.py                   # UIコンポーネント
│  ├─ utils.py                # ユーティリティ関数
│  └─ __init__.py
├─ restaurant/                # レストラングリッド & 事前設定レイアウトファイル
│  ├─ restaurant_layout.py    # レイアウト解析とAPI
│  ├─ restaurant.py           # `Restaurant`クラス
│  ├─ layouts.json            # 複数の事前設定レイアウト例
│  └─ README.md               # サブパッケージの説明
├─ robot/                     # ロボットのコアロジック
│  ├─ robot.py                # `Robot` & `AIEnhancedRobot`
│  ├─ motion_controller.py    # 実行レイヤー
│  ├─ planner.py              # 経路計画と注文管理
│  ├─ rag/                    # RAGサブパッケージ
│  │  ├─ knowledge            # デフォルト知識ベース
│  │  │  └─ restaurant_rule.json
│  │  ├─ llm_client.py        # LLMインターフェースラッパー
│  │  ├─ knowledge_base.py    # 知識ベースのロードとインデックス作成
│  │  ├─ retriever.py         # ベクトル検索
│  │  ├─ prompt_helper.py     # プロンプト構築と簡略化
│  │  ├─ rag_module.py        # 意思決定インターフェース
│  │  └─ README.md            # サブパッケージの説明
│  └─ __init__.py
├─ app.py                     # Streamlitエントリーポイント
├─ Dockerfile
├─ docker-compose.yml
├─ requirements.txt           # 依存リスト
├─ memo.md                    # 開発メモ
├─ .gitignore
```

---

## クイックスタート

- Dockerをインストールして起動:

```bash
docker compose up --build
```

- アクセス先：[http://localhost:8501]

## 将来の改善点

- なし
