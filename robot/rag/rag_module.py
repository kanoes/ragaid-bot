"""
供 Robot 使用的RAG一站式接口
"""

from __future__ import annotations

import logging
import os
from typing import List

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

    def obstacle_decision(
        self,
        robot_id: int,
        position,
        goal,
        obstacle,
    ) -> str:
        """
        障碍决策
        """
        query = PromptHelper.build_obstacle_query(robot_id, position, goal, obstacle)

        # 检索知识
        know: List[str] = (
            self.retriever.retrieve(query, self.top_k) if self.retriever else []
        )

        system_prompt = (
            "You are an intelligent delivery‑robot assistant. "
            "Given context and knowledge, return ONLY one of: "
            "`reroute`, `wait`, `report_unreachable`."
        )
        knowledge_block = "\n".join(f"- {k}" for k in know)
        user_prompt = f"{query}\n\nKnowledge:\n{knowledge_block}" if know else query

        raw_decision = self.llm.chat(
            system_prompt, user_prompt, temperature=0.0, max_tokens=16
        )
        return PromptHelper.simplify(raw_decision)
