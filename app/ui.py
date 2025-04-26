"""
UI组件函数
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
from rich.text import Text
from streamlit_plotly_events import plotly_events
import pandas as pd
import time
import os

from .state import (
    get_editor_height,
    set_editor_height,
    get_editor_width,
    set_editor_width,
    get_editor_grid,
    set_editor_grid,
    get_editor_tables,
    set_editor_tables,
    get_editor_kitchen,
    set_editor_kitchen,
    get_editor_parking,
    set_editor_parking,
    get_editor_layout_name,
    set_editor_layout_name,
    reset_editor,
    get_batch_histories,
)

# 性能优化配置
ENABLE_CACHING = True  # 开启缓存优化


def setup_page():
    """
    设置页面基本配置
    """
    st.set_page_config(page_title="餐厅送餐机器人模拟系统", layout="wide")
    st.title("餐厅送餐机器人模拟系统 (Web)")


def render_sidebar(layouts, restaurant):
    """
    渲染侧边栏组件
    """
    if not layouts:
        st.error("未找到任何餐厅布局文件")
        return None, None, None

    selected = st.sidebar.selectbox("选择餐厅布局", layouts)
    use_ai = st.sidebar.checkbox("使用 RAG 智能机器人", value=False)
    num_orders = st.sidebar.slider(
        "订单数量", 1, max(1, len(restaurant.layout.tables)), 1
    )

    sim_button = st.sidebar.button("开始模拟")

    return selected, use_ai, num_orders, sim_button


def render_restaurant_layout(
    restaurant, path=None, table_positions=None, title="餐厅布局"
):
    """
    使用 HTML+CSS 渲染餐厅网格，支持路径高亮和桌子显示。

    参数:
    - restaurant: Restaurant，餐厅实例
    - path: List[Tuple[int, int]]，可选，机器人路径
    - table_positions: Dict[str, Tuple[int, int]]，可选，桌子坐标
    - title: str，标题
    """
    path = path or []
    table_positions = table_positions or {}

    st.markdown(f"### {title}")
    st.markdown("⬇️ 当前餐厅网格布局：")

    html = f"""
    <div style="display: grid; grid-template-columns: repeat({len(restaurant.layout.grid[0])}, 24px); gap: 1px;">
    """

    for row in range(len(restaurant.layout.grid)):
        for col in range(len(restaurant.layout.grid[0])):
            pos = (row, col)
            color = "#ffffff"  # 默认空地白色
            label = ""

            val = restaurant.layout.grid[row][col]

            if pos in path:
                color = "#ff4d4d"  # 路径红色
            elif val == 1:
                color = "#333333"  # 墙壁
            elif val == 3:
                color = "#f5c518"  # 厨房
            elif val == 4:
                color = "#4da6ff"  # 停靠点
            elif val == 2 or pos in table_positions.values():
                color = "#00cc66"  # 桌子绿

            # 如果是桌子，显示字母
            for name, tpos in table_positions.items():
                if tpos == pos:
                    label = name
                    break

            html += f"""
            <div style="
                width: 24px;
                height: 24px;
                background-color: {color};
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
                color: black;
                font-weight: bold;
                border: 1px solid #aaa;
            ">{label}</div>
            """

    html += "</div>"

    st.markdown(html, unsafe_allow_html=True)


@st.cache_data(ttl=300, show_spinner=False, hash_funcs={object: lambda x: id(x)}) if ENABLE_CACHING else lambda f: f
def render_plotly_restaurant_layout(_restaurant, path=None, title="餐厅布局", random_key=None):
    """
    使用Plotly渲染餐厅布局，效果更好，视觉效果类似国际象棋棋盘。

    参数:
    - _restaurant: Restaurant，餐厅实例
    - path: List[Tuple[int, int]]，可选，机器人路径
    - title: str，标题
    - random_key: str，可选，用于强制重新渲染的随机键
    """
    layout = _restaurant.layout
    grid = layout.grid
    height = layout.height
    width = layout.width

    # 创建颜色映射
    colormap = {
        0: "white",  # 空地
        1: "#333333",  # 墙壁/障碍
        2: "#00cc66",  # 桌子
        3: "#f5c518",  # 厨房
        4: "#4da6ff",  # 停靠点
    }

    # 创建标签映射
    labels = [["" for _ in range(width)] for _ in range(height)]

    # 设置桌子标签
    for table_id, pos in layout.tables.items():
        row, col = pos
        labels[row][col] = table_id

    # 设置厨房标签
    for row, col in layout.kitchen:
        labels[row][col] = "厨"

    # 设置停靠点标签
    if layout.parking:
        row, col = layout.parking
        labels[row][col] = "停"

    # 创建热力图数据
    fig = go.Figure()

    # 添加热力图 - 显示颜色块
    heatmap_z = np.array(grid)
    colorscale = [
        [0, colormap[0]],
        [0.2, colormap[0]],
        [0.2, colormap[1]],
        [0.4, colormap[1]],
        [0.4, colormap[2]],
        [0.6, colormap[2]],
        [0.6, colormap[3]],
        [0.8, colormap[3]],
        [0.8, colormap[4]],
        [1.0, colormap[4]],
    ]

    fig.add_trace(
        go.Heatmap(
            z=heatmap_z,
            colorscale=colorscale,
            showscale=False,
            hoverinfo="none",
        )
    )

    # 添加文本注释 - 显示标签
    for i in range(height):
        for j in range(width):
            if labels[i][j]:
                fig.add_annotation(
                    x=j,
                    y=i,
                    text=labels[i][j],
                    showarrow=False,
                    font=dict(size=14, color="black", family="Arial Black"),
                )

    # 添加路径点（如果有）
    if path:
        path_y, path_x = zip(*path)  # 注意Plotly的坐标系
        fig.add_trace(
            go.Scatter(
                x=path_x,
                y=path_y,
                mode="lines+markers",
                marker=dict(size=8, color="red"),
                line=dict(width=2, color="red"),
                name="路径",
            )
        )

    # 设置图表布局
    fig.update_layout(
        title=dict(text=title, font=dict(size=20)),
        width=width * 50,  # 根据网格大小调整图表大小
        height=height * 50,
        margin=dict(l=0, r=0, t=40, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=True,
            gridcolor="lightgrey",
            gridwidth=1,
            zeroline=False,
            showticklabels=False,
            range=[-0.5, width - 0.5],
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="lightgrey",
            gridwidth=1,
            zeroline=False,
            showticklabels=False,
            scaleanchor="x",
            scaleratio=1,
            range=[height - 0.5, -0.5],  # 反转Y轴使(0,0)在左上角
        ),
        # 添加国际象棋棋盘样式的背景网格
        shapes=[
            # 水平线
            *[dict(
                type="line",
                x0=-0.5, x1=width-0.5,
                y0=i-0.5, y1=i-0.5,
                line=dict(color="lightgrey", width=1)
            ) for i in range(height+1)],
            # 垂直线
            *[dict(
                type="line",
                x0=j-0.5, x1=j-0.5,
                y0=-0.5, y1=height-0.5,
                line=dict(color="lightgrey", width=1)
            ) for j in range(width+1)]
        ]
    )

    st.plotly_chart(fig)

    return fig


def _get_table_style(x, y, tables):
    """
    获取桌子的样式和标签
    """
    # 通过位置反查桌子ID
    table_id = None
    for tid, pos in tables.items():
        if pos == (x, y):
            table_id = tid
            break

    if table_id:
        return Text(table_id.center(2), style="black on cyan")
    else:
        return Text("桌", style="black on cyan")


def render_stats(stats):
    """
    显示基本统计信息
    """
    st.subheader("本次模拟数据")
    
    # 显示指标 - 删除了total_steps
    metrics = {
        "total_orders": "总订单数",
        "total_time": "总配送时间",
        "avg_waiting_time": "平均订单等待时间",
        "总配送路程": "总配送路程",
        "餐厅布局": "餐厅布局",
        "机器人类型": "机器人类型",
    }
    
    if stats:
        # 添加餐厅布局名称
        if "配送历史" in stats and stats["配送历史"] and "餐厅布局" in stats["配送历史"][0]:
            stats["餐厅布局"] = stats["配送历史"][0]["餐厅布局"]
            
        # 使用更紧凑的布局
        col1, col2 = st.columns(2)
        
        # 左半部分
        with col1:
            if "total_orders" in stats:
                st.write(f"**总订单数:** {stats['total_orders']}")
            if "total_time" in stats:
                st.write(f"**总配送时间:** {stats['total_time']:.2f}")
            if "avg_waiting_time" in stats:
                st.write(f"**平均订单等待时间:** {stats['avg_waiting_time']:.2f}")
                
        # 右半部分
        with col2:
            if "总配送路程" in stats:
                st.write(f"**总配送路程:** {stats['总配送路程']}")
            if "餐厅布局" in stats:
                st.write(f"**餐厅布局:** {stats['餐厅布局']}")
            if "机器人类型" in stats:
                st.write(f"**机器人类型:** {stats['机器人类型']}")
        
        st.write("---")
        st.caption("注: 总配送时间和路径长度计算从停靠点出发到送达所有订单并返回停靠点")


@st.cache_data(ttl=300, show_spinner=False, hash_funcs={object: lambda x: id(x)}) if ENABLE_CACHING else lambda f: f
def render_plotly_stats(stats):
    """
    使用Plotly渲染统计数据图表
    """
    if not stats:
        return
        
    # 准备基本统计数据
    key_metrics = {
        "总订单数": stats.get("total_orders", 0),
        "总配送路程": stats.get("总配送路程", 0),
        "总配送时间": stats.get("total_time", 0),
        "平均订单等待时间": stats.get("avg_waiting_time", 0)
    }
    
    # 创建条形图
    fig = go.Figure()
    
    # 添加条形
    fig.add_trace(
        go.Bar(
            x=list(key_metrics.keys()),
            y=list(key_metrics.values()),
            text=[format_value(k, v, key_metrics) for k, v in key_metrics.items()],
            textposition='auto',
            marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        )
    )
    
    # 设置布局
    fig.update_layout(
        title="核心性能指标",
        xaxis_title="指标",
        yaxis_title="数值",
        height=400,
        margin=dict(l=40, r=40, t=40, b=40)
    )
    
    # 显示图表
    st.plotly_chart(fig, use_container_width=True)


def format_value(key, value, metrics):
    """
    格式化值显示
    """
    # 简单处理，不依赖metrics中的格式化器
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)


@st.cache_data(ttl=300, show_spinner=False, hash_funcs={object: lambda x: id(x)}) if ENABLE_CACHING else lambda f: f
def render_plotly_robot_path(_restaurant, path_history, orders=None, title="机器人路径"):
    """
    渲染机器人路径的动态图表
    
    Args:
        _restaurant: Restaurant 实例
        path_history: 路径历史
        orders: 订单列表
        title: 图表标题
    """
    layout = _restaurant.layout
    grid = layout.grid
    height = layout.height
    width = layout.width

    # 创建颜色映射
    colormap = {
        0: "white",  # 空地
        1: "#333333",  # 墙壁/障碍
        2: "#00cc66",  # 桌子
        3: "#f5c518",  # 厨房
        4: "#4da6ff",  # 停靠点
    }

    # 创建标签映射
    labels = [["" for _ in range(width)] for _ in range(height)]

    # 设置桌子标签
    for table_id, pos in layout.tables.items():
        row, col = pos
        labels[row][col] = table_id

    # 设置厨房标签
    for row, col in layout.kitchen:
        labels[row][col] = "厨"

    # 设置停靠点标签
    if layout.parking:
        row, col = layout.parking
        labels[row][col] = "停"

    # 创建热力图数据
    fig = go.Figure()

    # 添加热力图 - 显示颜色块
    heatmap_z = np.array(grid)
    colorscale = [
        [0, colormap[0]],
        [0.2, colormap[0]],
        [0.2, colormap[1]],
        [0.4, colormap[1]],
        [0.4, colormap[2]],
        [0.6, colormap[2]],
        [0.6, colormap[3]],
        [0.8, colormap[3]],
        [0.8, colormap[4]],
        [1.0, colormap[4]],
    ]

    fig.add_trace(
        go.Heatmap(
            z=heatmap_z,
            colorscale=colorscale,
            showscale=False,
            hoverinfo="none",
        )
    )

    # 添加文本注释 - 显示标签
    for i in range(height):
        for j in range(width):
            if labels[i][j]:
                fig.add_annotation(
                    x=j,
                    y=i,
                    text=labels[i][j],
                    showarrow=False,
                    font=dict(size=14, color="black", family="Arial Black"),
                )

    # 添加路径点
    if path_history and len(path_history) > 0:
        path_y, path_x = zip(*path_history)  # 注意Plotly的坐标系
        
        # 机器人起点和终点
        start_point = path_history[0]
        end_point = path_history[-1]
        
        # 绘制完整路径
        fig.add_trace(
            go.Scatter(
                x=path_x,
                y=path_y,
                mode="lines",
                line=dict(
                    width=3,
                    color="rgba(255, 0, 0, 0.6)",
                    dash="solid",
                ),
                name="机器人路径",
            )
        )
        
        # 突出显示起点
        fig.add_trace(
            go.Scatter(
                x=[start_point[1]],
                y=[start_point[0]],
                mode="markers+text",
                marker=dict(
                    size=16,
                    color="green",
                    symbol="circle",
                    line=dict(width=2, color="darkgreen"),
                ),
                text=["S"],  # 使用字母S标记起点
                textposition="middle center",
                textfont=dict(size=10, color="white", family="Arial Black"),
                name="出发点",
                hoverinfo="text",
                hovertext="出发点（停靠点）",
            )
        )
        
        # 判断终点是否与起点相同
        is_same_point = start_point == end_point
        
        # 突出显示终点/当前位置
        fig.add_trace(
            go.Scatter(
                x=[end_point[1]],
                y=[end_point[0]],
                mode="markers+text",
                marker=dict(
                    size=16,
                    color="red",
                    symbol="circle",
                    line=dict(width=2, color="darkred"),
                ),
                text=["E" if not is_same_point else "S/E"],  # 使用字母E标记终点
                textposition="middle center",
                textfont=dict(size=10, color="white", family="Arial Black"),
                name="返回点" if not is_same_point else "出发/返回点",
                hoverinfo="text",
                hovertext="返回点（停靠点）",
                visible=not is_same_point,  # 如果与起点相同则不显示
            )
        )
        
        # 如果提供了订单信息，按配送顺序排序并添加标注
        if orders:
            # 获取所有桌子的送餐点
            table_delivery_points = {}
            for table_id, table_pos in _restaurant.layout.tables.items():
                delivery_pos = _restaurant.layout.get_delivery_point(table_id)
                if delivery_pos:
                    table_delivery_points[table_id] = delivery_pos
                    
            # 尝试按配送顺序排序
            sorted_orders = sorted(orders, key=lambda x: x.get('delivery_sequence', float('inf')))
            
            # 为每个已配送的订单添加标记
            for order in sorted_orders:
                table_id = order.get('table_id')
                order_id = order.get('order_id')
                delivery_seq = order.get('delivery_sequence')
                
                # 只标注有配送顺序的订单（已完成配送的）
                if delivery_seq and table_id in table_delivery_points:
                    # 使用配送目标点而不是桌子位置
                    delivery_pos = table_delivery_points[table_id]
                    
                    # 显示配送顺序而不是订单ID
                    hover_text = f"配送顺序: #{delivery_seq}<br>订单ID: #{order_id}<br>桌号: {table_id}"
                    table_markers = go.Scatter(
                        x=[delivery_pos[1]],
                        y=[delivery_pos[0]],
                        mode='markers+text',
                        marker=dict(
                            size=20,
                            color="rgba(255, 165, 0, 0.8)",  # 橙色半透明
                            symbol="circle",
                            line=dict(width=2, color="orange"),
                        ),
                        text=[f"{delivery_seq}"],  # 只显示数字，不显示#符号
                        textposition="middle center",
                        textfont=dict(size=12, color="black", family="Arial Black"),
                        name="配送顺序",  # 简化图例名称
                        hoverinfo='text',
                        hovertext=hover_text,
                        showlegend=(order == sorted_orders[0])  # 只为第一个点显示图例
                    )
                    fig.add_trace(table_markers)

    # 设置图表布局
    fig.update_layout(
        title=dict(
            text=title, 
            font=dict(size=20),
            y=0.97,  # 把标题往上移一点
        ),
        width=width * 50,  # 根据网格大小调整图表大小
        height=height * 50,
        margin=dict(l=10, r=10, t=60, b=30),  # 增加顶部和底部边距
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=True,
            gridcolor="lightgrey",
            gridwidth=1,
            zeroline=False,
            showticklabels=False,
            range=[-0.5, width - 0.5],
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="lightgrey",
            gridwidth=1,
            zeroline=False,
            showticklabels=False,
            scaleanchor="x",
            scaleratio=1,
            range=[height - 0.5, -0.5],  # 反转Y轴使(0,0)在左上角
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",    # 改为底部对齐
            y=0.01,              # y=0.01 表示接近底部
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255,255,255,0.8)",  # 半透明白色背景
            bordercolor="lightgrey",
            borderwidth=1,
        ),
        # 添加国际象棋棋盘样式的背景网格
        shapes=[
            # 水平线
            *[dict(
                type="line",
                x0=-0.5, x1=width-0.5,
                y0=i-0.5, y1=i-0.5,
                line=dict(color="lightgrey", width=1)
            ) for i in range(height+1)],
            # 垂直线
            *[dict(
                type="line",
                x0=j-0.5, x1=j-0.5,
                y0=-0.5, y1=height-0.5,
                line=dict(color="lightgrey", width=1)
            ) for j in range(width+1)]
        ]
    )

    st.plotly_chart(fig)

    return fig


@st.cache_data(ttl=300, show_spinner=False, hash_funcs={object: lambda x: id(x)}) if ENABLE_CACHING else lambda f: f
def render_plotly_stats_extended(stats_data, custom_metrics=None):
    """
    渲染扩展的统计数据可视化，支持自定义指标

    参数:
    - stats_data: dict，统计数据字典
    - custom_metrics: dict，自定义指标配置，格式为{'指标名称': {'color': 颜色, 'format': 格式化函数}}
    """
    if not stats_data:
        return
        
    # 获取累积的历史批次数据
    batch_histories = get_batch_histories()

    st.header("高级统计分析")

    # 默认的指标配置
    default_metrics = {
        "total_orders": {"color": "#00cc66", "format": lambda x: int(x)},
        "total_batches": {"color": "#ff9900", "format": lambda x: int(x)},
        "总配送路程": {"color": "#4da6ff", "format": lambda x: int(x)},
        "平均每批次订单数": {"color": "#f5c518", "format": lambda x: f"{x:.2f}"},
        "平均每订单步数": {"color": "#2196f3", "format": lambda x: f"{x:.2f}"}
    }

    # 合并自定义指标
    metrics = default_metrics.copy()
    if custom_metrics:
        metrics.update(custom_metrics)

    # 准备数据
    data = []

    # 添加基础统计
    data.append(
        {
            "指标": "总订单数",
            "值": stats_data.get("total_orders", 0),
            "颜色": metrics.get("total_orders", {}).get("color", "#00cc66"),
        }
    )
    data.append(
        {
            "指标": "总批次数",
            "值": stats_data.get("total_batches", 0),
            "颜色": metrics.get("total_batches", {}).get("color", "#ff9900"),
        }
    )
    
    # 添加路径长度指标
    data.append(
        {
            "指标": "总配送路程",
            "值": stats_data.get("总配送路程", 0),
            "颜色": metrics.get("总配送路程", {}).get("color", "#4da6ff"),
        }
    )

    # 添加平均值指标
    for key in ["平均每批次订单数", "平均每订单步数", "平均每订单配送时间"]:
        if key in stats_data:
            metric_config = metrics.get(
                key, {"color": "#9467bd", "format": lambda x: f"{x:.2f}"}
            )
            data.append({"指标": key, "值": stats_data[key], "颜色": metric_config["color"]})

    # 添加其他统计指标
    for key, value in stats_data.items():
        if key not in ["total_orders", "total_batches", "总配送路程", "平均每批次订单数", "平均每订单步数", "平均每订单配送时间", "配送历史"]:
            metric_config = metrics.get(
                key, {"color": "#9467bd", "format": lambda x: x}
            )
            data.append({"指标": key, "值": value, "颜色": metric_config["color"]})

    # 创建图表
    tabs = st.tabs(["配送性能", "雷达图", "历史批次分析"])

    with tabs[0]:
        # 条形图
        fig_bar = go.Figure()
        fig_bar.add_trace(
            go.Bar(
                x=[item["指标"] for item in data],
                y=[item["值"] for item in data],
                marker_color=[item["颜色"] for item in data],
                text=[format_value(item["指标"], item["值"], metrics) for item in data],
                textposition="auto",
            )
        )

        fig_bar.update_layout(
            title="配送性能指标详情",
            xaxis=dict(title="指标"),
            yaxis=dict(title="数值"),
            height=400,
        )

        st.plotly_chart(fig_bar, use_container_width=True)

    with tabs[1]:
        # 雷达图
        fig_radar = go.Figure()

        fig_radar.add_trace(
            go.Scatterpolar(
                r=[item["值"] for item in data],
                theta=[item["指标"] for item in data],
                fill="toself",
                name="统计指标",
                line_color="rgba(255, 0, 0, 0.8)",
                fillcolor="rgba(255, 0, 0, 0.2)",
            )
        )

        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                ),
            ),
            title="配送性能雷达图",
            height=400,
        )

        st.plotly_chart(fig_radar, use_container_width=True)

    with tabs[2]:
        # 批次历史分析
        if batch_histories:  # 优先使用累积的历史批次数据
            # 将历史数据转换为DataFrame进行分析
            history_df = pd.DataFrame(batch_histories)
            
            # 批次订单数分布
            if "orders_count" in history_df.columns:
                st.subheader("批次订单数分布")
                fig_batch = go.Figure()
                fig_batch.add_trace(
                    go.Bar(
                        x=[f"批次 {i+1}" for i in range(len(history_df))],
                        y=history_df["orders_count"],
                        marker_color="#4da6ff",
                        text=history_df["orders_count"],
                        textposition="auto",
                    )
                )
                fig_batch.update_layout(
                    title="各批次订单数量",
                    xaxis=dict(title="批次"),
                    yaxis=dict(title="订单数量"),
                    height=300,
                )
                st.plotly_chart(fig_batch, use_container_width=True)
            
            # 批次路径长度分布
            if "path_length" in history_df.columns:
                st.subheader("批次路径长度分布")
                fig_path = go.Figure()
                fig_path.add_trace(
                    go.Bar(
                        x=[f"批次 {i+1}" for i in range(len(history_df))],
                        y=history_df["path_length"],
                        marker_color="#00cc66",
                        text=history_df["path_length"],
                        textposition="auto",
                    )
                )
                fig_path.update_layout(
                    title="各批次路径长度",
                    xaxis=dict(title="批次"),
                    yaxis=dict(title="路径长度"),
                    height=300,
                )
                st.plotly_chart(fig_path, use_container_width=True)
                
            # 批次配送时间分布
            if "duration" in history_df.columns:
                st.subheader("批次配送时间分布")
                fig_duration = go.Figure()
                fig_duration.add_trace(
                    go.Bar(
                        x=[f"批次 {i+1}" for i in range(len(history_df))],
                        y=history_df["duration"],
                        marker_color="#ff9900",
                        text=[f"{d:.2f}" for d in history_df["duration"]],
                        textposition="auto",
                    )
                )
                fig_duration.update_layout(
                    title="各批次配送时间(秒)",
                    xaxis=dict(title="批次"),
                    yaxis=dict(title="时间(秒)"),
                    height=300,
                )
                st.plotly_chart(fig_duration, use_container_width=True)
        elif "配送历史" in stats_data and stats_data["配送历史"]:  # 如果没有累积数据，使用当前模拟数据
            # 将历史数据转换为DataFrame进行分析
            history_df = pd.DataFrame(stats_data["配送历史"])
            
            # 批次订单数分布
            if "orders_count" in history_df.columns:
                st.subheader("批次订单数分布")
                fig_batch = go.Figure()
                fig_batch.add_trace(
                    go.Bar(
                        x=[f"批次 {i+1}" for i in range(len(history_df))],
                        y=history_df["orders_count"],
                        marker_color="#4da6ff",
                        text=history_df["orders_count"],
                        textposition="auto",
                    )
                )
                fig_batch.update_layout(
                    title="各批次订单数量",
                    xaxis=dict(title="批次"),
                    yaxis=dict(title="订单数量"),
                    height=300,
                )
                st.plotly_chart(fig_batch, use_container_width=True)
            
            # 批次路径长度分布
            if "path_length" in history_df.columns:
                st.subheader("批次路径长度分布")
                fig_path = go.Figure()
                fig_path.add_trace(
                    go.Bar(
                        x=[f"批次 {i+1}" for i in range(len(history_df))],
                        y=history_df["path_length"],
                        marker_color="#00cc66",
                        text=history_df["path_length"],
                        textposition="auto",
                    )
                )
                fig_path.update_layout(
                    title="各批次路径长度",
                    xaxis=dict(title="批次"),
                    yaxis=dict(title="路径长度"),
                    height=300,
                )
                st.plotly_chart(fig_path, use_container_width=True)
                
            # 批次配送时间分布
            if "duration" in history_df.columns:
                st.subheader("批次配送时间分布")
                fig_duration = go.Figure()
                fig_duration.add_trace(
                    go.Bar(
                        x=[f"批次 {i+1}" for i in range(len(history_df))],
                        y=history_df["duration"],
                        marker_color="#ff9900",
                        text=[f"{d:.2f}" for d in history_df["duration"]],
                        textposition="auto",
                    )
                )
                fig_duration.update_layout(
                    title="各批次配送时间(秒)",
                    xaxis=dict(title="批次"),
                    yaxis=dict(title="时间(秒)"),
                    height=300,
                )
                st.plotly_chart(fig_duration, use_container_width=True)
        else:
            st.info("暂无批次历史数据")

    return data


def render_layout_editor():
    """
    渲染餐厅布局编辑器，允许用户创建、修改和删除布局

    返回:
        dict: 编辑后的布局信息，如果没有改变则返回None
    """
    st.header("餐厅布局编辑器")

    # 布局参数设置
    col1, col2, col3 = st.columns(3)
    with col1:
        current_height = get_editor_height()
        new_height = st.number_input(
            "高度", min_value=3, max_value=30, value=current_height, key="editor_height_input"
        )
        if new_height != current_height:
            # 调整高度时保留现有数据
            current_grid = get_editor_grid()
            current_width = get_editor_width()
            new_grid = [[0 for _ in range(current_width)] for _ in range(new_height)]
            for i in range(min(new_height, current_height)):
                for j in range(current_width):
                    new_grid[i][j] = current_grid[i][j]
            set_editor_grid(new_grid)
            set_editor_height(new_height)

            # 检查并移除超出范围的特殊位置
            tables = get_editor_tables()
            tables = {k: v for k, v in tables.items() if v[0] < new_height}
            set_editor_tables(tables)

            kitchen = get_editor_kitchen()
            kitchen = [pos for pos in kitchen if pos[0] < new_height]
            set_editor_kitchen(kitchen)

            parking = get_editor_parking()
            if parking and parking[0] >= new_height:
                set_editor_parking(None)

            st.rerun()

    with col2:
        current_width = get_editor_width()
        new_width = st.number_input(
            "宽度", min_value=3, max_value=30, value=current_width, key="editor_width_input"
        )
        if new_width != current_width:
            # 调整宽度时保留现有数据
            current_grid = get_editor_grid()
            current_height = get_editor_height()
            new_grid = [[0 for _ in range(new_width)] for _ in range(current_height)]
            for i in range(current_height):
                for j in range(min(new_width, current_width)):
                    new_grid[i][j] = current_grid[i][j]
            set_editor_grid(new_grid)
            set_editor_width(new_width)

            # 检查并移除超出范围的特殊位置
            tables = get_editor_tables()
            tables = {k: v for k, v in tables.items() if v[1] < new_width}
            set_editor_tables(tables)

            kitchen = get_editor_kitchen()
            kitchen = [pos for pos in kitchen if pos[1] < new_width]
            set_editor_kitchen(kitchen)

            parking = get_editor_parking()
            if parking and parking[1] >= new_width:
                set_editor_parking(None)

            st.rerun()

    with col3:
        current_name = get_editor_layout_name()
        layout_name = st.text_input("布局名称", value=current_name, key="editor_layout_name_input")
        if layout_name != current_name:
            set_editor_layout_name(layout_name)

    # 创建一个可视化的布局编辑界面
    st.subheader("编辑布局")
    st.write("点击网格单元格来修改其类型")

    # 创建多行列布局，美化界面
    edit_col1, edit_col2 = st.columns([3, 1])
    
    with edit_col2:
        st.write("**元素工具箱**")
        # 选择要编辑的元素类型
        element_type = st.radio(
            "选择元素类型", 
            ["墙壁/障碍", "空地", "桌子", "厨房", "停靠点"],
            captions=["#", ".", "A-Z", "厨", "停"],
            key="element_type_radio"
        )
        
        # 元素类型映射到数值
        type_map = {"墙壁/障碍": 1, "空地": 0, "桌子": 2, "厨房": 3, "停靠点": 4}
        
        # 显示当前元素的颜色提示
        element_colors = {
            "墙壁/障碍": "#333333",
            "空地": "white",
            "桌子": "#00cc66",
            "厨房": "#f5c518",
            "停靠点": "#4da6ff"
        }
        
        st.markdown(
            f"""
            <div style="
                width: 100%; 
                height: 30px; 
                background-color: {element_colors[element_type]}; 
                border: 1px solid black;
                display: flex;
                align-items: center;
                justify-content: center;
                color: {"black" if element_type != "墙壁/障碍" else "white"};
                font-weight: bold;
            ">
                {element_type}
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # 在桌子模式下，需要输入桌子ID
        table_id = None
        if element_type == "桌子":
            table_id = st.text_input("桌子ID (单个字母A-Z)", max_chars=1, key="table_id_input")
            if table_id and (not table_id.isalpha() or len(table_id) != 1):
                st.warning("桌子ID必须是单个字母 (A-Z)")
                
        # 显示统计信息
        st.write("**布局统计**")
        tables = get_editor_tables()
        kitchen = get_editor_kitchen()
        parking = get_editor_parking()
        
        st.markdown(f"""
        - 网格尺寸: {get_editor_height()} × {get_editor_width()}
        - 桌子: {len(tables)} 个
        - 厨房: {len(kitchen)} 个
        - 停靠点: {"有" if parking else "无"}
        """)
        
        # 操作按钮
        st.write("**操作**")
        if st.button("重置布局", key="editor_reset_button"):
            # 重置为空白布局
            reset_editor()
            st.rerun()
            
        if st.button("自动添加围墙", key="editor_add_walls_button"):
            # 在布局边缘添加墙壁
            grid = get_editor_grid()
            height = get_editor_height()
            width = get_editor_width()

            # 添加顶部和底部墙壁
            for j in range(width):
                grid[0][j] = 1
                grid[height - 1][j] = 1

            # 添加左右墙壁
            for i in range(height):
                grid[i][0] = 1
                grid[i][width - 1] = 1

            # 更新网格
            set_editor_grid(grid)
            st.rerun()
    
    with edit_col1:
        # 创建Plotly图表以便交互编辑
        fig = render_interactive_editor_grid()
        
        # 使用 plotly_events 展示图表并监听点击事件
        clicked_point = plotly_events(fig, click_event=True, key="layout_editor_plotly")
        
        if clicked_point:
            # 获取点击的坐标
            try:
                point_data = clicked_point[0]
                row, col = int(point_data["y"]), int(point_data["x"])
                
                # 获取当前状态
                grid = get_editor_grid()
                tables = get_editor_tables()
                kitchen = get_editor_kitchen()
                parking = get_editor_parking()
                height = get_editor_height()
                width = get_editor_width()

                # 根据选择的元素类型进行修改
                if 0 <= row < height and 0 <= col < width:
                    if (
                        element_type == "桌子"
                        and table_id
                        and table_id.isalpha()
                        and len(table_id) == 1
                    ):
                        # 处理桌子 - 需要存储桌子ID和位置
                        # 先检查该ID是否已被使用
                        table_id_upper = table_id.upper()
                        if table_id_upper in tables and tables[table_id_upper] != (row, col):
                            # 如果已存在此ID但位置不同，找到并清除旧位置
                            old_row, old_col = tables[table_id_upper]
                            if grid[old_row][old_col] == 2:  # 确保旧位置确实是桌子
                                grid[old_row][old_col] = 0  # 设为空地
                                
                        # 检查该位置是否已有其他桌子
                        table_to_remove = None
                        for tid, pos in tables.items():
                            if pos == (row, col) and tid != table_id_upper:
                                table_to_remove = tid
                        if table_to_remove:
                            del tables[table_to_remove]
                                
                        grid[row][col] = type_map[element_type]
                        tables[table_id_upper] = (row, col)
                        set_editor_tables(tables)
                    elif element_type == "厨房":
                        # 处理厨房 - 可以有多个厨房位置
                        grid[row][col] = type_map[element_type]
                        if (row, col) not in kitchen:
                            kitchen.append((row, col))
                        set_editor_kitchen(kitchen)
                    elif element_type == "停靠点":
                        # 处理停靠点 - 只能有一个
                        # 先清除现有的停靠点
                        if parking:
                            old_row, old_col = parking
                            if grid[old_row][old_col] == 4:
                                grid[old_row][old_col] = 0  # 设为空地

                        grid[row][col] = type_map[element_type]
                        set_editor_parking((row, col))
                    else:
                        # 处理墙壁或空地
                        old_value = grid[row][col]
                        grid[row][col] = type_map[element_type]

                        # 如果将某个特殊位置设为墙壁或空地，需要从相应列表中移除
                        # 检查和清理桌子
                        if old_value == 2:  # 原来是桌子
                            tables_to_remove = []
                            for tid, pos in tables.items():
                                if pos == (row, col):
                                    tables_to_remove.append(tid)
                            for tid in tables_to_remove:
                                del tables[tid]
                            set_editor_tables(tables)

                        # 检查和清理厨房
                        if old_value == 3 and (row, col) in kitchen:  # 原来是厨房
                            kitchen.remove((row, col))
                            set_editor_kitchen(kitchen)

                        # 检查和清理停靠点
                        if old_value == 4 and parking == (row, col):  # 原来是停靠点
                            set_editor_parking(None)

                    # 更新网格
                    set_editor_grid(grid)

                    # 强制重新渲染
                    st.rerun()
            except (KeyError, IndexError) as e:
                st.error(f"无法处理点击: {e}")
    
    # 保存布局按钮
    st.write("")
    save_col1, save_col2 = st.columns([3, 1])
    
    with save_col1:
        st.write("**完成布局编辑后，点击保存：**")
        
    with save_col2:
        if st.button("保存布局", key="editor_save_layout_button", type="primary"):
            # 验证布局是否有效
            is_valid, message = validate_layout_extended()
            if not is_valid:
                st.error(f"布局无效! {message}")
                return None

            # 返回当前编辑的布局数据
            return {
                "name": get_editor_layout_name(),
                "grid": get_editor_grid(),
                "table_positions": get_editor_tables(),
                "kitchen_positions": get_editor_kitchen(),
                "parking_position": get_editor_parking(),
            }

    return None

