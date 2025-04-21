"""
UI组件函数
"""
import contextlib
from io import StringIO
import io
import streamlit as st
import plotly.graph_objects as go
import numpy as np
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from streamlit_plotly_events import plotly_events

from .state import (get_editor_height, set_editor_height, 
                   get_editor_width, set_editor_width,
                   get_editor_grid, set_editor_grid,
                   get_editor_tables, set_editor_tables,
                   get_editor_kitchen, set_editor_kitchen,
                   get_editor_parking, set_editor_parking,
                   get_editor_layout_name, set_editor_layout_name,
                   reset_editor)

def setup_page():
    """设置页面基本配置"""
    st.set_page_config(page_title="餐厅送餐机器人模拟系统", layout="wide")
    st.title("餐厅送餐机器人模拟系统 (Web)")

def render_sidebar(layouts, restaurant):
    """渲染侧边栏组件"""
    if not layouts:
        st.error("未找到任何餐厅布局文件")
        return None, None, None
    
    selected = st.sidebar.selectbox("选择餐厅布局", layouts)
    use_ai = st.sidebar.checkbox("使用 RAG 智能机器人", value=False)
    num_orders = st.sidebar.slider("订单数量", 1, max(1, len(restaurant.layout.tables)), 1)
    
    sim_button = st.sidebar.button("开始模拟")
    
    return selected, use_ai, num_orders, sim_button

def render_restaurant_layout(restaurant, path=None, table_positions=None, title="餐厅布局"):
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

    html = f'''
    <div style="display: grid; grid-template-columns: repeat({len(restaurant.layout.grid[0])}, 24px); gap: 1px;">
    '''

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

            html += f'''
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
            '''

    html += "</div>"

    st.markdown(html, unsafe_allow_html=True)

def render_plotly_restaurant_layout(restaurant, path=None, title="餐厅布局"):
    """
    使用Plotly渲染餐厅布局，效果更好，视觉效果类似国际象棋棋盘。
    
    参数:
    - restaurant: Restaurant，餐厅实例
    - path: List[Tuple[int, int]]，可选，机器人路径
    - title: str，标题
    """
    layout = restaurant.layout
    grid = layout.grid
    height = layout.height
    width = layout.width
    
    # 创建颜色映射
    colormap = {
        0: 'white',       # 空地
        1: '#333333',     # 墙壁/障碍
        2: '#00cc66',     # 桌子
        3: '#f5c518',     # 厨房
        4: '#4da6ff',     # 停靠点
    }
    
    # 创建标签映射
    labels = [['' for _ in range(width)] for _ in range(height)]
    
    # 设置桌子标签
    for table_id, pos in layout.tables.items():
        row, col = pos
        labels[row][col] = table_id
    
    # 设置厨房标签
    for row, col in layout.kitchen:
        labels[row][col] = '厨'
    
    # 设置停靠点标签
    if layout.parking:
        row, col = layout.parking
        labels[row][col] = '停'
    
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
        [1.0, colormap[4]]
    ]
    
    fig.add_trace(go.Heatmap(
        z=heatmap_z,
        colorscale=colorscale,
        showscale=False,
        hoverinfo='none',
    ))
    
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
                        size=14,
                        color='black',
                        family='Arial Black'
                    ),
                )
    
    # 添加路径点（如果有）
    if path:
        path_y, path_x = zip(*path)  # 注意Plotly的坐标系
        fig.add_trace(go.Scatter(
            x=path_x,
            y=path_y,
            mode='lines+markers',
            marker=dict(size=8, color='red'),
            line=dict(width=2, color='red'),
            name='路径'
        ))
    
    # 设置图表布局
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=20)
        ),
        width=width*50,  # 根据网格大小调整图表大小
        height=height*50,
        margin=dict(l=0, r=0, t=40, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=True,
            gridcolor='lightgrey',
            gridwidth=1,
            zeroline=False,
            showticklabels=False,
            range=[-0.5, width-0.5]
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgrey',
            gridwidth=1,
            zeroline=False,
            showticklabels=False,
            scaleanchor="x",
            scaleratio=1,
            range=[height-0.5, -0.5]  # 反转Y轴使(0,0)在左上角
        )
    )
    
    st.plotly_chart(fig)
    
    return fig

