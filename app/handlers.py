"""
UI事件处理函数
"""
import streamlit as st

from .utils import load_restaurant
from .simulation import SimulationEngine

def handle_layout_selection(layout_name):
    """处理布局选择事件"""
    return load_restaurant(layout_name)

def handle_simulation(restaurant, use_ai, num_orders):
    """处理模拟按钮点击事件"""
    with st.spinner(f"正在模拟 {num_orders} 个订单的配送过程..."):
        # 创建模拟引擎
        engine = SimulationEngine(restaurant, use_ai)
        # 运行模拟
        stats = engine.run(num_orders)
        return stats 