def render_interactive_editor_grid():
    """
    渲染交互式可编辑的Plotly餐厅布局网格，改进版本

    返回:
        go.Figure: Plotly图表对象
    """
    grid = get_editor_grid()
    height = get_editor_height()
    width = get_editor_width()
    tables = get_editor_tables()
    kitchen = get_editor_kitchen()
    parking = get_editor_parking()

    # 创建颜色映射
    colormap = {
        0: "white",         # 空地
        1: "#333333",       # 墙壁/障碍
        2: "#00cc66",       # 桌子
        3: "#f5c518",       # 厨房
        4: "#4da6ff",       # 停靠点
    }

    # 创建标签映射
    labels = [["" for _ in range(width)] for _ in range(height)]

    # 设置桌子标签
    for table_id, pos in tables.items():
        row, col = pos
        if 0 <= row < height and 0 <= col < width:  # 防止越界
            labels[row][col] = table_id

    # 设置厨房标签
    for row, col in kitchen:
        if 0 <= row < height and 0 <= col < width:  # 防止越界
            labels[row][col] = "厨"

    # 设置停靠点标签
    if parking:
        row, col = parking
        if 0 <= row < height and 0 <= col < width:  # 防止越界
            labels[row][col] = "停"

    # 创建热力图数据
    fig = go.Figure()

    # 添加热力图 - 显示颜色块
    heatmap_z = np.array(grid)
    colorscale = [
        [0, colormap[0]],      # 空地
        [0.2, colormap[0]],
        [0.2, colormap[1]],    # 墙壁
        [0.4, colormap[1]],
        [0.4, colormap[2]],    # 桌子
        [0.6, colormap[2]],
        [0.6, colormap[3]],    # 厨房
        [0.8, colormap[3]],
        [0.8, colormap[4]],    # 停靠点
        [1.0, colormap[4]],
    ]

    # 生成每个单元格的悬停文本
    hover_texts = []
    for i in range(height):
        row_texts = []
        for j in range(width):
            cell_type = grid[i][j]
            cell_desc = get_cell_description(i, j)
            row_texts.append(cell_desc)
        hover_texts.append(row_texts)

    fig.add_trace(
        go.Heatmap(
            z=heatmap_z,
            colorscale=colorscale,
            showscale=False,
            hoverinfo="text",
            hovertext=hover_texts,
            # 禁用默认的heatmap tooltips
            zhoverformat="none"
        )
    )

    # 添加文本注释 - 显示标签
    for i in range(height):
        for j in range(width):
            if labels[i][j]:
                fig.add_annotation(
                    x=j,
                    y=i,
                    text=labels[i][j],
                    showarrow=False,
                    font=dict(
                        size=16, 
                        color="black", 
                        family="Arial Black"
                    ),
                )

    # 设置图表布局
    fig.update_layout(
        width=min(800, max(400, width * 35)),  # 更合理的大小调整
        height=min(800, max(400, height * 35)),
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=False,  # 不显示网格线，我们会自己添加
            zeroline=False,
            range=[-0.5, width - 0.5],
            tickvals=list(range(width)),
            ticktext=[str(i) for i in range(width)],
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            showgrid=False,  # 不显示网格线，我们会自己添加
            zeroline=False,
            scaleanchor="x",
            scaleratio=1,
            range=[height - 0.5, -0.5],  # 反转Y轴使(0,0)在左上角
            tickvals=list(range(height)),
            ticktext=[str(i) for i in range(height)],
            tickfont=dict(size=10),
        ),
        # 添加棋盘样式网格
        shapes=[
            # 水平线
            *[dict(
                type="line",
                x0=-0.5, x1=width-0.5,
                y0=i-0.5, y1=i-0.5,
                line=dict(color="lightgrey", width=1)
            ) for i in range(height+1)],
            # 垂直线
            *[dict(
                type="line",
                x0=j-0.5, x1=j-0.5,
                y0=-0.5, y1=height-0.5,
                line=dict(color="lightgrey", width=1)
            ) for j in range(width+1)]
        ],
        hoverlabel=dict(
            bgcolor="white",
            font_size=14,
            font_family="Arial"
        )
    )

    # 添加额外的指导性提示
    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.5, y=-0.07,
        text="点击任意单元格应用当前选择的元素类型",
        showarrow=False,
        font=dict(size=12, color="grey"),
    )

    return fig


