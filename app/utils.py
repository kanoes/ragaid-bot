"""
工具函数
"""
import os
import json
from io import StringIO
from typing import Dict, Tuple, Optional, Any, List

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.box import ROUNDED
from rich.style import Style

from restaurant.restaurant_layout import RestaurantLayout
from restaurant.restaurant import Restaurant
from robot import AIEnhancedRobot, Robot
from robot.order import Order

from .constants import LAYOUT_DIR, RAG_KB_DIR, EMPTY_STYLE, WALL_STYLE, TABLE_STYLE, KITCHEN_STYLE, PARKING_STYLE, ERROR_STYLE


def available_layouts(layout_dir=LAYOUT_DIR):
    """获取可用的餐厅布局列表"""
    return sorted(os.path.splitext(f)[0] for f in os.listdir(layout_dir) if f.endswith(".json"))

def parse_layout_from_strings(layout_name: str, layout_lines: List[str]):
    """
    从字符串数组解析餐厅布局
    
    Args:
        layout_name: 布局名称
        layout_lines: 布局字符串数组
        
    Returns:
        dict: 包含解析后的布局配置
    """
    # 字符到数值的映射
    char_map = {
        "#": 1, "＃": 1, "W": 1,    # 墙壁/障碍
        "*": 0, ".": 0,             # 空地
        "台": 3,                    # 厨房
        "停": 4, "P": 4             # 停靠点
    }
    
    # 初始化数据结构
    height = len(layout_lines)
    width = max(len(line.split()) for line in layout_lines) if height else 0
    grid = [[0] * width for _ in range(height)]
    table_positions = {}
    kitchen_positions = []
    parking_position = None
    
    # 解析布局字符串
    for row, line in enumerate(layout_lines):
        tokens = line.split()
        for col, token in enumerate(tokens):
            if token in char_map:
                # 已知符号
                value = char_map[token]
                grid[row][col] = value
                
                # 特殊位置记录
                if value == 3:  # 厨房
                    kitchen_positions.append((row, col))
                elif value == 4:  # 停靠点
                    parking_position = (row, col)
            elif token.isalpha() and len(token) == 1:
                # 桌子
                grid[row][col] = 2
                table_positions[token] = (row, col)
            else:
                # 未知符号，当作空地处理
                grid[row][col] = 0
    
    return {
        "grid": grid,
        "table_positions": table_positions,
        "kitchen_positions": kitchen_positions,
        "parking_position": parking_position
    }

def display_restaurant_ascii(restaurant, restaurant_name=None):
    """
    显示ASCII格式的餐厅布局
    
    Args:
        restaurant: 餐厅对象或餐厅布局对象
        restaurant_name: 餐厅名称（可选）
    """
    layout = getattr(restaurant, 'layout', restaurant)
    name = restaurant_name or getattr(restaurant, 'name', 'Restaurant')
    
    # 符号映射
    symbols = {
        0: ".",    # 空地
        1: "#",    # 墙/障碍
        2: "?",    # 桌子（特殊处理）
        3: "K",    # 厨房
        4: "P",    # 停靠点
    }
    
    # 打印标题
    print(f"餐厅布局: {name} ({layout.width}x{layout.height})")
    print("-" * (layout.width * 2 + 3))
    
    # 反向查找表格ID
    rev_tables = {pos: tid for tid, pos in layout.tables.items()}
    
    # 打印布局
    for i in range(layout.height):
        print("|", end=" ")
        for j in range(layout.width):
            if layout.grid[i][j] == 2 and (i, j) in rev_tables:
                # 显示桌子字母
                print(rev_tables[(i, j)], end=" ")
            else:
                print(symbols.get(layout.grid[i][j], "?"), end=" ")
        print("|")
    
    print("-" * (layout.width * 2 + 3))

