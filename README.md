# RAG机器人模拟项目

这个项目使用面向对象的设计方法，模拟了两种机器人在餐厅环境中的路径规划和导航：
1. 基线机器人 (BaselineRobot)：基本的路径规划功能，遇到障碍则停止
2. RAG机器人 (RagRobot)：在基线机器人基础上增加了知识库，能够在遇到障碍时进行决策并重新规划路径

## 项目结构

```
project/
├── restaurant_grid.py       # 餐厅环境网格模拟
├── path_planner.py          # A*路径规划算法
├── robot.py                 # 机器人基类
├── visualization.py         # 可视化模块（轨迹动画）
├── main.py                  # 主程序
├── baseline/                # 基线机器人
│   └── robot_baseline.py
└── rag_robot/               # RAG机器人
    └── robot_rag.py
```

## 运行方式

```
cd project
python main.py
```

## 依赖项

- Python 3.6+
- matplotlib

## 功能说明

- `restaurant_grid.py`：餐厅环境的2D网格表示，0表示可通行区域，1表示障碍物
- `path_planner.py`：使用A*算法进行路径规划
- `robot.py`：定义机器人的基本行为和属性
- `visualization.py`：将机器人的运动轨迹可视化
- `baseline/robot_baseline.py`：基线机器人实现
- `rag_robot/robot_rag.py`：RAG机器人实现，包含简单的知识库 