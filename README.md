# RAG机器人模拟项目

这个项目使用面向对象的设计方法，模拟了两种机器人在餐厅环境中的路径规划和导航：
1. 基线机器人 (BaselineRobot)：基本的路径规划功能，遇到障碍则停止
2. RAG机器人 (RagRobot)：使用OpenAI API和向量数据库实现检索增强生成技术，能够在遇到障碍时进行决策并重新规划路径

## 项目结构

```
project/
├── restaurant_grid.py       # 餐厅环境网格模拟
├── restaurant_layout.py     # 创建带有20张桌子的餐厅布局
├── path_planner.py          # A*路径规划算法
├── robot.py                 # 机器人基类
├── order.py                 # 订单系统
├── visualization.py         # 可视化模块（轨迹动画）
├── main.py                  # 主程序（包含模拟运行逻辑）
├── baseline/                # 基线机器人
│   └── robot_baseline.py
└── rag_robot/               # RAG机器人
    ├── robot_rag.py         # RAG机器人实现
    ├── config_example.json  # 配置文件示例
    └── knowledge_example.json # 知识库文件示例
```

## 功能特点

- **餐厅环境模拟**：
  - 20x20网格表示餐厅空间
  - 20张桌子，每张桌子可点餐
  - 后厨区域用于订单准备
  - 支持障碍物和墙壁

- **订单系统**：
  - 用户可输入新订单（桌号+准备时间）
  - 订单状态跟踪（等待、准备中、准备完成、配送中、已送达）
  - 厨房模拟（同时处理多个订单）

- **机器人模拟**：
  - 基线机器人：遇到障碍停止并失败
  - RAG机器人：使用OpenAI API和向量数据库实现检索增强生成技术，能够在遇到障碍时进行决策并寻找替代路径

- **比较分析**：
  - 比较不同机器人的配送效率
  - 统计成功率、配送时间等指标
  - 可视化路径动画

## RAG机器人特性

RAG机器人使用OpenAI API和向量数据库实现检索增强生成技术：

1. **知识库管理**：
   - 支持从JSON文件加载知识
   - 支持动态添加新知识
   - 使用FAISS向量数据库进行高效检索

2. **决策流程**：
   - 将当前情境转换为查询
   - 检索相关知识
   - 使用LLM生成最佳决策

3. **配置选项**：
   - 可自定义API密钥、模型和参数
   - 配置文件支持
   - 错误处理和回退机制

## 安装依赖

基本依赖：
```
pip install matplotlib
```

使用RAG机器人需要额外安装：
```
pip install openai faiss-cpu numpy
```

## 运行方式

### 基本运行
```
python main.py
```

### 使用RAG机器人并指定API密钥
```
python main.py --api-key YOUR_OPENAI_API_KEY
```

### 指定配置和知识库文件
```
python main.py --config path/to/config.json --knowledge path/to/knowledge.json
```

## 创建自定义知识库

1. 复制`rag_robot/knowledge_example.json`到`rag_robot/knowledge.json`
2. 编辑该文件，添加您的知识条目。文件格式为JSON数组，每个元素是一个字符串，描述机器人应该了解的一条知识

## 配置RAG机器人

1. 复制`rag_robot/config_example.json`到`rag_robot/config.json`
2. 编辑该文件，设置您的OpenAI API密钥和其他参数

## 订单输入示例

```
订单> 5 10    # 桌号5，准备时间10秒
订单> 12 15   # 桌号12，准备时间15秒
订单> 完成    # 完成输入
```

## 依赖项

- Python 3.6+
- matplotlib
- threading
- OpenAI API (用于RAG机器人)
- FAISS (用于RAG机器人)
- numpy (用于RAG机器人)

## 如何扩展

- 在知识库中添加更多处理场景
- 增加更复杂的餐厅布局
- 添加更多类型的机器人算法
- 实现多机器人协同配送
- 扩展RAG系统使用更多的上下文信息 