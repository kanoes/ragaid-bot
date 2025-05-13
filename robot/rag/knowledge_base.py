"""
文档载入 + FAISS 索引管理
"""

from __future__ import annotations

import json
import logging
import os
import pickle
from typing import List, Dict, Any, Optional

import faiss
import numpy as np

from .llm_client import LLMClient

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """
    知識ベース管理クラス：文書のローディング、ベクトル化、保存、検索を行う
    """

    def __init__(
        self,
        knowledge_dir: str,
        llm: LLMClient,
        embed_model: str = "text-embedding-ada-002",
        vector_db_dir: str = None,
    ) -> None:
        """
        初期化

        Args:
            knowledge_dir: 知識ファイル（JSONなど）が保存されているディレクトリパス
            llm: LLMクライアントインスタンス
            embed_model: 埋め込みモデル名
            vector_db_dir: ベクトルデータベースの保存先ディレクトリ（指定がなければknowledge_dirの下にvector_dbディレクトリを作成）
        """
        self.knowledge_dir = knowledge_dir
        if not os.path.exists(knowledge_dir):
            raise FileNotFoundError(f"知識ディレクトリが見つかりません: {knowledge_dir}")
        
        self.llm = llm
        self.embed_model = embed_model
        
        # ベクトルDBの保存先ディレクトリ設定
        self.vector_db_dir = vector_db_dir or os.path.join(knowledge_dir, "vector_db")
        os.makedirs(self.vector_db_dir, exist_ok=True)
        
        # ドキュメントとベクトルインデックスの初期化
        self.docs: List[Dict[str, Any]] = []
        self.doc_contents: List[str] = []
        self.index: Optional[faiss.Index] = None
        self.embeddings: Optional[np.ndarray] = None
        
        # インデックスパス
        self.index_path = os.path.join(self.vector_db_dir, "faiss_index.bin")
        self.docs_path = os.path.join(self.vector_db_dir, "documents.pkl")
        
        # 既存のベクトルDBがあれば読み込み、なければ構築
        if os.path.exists(self.index_path) and os.path.exists(self.docs_path):
            self._load_vector_db()
        else:
            self._build_vector_db()

    def _load_docs_from_dir(self) -> List[Dict[str, Any]]:
        """
        ディレクトリから文書をロードする
        
        Returns:
            List[Dict[str, Any]]: 文書オブジェクトのリスト
        """
        all_docs = []
        
        # JSONファイルを探索
        for filename in os.listdir(self.knowledge_dir):
            if filename.endswith('.json') and not filename.startswith('.'):
                filepath = os.path.join(self.knowledge_dir, filename)
                try:
                    # JSONファイルを読み込む
                    with open(filepath, encoding="utf-8") as fp:
                        data = json.load(fp)
                    
                    # データ形式に応じて処理
                    if isinstance(data, list):
                        for i, item in enumerate(data):
                            if isinstance(item, dict) and "content" in item:
                                doc = item
                            else:
                                doc = {
                                    "content": str(item),
                                    "source": f"{filename}[{i}]",
                                    "type": "rule"
                                }
                            all_docs.append(doc)
                    elif isinstance(data, dict):
                        if "documents" in data:
                            for doc in data["documents"]:
                                if not isinstance(doc, dict):
                                    doc = {"content": str(doc)}
                                if "source" not in doc:
                                    doc["source"] = filename
                                all_docs.append(doc)
                        else:
                            # 単一文書の場合
                            doc = {
                                "content": json.dumps(data, ensure_ascii=False),
                                "source": filename,
                                "type": "document"
                            }
                            all_docs.append(doc)
                    
                    logger.info(f"ロードしました: {filename}, {len(all_docs)}件")
                except Exception as e:
                    logger.error(f"ファイル読み込みエラー {filepath}: {e}")
        
        logger.info(f"合計{len(all_docs)}件の知識スニペットをロードしました")
        return all_docs

    def _build_vector_db(self) -> None:
        """
        ベクトルデータベースを構築してディスクに保存する
        """
        # 文書をロード
        self.docs = self._load_docs_from_dir()
        self.doc_contents = [doc["content"] for doc in self.docs]
        
        if not self.doc_contents:
            logger.warning("文書が見つかりませんでした。空のインデックスを作成します。")
            # 空のインデックスを作成（1次元の埋め込みでダミーインデックスを作成）
            dummy_embed = np.zeros((1, 1536), dtype=np.float32)  # OpenAIのembedding次元は1536
            self.index = faiss.IndexFlatL2(1536)
            self.embeddings = dummy_embed
        else:
            # 文書をベクトル化
            logger.info(f"{len(self.doc_contents)}件の文書を埋め込みます...")
            self.embeddings = self.llm.embed(self.doc_contents, model=self.embed_model)
            
            # FAISSインデックスを構築
            dim = self.embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dim)
            self.index.add(self.embeddings)
            logger.info(f"FAISSインデックスを構築しました (dim={dim})")
        
        # ディスクに保存
        self._save_vector_db()

    def _save_vector_db(self) -> None:
        """
        ベクトルDBをディスクに保存
        """
        # FAISSインデックスを保存
        faiss.write_index(self.index, self.index_path)
        
        # 文書を保存
        with open(self.docs_path, 'wb') as f:
            pickle.dump({
                'docs': self.docs,
                'doc_contents': self.doc_contents
            }, f)
        
        logger.info(f"ベクトルDBを保存しました: {self.vector_db_dir}")

    def _load_vector_db(self) -> None:
        """
        保存済みのベクトルDBを読み込む
        """
        try:
            # FAISSインデックスを読み込む
            self.index = faiss.read_index(self.index_path)
            
            # 文書を読み込む
            with open(self.docs_path, 'rb') as f:
                data = pickle.load(f)
                self.docs = data['docs']
                self.doc_contents = data['doc_contents']
            
            logger.info(f"ベクトルDBを読み込みました: {len(self.doc_contents)}件")
            
            # 埋め込みを取得
            if hasattr(self.index, 'xb'):
                self.embeddings = self.index.xb
            else:
                # IndexFlatL2の場合は再構築
                logger.info("埋め込みを再構築中...")
                self.embeddings = np.zeros((len(self.doc_contents), self.index.d), dtype=np.float32)
                for i in range(len(self.doc_contents)):
                    self.embeddings[i] = self.llm.embed([self.doc_contents[i]], model=self.embed_model)[0]
            
        except Exception as e:
            logger.error(f"ベクトルDB読み込みエラー: {e}")
            # エラー時は再構築
            logger.info("ベクトルDBを再構築します...")
            self._build_vector_db()

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        クエリに基づいて最も関連性の高い文書を検索

        Args:
            query: 検索クエリ
            top_k: 返す結果の数

        Returns:
            List[Dict[str, Any]]: 検索結果の文書オブジェクト
        """
        if not self.index or not self.docs:
            logger.warning("検索するインデックスまたは文書がありません")
            return []
        
        # クエリをベクトル化
        query_vector = self.llm.embed([query], model=self.embed_model)
        
        # FAISSで検索
        distances, indices = self.index.search(query_vector, top_k)
        
        # 結果を整形
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.docs):
                doc = self.docs[idx].copy()
                doc['score'] = float(distances[0][i])
                results.append(doc)
        
        return results
    
    def get_content_from_results(self, results: List[Dict[str, Any]]) -> List[str]:
        """
        検索結果から内容のみを抽出

        Args:
            results: search()メソッドの結果

        Returns:
            List[str]: 内容のリスト
        """
        return [doc["content"] for doc in results]

    def update_knowledge_base(self) -> None:
        """
        知識ベースを更新する
        """
        logger.info("知識ベースの更新を開始します...")
        self._build_vector_db()
        logger.info("知識ベースの更新が完了しました")
