# ragaid-bot

このプロジェクトは、Pythonベースの2D配送ロボットシミュレーションフレームワークを構築し、従来の規則ベースロボットとRAG（Retrieval-Augmented Generation）強化ロボットの経路効率、成功率、意思決定などのさまざまなパフォーマンスを比較することを目的としています。

---

## 実験

### 実験内容

- **基本実験（通常のロボットの経路探索方法）**
  - ロボットが注文を受ける
  - ロボットが経路を計画する
  - ロボットが行動する
  - レストランの作成
- **RAG（Retrieval-Augmented Generation）の構築**
  - 知識ベースの作成（ベクトルデータベース）
  - リトリーバー
  - LLMリクエスト
- **RAG（Retrieval-Augmented Generation）ロボットの構築**
  - RAGを通常のロボットに接続する

### 実験データ

- **現在のデータ**：
  - 配送総時間、配送総距離、注文平均待ち時間
- **拡張可能なデータ**：
  - 障害物
  - 突発的な状況
  - その他

---

## 環境構築&起動

### 共通

- エクステンションをインストール（必須）

```bash
cat extensions.txt | xargs -n 1 code --install-extension
```

### venv

#### Windows環境

- 仮想環境の作成と有効化

```bash
venv\Scripts\activate
```

- 依存関係のインストール

```bash
pip install -r requirements.txt
```

- envファイルの作成（OpenAI APIキーなどが必要な場合）

```bash
echo OPENAI_API_KEY=your_api_key > .env
```

- アプリケーションの実行

```bash
streamlit run app.py
```

#### MacOS環境

- リポジトリをクローン

```bash
git clone https://github.com/yourusername/ragaid-bot.git
cd ragaid-bot
```

- 仮想環境の作成と有効化

```bash
source venv/bin/activate
```

- 依存関係のインストール

```bash
pip install -r requirements.txt
```

- envファイルの作成（OpenAI APIキーなどが必要な場合）

```bash
echo "OPENAI_API_KEY=your_api_key" > .env
```

- アプリケーションの実行

```bash
streamlit run app.py
```

---

### Docker

- envファイルを作成

- Docker Desktopを起動

- ターミナルで以下のコマンドを実行

```bash
docker compose up --build
```

- ブラウザで以下のURLにアクセス：[http://localhost:8501]

---

## 将来の改善点

なし
