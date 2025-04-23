"""
供 Robot 使用的RAG一站式接口
"""

from __future__ import annotations

import logging
import os
from typing import List, Dict, Any

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
        knowledge_file: str | None = None,
        top_k: int = 3,
    ) -> None:
        self.llm = LLMClient(api_key)
        self.top_k = top_k

        if knowledge_file and os.path.exists(knowledge_file):
            kb = KnowledgeBase(knowledge_file, self.llm)
            self.retriever = Retriever(kb)
        else:
            self.retriever = None
            logger.warning("No knowledge base provided; RAG fallback to zero‑shot.")

    # ---------------- 公共 ---------------- #
    def is_ready(self) -> bool:
        """
        检查是否已加载知识库
        """
        return self.retriever is not None

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
