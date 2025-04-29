"""
编辑器相关组件
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
from streamlit_plotly_events import plotly_events

from ..state import (
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
)


def render_layout_editor():
    """
    渲染布局编辑器界面
    
    返回值:
        dict: 编辑后的布局数据，如果未保存则返回None
    """
    # 创建简单的表格式布局编辑器
    st.subheader("餐厅布局编辑器")
    
    # 布局尺寸控制
    st.write("**网格尺寸控制**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        current_height = get_editor_height()
        new_height = st.number_input(
            "高度", min_value=3, max_value=30, value=current_height, key="editor_height_input"
        )
        if new_height != current_height:
            # 更改高度时保留现有数据
            current_grid = get_editor_grid()
            current_width = get_editor_width()
            new_grid = [[0 for _ in range(current_width)] for _ in range(new_height)]
            for i in range(min(new_height, current_height)):
                for j in range(current_width):
                    new_grid[i][j] = current_grid[i][j]
            set_editor_grid(new_grid)
            set_editor_height(new_height)
            
            # 更新表格位置
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
            # 更改宽度时保留现有数据
            current_grid = get_editor_grid()
            current_height = get_editor_height()
            new_grid = [[0 for _ in range(new_width)] for _ in range(current_height)]
            for i in range(current_height):
                for j in range(min(new_width, current_width)):
                    new_grid[i][j] = current_grid[i][j]
            set_editor_grid(new_grid)
            set_editor_width(new_width)

            # 更新表格位置
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

    # 创建用于布局编辑的视觉界面
    st.subheader("布局编辑")
    st.write("点击网格单元格更改类型")

    # 为布局编辑创建多列布局
    edit_col1, edit_col2 = st.columns([3, 1])
    
    with edit_col2:
        st.write("**元素工具箱**")
        # 选择要编辑的元素类型
        element_type = st.radio(
            "选择元素类型", 
            ["墙/障碍物", "空地", "餐桌", "厨房", "停车点"],
            captions=["#", ".", "A-Z", "厨", "停"],
            key="element_type_radio"
        )
        
        # 显示当前元素的颜色
        element_colors = {
            "墙/障碍物": "#333333",
            "空地": "white",
            "餐桌": "#00cc66",
            "厨房": "#f5c518",
            "停车点": "#4da6ff"
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
                color: {"black" if element_type != "墙/障碍物" else "white"};
                font-weight: bold;
            ">
                {element_type}
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # 餐桌模式时，需要输入餐桌ID
        table_id = None
        if element_type == "餐桌":
            table_id = st.text_input("餐桌ID (单个字母 A-Z)", max_chars=1, key="table_id_input")
            if table_id and (not table_id.isalpha() or len(table_id) != 1):
                st.warning("餐桌ID必须是单个字母(A-Z)")
                
        # 显示布局统计信息
        st.write("**布局统计**")
        tables = get_editor_tables()
        kitchen = get_editor_kitchen()
        parking = get_editor_parking()
        
        st.markdown(f"""
        - 网格大小: {get_editor_height()} × {get_editor_width()}
        - 餐桌: {len(tables)} 个
        - 厨房: {len(kitchen)} 个
        - 停车点: {"有" if parking else "无"}
        """)
        
        # 操作按钮
        st.write("**操作**")
        if st.button("重置布局", key="editor_reset_button"):
            # 重置为空白布局
            reset_editor()
            st.rerun()
            
        if st.button("自动添加墙壁", key="editor_add_walls_button"):
            # 在布局边缘添加墙壁
            grid = get_editor_grid()
            height = get_editor_height()
            width = get_editor_width()

            # 添加上下墙壁
            for j in range(width):
                grid[0][j] = 1
                grid[height - 1][j] = 1

            # 添加左右墙壁
            for i in range(height):
                grid[i][0] = 1
                grid[i][width - 1] = 1

            # 更新布局
            set_editor_grid(grid)
            st.rerun()
    
    with edit_col1:
        # 创建Plotly图表实现交互式编辑
        fig = render_interactive_editor_grid()
        
        # 使用plotly_events显示图表并监听点击事件
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
                
                # 确保坐标在有效范围内
                if 0 <= row < height and 0 <= col < width:
                    
                    # 处理特殊元素类型
                    if element_type == "餐桌":
                        if table_id:
                            # 更新表格位置，同一ID只能有一个
                            for k, v in list(tables.items()):
                                if k == table_id:
                                    tables.pop(k)
                            tables[table_id] = (row, col)
                            grid[row][col] = 2
                            
                            # 如果这个位置之前是其他特殊元素，需要移除
                            for k, v in list(tables.items()):
                                if v == (row, col) and k != table_id:
                                    tables.pop(k)
                            
                            if (row, col) in kitchen:
                                kitchen.remove((row, col))
                            
                            if parking == (row, col):
                                parking = None
                    
                    elif element_type == "厨房":
                        # 更新厨房位置，可以有多个
                        if (row, col) not in kitchen:
                            kitchen.append((row, col))
                        grid[row][col] = 3
                        
                        # 移除其他重叠的元素
                        for k, v in list(tables.items()):
                            if v == (row, col):
                                tables.pop(k)
                        
                        if parking == (row, col):
                            parking = None
                    
                    elif element_type == "停车点":
                        # 更新停车点，只能有一个
                        parking = (row, col)
                        grid[row][col] = 4
                        
                        # 移除其他重叠的元素
                        for k, v in list(tables.items()):
                            if v == (row, col):
                                tables.pop(k)
                        
                        if (row, col) in kitchen:
                            kitchen.remove((row, col))
                    
                    elif element_type == "空地":
                        # 清除该位置的所有元素
                        grid[row][col] = 0
                        
                        for k, v in list(tables.items()):
                            if v == (row, col):
                                tables.pop(k)
                        
                        if (row, col) in kitchen:
                            kitchen.remove((row, col))
                        
                        if parking == (row, col):
                            parking = None
                    
                    else:  # 墙/障碍物
                        grid[row][col] = 1
                        
                        # 移除重叠的元素
                        for k, v in list(tables.items()):
                            if v == (row, col):
                                tables.pop(k)
                        
                        if (row, col) in kitchen:
                            kitchen.remove((row, col))
                        
                        if parking == (row, col):
                            parking = None
                    
                    # 更新状态
                    set_editor_grid(grid)
                    set_editor_tables(tables)
                    set_editor_kitchen(kitchen)
                    set_editor_parking(parking)
                    
                    # 强制重新渲染
                    st.rerun()
            except Exception as e:
                st.error(f"处理点击事件时出错: {e}")
        
    # 保存按钮区域
    save_col1, save_col2 = st.columns([3, 1])
        
    with save_col2:
        if st.button("保存布局", key="editor_save_layout_button", type="primary"):
            # 验证布局有效性
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
    渲染交互式可编辑的Plotly餐厅布局网格，增强版

    返回值:
        go.Figure: Plotly图表对象
    """
    grid = get_editor_grid()
    height = get_editor_height()
    width = get_editor_width()
    tables = get_editor_tables()
    kitchen = get_editor_kitchen()
    parking = get_editor_parking()

    # 颜色映射
    colormap = {
        0: "white",         # 空地
        1: "#333333",       # 墙/障碍物
        2: "#00cc66",       # 餐桌
        3: "#f5c518",       # 厨房
        4: "#4da6ff",       # 停车点
    }

    # 标签映射
    labels = [["" for _ in range(width)] for _ in range(height)]

    # 餐桌标签
    for table_id, pos in tables.items():
        row, col = pos
        if 0 <= row < height and 0 <= col < width:  # 防止越界
            labels[row][col] = table_id

    # 厨房标签
    for row, col in kitchen:
        if 0 <= row < height and 0 <= col < width:  # 防止越界
            labels[row][col] = "厨"

    # 停车点标签
    if parking:
        row, col = parking
        if 0 <= row < height and 0 <= col < width:  # 防止越界
            labels[row][col] = "停"

    # 创建图表
    fig = go.Figure()

    # 热力图数据
    heatmap_z = np.array(grid)
    colorscale = [
        [0, colormap[0]],      # 空地
        [0.2, colormap[0]],
        [0.2, colormap[1]],    # 墙/障碍物
        [0.4, colormap[1]],
        [0.4, colormap[2]],    # 餐桌
        [0.6, colormap[2]],
        [0.6, colormap[3]],    # 厨房
        [0.8, colormap[3]],
        [0.8, colormap[4]],    # 停车点
        [1.0, colormap[4]],
    ]

    # 生成每个单元格的悬停文本
    hover_texts = []
    for i in range(height):
        row_texts = []
        for j in range(width):
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
            # 禁用默认的heatmap提示
            zhoverformat="none"
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
                    font=dict(
                        size=16, 
                        color="black", 
                        family="Arial Black"
                    ),
                )

    # 设置图表布局
    fig.update_layout(
        width=min(800, max(400, width * 35)),
        height=min(800, max(400, height * 35)),
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            range=[-0.5, width - 0.5],
            tickvals=list(range(width)),
            ticktext=[str(i) for i in range(width)],
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            scaleanchor="x",
            scaleratio=1,
            range=[height - 0.5, -0.5],
            tickvals=list(range(height)),
            ticktext=[str(i) for i in range(height)],
            tickfont=dict(size=10),
        ),
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
        ],
        hoverlabel=dict(
            bgcolor="white",
            font_size=14,
            font_family="Arial"
        )
    )

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
    
    返回值:
        tuple: (is_valid, message) 布局是否有效及详细信息
    """
    # 检查是否至少有一个餐桌
    if not get_editor_tables():
        return False, "至少需要一个餐桌"

    # 检查是否至少有一个厨房
    if not get_editor_kitchen():
        return False, "至少需要一个厨房"

    # 检查是否至少有一个停车点
    if not get_editor_parking():
        return False, "至少需要一个停车点"
        
    # 检查布局名称
    if not get_editor_layout_name() or get_editor_layout_name() == "新レイアウト":
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
    descriptions = {0: "空地", 1: "墙/障碍物", 2: "餐桌", 3: "厨房", 4: "停车点"}

    base_desc = f"({row}, {col}): {descriptions.get(cell_type, '未知')}"

    # 添加额外信息
    if cell_type == 2:  # 餐桌
        for tid, pos in get_editor_tables().items():
            if pos == (row, col):
                return f"{base_desc} {tid}"

    return base_desc 