def validate_layout_extended():
    """
    验证布局是否有效，并提供详细的错误信息
    
    返回:
        tuple: (is_valid, message) 布局是否有效及详细信息
    """
    # 检查是否至少有一个桌子
    if not get_editor_tables():
        return False, "至少需要一个桌子"

    # 检查是否至少有一个厨房
    if not get_editor_kitchen():
        return False, "至少需要一个厨房"

    # 检查是否有停靠点
    if not get_editor_parking():
        return False, "需要一个停靠点"
        
    # 检查布局名称
    if not get_editor_layout_name() or get_editor_layout_name() == "新布局":
        return False, "请提供有效的布局名称"

    return True, "布局有效"


def get_cell_description(row, col):
    """
    获取单元格的描述文本，用于悬停提示
    """
    grid = get_editor_grid()
    if row >= len(grid) or col >= len(grid[0]):
        return ""

    cell_type = grid[row][col]
    descriptions = {0: "空地", 1: "墙壁/障碍", 2: "桌子", 3: "厨房", 4: "停靠点"}

    base_desc = f"({row}, {col}): {descriptions.get(cell_type, '未知')}"

    # 添加额外信息
    if cell_type == 2:  # 桌子
        for tid, pos in get_editor_tables().items():
            if pos == (row, col):
                return f"{base_desc} {tid}"

    return base_desc


