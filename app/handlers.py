"""
UI事件处理函数
"""

import streamlit as st

from restaurant.restaurant_layout import RestaurantLayout
from restaurant.restaurant import Restaurant
from .utils import load_restaurant, save_restaurant_layout, delete_restaurant_layout
from .simulation import SimulationEngine


def handle_layout_selection(layout_name):
    """
    处理布局选择事件
    """
    return load_restaurant(layout_name)


def handle_layout_save(layout_data):
    """
    处理布局保存事件
    
    Args:
        layout_data: dict, 布局数据

    Returns:
        Restaurant: 创建的餐厅对象
    """
    if layout_data:
        # 保存到文件
        save_restaurant_layout(layout_data)

        # 创建一个新的RestaurantLayout实例
        layout = RestaurantLayout(
            grid=layout_data.get("grid"),
            table_positions=layout_data.get("table_positions"),
            kitchen_positions=layout_data.get("kitchen_positions"),
            parking_position=layout_data.get("parking_position"),
        )

        # 创建并返回Restaurant对象
        return Restaurant(layout_data.get("name", "新布局"), layout)

    return None


def handle_layout_delete(layout_name):
    """
    处理布局删除事件

    Args:
        layout_name: str, 要删除的布局名称

    Returns:
        bool: 是否成功删除
    """
    return delete_restaurant_layout(layout_name)


def handle_simulation(restaurant, use_ai, num_orders):
    """
    处理模拟按钮点击事件
    """
    with st.spinner(f"正在模拟 {num_orders} 个订单的配送过程..."):
        # 创建模拟引擎
        engine = SimulationEngine(restaurant, use_ai)
        # 运行模拟
        stats, path_histories = engine.run(num_orders)
        return stats, path_histories
