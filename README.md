# ragaid-bot

该项目旨在建立一个基于Python的2D配送机器人模拟框架，用于比较传统规则机器人与RAG（Retrieval-Augmented Generation）增强机器人的路径效率、成功率和决策等各种表现。

---

## 一、实验内容

1. **基础实验**：
   - 正常的机器人如何寻路（基于 A* 算法）。
2. **RAG（Retrieval-Augmented Generation）机器人构建**：
   - RAG 机器人是如何设计和组装的。
   - RAG 的工作机制与触发方式。
3. **模拟系统介绍**：
   - 模拟方法与运行逻辑。
   - 餐厅布局区域的定义及可自定义功能。

## 二、实验数据

- **当前数据**：
  - 配送总时间，配送总路程，订单平均等待时间
- **可扩展数据**：
  - 障碍
  - 突发状况
  - ？？？

---

## 目录结构

```text
ragaid-bot/
├─ app/                       # Streamlit Web 应用
│  ├─ constants.py            # 常量定义
│  ├─ handlers.py             # UI 事件处理
│  ├─ main.py                 # 应用主逻辑
│  ├─ simulation.py           # 模拟引擎
│  ├─ state.py                # 状态管理
│  ├─ ui.py                   # UI 组件
│  ├─ utils.py                # 工具函数
│  └─ __init__.py
├─ restaurant/                # 餐厅网格 & 预置布局文件
│  ├─ restaurant_layout.py    # 布局解析与 API
│  ├─ restaurant.py           # `Restaurant` 类
│  ├─ layouts.json            # 多个预置布局示例
│  └─ README.md               # 子包说明
├─ robot/                     # 机器人核心逻辑
│  ├─ robot.py                # `Robot` & `AIEnhancedRobot`
│  ├─ motion_controller.py    # 执行层
│  ├─ planner.py              # 路径规划与订单管理
│  ├─ rag/                    # RAG 子包
│  │  ├─ knowledge            # 默认知识库
│  │  │  └─ restaurant_rule.json
│  │  ├─ llm_client.py        # LLM 接口封装
│  │  ├─ knowledge_base.py    # 知识库加载与索引
│  │  ├─ retriever.py         # 向量检索
│  │  ├─ prompt_helper.py     # Prompt 构建与简化
│  │  ├─ rag_module.py        # 决策接口
│  │  └─ README.md            # 子包说明
│  └─ __init__.py
├─ app.py                     # Streamlit 入口
├─ Dockerfile
├─ docker-compose.yml
├─ requirements.txt           # 依赖列表
├─ memo.md                    # 开发备忘
├─ .gitignore
```

---

## 快速开始

- 安装Docker并启动:

```bash
docker compose up --build
```

- 访问：[http://localhost:8501]

## 未来改进

- 暂无