def render_plotly_restaurant_layout_no_cache(_restaurant, path=None, title="餐厅布局"):
    """
    无缓存版本的餐厅布局渲染函数，确保每次都重新渲染最新的布局。
    
    参数:
    - _restaurant: Restaurant，餐厅实例
    - path: List[Tuple[int, int]]，可选，机器人路径
    - title: str，标题
    """
    layout = _restaurant.layout
    grid = layout.grid
    height = layout.height
    width = layout.width

    # 创建颜色映射
    colormap = {
        0: "white",  # 空地
        1: "#333333",  # 墙壁/障碍
        2: "#00cc66",  # 桌子
        3: "#f5c518",  # 厨房
        4: "#4da6ff",  # 停靠点
    }

    # 创建标签映射
    labels = [["" for _ in range(width)] for _ in range(height)]

    # 设置桌子标签
    for table_id, pos in layout.tables.items():
        row, col = pos
        labels[row][col] = table_id

    # 设置厨房标签
    for row, col in layout.kitchen:
        labels[row][col] = "厨"

    # 设置停靠点标签
    if layout.parking:
        row, col = layout.parking
        labels[row][col] = "停"

    # 创建热力图数据
    fig = go.Figure()

    # 添加热力图 - 显示颜色块
    heatmap_z = np.array(grid)
    colorscale = [
        [0, colormap[0]],
        [0.2, colormap[0]],
        [0.2, colormap[1]],
        [0.4, colormap[1]],
        [0.4, colormap[2]],
        [0.6, colormap[2]],
        [0.6, colormap[3]],
        [0.8, colormap[3]],
        [0.8, colormap[4]],
        [1.0, colormap[4]],
    ]

    fig.add_trace(
        go.Heatmap(
            z=heatmap_z,
            colorscale=colorscale,
            showscale=False,
            hoverinfo="none",
        )
    )

    # 添加文本注释 - 显示标签
    for i in range(height):
        for j in range(width):
            if labels[i][j]:
                fig.add_annotation(
                    x=j,
                    y=i,
                    text=labels[i][j],
                    showarrow=False,
                    font=dict(size=14, color="black", family="Arial Black"),
                )

    # 添加路径点（如果有）
    if path:
        path_y, path_x = zip(*path)  # 注意Plotly的坐标系
        fig.add_trace(
            go.Scatter(
                x=path_x,
                y=path_y,
                mode="lines+markers",
                marker=dict(size=8, color="red"),
                line=dict(width=2, color="red"),
                name="路径",
            )
        )

    # 设置图表布局
    fig.update_layout(
        title=dict(text=title, font=dict(size=20)),
        width=width * 50,  # 根据网格大小调整图表大小
        height=height * 50,
        margin=dict(l=0, r=0, t=40, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=True,
            gridcolor="lightgrey",
            gridwidth=1,
            zeroline=False,
            showticklabels=False,
            range=[-0.5, width - 0.5],
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="lightgrey",
            gridwidth=1,
            zeroline=False,
            showticklabels=False,
            scaleanchor="x",
            scaleratio=1,
            range=[height - 0.5, -0.5],  # 反转Y轴使(0,0)在左上角
        ),
        # 添加国际象棋棋盘样式的背景网格
        shapes=[
            # 水平线
            *[dict(
                type="line",
                x0=-0.5, x1=width-0.5,
                y0=i-0.5, y1=i-0.5,
                line=dict(color="lightgrey", width=1)
            ) for i in range(height+1)],
            # 垂直线
            *[dict(
                type="line",
                x0=j-0.5, x1=j-0.5,
                y0=-0.5, y1=height-0.5,
                line=dict(color="lightgrey", width=1)
            ) for j in range(width+1)]
        ]
    )

    st.plotly_chart(fig)

    return fig


