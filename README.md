# ragaid‑bot

**ragaid‑bot** 是一个基于 Python 的 2‑D 餐厅配送机器人模拟框架，用来比较  
传统规则机器人与 **RAG（Retrieval‑Augmented Generation）增强机器人** 的
路径效率、成功率与决策表现。  

---

## 功能速览

| 功能 | 说明 |
|------|------|
| **餐厅布局** | JSON 描述房间网格，可视化 CLI 设计器 |
| **路径规划** | A\* 寻路 + 可扩展 Planner 策略 |
| **基础机器人** | 单体机器人，支持接单、移动、统计 |
| **AI 增强机器人** | 内置 RAGModule<br>• FAISS + OpenAI Embedding<br>• ChatCompletion 产出「绕行 / 等待 / 放弃」决策 |
| **动作层** | `MotionController` 负责一步移动 + 障碍应对 |
| **可视化** | Matplotlib 动画实时 / 离线 (`.gif` / `.mp4`) |
| **统计与对比** | 成功率、平均时长、路径长度 |
| **模块化设计** | 清晰的责任分离，高度可扩展的应用结构 |

---

## 目录结构

```text
ragaid-bot/
├─ app/                       # Web应用模块
│  ├─ constants.py            # 应用常量定义
│  ├─ handlers.py             # UI事件处理
│  ├─ main.py                 # 主页面逻辑
│  ├─ simulation.py           # 模拟引擎
│  ├─ state.py                # 状态管理
│  ├─ ui.py                   # UI组件函数
│  ├─ utils.py                # 工具函数
│  └─ __init__.py             # 包入口
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
├─ app.py                     # Streamlit Web App 入口
└─ requirements.txt           # 依赖列表
```

---

## 应用架构设计

项目采用模块化设计模式，具有清晰的职责分离：

| 模块 | 职责 |
|------|------|
| **app/main.py** | 应用主流程与控制逻辑 |
| **app/ui.py** | 所有UI组件与渲染函数 |
| **app/handlers.py** | 处理用户交互事件 |
| **app/simulation.py** | 模拟引擎，业务核心逻辑 | 
| **app/state.py** | 应用状态管理 |
| **app/utils.py** | 通用工具函数 |
| **app/constants.py** | 常量定义 |

这种架构带来以下优势：
- **高内聚低耦合**：每个模块专注于单一职责
- **可测试性**：业务逻辑与UI分离，便于单元测试
- **可扩展性**：轻松添加新功能而不影响现有代码
- **可维护性**：定位问题和修改更加高效

---

## 安装

环境要求：Python 3.9+

```bash
pip install -r requirements.txt
# 或手动安装
pip install numpy matplotlib faiss-cpu openai python-dotenv
```

> 若需保存 `.mp4` 请确保本机安装 [ffmpeg](https://ffmpeg.org)。

---

## 快速开始

### 本地运行 (Streamlit)

```bash
pip install -r requirements.txt
streamlit run app.py
```

### Docker 模式

```bash
docker compose up --build
```

然后访问 http://localhost:8501

---

## 餐厅布局格式

*布局文件示例 `resources/my_restaurant/default_restaurant.json`*

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

* **多机器人**：在 `main_runner` 中创建多个 `Robot` 实例并加入简单调度即可。  
* **接入私有 LLM**：替换 `robot/rag/llm_client.py` 中的 `LLMClient` 实现即可。  
* **更复杂底盘 / 物理碰撞**：仅需扩展 `MotionController`。  
* **布局设计器**：运行 `python restaurant/restaurant_layout.py`（TODO: 待补充 CLI）。
* **新增UI功能**：在 `app/ui.py` 添加新组件，然后在 `app/main.py` 中整合。
* **新增业务逻辑**：扩展 `SimulationEngine` 或创建新的业务服务类。
