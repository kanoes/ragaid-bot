"""
布局渲染组件
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
from rich.text import Text

from .base import ENABLE_CACHING


def render_sidebar(layouts, restaurant):
    """
    渲染侧边栏组件
    """
    if not layouts:
        st.error("レストランレイアウトファイルが見つかりません")
        return None, None, None

    selected = st.sidebar.selectbox("レストランレイアウトを選択", layouts)
    use_ai = st.sidebar.checkbox("RAGインテリジェントロボットを使用", value=False)
    num_orders = st.sidebar.slider(
        "注文数", 1, max(1, len(restaurant.layout.tables)), 1
    )

    sim_button = st.sidebar.button("シミュレーション開始")

    return selected, use_ai, num_orders, sim_button


def render_restaurant_layout(
    restaurant, path=None, table_positions=None, title="レストランレイアウト"
):
    """
    使用HTML+CSS渲染餐厅网格，支持路径高亮和表格显示。

    参数:
    - restaurant: Restaurant，餐厅实例
    - path: List[Tuple[int, int]]，可选，机器人路径
    - table_positions: Dict[str, Tuple[int, int]]，可选，表格坐标
    - title: str，标题
    """
    path = path or []
    table_positions = table_positions or {}

    st.markdown(f"### {title}")
    st.markdown("⬇️ 現在のレストラングリッドレイアウト：")

    html = f"""
    <div style="display: grid; grid-template-columns: repeat({len(restaurant.layout.grid[0])}, 24px); gap: 1px;">
    """

    for row in range(len(restaurant.layout.grid)):
        for col in range(len(restaurant.layout.grid[0])):
            pos = (row, col)
            color = "#ffffff"  # 默认空地为白色
            label = ""

            val = restaurant.layout.grid[row][col]

            if pos in path:
                color = "#ff4d4d"  # 路径为红色
            elif val == 1:
                color = "#333333"  # 墙
            elif val == 3:
                color = "#f5c518"  # 厨房
            elif val == 4:
                color = "#4da6ff"  # 停车点
            elif val == 2 or pos in table_positions.values():
                color = "#00cc66"  # 表格为绿色

            # 如果是表格，显示文字
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
def render_plotly_restaurant_layout(_restaurant, path=None, title="レストランレイアウト", random_key=None):
    """
    使用Plotly渲染餐厅布局，具有更好的视觉效果，类似棋盘表示。

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
        1: "#333333",  # 墙/障碍物
        2: "#00cc66",  # 表格
        3: "#f5c518",  # 厨房
        4: "#4da6ff",  # 停车点
    }

    # 创建标签映射
    labels = [["" for _ in range(width)] for _ in range(height)]

    # 设置表格标签
    for table_id, pos in layout.tables.items():
        row, col = pos
        labels[row][col] = table_id

    # 设置厨房标签
    for row, col in layout.kitchen:
        labels[row][col] = "厨"

    # 设置停车点标签
    if layout.parking:
        row, col = layout.parking
        labels[row][col] = "停"

    # 创建热图数据
    fig = go.Figure()

    # 添加热图 - 显示颜色块
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
                name="経路",
            )
        )

    # 设置图表布局
    fig.update_layout(
        title=dict(text=title, font=dict(size=20)),
        width=width * 50,  # 基于网格大小调整图表大小
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
            range=[height - 0.5, -0.5],  # 反转Y轴使(0,0)位于左上角
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
    获取表格的样式和标签
    """
    # 从位置反向查找表格ID
    table_id = None
    for tid, pos in tables.items():
        if pos == (x, y):
            table_id = tid
            break

    if table_id:
        return Text(table_id.center(2), style="black on cyan")
    else:
        return Text("卓", style="black on cyan")


@st.cache_data(ttl=300, show_spinner=False, hash_funcs={object: lambda x: id(x)}) if ENABLE_CACHING else lambda f: f
def render_plotly_robot_path(_restaurant, path_history, orders=None, title="ロボット経路"):
    """
    渲染机器人路径的动态图表
    
    Args:
        _restaurant: Restaurant实例
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
        1: "#333333",  # 墙/障碍物
        2: "#00cc66",  # 表格
        3: "#f5c518",  # 厨房
        4: "#4da6ff",  # 停车点
    }

    # 创建标签映射
    labels = [["" for _ in range(width)] for _ in range(height)]

    # 设置表格标签
    for table_id, pos in layout.tables.items():
        row, col = pos
        labels[row][col] = table_id

    # 设置厨房标签
    for row, col in layout.kitchen:
        labels[row][col] = "厨"

    # 设置停车点标签
    if layout.parking:
        row, col = layout.parking
        labels[row][col] = "停"

    # 创建热图数据
    fig = go.Figure()

    # 添加热图 - 显示颜色块
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

    # 提取路径点
    if path_history:
        # 解包路径点
        path_points = path_history
        if path_points:
            path_y, path_x = zip(*path_points)

            # 添加带有标记的路径线
            fig.add_trace(
                go.Scatter(
                    x=path_x,
                    y=path_y,
                    mode="lines+markers",
                    marker=dict(
                        size=8,
                        color="#ff4d4d",
                        symbol="circle",
                    ),
                    line=dict(
                        width=2,
                        color="#ff4d4d",
                    ),
                    name="配達経路",
                )
            )

            # 起点和终点标记
            if len(path_points) > 1:
                # 起点（绿色三角）
                fig.add_trace(
                    go.Scatter(
                        x=[path_x[0]],
                        y=[path_y[0]],
                        mode="markers",
                        marker=dict(
                            size=12,
                            color="#00cc66",
                            symbol="triangle-up",
                            line=dict(width=1, color="black"),
                        ),
                        name="スタート",
                    )
                )

                # 终点（红色星）
                fig.add_trace(
                    go.Scatter(
                        x=[path_x[-1]],
                        y=[path_y[-1]],
                        mode="markers",
                        marker=dict(
                            size=12,
                            color="#ff4d4d",
                            symbol="star",
                            line=dict(width=1, color="black"),
                        ),
                        name="ゴール",
                    )
                )
        
        # 如果提供了订单信息，根据配送顺序添加评论
        if orders:
            # 获取所有表格的配送点
            table_delivery_points = {}
            for table_id, table_pos in _restaurant.layout.tables.items():
                delivery_pos = _restaurant.layout.get_delivery_point(table_id)
                if delivery_pos:
                    table_delivery_points[table_id] = delivery_pos

            # 根据配送顺序添加评论
            sorted_orders = sorted(orders, key=lambda x: x.get('delivery_sequence', float('inf')))

            for order in sorted_orders:
                table_id = order.get('table_id')
                order_id = order.get('order_id')
                delivery_seq = order.get('delivery_sequence')
                
                # 如果有配送顺序，添加带有顺序的标记
                if delivery_seq is not None and table_id in table_delivery_points:
                    pos = table_delivery_points[table_id]
                    fig.add_trace(
                        go.Scatter(
                            x=[pos[1]],  # 注意坐标轴交换
                            y=[pos[0]],
                            mode="markers+text",
                            marker=dict(
                                size=20,
                                color="rgba(255, 255, 255, 0.8)",
                                symbol="circle",
                                line=dict(width=2, color="blue"),
                            ),
                            text=str(delivery_seq),
                            textposition="middle center",
                            textfont=dict(
                                size=14,
                                color="blue",
                                family="Arial Black",
                            ),
                            name=f"注文 #{order_id} (テーブル {table_id})",
                            showlegend=False,
                        )
                    )

    # 设置图表布局
    fig.update_layout(
        title=dict(
            text=title, 
            font=dict(size=20),
            y=0.97,  # 标题稍微上移
        ),
        width=width * 50,  # 基于网格大小调整图表大小
        height=height * 50,
        margin=dict(l=10, r=10, t=60, b=30),  # 增加上下边距
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
            range=[height - 0.5, -0.5],  # 反转Y轴使(0,0)位于左上角
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",    # 对齐底部
            y=0.01,              # y=0.01 接近底部
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


def render_plotly_restaurant_layout_no_cache(_restaurant, path=None, title="レストランレイアウト"):
    """
    无缓存的餐厅布局渲染函数，确保重新渲染最新的布局。
    
    参数:
    - _restaurant: Restaurant，餐厅实例
    - path: List[Tuple[int, int]]，可选，机器人路径
    - title: str，标题
    """
    layout = _restaurant.layout
    grid = layout.grid
    height = layout.height
    width = layout.width

    # 颜色映射
    colormap = {
        0: "white",  # 空地
        1: "#333333",  # 墙/障碍物
        2: "#00cc66",  # 表格
        3: "#f5c518",  # 厨房
        4: "#4da6ff",  # 停车点
    }

    # 标签映射
    labels = [["" for _ in range(width)] for _ in range(height)]

    # 表格标签
    for table_id, pos in layout.tables.items():
        row, col = pos
        labels[row][col] = table_id

    # 厨房标签
    for row, col in layout.kitchen:
        labels[row][col] = "厨"

    # 停车点标签
    if layout.parking:
        row, col = layout.parking
        labels[row][col] = "停"

    # 创建图表
    fig = go.Figure()

    # 图表数据
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

    # 文本注释 - 显示标签
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

    # 路径点（如果存在）
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
        width=width * 50,  # 基于网格大小调整图表大小
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
            range=[height - 0.5, -0.5],
        ),
        # 国际象棋棋盘背景网格
        shapes=[
            *[dict(
                type="line",
                x0=-0.5, x1=width-0.5,
                y0=i-0.5, y1=i-0.5,
                line=dict(color="lightgrey", width=1)
            ) for i in range(height+1)],
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