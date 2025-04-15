import os
import json
import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union

# 尝试导入OpenAI和FAISS
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("警告: OpenAI库未安装，RAG功能将不可用")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("警告: FAISS库未安装，RAG功能将不可用")

class RagAssistant:
    """
    RAG（检索增强生成）助手类
    负责知识库管理和基于知识的决策
    """
    
    def __init__(self, api_key=None, config_file=None, knowledge_file=None):
        """
        初始化RAG助手
        
        参数:
            api_key: OpenAI API密钥
            config_file: 配置文件路径
            knowledge_file: 知识库文件路径
        """
        self.api_key = api_key
        self.config_file = config_file
        self.knowledge_file = knowledge_file
        
        # 默认配置
        self.embedding_model = "text-embedding-ada-002"
        self.completion_model = "gpt-3.5-turbo"
        self.temperature = 0.0
        self.top_k = 3
        
        # 初始化状态
        self.client = None
        self.documents = []
        self.embeddings = None
        self.index = None
        self.is_ready = False
        
        # 加载配置
        if config_file:
            self.load_config()
        
        # 初始化OpenAI客户端
        self.init_openai()
        
        # 初始化向量存储
        if knowledge_file:
            self.load_knowledge()
        
        # 验证是否就绪
        self.check_ready()
    
    def check_ready(self):
        """验证是否所有组件都已就绪"""
        self.is_ready = (
            OPENAI_AVAILABLE and 
            FAISS_AVAILABLE and 
            self.client is not None and 
            self.documents and 
            self.embeddings is not None and 
            self.index is not None
        )
        return self.is_ready
    
    def load_config(self):
        """从配置文件加载设置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 更新API密钥（如果未通过参数提供）
                if not self.api_key and "api_key" in config:
                    self.api_key = config.get("api_key")
                
                # 更新模型配置
                self.embedding_model = config.get("embedding_model", self.embedding_model)
                self.completion_model = config.get("completion_model", self.completion_model)
                self.temperature = config.get("temperature", self.temperature)
                self.top_k = config.get("top_k", self.top_k)
                
                print(f"从 {self.config_file} 加载配置成功")
                return True
            else:
                print(f"配置文件 {self.config_file} 不存在")
                return False
        except Exception as e:
            print(f"加载配置时出错: {e}")
            return False
    
    def init_openai(self):
        """初始化OpenAI客户端"""
        if not OPENAI_AVAILABLE:
            print("OpenAI库未安装，无法初始化客户端")
            return False
        
        if not self.api_key:
            print("未提供OpenAI API密钥，无法初始化客户端")
            return False
        
        try:
            self.client = OpenAI(api_key=self.api_key)
            print("OpenAI客户端初始化成功")
            return True
        except Exception as e:
            print(f"初始化OpenAI客户端时出错: {e}")
            return False
    
    def load_knowledge(self):
        """从知识库文件加载知识并创建向量索引"""
        if not os.path.exists(self.knowledge_file):
            print(f"知识库文件 {self.knowledge_file} 不存在")
            return False
        
        try:
            with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 处理不同的知识库格式
            if isinstance(data, list):
                self.documents = data
            elif isinstance(data, dict) and "documents" in data:
                self.documents = data["documents"]
            else:
                print(f"知识库格式不正确: {self.knowledge_file}")
                return False
            
            print(f"已加载 {len(self.documents)} 条知识条目")
            
            # 生成嵌入
            self.create_embeddings()
            return True
        except Exception as e:
            print(f"加载知识库时出错: {e}")
            return False
    
    def create_embeddings(self):
        """为知识条目创建嵌入向量并建立索引"""
        if not self.client or not self.documents:
            return False
        
        try:
            # 提取文本内容
            texts = [doc["content"] if isinstance(doc, dict) and "content" in doc else str(doc) 
                    for doc in self.documents]
            
            print(f"为 {len(texts)} 条知识条目创建嵌入...")
            
            # 批量创建嵌入
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=texts
            )
            
            # 提取嵌入向量
            self.embeddings = np.array([item.embedding for item in response.data])
            
            # 创建FAISS索引
            vector_dimension = len(self.embeddings[0])
            self.index = faiss.IndexFlatL2(vector_dimension)
            self.index.add(self.embeddings.astype('float32'))
            
            print(f"成功创建 {len(self.embeddings)} 个嵌入向量，维度为 {vector_dimension}")
            return True
        except Exception as e:
            print(f"创建嵌入时出错: {e}")
            return False
    
    def search_knowledge(self, query: str, top_k: int = None) -> List[Dict]:
        """
        搜索与查询最相关的知识条目
        
        参数:
            query: 查询文本
            top_k: 返回的结果数量
        
        返回:
            相关知识条目列表
        """
        if not self.is_ready:
            print("RAG助手未就绪，无法搜索知识")
            return []
        
        if top_k is None:
            top_k = self.top_k
        
        try:
            # 获取查询的嵌入向量
            query_embedding_response = self.client.embeddings.create(
                model=self.embedding_model,
                input=[query]
            )
            query_embedding = np.array([query_embedding_response.data[0].embedding]).astype('float32')
            
            # 使用FAISS搜索最近邻
            distances, indices = self.index.search(query_embedding, top_k)
            
            # 提取相关文档
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.documents):
                    doc = self.documents[idx]
                    results.append({
                        "document": doc,
                        "distance": float(distances[0][i]),
                        "relevance_score": 1.0 - float(distances[0][i]) / 2.0  # 简单转换为相关性分数
                    })
            
            return results
        except Exception as e:
            print(f"搜索知识库时出错: {e}")
            return []
    
    def make_decision(self, situation_type: str, **context) -> str:
        """
        基于当前情况和知识库做出决策
        
        参数:
            situation_type: 情境类型（如"obstacle", "table_selection"等）
            **context: 上下文参数（如机器人位置、目标等）
        
        返回:
            决策结果
        """
        if not self.is_ready:
            print("RAG助手未就绪，无法做出决策")
            return "无法决策"
        
        # 构建提示
        if situation_type == "obstacle":
            query = self.build_obstacle_query(**context)
            system_prompt = "你是一个智能机器人助手，负责帮助送餐机器人处理复杂情况。请根据提供的信息，做出最合理的决策。"
        else:
            query = f"机器人需要在{situation_type}情况下做出决策。上下文：{context}"
            system_prompt = "你是一个智能机器人助手，负责帮助送餐机器人处理各种情况。"
        
        # 检索相关知识
        relevant_docs = self.search_knowledge(query)
        
        # 构建包含相关知识的提示
        knowledge_context = ""
        if relevant_docs:
            knowledge_context = "相关知识：\n"
            for i, doc in enumerate(relevant_docs):
                content = doc["document"]["content"] if isinstance(doc["document"], dict) and "content" in doc["document"] else str(doc["document"])
                knowledge_context += f"{i+1}. {content}\n"
        
        # 生成最终提示
        full_prompt = f"{query}\n\n{knowledge_context}"
        
        try:
            # 调用OpenAI生成决策
            response = self.client.chat.completions.create(
                model=self.completion_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=self.temperature,
                max_tokens=150
            )
            
            decision = response.choices[0].message.content.strip()
            
            # 简化决策（仅返回核心决策）
            simple_decision = self.simplify_decision(decision)
            return simple_decision
        except Exception as e:
            print(f"生成决策时出错: {e}")
            return "无法决策"
    
    def build_obstacle_query(self, robot_id, position, goal, context, **kwargs) -> str:
        """构建障碍物处理的查询"""
        return (
            f"机器人#{robot_id}在位置{position}遇到障碍物，目标位置是{goal}，障碍位置是{context}。"
            f"请分析情况并给出如何处理这个障碍物的决策。"
            f"可能的决策有：绕行、等待、报告无法达到。"
        )
    
    def simplify_decision(self, decision: str) -> str:
        """
        从决策文本中提取核心决策
        例如从"我建议机器人绕过障碍物，尝试另一条路径"提取为"绕行"
        """
        decision = decision.lower()
        
        # 障碍物处理决策
        if "绕" in decision or "另一条路" in decision or "新路径" in decision or "重新规划" in decision:
            return "绕行"
        elif "等待" in decision:
            return "等待片刻后重试"
        elif "无法" in decision or "放弃" in decision or "返回" in decision:
            return "报告无法达到"
        
        # 如果无法简化，返回原始决策
        return decision 