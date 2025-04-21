"""
状态管理
"""
import streamlit as st

def init_session_state():
    """初始化会话状态"""
    if "restaurant" not in st.session_state:
        st.session_state["restaurant"] = None
    
    if "stats" not in st.session_state:
        st.session_state["stats"] = None

def get_restaurant():
    """获取当前餐厅实例"""
    return st.session_state.get("restaurant")

def set_restaurant(restaurant):
    """设置当前餐厅实例"""
    st.session_state["restaurant"] = restaurant

def get_stats():
    """获取模拟统计结果"""
    return st.session_state.get("stats")

def set_stats(stats):
    """设置模拟统计结果"""
    st.session_state["stats"] = stats 