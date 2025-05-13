"""
基本UIコンポーネントと設定
"""

import streamlit as st

# パフォーマンス最適化設定
ENABLE_CACHING = True  # キャッシュ最適化を有効化


def setup_page():
    """
    ページの基本設定
    """
    st.set_page_config(page_title="レストラン配達ロボットシミュレーションシステム", layout="wide")
    st.title("レストラン配達ロボットシミュレーションシステム (Web)") 

# 互換性のため、ui_baseとしてエクスポート
ui_base = {
    "ENABLE_CACHING": ENABLE_CACHING
} 