def render_rag_test():
    """
    渲染RAG测试界面，允许用户直接测试RAG模块的问答能力
    """
    from robot.rag import RAGModule
    
    st.header("RAG系统测试")
    
    # 使用OpenAI API密钥
    api_key = os.environ.get("OPENAI_API_KEY", None)
    
    # 初始化RAG模块
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    knowledge_file = os.path.join(current_dir, "robot", "rag", "knowledge", "restaurant_rule.json")
    
    # 初始化RAG模块，如果密钥存在
    if "rag_module" not in st.session_state:
        rag = RAGModule(
            api_key=api_key,
            knowledge_file=knowledge_file,
        )
        st.session_state["rag_module"] = rag
    else:
        rag = st.session_state["rag_module"]
    
    # 检查RAG模块是否准备就绪
    if not rag.is_ready():
        st.warning("未加载知识库或API密钥未设置，将使用纯LLM回答或无法获得回应")
    else:
        st.success(f"已成功加载知识库: {knowledge_file}")
    
    # 创建测试界面
    test_tabs = st.tabs(["问答测试", "思考层测试", "触发层测试", "决策接口测试"])
    
    # 问答测试标签页
    with test_tabs[0]:
        st.subheader("直接问答测试")
        query = st.text_input("请输入问题:（例：现在有订单3号桌，5号桌，8号桌，告诉我配送顺序）", key="qa_query")
        use_rag = st.checkbox("使用RAG增强回答", value=True, key="qa_use_rag")
        
        if st.button("提交问题", key="qa_submit"):
            if not query:
                st.error("请输入问题内容")
            else:
                with st.spinner("正在思考中..."):
                    try:
                        answer = rag.query_answer(query, use_rag=use_rag)
                        st.success("回答成功")
                        st.info(answer)
                    except Exception as e:
                        st.error(f"发生错误: {e}")
    
    # 思考层测试标签页
    with test_tabs[1]:
        st.subheader("思考层测试")
        query = st.text_input("请输入问题:（例：现在有订单3号桌，5号桌，8号桌，告诉我配送顺序）", key="thinking_query")
        use_rag = st.checkbox("使用RAG增强回答", value=True, key="thinking_use_rag")
        
        if st.button("提交问题", key="thinking_submit"):
            if not query:
                st.error("请输入问题内容")
            else:
                with st.spinner("正在通过思考层处理..."):
                    try:
                        raw_response, context_docs = rag.thinking_layer(query, use_rag=use_rag)
                        
                        # 展示结果
                        st.write("#### 思考层输出")
                        st.write(f"**检索到的文档:** {len(context_docs)} 条")
                        
                        # 显示检索的文档
                        for i, doc in enumerate(context_docs, 1):
                            with st.expander(f"文档 {i}"):
                                st.write(doc)
                        
                        # 显示LLM原始响应
                        st.write("#### LLM原始响应:")
                        st.info(raw_response)
                        
                        # 显示决策层的处理结果
                        action = rag.decision_layer(raw_response)
                        st.write("#### 决策层简化结果:")
                        st.success(action)
                        
                    except Exception as e:
                        st.error(f"发生错误: {e}")
    
    # 触发层测试标签页
    with test_tabs[2]:
        st.subheader("触发层测试")
        event_type = st.selectbox(
            "请选择事件类型:",
            ["plan", "obstacle"],
            format_func=lambda x: "路径规划事件" if x == "plan" else "障碍处理事件"
        )
        
        # 根据事件类型显示不同的输入字段
        if event_type == "plan":
            robot_id = st.number_input("机器人ID", value=1, min_value=1, step=1)
            start_x = st.number_input("起点X坐标", value=0, step=1)
            start_y = st.number_input("起点Y坐标", value=0, step=1)
            goal_x = st.number_input("目标X坐标", value=10, step=1)
            goal_y = st.number_input("目标Y坐标", value=10, step=1)
            
            context = {
                'robot_id': robot_id,
                'start': (start_x, start_y),
                'goal': (goal_x, goal_y)
            }
        else:  # obstacle
            robot_id = st.number_input("机器人ID", value=1, min_value=1, step=1)
            pos_x = st.number_input("当前X坐标", value=5, step=1)
            pos_y = st.number_input("当前Y坐标", value=5, step=1)
            goal_x = st.number_input("目标X坐标", value=10, step=1)
            goal_y = st.number_input("目标Y坐标", value=10, step=1)
            obstacle_x = st.number_input("障碍X坐标", value=6, step=1)
            obstacle_y = st.number_input("障碍Y坐标", value=6, step=1)
            
            context = {
                'robot_id': robot_id,
                'position': (pos_x, pos_y),
                'goal': (goal_x, goal_y),
                'obstacle': (obstacle_x, obstacle_y)
            }
        
        if st.button("提交测试", key="trigger_submit"):
            with st.spinner(f"正在通过触发层处理 {event_type} 事件..."):
                try:
                    result = rag.trigger_layer(event_type, context)
                    
                    # 展示结果
                    st.write("#### 触发层结果")
                    st.write(f"**动作:** {result['action']}")
                    st.write(f"**是否使用上下文:** {result['context_used']}")
                    st.write(f"**检索到的文档数:** {len(result['context_docs'])}")
                    
                    # 显示检索的文档
                    if result['context_docs']:
                        with st.expander("检索到的文档"):
                            for i, doc in enumerate(result['context_docs'], 1):
                                st.write(f"文档 {i}:")
                                st.write(doc)
                                st.write("---")
                    
                    # 显示LLM原始响应
                    st.write("#### LLM原始响应:")
                    st.info(result['raw_response'])
                    
                except Exception as e:
                    st.error(f"发生错误: {e}")
    
    # 决策接口测试标签页
    with test_tabs[3]:
        st.subheader("决策接口测试")
        situation_type = st.selectbox(
            "请选择情境类型:",
            ["plan", "obstacle"], 
            format_func=lambda x: "路径规划" if x == "plan" else "障碍处理"
        )
        
        # 根据情境类型显示不同的输入字段
        if situation_type == "plan":
            robot_id = st.number_input("机器人ID", value=1, min_value=1, step=1, key="decision_robot_id")
            start_x = st.number_input("起点X坐标", value=0, step=1, key="decision_start_x")
            start_y = st.number_input("起点Y坐标", value=0, step=1, key="decision_start_y")
            goal_x = st.number_input("目标X坐标", value=10, step=1, key="decision_goal_x")
            goal_y = st.number_input("目标Y坐标", value=10, step=1, key="decision_goal_y")
            
            kwargs = {
                'robot_id': robot_id,
                'start': (start_x, start_y),
                'goal': (goal_x, goal_y)
            }
        else:  # obstacle
            robot_id = st.number_input("机器人ID", value=1, min_value=1, step=1, key="decision_robot_id")
            pos_x = st.number_input("当前X坐标", value=5, step=1, key="decision_pos_x")
            pos_y = st.number_input("当前Y坐标", value=5, step=1, key="decision_pos_y")
            goal_x = st.number_input("目标X坐标", value=10, step=1, key="decision_goal_x")
            goal_y = st.number_input("目标Y坐标", value=10, step=1, key="decision_goal_y")
            obstacle_x = st.number_input("障碍X坐标", value=6, step=1, key="decision_obs_x")
            obstacle_y = st.number_input("障碍Y坐标", value=6, step=1, key="decision_obs_y")
            
            kwargs = {
                'robot_id': robot_id,
                'position': (pos_x, pos_y),
                'goal': (goal_x, goal_y),
                'context': (obstacle_x, obstacle_y)
            }
        
        if st.button("提交测试", key="decision_submit"):
            with st.spinner(f"正在测试决策接口，情境: {situation_type}..."):
                try:
                    action = rag.make_decision(situation_type, **kwargs)
                    
                    # 展示结果
                    st.write("#### 决策结果")
                    st.success(action)
                    
                except Exception as e:
                    st.error(f"发生错误: {e}")
