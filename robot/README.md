# robot — 机器人模拟核心

`robot` 包负责餐厅配送机器人的 **全栈逻辑**，并严格按照“**三层架构**”划分代码：

```
┌───────────────┐
│  调度层 Robot  │  主要交互的接口
└───────────────┘
        │   依赖
┌───────────────┐
│  规划层 Planner│  A* Path / 订单调度
└───────────────┘
        │   调用
┌───────────────┐
│  执行层 Motion │  一步移动 + 障碍应对（可插 RAG）
└───────────────┘
```

> **AIEnhancedRobot** 在执行层注入 `RAGModule`，利用知识库 + LLM 决策。

---

## 1. 目录结构

| 文件 / 目录 | 功能 |
|-------------|------|
| **`robot.py`** | `Robot`（基础）与 `AIEnhancedRobot`（RAG 加持） |
| **`motion_controller.py`** | 行为执行层：单步运动、障碍处理 |
| **`planner.py`** | <br>• `PathPlanner` —— A* 寻路<br>• `OrderManager` / `Order` —— 订单生命周期 |
| **`rag/`** | RAG 子包（向量检索 & LLM 调用）；详见 [robot/rag/README](rag/README.md) |
| **`__init__.py`** | 便捷 re‑export：`Robot`, `AIEnhancedRobot`, `PathPlanner`, `RAGModule` |

---

## 2. 快速上手

```python
from restaurant.restaurant_layout import RestaurantLayout
from restaurant.restaurant import Restaurant
from robot import Robot, AIEnhancedRobot

# 创建餐厅
layout_cfg = RestaurantLayout.parse_layout_from_strings("demo", demo_layout)
rest = Restaurant("Demo", RestaurantLayout(**layout_cfg))

# 基础机器人
bot = Robot(rest.layout, robot_id=1)

# RAG 机器人（需 OPENAI_API_KEY）
smart = AIEnhancedRobot(rest.layout, robot_id=2, knowledge_dir="resources/rag_knowledge")
```

接单并模拟：

```python
from robot.planner import Order
order = Order(order_id=1, table_id="A", prep_time=0)
bot.assign_order(order)
bot.simulate()
```

---

## 3. 关键类一览

| 类 | 层 | 主要职责 |
|----|----|----------|
| `Robot` | 调度层 | 订单分配 → 路径规划 → 驱动 `MotionController`；统计成功率/时间 |
| `AIEnhancedRobot` | 调度层 | 在构造函数内强制启用 `RAGModule`；覆盖障碍处理策略 |
| `MotionController` | 执行层 | 调用 `PathPlanner` 逐步执行，一旦遇障碍→`RAGModule` 决策 |
| `PathPlanner` | 规划层 | 标准 A*，支持无法到达时扩大搜索半径 |
| `OrderManager` | 规划层 | 订单状态机 + 多订单队列（目前 CLI Demo 用不到） |
| `RAGModule` | 智能 | 向量检索 + LLM Chat → 返回 `reroute / wait / unreachable` |

---

## 4. 依赖关系

```
Robot -> PathPlanner -> RestaurantLayout
      -> MotionController -> PathPlanner
                         -> RAGModule (仅 AIEnhancedRobot)
```

* **无循环依赖**：`MotionController` 只引用外部策略接口。
* **可热插拔**：要换 RL 控制器，仅需重写 `MotionController` 并在 `Robot` 中注入。

---

## 5. 扩展指南

| 需求 | 修改点 |
|------|--------|
| **支持多人协同** | 编写 `MultiRobotSimulator`（新文件）统一调度多个 `Robot` 实例 |
| **新底盘 / 物理引擎** | 继承 `MotionController` → `DifferentialDriveController`；重写 `step()` |
| **自定义路径规划** | 在 `planner.py` 中实现 `class DijkstraPlanner(PathPlanner): ...` |
| **替换 LLM / 本地模型** | 更改 `robot/rag/llm_client.py` 即可，不影响其他层 |
| **订单优先级 / 动态插队** | 扩展 `OrderManager` 的队列逻辑 |

---

## 6. 单元测试

建议使用 `pytest`：

```bash
pip install pytest
pytest tests/  # TODO: 自行补充 test_xxx.py
```

---

## 7. 依赖

```text
numpy
faiss-cpu          # 向量检索
openai             # LLM 调用（可替换）
python-dotenv
matplotlib         # 可视化 (optional)
```
