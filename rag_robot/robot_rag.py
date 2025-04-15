import sys
import os
import json
import time
import random
from typing import List, Dict, Any, Optional
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from robot import Robot

class RagRobot(Robot):
    """
    真实的RAG机器人，使用OpenAI API和向量数据库实现真正的检索增强生成技术
    
    依赖：
    - openai: pip install openai
    - faiss-cpu: pip install faiss-cpu
    - numpy: pip install numpy
    """
    def __init__(self, environment, start=None, goal=None, robot_id=1,
                api_key=None, config_file=None, knowledge_file=None):
        """
        初始化RAG机器人
        
        参数:
            environment: 环境对象
            start: 起始位置
            goal: 目标位置
            robot_id: 机器人ID
            api_key: OpenAI API密钥
            config_file: 配置文件路径(JSON)
            knowledge_file: 知识库文件路径(JSON)
        """
        super().__init__(environment, start, goal, robot_id)
        self.name = "RAG机器人"
        
        # 用于记忆障碍物位置
        self.obstacle_memory = {}
        
        # 配置参数
        self.config = {
            "api_key": api_key,
            "embedding_model": "text-embedding-ada-002",
            "completion_model": "gpt-3.5-turbo",
            "temperature": 0.3,
            "top_k": 3  # 检索的文档数量
        }
        
        # 如果提供了配置文件，则从文件加载配置
        if config_file and os.path.exists(config_file):
            self._load_config(config_file)
        
        # 初始化OpenAI客户端和向量存储
        self._initialize_openai()
        self._initialize_vector_store()
        
        # 加载知识库
        if knowledge_file and os.path.exists(knowledge_file):
            self.load_knowledge_from_file(knowledge_file)
    
    def _load_config(self, config_file):
        """加载配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.config.update(config)
            print(f"从 {config_file} 加载配置成功")
        except Exception as e:
            print(f"加载配置文件出错: {e}")
    
    def _initialize_openai(self):
        """初始化OpenAI客户端"""
        try:
            # 确保必要的依赖已安装
            import openai
            import numpy as np
            
            # 设置API密钥
            if self.config.get("api_key"):
                openai.api_key = self.config["api_key"]
                self.openai_client = openai.OpenAI(api_key=self.config["api_key"])
                print("OpenAI客户端初始化成功")
            else:
                print("警告: 未设置OpenAI API密钥，请使用set_api_key方法设置")
                self.openai_client = None
            
        except ImportError as e:
            print(f"错误: {e}")
            print("请安装必要的依赖: pip install openai numpy faiss-cpu")
            self.openai_client = None
    
    def _initialize_vector_store(self):
        """初始化向量存储"""
        try:
            import numpy as np
            import faiss
            
            # 初始化向量存储
            self.documents = []  # 文档内容
            self.embeddings = None  # 文档嵌入
            self.faiss_index = None  # FAISS索引
            
            print("向量存储初始化成功")
            
        except ImportError as e:
            print(f"错误: {e}")
            print("请安装必要的依赖: pip install numpy faiss-cpu")
    
    def set_api_key(self, api_key):
        """设置OpenAI API密钥"""
        self.config["api_key"] = api_key
        self._initialize_openai()
    
    def save_config(self, config_file):
        """保存配置到文件"""
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            print(f"配置已保存到 {config_file}")
        except Exception as e:
            print(f"保存配置出错: {e}")
    
    def load_knowledge_from_file(self, knowledge_file):
        """从文件加载知识库"""
        try:
            with open(knowledge_file, 'r', encoding='utf-8') as f:
                knowledge = json.load(f)
                
                # 知识库可以是字典或列表
                if isinstance(knowledge, dict):
                    # 如果是字典，转换成文档列表
                    documents = []
                    for situation, content in knowledge.items():
                        if isinstance(content, dict):
                            doc = f"情境: {situation}\n"
                            for key, value in content.items():
                                doc += f"{key}: {value}\n"
                            documents.append(doc)
                        else:
                            documents.append(f"情境: {situation}\n内容: {content}")
                else:
                    # 如果是列表，直接使用
                    documents = knowledge
                
                self.add_knowledge(documents)
                print(f"从 {knowledge_file} 加载知识库成功，共 {len(documents)} 条")
                
        except Exception as e:
            print(f"加载知识库文件出错: {e}")
    
    def add_knowledge(self, documents):
        """添加知识到向量存储"""
        if not self.openai_client:
            print("错误: OpenAI客户端未初始化，请先设置API密钥")
            return
        
        if not documents:
            print("警告: 没有提供文档内容")
            return
        
        try:
            import numpy as np
            import faiss
            
            # 保存文档
            self.documents.extend(documents)
            
            # 生成嵌入
            embeddings = []
            batch_size = 20  # 批量处理以避免API限制
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i+batch_size]
                print(f"生成嵌入 {i+1}-{i+len(batch)}/{len(documents)}")
                
                response = self.openai_client.embeddings.create(
                    input=batch,
                    model=self.config["embedding_model"]
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
            
            # 转换为numpy数组
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            # 如果已有嵌入，合并新旧嵌入
            if self.embeddings is not None:
                self.embeddings = np.vstack([self.embeddings, embeddings_array])
            else:
                self.embeddings = embeddings_array
            
            # 创建或更新FAISS索引
            dimension = self.embeddings.shape[1]
            new_index = faiss.IndexFlatL2(dimension)
            new_index.add(self.embeddings)
            self.faiss_index = new_index
            
            print(f"成功添加 {len(documents)} 条知识，当前共有 {len(self.documents)} 条")
            
        except Exception as e:
            print(f"添加知识出错: {e}")
    
    def handle_obstacle(self, obstacle_position):
        """
        使用RAG技术处理障碍物
        """
        print(f"{self.name}#{self.robot_id} - 在 {obstacle_position} 处遇到障碍。")
        
        # 检查是否短时间内重复遇到同一障碍
        current_time = time.time()
        if obstacle_position in self.obstacle_memory:
            time_diff = current_time - self.obstacle_memory[obstacle_position]
            if time_diff < 5:  # 5秒内重复遇到同一障碍
                print(f"{self.name}#{self.robot_id} - 短时间内再次遇到同一障碍，可能是永久性障碍")
                # 使用"blocked_path"策略
                decision = self.rag_decision("blocked_path", obstacle_position)
            else:
                # 使用普通的"obstacle"策略
                decision = self.rag_decision("obstacle", obstacle_position)
        else:
            # 首次遇到此障碍
            decision = self.rag_decision("obstacle", obstacle_position)
        
        self.obstacle_memory[obstacle_position] = current_time
        print(f"{self.name}#{self.robot_id} - RAG决策：{decision}")
        
        # 根据决策选择行动
        if decision == "绕行" or decision == "重新规划" or decision == "探索新路径":
            # 尝试找到绕开当前障碍的路径
            self.find_alternative_path(obstacle_position)
        elif decision == "等待" or decision == "等待片刻后重试":
            # 模拟等待
            print(f"{self.name}#{self.robot_id} - 等待片刻后再尝试...")
            time.sleep(0.5)  # 模拟等待0.5秒
            # 保持当前路径，但移除第一个点以避免立即再次尝试相同的移动
            if len(self.path) > 1:
                self.path.pop(0)
        elif decision == "报告无法达到":
            print(f"{self.name}#{self.robot_id} - 路径完全阻塞，无法到达目标")
            if self.current_order:
                self.fail_current_order("路径被阻塞，无法到达目标桌位")
            else:
                # 如果没有当前订单，尝试返回后厨
                self.return_to_kitchen()
    
    def rag_decision(self, situation_type, context=None):
        """
        使用RAG技术进行决策
        """
        # 如果OpenAI客户端未初始化或知识库为空，使用备选决策方法
        if not self.openai_client or not self.documents:
            print("警告: 使用备选决策方法 (OpenAI未配置或知识库为空)")
            return self._fallback_decision(situation_type)
        
        try:
            import numpy as np
            
            # 构建查询
            robot_context = {
                "position": self.position,
                "goal": self.goal,
                "obstacle": context
            }
            query = f"机器人在位置{self.position}遇到{situation_type}情况，目标位置是{self.goal}"
            if context:
                query += f"，上下文信息: {context}"
            
            print(f"{self.name}#{self.robot_id} - RAG查询: {query}")
            
            # 生成查询嵌入
            query_embedding_response = self.openai_client.embeddings.create(
                input=query,
                model=self.config["embedding_model"]
            )
            query_embedding = np.array([query_embedding_response.data[0].embedding], dtype=np.float32)
            
            # 检索相关文档
            D, I = self.faiss_index.search(query_embedding, min(self.config["top_k"], len(self.documents)))
            retrieved_docs = [self.documents[i] for i in I[0]]
            
            # 构建提示
            system_prompt = (
                "你是一个智能送餐机器人的决策系统。你需要根据当前情况和检索到的相关知识，"
                "决定最佳的行动方案。只返回一个行动，不要解释。"
            )
            
            user_prompt = f"""
