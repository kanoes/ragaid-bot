"""
KBクエリ結果をRAGに使用
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any

from .knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)

class Retriever:
    """
    検索エンジン：複数の知識ソースから関連情報を検索
    """

    def __init__(self, kb: KnowledgeBase):
        """
        初期化
        
        Args:
            kb: 知識ベースインスタンス
        """
        self.kb = kb
        logger.info("検索エンジンを初期化しました")

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        """
        クエリに基づいて関連文書を検索
        
        Args:
            query: 検索クエリ
            top_k: 取得する結果の数
            
        Returns:
            List[str]: 関連文書の内容リスト
        """
        logger.debug(f"検索クエリ: {query}")
        
        # 知識ベースから検索
        search_results = self.kb.search(query, top_k=top_k)
        
        # 結果のスコアをログに記録
        for i, doc in enumerate(search_results):
            score = doc.get('score', 0.0)
            source = doc.get('source', 'unknown')
            logger.debug(f"検索結果 #{i+1}: スコア={score:.4f}, ソース={source}")
        
        # 内容のみを抽出して返す
        contents = self.kb.get_content_from_results(search_results)
        return contents
    
    def retrieve_with_metadata(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        クエリに基づいて関連文書をメタデータ付きで検索
        
        Args:
            query: 検索クエリ
            top_k: 取得する結果の数
            
        Returns:
            List[Dict[str, Any]]: 関連文書オブジェクト（メタデータ含む）
        """
        return self.kb.search(query, top_k=top_k)
