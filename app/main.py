"""
Streamlit Web App 主页面逻辑
"""
import streamlit as st
from .constants import logger
from .utils import available_layouts
from .ui import (
    setup_page,
    render_restaurant_layout,
    render_stats,
    render_plotly_restaurant_layout,
    render_layout_editor,
)
from .handlers import (
    handle_layout_selection,
    handle_simulation,
    handle_layout_save,
    handle_layout_delete,
)
from .state import (
    init_session_state,
    get_restaurant,
    set_restaurant,
    get_stats,
    set_stats,
    load_layout_to_editor,
    is_editor_loaded,
    set_editor_loaded,
)

def run():
    """
    运行Streamlit应用
    """
    # 配置页面
    setup_page()
    init_session_state()

    # 获取可用布局
    layouts = available_layouts()

    # --- Sidebar 布局选择 & 参数 ---
    # 先渲染布局下拉框，确保后续依赖它的控件拿到最新的 restaurant
    if layouts:
        selected_layout = st.sidebar.selectbox(
            "选择餐厅布局", layouts, key="layout_select"
        )
    else:
        selected_layout = None

    # 获取当前餐厅并在切换时立即更新
    restaurant = get_restaurant()
    if selected_layout and (restaurant is None or selected_layout != restaurant.name):
        restaurant = handle_layout_selection(selected_layout)
        set_restaurant(restaurant)
        logger.info(f"加载餐厅布局: {selected_layout}")

    # 其他 sidebar 控件
    use_ai = st.sidebar.checkbox("使用 RAG 智能机器人", value=False, key="use_ai")
    num_tables = len(restaurant.layout.tables) if (restaurant and restaurant.layout) else 1
    num_orders = st.sidebar.slider(
        "订单数量", 1, max(1, num_tables), 1, key="num_orders"
    )
    sim_button = st.sidebar.button("开始模拟", key="sim_button")

    # --- 主界面标签页 ---
    tab1, tab2 = st.tabs(["模拟器", "布局编辑器"])

    with tab1:
        # 可视化当前布局
        if restaurant:
            render_plotly_restaurant_layout(restaurant)

        # 处理模拟
        if sim_button and restaurant:
            stats = handle_simulation(restaurant, use_ai, num_orders)
            set_stats(stats)

        # 显示统计结果
        stats = get_stats()
        if stats:
            render_stats(stats)

    with tab2:
        st.header("餐厅布局管理")

        # 布局列表 和 删除按钮
        col1, col2 = st.columns([3, 1])
        with col1:
            if layouts:
                layout_to_edit = st.selectbox(
                    "编辑现有布局", ["创建新布局"] + layouts, key="layout_editor_select"
                )
            else:
                st.info("当前没有可用的布局，请创建新布局")
                layout_to_edit = "创建新布局"
        with col2:
            if layout_to_edit != "创建新布局" and st.button(
                "删除所选布局", key="delete_layout"
            ):
                if handle_layout_delete(layout_to_edit):
                    st.success(f"已删除布局: {layout_to_edit}")
                    # 如果删除的布局正是当前使用的，则清除
                    if restaurant and restaurant.name == layout_to_edit:
                        set_restaurant(None)
                    st.experimental_rerun()
                else:
                    st.error("删除失败")

        st.divider()

        # 加载选中的布局到编辑器（只加载一次）
        if layout_to_edit != "创建新布局" and not is_editor_loaded():
            try:
                edit_restaurant = handle_layout_selection(layout_to_edit)
                if load_layout_to_editor(edit_restaurant):
                    st.success(f"已加载布局: {layout_to_edit}")
            except Exception as e:
                st.error(f"加载布局失败: {e}")

        # 渲染布局编辑器
        layout_data = render_layout_editor()

        # 保存编辑后的布局
        if layout_data:
            new_restaurant = handle_layout_save(layout_data)
            if new_restaurant:
                st.success(f"布局已保存: {new_restaurant.name}")
                set_editor_loaded(False)
                set_restaurant(new_restaurant)
                st.experimental_rerun()
