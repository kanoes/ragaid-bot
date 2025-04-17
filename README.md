# ragaid‑bot

**ragaid‑bot** 是一个基于 Python 的 2‑D 餐厅配送机器人模拟框架，用来比较  
传统规则机器人与 **RAG（Retrieval‑Augmented Generation）增强机器人** 的
路径效率、成功率与决策表现。  

---

## 功能速览

| 功能 | 说明 |
|------|------|
| **餐厅布局** | JSON 描述房间网格，可视化 CLI 设计器 |
| **路径规划** | A\* 寻路 + 可扩展 Planner 策略 |
| **基础机器人** | 单体机器人，支持接单、移动、统计 |
| **AI 增强机器人** | 内置 RAGModule<br>• FAISS + OpenAI Embedding<br>• ChatCompletion 产出「绕行 / 等待 / 放弃」决策 |
| **动作层** | `MotionController` 负责一步移动 + 障碍应对 |
| **可视化** | Matplotlib 动画实时 / 离线 (`.gif` / `.mp4`) |
| **统计与对比** | 成功率、平均时长、路径长度 |

---

## 目录结构

```text
ragaid-bot/
├─ resources/                 # JSON 布局 & 知识库
│  ├─ my_restaurant/          # 预置餐厅布局
│  └─ rag_knowledge/          # RAG 知识库
├─ restaurant/                # 餐厅网格 & 布局解析
├─ robot/
│  ├─ motion_controller.py    # 行为执行层
│  ├─ planner.py              # PathPlanner + OrderManager
│  ├─ robot.py                # Robot / AIEnhancedRobot（调度层）
│  └─ rag/                    # RAG 子包
│      ├─ llm_client.py / …   # LLM & 向量检索
├─ visualization/             # 动画可视化
├─ main_runner.py             # 交互式 CLI
└─ main.py                    # 仅包装 run()
```

---

## 安装

环境要求：Python 3.9+

```bash
pip install -r requirements.txt
# 或手动安装
pip install numpy matplotlib faiss-cpu openai python-dotenv
```

> 若需保存 `.mp4` 请确保本机安装 [ffmpeg](https://ffmpeg.org)。

---

## 快速开始

### 1. CLI 模式（本地运行）

确保已安装 Python 3.10+ 并配置好环境变量（如 `OPENAI_API_KEY`）：

首先安装需要的插件

```bash
pip install -r requirements.txt
```

直接运行main文件

```bash
python main.py
```

---

### 2. Docker 模式（一键运行）

无需本地 Python 环境，只需安装 Docker。

1. **安装 Docker**

   - **Windows / macOS**  
     下载并安装 [Docker Desktop](https://www.docker.com/products/docker-desktop) 

2. **构建DockerImage**

   在项目根目录执行：

   ```bash
   docker-compose up --build
   ```

   - 第一次会拉取基础镜像并构建，后续构建速度极快。  

3. **运行**

   访问 http://localhost:8501 即可打开 Web 界面。


---

## 餐厅布局格式

*布局文件示例 `resources/my_restaurant/default_restaurant.json`*

```json
{
  "name": "default_restaurant",
  "layout": [
    "＃ ＃ ＃ ＃ ＃ ＃ ＃",
    "＃ * * * * * * ＃",
    "＃ * A * B * C ＃",
    "＃ * * * * * * ＃",
    "＃ * D * * * E ＃",
    "＃ * * * * * * ＃",
    "＃ * 台 台 * F ＃ P",
    "＃ ＃ ＃ ＃ ＃ ＃ ＃"
  ]
}
```

| 符号 | 含义 | 对应数值 |
|------|------|----------|
| `＃` / `W` | 墙壁 / 障碍 | 1 |
| `*` / `.`  | 空地       | 0 |
| `A‑Z`      | 桌子编号    | 2 |
| `台`       | 厨房       | 3 |
| `停` / `P` | 机器人停靠点 | 4 |

---

## 扩展指南

* **多机器人**：在 `main_runner` 中创建多个 `Robot` 实例并加入简单调度即可。  
* **接入私有 LLM**：替换 `robot/rag/llm_client.py` 中的 `LLMClient` 实现即可。  
* **更复杂底盘 / 物理碰撞**：仅需扩展 `MotionController`。  
* **布局设计器**：运行 `python restaurant/restaurant_layout.py`（TODO: 待补充 CLI）。
