"""
聚合 KB 查询结果为 RAG 使用
"""

from __future__ import annotations

from typing import List

from .knowledge_base import KnowledgeBase


class Retriever:
    """
    简单包装多知识库检索
    """

    def __init__(self, kb: KnowledgeBase):
        self.kb = kb

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        return self.kb.search(query, top_k=top_k)
