import os
import json
import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
import dotenv

# 自動的に環境変数をロードする
dotenv.load_dotenv()

# OpenAIとFAISSのインポートを試みる
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("警告: OpenAIライブラリがインストールされていません、RAG機能は利用できません")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("警告: FAISSライブラリがインストールされていません、RAG機能は利用できません")

class RagAssistant:
    """
    RAG（検索拡張生成）アシスタントクラス
    知識ベース管理と知識に基づく意思決定を担当
    """
    
    def __init__(self, api_key=None, knowledge_file=None):
        """
        RAGアシスタントを初期化
        
        パラメータ:
            api_key: OpenAI APIキー
            knowledge_file: 知識ベースファイルのパス
        """
        # 環境変数またはパラメータからAPIキーを取得
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.knowledge_file = knowledge_file
        
        # 環境変数から設定を取得
        self.embedding_model = os.environ.get("EMBEDDING_MODEL", "text-embedding-ada-002")
        self.completion_model = os.environ.get("COMPLETION_MODEL", "gpt-3.5-turbo")
        self.temperature = float(os.environ.get("TEMPERATURE", "0.0"))
        self.top_k = int(os.environ.get("TOP_K", "3"))
        
        # 状態を初期化
        self.client = None
        self.documents = []
        self.embeddings = None
        self.index = None
        self.is_ready = False
        
        # OpenAIクライアントを初期化
        self.init_openai()
        
        # ベクトルストレージを初期化
        if knowledge_file:
            self.load_knowledge()
        
        # 準備完了かどうかを確認
        self.check_ready()
    
    def check_ready(self):
        """すべてのコンポーネントが準備完了か確認"""
        self.is_ready = (
            OPENAI_AVAILABLE and 
            FAISS_AVAILABLE and 
            self.client is not None and 
            self.documents and 
            self.embeddings is not None and 
            self.index is not None
        )
        return self.is_ready
    
    def init_openai(self):
        """OpenAIクライアントを初期化"""
        if not OPENAI_AVAILABLE:
            print("OpenAIライブラリがインストールされていません、クライアントを初期化できません")
            return False
        
        if not self.api_key:
            print("OpenAI APIキーが提供されていません、クライアントを初期化できません")
            return False
        
        try:
            self.client = OpenAI(api_key=self.api_key)
            print("OpenAIクライアントの初期化に成功しました")
            return True
        except Exception as e:
            print(f"OpenAIクライアントの初期化中にエラーが発生しました: {e}")
            return False
    
    def load_knowledge(self):
        """知識ベースファイルから知識を読み込み、ベクトルインデックスを作成"""
        if not os.path.exists(self.knowledge_file):
            print(f"知識ベースファイル {self.knowledge_file} が存在しません")
            return False
        
        try:
            with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 異なる知識ベース形式を処理
            if isinstance(data, list):
                self.documents = data
            elif isinstance(data, dict) and "documents" in data:
                self.documents = data["documents"]
            else:
                print(f"知識ベースの形式が正しくありません: {self.knowledge_file}")
                return False
            
            print(f"{len(self.documents)} 件の知識項目を読み込みました")
            
            # 埋め込みを生成
            self.create_embeddings()
            return True
        except Exception as e:
            print(f"知識ベースの読み込み中にエラーが発生しました: {e}")
            return False
    
    def create_embeddings(self):
        """知識項目の埋め込みベクトルを作成し、インデックスを構築"""
        if not self.client or not self.documents:
            return False
        
        try:
            # テキスト内容を抽出
            texts = [doc["content"] if isinstance(doc, dict) and "content" in doc else str(doc) 
                    for doc in self.documents]
            
            print(f"{len(texts)} 件の知識項目の埋め込みを作成中...")
            
            # バッチで埋め込みを作成
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=texts
            )
            
            # 埋め込みベクトルを抽出
            self.embeddings = np.array([item.embedding for item in response.data])
            
            # FAISSインデックスを作成
            vector_dimension = len(self.embeddings[0])
            self.index = faiss.IndexFlatL2(vector_dimension)
            self.index.add(self.embeddings.astype('float32'))
            
            print(f"{len(self.embeddings)} 個の埋め込みベクトルを次元 {vector_dimension} で作成しました")
            return True
        except Exception as e:
            print(f"埋め込み作成中にエラーが発生しました: {e}")
            return False
    
    def search_knowledge(self, query: str, top_k: int = None) -> List[Dict]:
        """
        クエリに最も関連する知識項目を検索
        
        パラメータ:
            query: クエリテキスト
            top_k: 返す結果の数
        
        戻り値:
            関連知識項目のリスト
        """
        if not self.is_ready:
            print("RAGアシスタントの準備ができていません、知識を検索できません")
            return []
        
        if top_k is None:
            top_k = self.top_k
        
        try:
            # クエリの埋め込みベクトルを取得
            query_embedding_response = self.client.embeddings.create(
                model=self.embedding_model,
                input=[query]
            )
            query_embedding = np.array([query_embedding_response.data[0].embedding]).astype('float32')
            
            # FAISSで最近傍を検索
            distances, indices = self.index.search(query_embedding, top_k)
            
            # 関連文書を抽出
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.documents):
                    doc = self.documents[idx]
                    results.append({
                        "document": doc,
                        "distance": float(distances[0][i]),
                        "relevance_score": 1.0 - float(distances[0][i]) / 2.0  # 関連性スコアに簡単に変換
                    })
            
            return results
        except Exception as e:
            print(f"知識ベース検索中にエラーが発生しました: {e}")
            return []
    
    def make_decision(self, situation_type: str, **context) -> str:
        """
        現在の状況と知識ベースに基づいて意思決定を行う
        
        パラメータ:
            situation_type: 状況タイプ（例: "obstacle", "table_selection"など）
            **context: コンテキストパラメータ（例: ロボットの位置、目標など）
        
        戻り値:
            意思決定結果
        """
        if not self.is_ready:
            print("RAGアシスタントの準備ができていません、意思決定できません")
            return "意思決定できません"
        
        # プロンプトを構築
        if situation_type == "obstacle":
            query = self.build_obstacle_query(**context)
            system_prompt = "あなたはインテリジェントロボットアシスタントで、配膳ロボットが複雑な状況を処理するのを支援します。提供された情報に基づいて、最も合理的な決定を下してください。"
        else:
            query = f"ロボットは{situation_type}状況で意思決定を行う必要があります。コンテキスト：{context}"
            system_prompt = "あなたはインテリジェントロボットアシスタントで、配膳ロボットがさまざまな状況を処理するのを支援します。"
        
        # 関連知識を検索
        relevant_docs = self.search_knowledge(query)
        
        # 関連知識を含むプロンプトを構築
        knowledge_context = ""
        if relevant_docs:
            knowledge_context = "関連知識：\n"
            for i, doc in enumerate(relevant_docs):
                content = doc["document"]["content"] if isinstance(doc["document"], dict) and "content" in doc["document"] else str(doc["document"])
                knowledge_context += f"{i+1}. {content}\n"
        
        # 最終プロンプトを生成
        full_prompt = f"{query}\n\n{knowledge_context}"
        
        try:
            # OpenAIを呼び出して決定を生成
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
            
            # 決定を簡略化（コア決定のみを返す）
            simple_decision = self.simplify_decision(decision)
            return simple_decision
        except Exception as e:
            print(f"決定生成中にエラーが発生しました: {e}")
            return "意思決定できません"
    
    def build_obstacle_query(self, robot_id, position, goal, context, **kwargs) -> str:
        """障害物処理のためのクエリを構築"""
        return (
            f"ロボット#{robot_id}は位置{position}で障害物に遭遇し、目標位置は{goal}、障害物位置は{context}です。"
            f"状況を分析し、この障害物をどう処理するかの決定を提供してください。"
            f"可能な決定：迂回、待機、到達不能を報告。"
        )
    
    def simplify_decision(self, decision: str) -> str:
        """
        決定テキストからコア決定を抽出
        例えば「ロボットが障害物を回避し、別のルートを試すことをお勧めします」から「迂回」を抽出
        """
        decision = decision.lower()
        
        # 障害物処理決定
        if "回避" in decision or "別のルート" in decision or "新しい経路" in decision or "再計画" in decision:
            return "迂回"
        elif "待機" in decision:
            return "しばらく待ってから再試行"
        elif "不能" in decision or "諦め" in decision or "戻る" in decision:
            return "到達不能を報告"
        
        # 簡略化できない場合は元の決定を返す
        return decision 