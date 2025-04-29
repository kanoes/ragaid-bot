"""
基础UI组件和设置
"""

import streamlit as st

# 性能优化设置
ENABLE_CACHING = True  # 启用缓存优化


def setup_page():
    """
    页面基本设置
    """
    st.set_page_config(page_title="レストラン配達ロボットシミュレーションシステム", layout="wide")
    st.title("レストラン配達ロボットシミュレーションシステム (Web)") 

# 为了兼容性，导出为ui_base
ui_base = {
    "ENABLE_CACHING": ENABLE_CACHING
} 