def _get_table_style(x, y, tables):
    """获取桌子的样式和标签"""
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
    """渲染统计结果"""
    st.header("统计结果")
    col1, col2, col3 = st.columns(3)
    col1.metric("成功配送", stats["delivered"])
    col2.metric("配送失败", stats["failed"])
    
    total = stats["delivered"] + stats["failed"]
    if total > 0:
        rate = stats["delivered"] / total * 100
        col3.metric("成功率", f"{rate:.1f}%")
    else:
        col3.metric("成功率", "0.0%")

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
        new_height = st.number_input("高度", min_value=3, max_value=30, value=current_height)
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
            tables = {k:v for k,v in tables.items() if v[0] < new_height}
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
        new_width = st.number_input("宽度", min_value=3, max_value=30, value=current_width)
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
            tables = {k:v for k,v in tables.items() if v[1] < new_width}
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
        layout_name = st.text_input("布局名称", value=current_name)
        if layout_name != current_name:
            set_editor_layout_name(layout_name)
    
    # 创建一个可视化的布局编辑界面
    st.subheader("编辑布局")
    st.write("点击网格单元格来修改其类型")
    
    # 选择要编辑的元素类型
    element_type = st.radio(
        "选择元素类型", 
        ["墙壁/障碍", "空地", "桌子", "厨房", "停靠点"],
        horizontal=True
    )
    
    # 元素类型映射到数值
    type_map = {
        "墙壁/障碍": 1,
        "空地": 0,
        "桌子": 2,
        "厨房": 3,
        "停靠点": 4
    }
    
    # 在桌子模式下，需要输入桌子ID
    table_id = None
    if element_type == "桌子":
        table_id = st.text_input("桌子ID (单个字母A-Z)", max_chars=1)
    
    # 创建Plotly图表以便交互编辑
    fig = render_plotly_editor_grid()

    # 显示图表
    st.plotly_chart(fig, use_container_width=True)
    
    # 检测点击事件
    clicked_point = plotly_events(fig, click_event=True)
    if clicked_point:
        # 获取点击的坐标
        try:
            point_data = clicked_point[0]
            row, col = int(point_data['y']), int(point_data['x'])
            
            # 获取当前状态
            grid = get_editor_grid()
            tables = get_editor_tables()
            kitchen = get_editor_kitchen()
            parking = get_editor_parking()
            height = get_editor_height()
            width = get_editor_width()
            
            # 根据选择的元素类型进行修改
            if 0 <= row < height and 0 <= col < width:
                if element_type == "桌子" and table_id and table_id.isalpha() and len(table_id) == 1:
                    # 处理桌子 - 需要存储桌子ID和位置
                    grid[row][col] = type_map[element_type]
                    tables[table_id.upper()] = (row, col)
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
                            grid[old_row][old_col] = 0
                    
                    grid[row][col] = type_map[element_type]
                    set_editor_parking((row, col))
                else:
                    # 处理墙壁或空地
                    grid[row][col] = type_map[element_type]
                    
                    # 如果将某个特殊位置设为墙壁或空地，需要从相应列表中移除
                    # 检查和清理桌子
                    tables_to_remove = []
                    for tid, pos in tables.items():
                        if pos == (row, col) and grid[row][col] != 2:
                            tables_to_remove.append(tid)
                    for tid in tables_to_remove:
                        del tables[tid]
                    set_editor_tables(tables)
                    
                    # 检查和清理厨房
                    if (row, col) in kitchen and grid[row][col] != 3:
                        kitchen.remove((row, col))
                        set_editor_kitchen(kitchen)
                    
                    # 检查和清理停靠点
                    if parking == (row, col) and grid[row][col] != 4:
                        set_editor_parking(None)
                
                # 更新网格
                set_editor_grid(grid)
                
                # 强制重新渲染
                st.rerun()
        except (KeyError, IndexError) as e:
            st.error(f"无法处理点击: {e}")
    
    # 保存、重置和自动围墙按钮
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("保存布局"):
            # 验证布局是否有效
            if not validate_layout():
                st.error("布局无效! 需要至少一个桌子、厨房和停靠点")
                return None
            
            # 返回当前编辑的布局数据
            return {
                "name": get_editor_layout_name(),
                "grid": get_editor_grid(),
                "table_positions": get_editor_tables(),
                "kitchen_positions": get_editor_kitchen(),
                "parking_position": get_editor_parking()
            }
    
    with col2:
        if st.button("重置布局"):
            # 重置为空白布局
            reset_editor()
            st.rerun()
    
    with col3:
        if st.button("自动添加围墙"):
            # 在布局边缘添加墙壁
            grid = get_editor_grid()
            height = get_editor_height()
            width = get_editor_width()
            
            # 添加顶部和底部墙壁
            for j in range(width):
                grid[0][j] = 1
                grid[height-1][j] = 1
            
            # 添加左右墙壁
            for i in range(height):
                grid[i][0] = 1
                grid[i][width-1] = 1
            
            # 更新网格
            set_editor_grid(grid)
            
            st.rerun()
    
    return None

