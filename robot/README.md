# robot — 机器人核心逻辑

`robot` 包负责餐厅配送机器人的核心功能，遵循三层架构：

```text
┌────────────┐     ┌───────────────┐     ┌──────────────────┐
│ 调度层      │ --> │ 规划层         │ --> │ 执行层            │
│ Robot      │     │ PathPlanner   │     │ MotionController │
│ AIEnhanced │     │ OrderManager  │     │ + RAGModule      │
└────────────┘     └───────────────┘     └──────────────────┘
```

- **调度层**：`Robot` / `AIEnhancedRobot` 负责订单分配、路径规划与执行
- **规划层**：`PathPlanner` (A*) 与 `OrderManager` / `Order` 实现订单生命周期管理
- **执行层**：`MotionController` 执行单步移动并处理障碍，可选 `RAGModule` 进行智能决策

## 目录结构

```text
robot/
├─ robot.py                # `Robot` & `AIEnhancedRobot`
├─ motion_controller.py    # 行为执行层
├─ plan.py                 # `PathPlanner` 实现
├─ order.py                # `Order`, `OrderStatus`, `OrderManager`
├─ rag/                    # RAG 子包 (检索 + 决策)
│  ├─ knowledge/           # 默认知识库
│  │  └─ restaurant_rule.json
│  ├─ llm_client.py        # LLM 接口封装
│  ├─ knowledge_base.py    # 知识库加载与索引
│  ├─ retriever.py         # 向量检索组件
│  ├─ prompt_helper.py     # Prompt 构建与解析
│  ├─ rag_module.py        # `RAGModule` 核心类
│  └─ README.md            # 本说明文档
└─ __init__.py
```

## 主要组件

- **Robot** / **AIEnhancedRobot**：调度层接口，管理订单、路径与执行
- **PathPlanner**：A* 算法实现，支持扩圈搜索策略
- **Order** & **OrderManager**：订单实体和队列管理
- **MotionController**：执行层，负责单步移动及障碍应对
- **RAGModule**：基于知识库 + LLM 的智能决策

## 改进建议

- 在 `plan.py` 中支持多种路径规划算法插件化（如 Dijkstra、遗传算法等）
- 在 `motion_controller.py` 中加入模拟电池消耗和避障策略
- 基于restaurant侧增加的多种突发情况，增加测试例与测试数据
