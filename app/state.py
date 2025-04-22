"""
状态管理
"""

import streamlit as st


def init_session_state():
    """
    初始化会话状态
    """
    if "restaurant" not in st.session_state:
        st.session_state["restaurant"] = None

    if "stats" not in st.session_state:
        st.session_state["stats"] = None

    # 初始化布局编辑器状态
    if "editor_height" not in st.session_state:
        st.session_state["editor_height"] = 10

    if "editor_width" not in st.session_state:
        st.session_state["editor_width"] = 10

    if "editor_grid" not in st.session_state:
        st.session_state["editor_grid"] = [[0 for _ in range(10)] for _ in range(10)]

    if "editor_tables" not in st.session_state:
        st.session_state["editor_tables"] = {}

    if "editor_kitchen" not in st.session_state:
        st.session_state["editor_kitchen"] = []

    if "editor_parking" not in st.session_state:
        st.session_state["editor_parking"] = None

    if "editor_layout_name" not in st.session_state:
        st.session_state["editor_layout_name"] = "新布局"

    if "editor_loaded" not in st.session_state:
        st.session_state["editor_loaded"] = False


def get_restaurant():
    """
    获取当前餐厅实例
    """
    return st.session_state.get("restaurant")


def set_restaurant(restaurant):
    """
    设置当前餐厅实例
    """
    st.session_state["restaurant"] = restaurant


def get_stats():
    """
    获取模拟统计结果
    """
    return st.session_state.get("stats")


def set_stats(stats):
    """
    设置模拟统计结果
    """
    st.session_state["stats"] = stats


def get_path_histories():
    """
    获取路径历史记录
    """
    return st.session_state.get("path_histories", [])


def set_path_histories(path_histories):
    """
    设置路径历史记录
    """
    st.session_state["path_histories"] = path_histories


# 布局编辑器状态管理函数
def get_editor_height():
    """
    获取编辑器高度
    """
    return st.session_state.get("editor_height")


def set_editor_height(height):
    """
    设置编辑器高度
    """
    st.session_state["editor_height"] = height


def get_editor_width():
    """
    获取编辑器宽度
    """
    return st.session_state.get("editor_width")


def set_editor_width(width):
    """
    设置编辑器宽度
    """
    st.session_state["editor_width"] = width


def get_editor_grid():
    """
    获取编辑器网格
    """
    return st.session_state.get("editor_grid")


def set_editor_grid(grid):
    """
    设置编辑器网格
    """
    st.session_state["editor_grid"] = grid


def get_editor_tables():
    """
    获取编辑器桌子位置
    """
    return st.session_state.get("editor_tables")


def set_editor_tables(tables):
    """
    设置编辑器桌子位置
    """
    st.session_state["editor_tables"] = tables


def get_editor_kitchen():
    """
    获取编辑器厨房位置
    """
    return st.session_state.get("editor_kitchen")


def set_editor_kitchen(kitchen):
    """
    设置编辑器厨房位置
    """
    st.session_state["editor_kitchen"] = kitchen


def get_editor_parking():
    """
    获取编辑器停靠点位置
    """
    return st.session_state.get("editor_parking")


def set_editor_parking(parking):
    """
    设置编辑器停靠点位置
    """
    st.session_state["editor_parking"] = parking


def get_editor_layout_name():
    """
    获取编辑器布局名称
    """
    return st.session_state.get("editor_layout_name")


def set_editor_layout_name(name):
    """
    设置编辑器布局名称
    """
    st.session_state["editor_layout_name"] = name


def is_editor_loaded():
    """
    检查编辑器是否已加载布局
    """
    return st.session_state.get("editor_loaded", False)


def set_editor_loaded(loaded):
    """
    设置编辑器已加载状态
    """
    st.session_state["editor_loaded"] = loaded


def reset_editor():
    """
    重置编辑器状态
    """
    height = get_editor_height()
    width = get_editor_width()

    st.session_state["editor_grid"] = [[0 for _ in range(width)] for _ in range(height)]
    st.session_state["editor_tables"] = {}
    st.session_state["editor_kitchen"] = []
    st.session_state["editor_parking"] = None


def get_editor_state():
    """
    获取完整的编辑器状态
    """
    return {
        "editor_height": get_editor_height(),
        "editor_width": get_editor_width(),
        "editor_grid": get_editor_grid(),
        "editor_tables": get_editor_tables(),
        "editor_kitchen": get_editor_kitchen(),
        "editor_parking": get_editor_parking(),
        "editor_layout_name": get_editor_layout_name(),
    }


def load_layout_to_editor(restaurant):
    """
    加载餐厅布局到编辑器
    """
    if restaurant and restaurant.layout:
        set_editor_height(restaurant.layout.height)
        set_editor_width(restaurant.layout.width)
        set_editor_grid(restaurant.layout.grid)
        set_editor_tables(restaurant.layout.tables)
        set_editor_kitchen(restaurant.layout.kitchen)
        set_editor_parking(restaurant.layout.parking)
        set_editor_layout_name(restaurant.name)
        set_editor_loaded(True)
        return True
    return False
