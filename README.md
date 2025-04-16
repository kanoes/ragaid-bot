# 餐厅送餐机器人模拟系统

这是一个基于Python的餐厅送餐机器人模拟系统，旨在比较传统机器人与基于生成式AI和检索增强生成(RAG)技术的智能机器人在餐厅环境中的送餐效率。

## 项目概述

本项目是一个毕业设计项目，主要包含以下功能：

- 餐厅环境设计与布局编辑
- 基础送餐机器人实现
- AI增强型送餐机器人实现
- 路径规划与寻路算法
- 订单处理与管理
- 性能对比与分析

## 文件结构

```
餐厅送餐机器人模拟系统/
├── main.py                      # 主程序入口
├── create_restaurant_example.py # 餐厅布局创建示例
├── modules/
│   ├── restaurant/              # 餐厅相关模块
│   │   ├── __init__.py          # 模块初始化文件
│   │   ├── restaurant_grid.py   # 餐厅网格环境
│   │   ├── restaurant.py        # 餐厅类
│   │   ├── restaurant_layout.py # 餐厅布局工具
│   │   ├── utils.py             # 餐厅工具函数
│   │   └── layouts/             # 餐厅布局文件
│   ├── robot/                   # 机器人相关模块
│   │   ├── __init__.py          # 模块初始化文件
│   │   ├── robot.py             # 机器人基类和AI增强型机器人
│   │   └── path_planning/       # 路径规划子模块
│   │       ├── __init__.py      # 模块初始化文件
│   │       └── path_planner.py  # 路径规划算法
│   ├── rag/                     # RAG相关模块
│   │   ├── __init__.py          # 模块初始化文件
│   │   ├── rag_assistant.py     # RAG助手
│   │   └── knowledge/           # 知识库
│   ├── order/                   # 订单处理模块
│   │   ├── __init__.py          # 模块初始化文件
│   │   └── order.py             # 订单类和订单管理器
│   └── utils/                   # 工具模块
│       ├── __init__.py          # 模块初始化文件
│       └── visualization.py     # 可视化工具
└── test/                        # 测试脚本
    ├── test_load_restaurant.py  # 餐厅加载测试
    └── test_delivery_simulation.py # 送餐模拟测试
```

## 如何使用

### 安装依赖

```bash
pip install colorama numpy matplotlib
```

### 运行主程序

```bash
python main.py
```

### 创建餐厅布局

```bash
python create_restaurant_example.py
```

## 主要功能

1. **餐厅布局设计**
   - 支持自定义餐厅大小和布局
   - 包含墙壁、餐桌、厨房和停车点
   - 支持从JSON文件加载和保存布局

2. **机器人模拟**
   - 基础送餐机器人：使用基本寻路算法
   - AI增强型机器人：结合RAG技术优化路径决策

3. **性能对比**
   - 对比两种机器人的送餐效率
   - 分析成功率、平均送达时间和路径长度

## 餐厅布局格式

餐厅布局使用JSON文件存储，格式如下：

```json
{
  "layout": [
    "W W W W W W W",
    "W S S . . S W",
    "W . . . . . W",
    "W . K1 . K2 . W",
    "W . . P . . W",
    "W W W W W W W"
  ]
}
```

其中：
- W: 墙壁
- S: 座位/餐桌
- K1-K9: 厨房点
- P: 机器人停车点
- .: 空白区域

## 扩展功能

- 支持多机器人协作
- 添加真实AI服务连接
- 实现更复杂的餐厅环境和障碍物
- 优化路径规划算法

## 贡献

欢迎提交问题和改进建议！