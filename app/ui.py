"""
UI组件函数
"""
import contextlib
from io import StringIO
import io
import streamlit as st
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

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