def load_restaurant(layout_name, layout_dir=LAYOUT_DIR):
    """加载餐厅布局"""
    json_path = os.path.join(layout_dir, f"{layout_name}.json")
    with open(json_path, encoding="utf-8") as fp:
        data = json.load(fp)
    
    # 使用RestaurantLayout类的静态方法解析布局
    cfg = RestaurantLayout.parse_layout_from_strings(layout_name, data["layout"])
    return Restaurant(data.get("name", layout_name), RestaurantLayout(**cfg))

def build_robot(use_ai, layout):
    """构建机器人实例"""
    if use_ai:
        return AIEnhancedRobot(layout, robot_id=1, knowledge_dir=RAG_KB_DIR)
    return Robot(layout, robot_id=1)

def make_order(seq, table_id):
    """创建订单实例"""
    return Order(order_id=seq, table_id=table_id, prep_time=0)

def create_rich_layout(grid, height, width, tables, 
                       robot_position: Optional[Tuple[int, int]] = None,
                       highlight_path: Optional[list] = None):
    """
    创建富文本格式的餐厅布局
    
    Args:
        grid: 餐厅网格数据
        height: 网格高度
        width: 网格宽度
        tables: 桌子位置字典
        robot_position: 机器人当前位置（可选）
        highlight_path: 需要高亮显示的路径点列表（可选）
    """
    # 存储高亮点的集合
    highlight_points = set(highlight_path or [])
    
    # 定义各种元素的样式
    cell_chars = {
        0: "  ",              # 空地
        1: "██",              # 墙/障碍
        2: None,              # 桌子 (特殊处理)
        3: "厨",              # 厨房
        4: "停",              # 停靠点
    }
    
    cell_styles = {
        0: EMPTY_STYLE,
        1: WALL_STYLE,
        2: TABLE_STYLE,
        3: KITCHEN_STYLE,
        4: PARKING_STYLE,
    }
    
    layout_text = Text()
    
    for x in range(height):
        for y in range(width):
            cell_type = grid[x][y]
            pos = (x, y)
            
            # 检查是否需要突出显示当前点
            is_robot_pos = robot_position and pos == robot_position
            is_highlight = pos in highlight_points
            
            # 获取单元格文本
            if cell_type == 2:  # 桌子特殊处理
                cell_text = get_table_id(pos, tables)
            else:
                cell_text = cell_chars.get(cell_type, "??")
            
            # 获取样式
            style = cell_styles.get(cell_type, ERROR_STYLE)
            
            # 处理高亮情况
            if is_robot_pos:
                # 机器人位置使用特殊符号和红色背景
                text_segment = Text("🤖", style=Style(bgcolor="red", color="white", bold=True))
            elif is_highlight:
                # 路径点使用特殊背景色
                text_segment = Text(cell_text, style=Style(bgcolor="magenta", color="white"))
            else:
                # 普通单元格
                text_segment = Text(cell_text, style=style)
                
            layout_text.append(text_segment)
            
        # 行结束，添加换行符
        layout_text.append("\n")
        
    return layout_text

def get_table_id(pos, tables):
    """获取特定位置对应的桌子ID"""
    # 通过位置反查桌子ID
    for tid, tpos in tables.items():
        if tpos == pos:
            return tid.center(2)
    return "桌"

def create_rich_restaurant_panel(restaurant, 
                                robot_position=None, 
                                highlight_path=None,
                                title_suffix=""):
    """
    创建富文本格式的餐厅布局面板
    
    Args:
        restaurant: 餐厅对象
        robot_position: 机器人当前位置（可选）
        highlight_path: 需要高亮显示的路径（可选）
        title_suffix: 标题后缀（可选）
    """
    layout = restaurant.layout
    
    title = f"{restaurant.name}"
    if title_suffix:
        title += f" - {title_suffix}"
        
    panel = Panel(
        create_rich_layout(
            layout.grid, 
            layout.height, 
            layout.width, 
            layout.tables,
            robot_position=robot_position,
            highlight_path=highlight_path
        ),
        title=f"[bold blue]{title}[/bold blue]",
        border_style="blue",
        box=ROUNDED,
        padding=(1, 2)
    )
    return panel 