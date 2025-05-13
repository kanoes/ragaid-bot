"""
供 Robot 使用的RAG一站式接口
"""

from __future__ import annotations

import logging
import os
from typing import List, Dict, Any, Tuple

from .llm_client import LLMClient
from .knowledge_base import KnowledgeBase
from .prompt_helper import PromptHelper
from .retriever import Retriever

logger = logging.getLogger(__name__)


class RAGModule:
    """
    Robot 调用的智能决策模块
    """

    def __init__(
        self,
        api_key: str | None = None,
        knowledge_dir: str | None = None,
        vector_db_dir: str | None = None,
        top_k: int = 3,
    ) -> None:
        """
        初期化

        Args:
            api_key: OpenAI API キー
            knowledge_dir: 知識ディレクトリパス
            vector_db_dir: ベクトルDB保存ディレクトリ
            top_k: 検索で取得する結果数
        """
        self.llm = LLMClient(api_key)
        self.top_k = top_k
        
        # 知識ディレクトリのデフォルト値を設定
        if knowledge_dir is None:
            # モジュールのディレクトリを取得
            module_dir = os.path.dirname(os.path.abspath(__file__))
            knowledge_dir = os.path.join(module_dir, "knowledge")
        
        # 知識ベースとレトリーバーを初期化
        if os.path.exists(knowledge_dir):
            kb = KnowledgeBase(knowledge_dir, self.llm, vector_db_dir=vector_db_dir)
            self.retriever = Retriever(kb)
            logger.info(f"知識ベースを初期化しました: {knowledge_dir}")
        else:
            self.retriever = None
            logger.warning(f"知識ディレクトリが見つかりません: {knowledge_dir}; RAGはゼロショットにフォールバックします。")

    # ---------------- 公共 ---------------- #
    def is_ready(self) -> bool:
        """
        检查是否已加载知识库
        """
        return self.retriever is not None

    def update_knowledge_base(self) -> bool:
        """
        知識ベースを更新する
        
        Returns:
            bool: 成功したかどうか
        """
        if not self.retriever:
            logger.error("知識ベースが初期化されていません")
            return False
        
        try:
            self.retriever.kb.update_knowledge_base()
            logger.info("知識ベースを更新しました")
            return True
        except Exception as e:
            logger.error(f"知識ベース更新エラー: {e}")
            return False

    def obstacle_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取面对障碍时的决策方案
        
        注意: 此方法当前未使用，但保留作为未来扩展点，用于处理机器人遇到障碍时的特殊决策
        
        Args:
            context: 决策上下文，包含机器人状态、障碍物信息等
            
        Returns:
            dict: 决策结果，包含行动建议
        """
        query = self._format_obstacle_prompt(context)
        return self._get_rag_decision(query)
    
    def query_answer(self, query: str, use_rag: bool = True) -> str:
        """
        问答功能
        
        根据用户查询生成回答，可选择是否使用RAG增强
        
        Args:
            query: 用户问题
            use_rag: 是否使用检索增强
            
        Returns:
            str: LLM回答
        """
        context = []
        if use_rag and self.is_ready():
            # 检索相关文档
            context = self._get_rag_context(query)
            
        # 构建系统提示
        system_prompt = "你是一个知识丰富的助手，请依据提供的上下文回答问题。"
        if context:
            # 将检索到的文档添加到系统提示中
            system_prompt += "\n\n相关参考信息:\n" + "\n\n".join([f"- {doc}" for doc in context])
        
        # 调用LLM生成回答
        return self.llm.chat(system=system_prompt, user=query)
    
    def trigger_layer(self, event: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        触发层：在特定事件触发时调用思考层和决策层
        """
        if event == 'plan':
            query = PromptHelper.build_plan_query(
                robot_id=context.get('robot_id', 0),
                start=context.get('start'),
                goal=context.get('goal'),
            )
        elif event == 'obstacle':
            query = PromptHelper.build_obstacle_query(
                robot_id=context.get("robot_id", 0),
                position=context.get("position", (0, 0)),
                goal=context.get("goal", (0, 0)),
                obstacle=context.get("obstacle", (0, 0)),
            )
        else:
            raise ValueError(f"Unknown event type: {event}")

        raw_response, docs = self.thinking_layer(query, use_rag=True)
        action = self.decision_layer(raw_response)
        return {
            "action": action,
            "raw_response": raw_response,
            "context_used": bool(docs),
            "context_docs": docs,
        }

    def thinking_layer(self, query: str, use_rag: bool = True) -> Tuple[str, List[str]]:
        """
        思考层：检索知识并调用LLM生成回答，返回(raw_response, context)
        """
        context = self._get_rag_context(query) if use_rag and self.is_ready() else []
        system_prompt = "你是一个知识丰富的助手，请依据提供的上下文回答问题。"
        if context:
            system_prompt += "\n\n相关参考信息:\n" + "\n\n".join([f"- {doc}" for doc in context])
        raw_response = self.llm.chat(system=system_prompt, user=query)
        return raw_response, context

    def decision_layer(self, raw_response: str) -> str:
        """
        决策层：将LLM响应结果转化为简化的动作
        """
        return PromptHelper.simplify(raw_response)

    def make_decision(self, situation_type: str, **kwargs) -> str:
        """
        决策接口：根据事件类型和上下文返回动作
        """
        # 根据事件类型映射上下文
        context: Dict[str, Any]
        if situation_type == 'obstacle':
            context = {
                'robot_id': kwargs.get('robot_id', 0),
                'position': kwargs.get('position'),
                'goal': kwargs.get('goal'),
                'obstacle': kwargs.get('context'),
            }
        elif situation_type == 'plan':
            context = {
                'robot_id': kwargs.get('robot_id', 0),
                'start': kwargs.get('start'),
                'goal': kwargs.get('goal'),
            }
        else:
            context = kwargs  # 其他事件直接使用原始kwargs
        result = self.trigger_layer(situation_type, context)
        return result.get('action', '')

    # ---------------- 私有 ---------------- #
    def _get_rag_context(self, query: str) -> List[str]:
        """
        获取RAG上下文
        
        使用检索器从知识库中找出与查询最相关的文档
        
        Args:
            query: 用户问题
            
        Returns:
            List[str]: 检索到的相关文档列表
        """
        if self.retriever:
            return self.retriever.retrieve(query, self.top_k)
        return []
    
    def _format_obstacle_prompt(self, context: Dict[str, Any]) -> str:
        """格式化障碍物提示词"""
        return PromptHelper.build_obstacle_query(
            robot_id=context.get("robot_id", 0),
            position=context.get("position", (0, 0)),
            goal=context.get("goal", (0, 0)),
            obstacle=context.get("obstacle", (0, 0)),
        )
    
    def _get_rag_decision(self, query: str) -> Dict[str, Any]:
        """基于RAG获取决策结果"""
        context = self._get_rag_context(query) if self.is_ready() else []
        
        system_prompt = "你是机器人控制器，依据情境给出最佳决策。"
        if context:
            system_prompt += "\n\n参考知识：\n" + "\n".join([f"- {doc}" for doc in context])
        
        decision = self.llm.chat(system=system_prompt, user=query)
        simplified = PromptHelper.simplify(decision)
        
        return {
            "action": simplified,
            "raw_response": decision,
            "context_used": bool(context),
        }
