"""
Streamlit Web App 主页面逻辑
"""

import gc
import streamlit as st
import pandas as pd
from .constants import logger
from .utils import available_layouts
from .ui import (
    setup_page,
    render_stats,
    render_plotly_restaurant_layout_no_cache,
    render_layout_editor,
    render_plotly_stats,
    render_plotly_robot_path,
    render_plotly_stats_extended,
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
    get_path_histories,
    set_path_histories,
)


def run():
    """
    运行Streamlit应用
    """
    # 配置页面和性能优化
    setup_page()
    init_session_state()

    # 性能优化：限制Plotly渲染过程中的内存消耗
    if "plotly_performance_tuned" not in st.session_state:
        st.session_state["plotly_performance_tuned"] = True
        # 强制垃圾回收
        gc.collect()

    # 性能优化：使用内存效率更高的绘图设置
    if "performance_config" not in st.session_state:
        st.session_state["performance_config"] = {
            "max_points_per_chart": 1000,  # 限制每个图表的最大点数
            "use_webgl": True,  # 使用WebGL渲染（如果浏览器支持）
            "batch_size": 10,  # 批处理大小
        }

    # 获取可用布局
    layouts = available_layouts()

    # --- Sidebar 布局选择 & 参数 ---
    # 渲染布局下拉框，确保后续依赖它的控件拿到最新的 restaurant
    if layouts:
        selected_layout = st.sidebar.selectbox(
            "选择餐厅布局", layouts, key="layout_select"
        )
    else:
        selected_layout = None

    # 获取当前餐厅并在切换时立即更新
    restaurant = get_restaurant()
    if selected_layout and (restaurant is None or selected_layout != restaurant.name):
        # 添加调试日志
        logger.info(f"当前餐厅: {restaurant.name if restaurant else 'None'}")
        logger.info(f"选择布局: {selected_layout}")
        
        # 加载新布局
        restaurant = handle_layout_selection(selected_layout)
        set_restaurant(restaurant)
        logger.info(f"加载餐厅布局完成: {restaurant.name}")
        
        # 强制刷新页面 - 确保UI更新
        st.rerun()

    # 其他 sidebar 控件
    use_ai = st.sidebar.checkbox("使用 RAG 智能机器人", value=False, key="use_ai")
    num_tables = (
        len(restaurant.layout.tables) if (restaurant and restaurant.layout) else 1
    )
    num_orders = st.sidebar.slider(
        "订单数量", 1, max(1, num_tables), 1, key="num_orders"
    )
    sim_button = st.sidebar.button("开始模拟", key="sim_button")

    # --- 主界面标签页 ---
    tab1, tab2, tab3 = st.tabs(["模拟器", "数据分析", "布局编辑器"])

    with tab1:
        # 可视化当前布局
        if restaurant:
            # 使用无缓存版本，确保每次都显示最新布局
            render_plotly_restaurant_layout_no_cache(restaurant)

        # 处理模拟
        if sim_button and restaurant:
            stats, path_histories = handle_simulation(restaurant, use_ai, num_orders)
            set_stats(stats)
            set_path_histories(path_histories)

        # 显示路径可视化
        path_histories = get_path_histories()
        if path_histories and restaurant:
            st.subheader("配送路径可视化")
            
            # 显示所有被分配的订单信息
            if path_histories[0].get("orders"):
                orders = path_histories[0]["orders"]
                st.write(f"**分配的所有订单 ({len(orders)}个):**")
                order_df = pd.DataFrame(orders)
                st.dataframe(order_df, use_container_width=True)
            
            # 显示路径
            st.write("**配送路径:**")
            render_plotly_robot_path(
                restaurant,
                path_histories[0]["path"],
                orders=path_histories[0].get("orders", []),
                title=f"机器人 #{path_histories[0]['robot_id']} 配送路径（从停靠点出发并返回）",
            )

    with tab2:
        # 显示统计结果
        stats = get_stats()
        if stats:
            # 基本统计
            render_stats(stats)

            # Plotly统计可视化
            render_plotly_stats(stats)

            # 扩展统计分析
            render_plotly_stats_extended(stats)

    with tab3:
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
                        st.rerun()

        # 加载或创建新布局
        if layout_to_edit != "创建新布局" and not is_editor_loaded():
            # 加载已有布局对象到编辑器
            restaurant_to_edit = handle_layout_selection(layout_to_edit)
            load_layout_to_editor(restaurant_to_edit)
            set_editor_loaded(True)
        elif layout_to_edit == "创建新布局" and is_editor_loaded():
            set_editor_loaded(False)
            st.rerun()

        # 渲染编辑器
        new_layout = render_layout_editor()

        # 保存布局按钮
        save_col1, save_col2 = st.columns([3, 1])
        with save_col1:
            layout_name = st.text_input(
                "布局名称",
                value=layout_to_edit if layout_to_edit != "创建新布局" else "",
                key="layout_name",
            )

        with save_col2:
            st.write("")
            st.write("")
            if st.button("保存布局", key="save_layout") and layout_name and new_layout:
                # 更新布局名称并保存到同一目录
                new_layout["name"] = layout_name
                saved_restaurant = handle_layout_save(new_layout)
                if saved_restaurant:
                    st.success(f"已保存布局: {layout_name}")
                    # 自动将新布局设为当前餐厅
                    set_restaurant(saved_restaurant)