情境: {situation_type}
机器人当前位置: {self.position}
目标位置: {self.goal}
障碍位置: {context}

检索到的相关知识:
{''.join([f"- {doc}\n" for doc in retrieved_docs])}

请从以下选项中选择一个最佳行动(只返回行动名称):
- 重新规划
- 绕行
- 等待
- 报告无法达到
"""
            
            # 调用OpenAI API
            response = self.openai_client.chat.completions.create(
                model=self.config["completion_model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.config["temperature"],
                max_tokens=20
            )
            
            # 获取决策
            decision = response.choices[0].message.content.strip()
            
            # 标准化决策，确保返回的是预定义的动作之一
            valid_actions = ["重新规划", "绕行", "等待", "报告无法达到"]
            for action in valid_actions:
                if action in decision:
                    return action
            
            # 如果不匹配任何预定义动作，返回原始响应
            return decision
            
        except Exception as e:
            print(f"RAG决策出错: {e}")
            # 出错时使用备选决策
            return self._fallback_decision(situation_type)
    
    def _fallback_decision(self, situation_type):
        """当RAG决策失败时的备选决策方法"""
        # 简单的基于规则的决策
        if situation_type == "blocked_path":
            return "报告无法达到"
        elif situation_type == "obstacle":
            return "绕行"
        else:
            return "重新规划"
    
    def find_alternative_path(self, obstacle_position):
        """
        尝试找到绕开障碍物的替代路径
        """
        # 当前位置到目标的路径已被阻塞，需要找替代路径
        
        # 策略1: 尝试直接重新规划
        print(f"{self.name}#{self.robot_id} - 尝试重新规划路径...")
        new_path = self.planner.find_path(self.position, self.goal)
        
        if new_path:
            self.path = new_path
            print(f"{self.name}#{self.robot_id} - 找到新路径: {self.path}")
            return True
        
        # 策略2: 如果直接重规划失败，尝试先向周围几个方向移动，然后再规划
        print(f"{self.name}#{self.robot_id} - 直接路径规划失败，尝试探索周围区域...")
        
        # 获取当前位置的所有邻居
        neighbors = self.env.neighbors(self.position)
        
        # 按照与目标的距离排序邻居
        neighbors.sort(key=lambda pos: self.planner.heuristic(pos, self.goal))
        
        # 尝试从每个邻居位置规划到目标
        for next_pos in neighbors:
            if next_pos == obstacle_position:
                continue  # 跳过障碍位置
            
            temp_path = self.planner.find_path(next_pos, self.goal)
            if temp_path:
                # 找到从邻居到目标的路径，先移动到这个邻居
                self.path = [self.position, next_pos] + temp_path[1:]
                print(f"{self.name}#{self.robot_id} - 找到绕行路径，经过 {next_pos}")
                return True
        
        print(f"{self.name}#{self.robot_id} - 无法找到任何有效的替代路径")
        return False
        
    def simulate_with_dynamic_obstacles(self, max_steps=50, obstacle_probability=0.1):
        """
        使用动态障碍物模拟机器人配送
        obstacle_probability: 每一步随机生成临时障碍的概率
        """
        if not self.goal:
            print(f"{self.name}#{self.robot_id} - 未设置目标位置，无法开始模拟")
            return False
            
        self.plan_path()
        steps = 0
        
        # 记录原始网格状态以便恢复
        original_grid = [row.copy() for row in self.env.grid]
        
        try:
            while self.position != self.goal and self.path is not None:
                print(f"步骤 {steps}：{self.name}#{self.robot_id} - 当前位置 {self.position}")
                self.env.display(self.path, self.position)
                
                # 随机生成临时障碍物
                if random.random() < obstacle_probability and len(self.path) > 1:
                    # 在下一个位置可能生成临时障碍
                    next_position = self.path[1]
                    if self.env.is_free(next_position):
                        # 临时将其设为障碍
                        x, y = next_position
                        self.env.grid[x][y] = 1
                        print(f"{self.name}#{self.robot_id} - 前方出现临时障碍 {next_position}")
                
                # 尝试移动
                self.move()
                steps += 1
                
                # 移动后清除临时障碍（恢复原始状态）
                for i in range(self.env.height):
                    for j in range(self.env.width):
                        if original_grid[i][j] == 0 and self.env.grid[i][j] == 1:
                            # 恢复临时障碍为通行区域
                            self.env.grid[i][j] = 0
                
                if steps > max_steps:
                    print(f"{self.name}#{self.robot_id} - 仿真结束：步数过多。")
                    if self.current_order:
                        self.fail_current_order("模拟步数超限")
                    break
                    
            if self.position == self.goal:
                print(f"{self.name}#{self.robot_id} - 任务完成，在 {steps} 步后到达目标 {self.position}。")
                self.on_goal_reached()
                return True
                
            return False
            
        finally:
            # 恢复原始网格状态
            self.env.grid = [row.copy() for row in original_grid] 