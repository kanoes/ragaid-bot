# ───────────────────────────────────────────────────────────────
# Stage 1: 安装依赖
# ───────────────────────────────────────────────────────────────
FROM python:3.10-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 拷贝并安装依赖到 /usr/local （PREFIX）
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/usr/local -r requirements.txt

# ───────────────────────────────────────────────────────────────
# Stage 2: 运行时镜像
# ───────────────────────────────────────────────────────────────
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 从 builder 镜像拷贝已安装的包
COPY --from=builder /usr/local /usr/local

# 拷贝应用源码
COPY . .

# 暴露 Streamlit 默认端口
EXPOSE 8501

# 容器启动时执行
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
