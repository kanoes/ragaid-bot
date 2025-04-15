# 真实RAG机器人使用说明

## 准备工作

1. 安装必要的依赖：
   ```
   pip install openai faiss-cpu numpy matplotlib
   ```

2. 获取OpenAI API密钥：
   - 访问 https://platform.openai.com/api-keys
   - 创建一个新的API密钥
   - 记录密钥用于后续配置

## 配置步骤

### 方法1：命令行参数

直接在命令行运行时提供API密钥：
```
python main.py --rag real --api-key sk-your-openai-api-key
```

### 方法2：配置文件

1. 创建配置文件：
   ```
   cp rag_robot/config_example.json rag_robot/config.json
   ```

2. 编辑配置文件，添加您的API密钥和其他参数：
   ```json
   {
     "api_key": "sk-your-openai-api-key",
     "embedding_model": "text-embedding-ada-002",
     "completion_model": "gpt-3.5-turbo",
     "temperature": 0.3,
     "top_k": 3
   }
   ```

3. 运行时指定配置文件：
   ```
   python main.py --rag real --config rag_robot/config.json
   ```

### 方法3：交互式配置

直接运行程序并在提示时输入API密钥：
```
python main.py --rag real
```
程序会提示您输入API密钥并询问是否保存到配置文件。

## 创建知识库

1. 创建知识库文件：
   ```
   cp rag_robot/knowledge_example.json rag_robot/knowledge.json
   ```

2. 编辑知识库文件，添加您自己的知识条目。知识库是一个JSON数组，每个元素是一个字符串，描述机器人应该了解的一条知识：
   ```json
   [
     "当机器人遇到障碍物时，应该先评估障碍物的性质。如果是临时障碍，可以短暂等待后重试；如果是永久性障碍，应该重新规划路径。",
     "在餐厅环境中，拥挤区域通常是临时性障碍，机器人应该减速并等待通行。",
     "当机器人无法找到任何可行路径时，应该报告无法到达目标。"
   ]
   ```

3. 运行时指定知识库文件：
   ```
   python main.py --rag real --knowledge rag_robot/knowledge.json
   ```

## 运行程序

完整的运行命令示例：
```
python main.py --rag real --config rag_robot/config.json --knowledge rag_robot/knowledge.json
```

## 程序执行流程

1. 程序启动后会显示餐厅布局
2. 提示您输入订单信息（格式：桌号 准备时间）
3. 输入多个订单后，输入"完成"结束订单输入
4. 程序会先运行基线机器人模拟
5. 然后运行真实RAG机器人模拟
6. 最后比较两种机器人的性能差异

## 自定义RealRagRobot类

如果您想要在自己的代码中使用RealRagRobot类，可以参考以下示例：

```python
from rag_robot.robot_rag import RealRagRobot

# 创建机器人实例
robot = RealRagRobot(
    environment=my_environment,
    api_key="your-openai-api-key",
    config_file="path/to/config.json",
    knowledge_file="path/to/knowledge.json"
)

# 或者手动设置API密钥
robot.set_api_key("your-openai-api-key")

# 添加自定义知识
robot.add_knowledge([
    "机器人在遇到拥挤区域时应该减速慢行",
    "机器人应该避开易碎物品和危险区域"
])

# 为机器人分配订单
robot.assign_order(my_order)

# 机器人开始移动
robot.move()
```

## 调整真实RAG机器人的参数

您可以通过编辑配置文件来调整RAG机器人的行为：

- `embedding_model`：用于生成嵌入的模型
- `completion_model`：用于生成决策的模型
- `temperature`：控制生成文本的多样性，较低的值会使输出更加确定
- `top_k`：检索的知识条目数量

## 故障排除

1. 如果遇到导入错误，请确保已安装所有必要的依赖
2. 如果API调用失败，请检查API密钥是否正确
3. 如果生成的决策不符合预期，可以尝试：
   - 添加更多相关知识条目
   - 调整temperature参数
   - 增加top_k检索更多相关知识 