def render_plotly_editor_grid():
    """
    渲染可编辑的Plotly餐厅布局网格
    
    返回:
        go.Figure: Plotly图表对象
    """
    grid = get_editor_grid()
    height = get_editor_height()
    width = get_editor_width()
    
    # 创建颜色映射
    colormap = {
        0: 'white',       # 空地
        1: '#333333',     # 墙壁/障碍
        2: '#00cc66',     # 桌子
        3: '#f5c518',     # 厨房
        4: '#4da6ff',     # 停靠点
    }
    
    # 创建标签映射
    labels = [['' for _ in range(width)] for _ in range(height)]
    
    # 设置桌子标签
    for table_id, pos in get_editor_tables().items():
        row, col = pos
        if 0 <= row < height and 0 <= col < width:  # 防止越界
            labels[row][col] = table_id
    
    # 设置厨房标签
    for row, col in get_editor_kitchen():
        if 0 <= row < height and 0 <= col < width:  # 防止越界
            labels[row][col] = '厨'
    
    # 设置停靠点标签
    parking = get_editor_parking()
    if parking:
        row, col = parking
        if 0 <= row < height and 0 <= col < width:  # 防止越界
            labels[row][col] = '停'
    
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
        [1.0, colormap[4]]
    ]
    
    fig.add_trace(go.Heatmap(
        z=heatmap_z,
        colorscale=colorscale,
        showscale=False,
        hoverinfo='text',
        text=[[get_cell_description(i, j) for j in range(width)] for i in range(height)],
    ))
    
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
                        size=14,
                        color='black',
                        family='Arial Black'
                    ),
                )
    
    # 设置图表布局
    fig.update_layout(
        width=min(700, width*40),  # 限制最大宽度
        height=min(700, height*40),  # 限制最大高度
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=True,
            gridcolor='lightgrey',
            gridwidth=1,
            zeroline=False,
            range=[-0.5, width-0.5],
            tickvals=list(range(width)),
            ticktext=[str(i) for i in range(width)],
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgrey',
            gridwidth=1,
            zeroline=False,
            scaleanchor="x",
            scaleratio=1,
            range=[height-0.5, -0.5],  # 反转Y轴使(0,0)在左上角
            tickvals=list(range(height)),
            ticktext=[str(i) for i in range(height)],
        )
    )
    
    return fig

def get_cell_description(row, col):
    """获取单元格的描述文本，用于悬停提示"""
    grid = get_editor_grid()
    if row >= len(grid) or col >= len(grid[0]):
        return ""
    
    cell_type = grid[row][col]
    descriptions = {
        0: "空地",
        1: "墙壁/障碍",
        2: "桌子",
        3: "厨房",
        4: "停靠点"
    }
    
    base_desc = f"({row}, {col}): {descriptions.get(cell_type, '未知')}"
    
    # 添加额外信息
    if cell_type == 2:  # 桌子
        for tid, pos in get_editor_tables().items():
            if pos == (row, col):
                return f"{base_desc} {tid}"
    
    return base_desc

def validate_layout():
    """验证布局是否有效"""
    # 检查是否至少有一个桌子
    if not get_editor_tables():
        return False
    
    # 检查是否至少有一个厨房
    if not get_editor_kitchen():
        return False
    
    # 检查是否有停靠点
    if not get_editor_parking():
        return False
    
    return True 