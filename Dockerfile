# ───────────────────────────────────────────────────────────────
# ステージ1: 依存関係のインストール
# ───────────────────────────────────────────────────────────────
FROM python:3.10-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 依存関係をコピーして /usr/local （PREFIX）にインストール
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# ───────────────────────────────────────────────────────────────
# ステージ2: ランタイムイメージ
# ───────────────────────────────────────────────────────────────
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# builderイメージからインストール済みパッケージをコピー
COPY --from=builder /usr/local /usr/local

# アプリケーションソースコードをコピー
COPY . .

# Streamlitのデフォルトポートを公開
EXPOSE 8501

# コンテナ起動時に実行
CMD ["streamlit", "run", "app.py", \
    "--server.port=8501", \
    "--server.address=0.0.0.0", \
    "--server.headless=true"]
