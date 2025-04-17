"""
OpenAI API（嵌入 + ChatCompletion）
"""

from __future__ import annotations

import logging
from typing import List

import numpy as np
from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMClient:
    """
    简单包装 OpenAI Embedding / Chat
    """

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY not provided")
        self.client = OpenAI(api_key=self.api_key)

    def embed(
        self, texts: List[str], model: str = "text-embedding-ada-002"
    ) -> np.ndarray:
        """
        嵌入文本
        """
        resp = self.client.embeddings.create(model=model, input=texts)
        return np.array([item.embedding for item in resp.data], dtype="float32")

    def chat(self, system: str, user: str, model: str = "gpt-3.5-turbo", **kw) -> str:
        """
        对话
        """
        resp = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            **kw,
        )
        return resp.choices[0].message.content.strip()
