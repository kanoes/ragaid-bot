"""
知識ベース更新スクリプト

このスクリプトは、robot/rag/knowledgeディレクトリ内の
JSONファイルを読み込み、ベクトルデータベースを更新します。
"""

import argparse
import logging
import os
import sys
from typing import Optional

from .llm_client import LLMClient
from .knowledge_base import KnowledgeBase

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("knowledge_updater")

def setup_arg_parser() -> argparse.ArgumentParser:
    """コマンドライン引数パーサーの設定"""
    parser = argparse.ArgumentParser(description="RAG知識ベース更新ツール")
    
    parser.add_argument(
        "--knowledge-dir",
        type=str,
        default=None,
        help="知識ファイルディレクトリのパス（デフォルト: robot/rag/knowledge）",
    )
    
    parser.add_argument(
        "--vector-db-dir",
        type=str,
        default=None,
        help="ベクトルDBの保存先ディレクトリ（デフォルト: knowledge_dir/vector_db）",
    )
    
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="OpenAI APIキー（デフォルト: 環境変数OPENAI_API_KEYを使用）",
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="詳細なログ出力を有効にする",
    )
    
    return parser

def update_knowledge_base(
    knowledge_dir: Optional[str] = None,
    vector_db_dir: Optional[str] = None,
    api_key: Optional[str] = None,
    verbose: bool = False,
) -> bool:
    """
    知識ベースの更新を実行
    
    Args:
        knowledge_dir: 知識ディレクトリのパス
        vector_db_dir: ベクトルDBディレクトリのパス
        api_key: OpenAI APIキー
        verbose: 詳細ログを出力するかどうか
        
    Returns:
        bool: 更新が成功したかどうか
    """
    # ログレベル設定
    if verbose:
        logger.setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # モジュールのパスを設定
        if knowledge_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            knowledge_dir = os.path.join(current_dir, "knowledge")
        
        logger.info(f"知識ディレクトリ: {knowledge_dir}")
        
        # LLMクライアントの初期化
        llm = LLMClient(api_key)
        
        # 知識ベースの初期化と更新
        kb = KnowledgeBase(knowledge_dir, llm, vector_db_dir=vector_db_dir)
        kb.update_knowledge_base()
        
        logger.info("知識ベースの更新が完了しました")
        return True
        
    except ImportError as e:
        logger.error(f"必要なモジュールのインポートに失敗しました: {e}")
        return False
    except Exception as e:
        logger.error(f"知識ベース更新中にエラーが発生しました: {e}")
        return False

def main() -> int:
    """メインエントリーポイント"""
    parser = setup_arg_parser()
    args = parser.parse_args()
    
    # 知識ベース更新実行
    success = update_knowledge_base(
        knowledge_dir=args.knowledge_dir,
        vector_db_dir=args.vector_db_dir,
        api_key=args.api_key,
        verbose=args.verbose,
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    try:
        # モジュールとしてインポートされた場合は相対インポートが機能するが、
        # スクリプトとして実行された場合は親ディレクトリをシステムパスに追加する
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(os.path.dirname(script_dir))
        sys.path.insert(0, parent_dir)
        
        # コマンドライン実行
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("ユーザーによる中断")
        sys.exit(130) 