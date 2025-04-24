"""
文档载入 + FAISS 索引管理
"""

from __future__ import annotations

import json
import logging
import os
from typing import List

import faiss

from .llm_client import LLMClient

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """
    加载 JSON 文档并构建向量索引
    """

    def __init__(
        self,
        filepath: str,
        llm: LLMClient,
        embed_model: str = "text-embedding-ada-002",
    ) -> None:
        if not os.path.exists(filepath):
            raise FileNotFoundError(filepath)
        self.filepath = filepath
        self.llm = llm
        self.embed_model = embed_model

        self.docs: List[str] = self._load_docs()
        self.index, self.embeddings = self._build_index()

    def _load_docs(self) -> List[str]:
        """
        加载 JSON 文档
        """
        with open(self.filepath, encoding="utf-8") as fp:
            data = json.load(fp)
        if isinstance(data, list):
            docs = [str(item) if not isinstance(item, dict) else item["content"] for item in data]
        elif isinstance(data, dict) and "documents" in data:
            docs = [d["content"] for d in data["documents"]]
        else:
            raise ValueError("Unsupported knowledge JSON format.")
        logger.info("Loaded %s knowledge snippets", len(docs))
        return docs

    def _build_index(self):
        """
        构建 FAISS 索引
        """
        embeds = self.llm.embed(self.docs, model=self.embed_model)
        dim = embeds.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(embeds)
        logger.info("FAISS index built, dim=%s", dim)
        return index, embeds

    def search(self, query: str, top_k: int = 3) -> List[str]:
        """
        查询
        """
        qvec = self.llm.embed([query], model=self.embed_model)
        _, idx = self.index.search(qvec, top_k)
        return [self.docs[i] for i in idx[0] if i < len(self.docs)]
