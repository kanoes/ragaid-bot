"""
工具函数
"""
import os
import json
from typing import Tuple, Optional, List, Dict, Any

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
    """
    获取可用的レストランレイアウト列表
    """
    # 检查是否存在新式布局文件
    new_format_path = os.path.join(layout_dir, "layouts.json")
    if os.path.exists(new_format_path):
        try:
            with open(new_format_path, encoding="utf-8") as f:
                layouts_data = json.load(f)
                return [layout["name"] for layout in layouts_data["layouts"]]
        except (json.JSONDecodeError, KeyError) as e:
            print(f"加载新式布局文件失败: {e}")
            return []
    
    # 回退到旧式布局文件
    if os.path.exists(layout_dir):
        return sorted(os.path.splitext(f)[0] for f in os.listdir(layout_dir) if f.endswith(".json") and f != "layouts.json")
    return []

def parse_layout_from_strings(layout_name: str, layout_lines: List[str]):
    """
    从字符串数组解析レストランレイアウト
    
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
    显示ASCII格式的レストランレイアウト
    
    Args:
        restaurant: 餐厅对象或レストランレイアウト对象
        restaurant_name: 餐厅名称（可选）
    """
    layout = getattr(restaurant, 'layout', restaurant)
    name = restaurant_name or getattr(restaurant, 'name', 'Restaurant')
    
    # 符号映射（根据数字编码）
    symbols = {
        0: ".",    # 空地
        1: "#",    # 墙/障碍
        2: "?",    # 桌子（将被替换为桌号）
        3: "?",    # 厨房
        4: "P",    # 停靠点
        100: "K",  # 厨房（新格式）
        200: "P",  # 停靠点（新格式）
    }
    
    # 打印标题
    print(f"レストランレイアウト: {name} ({layout.width}x{layout.height})")
    print("-" * (layout.width * 2 + 3))
    
    # 反向查找表格ID
    rev_tables = {pos: tid for tid, pos in layout.tables.items()}
    
    # 打印布局
    for i in range(layout.height):
        print("|", end=" ")
        for j in range(layout.width):
            cell_value = layout.grid[i][j]
            if cell_value == 2 and (i, j) in rev_tables:
                # 显示桌子ID
                print(rev_tables[(i, j)], end=" ")
            elif 2 <= cell_value <= 99:
                # 数字表示的桌子ID（尝试从rev_tables获取，否则显示?）
                print(rev_tables.get((i, j), "?"), end=" ")
            else:
                # 其他类型单元格
                print(symbols.get(cell_value, "?"), end=" ")
        print("|")
    
    print("-" * (layout.width * 2 + 3))

def load_restaurant(layout_name, layout_dir=LAYOUT_DIR):
    """
    加载レストランレイアウト
    """
    new_format_path = os.path.join(layout_dir, "layouts.json")
    if not os.path.exists(new_format_path):
        raise FileNotFoundError(f"找不到布局文件: {new_format_path}")

    with open(new_format_path, encoding="utf-8") as f:
        layouts_data = json.load(f)
    for layout in layouts_data["layouts"]:
        if layout["name"] == layout_name:
            cfg = RestaurantLayout.parse_layout_from_array(
                layout_name, layout["grid"]
            )
            return Restaurant(layout_name, RestaurantLayout(**cfg))

    raise KeyError(f"在 layouts.json 中未找到名为 {layout_name} 的布局")

def save_restaurant_layout(layout_data, layout_dir=LAYOUT_DIR):
    """
    保存レストランレイアウト到JSON文件
    
    Args:
        layout_data: dict, 包含布局数据
        layout_dir: 保存目录路径
    
    Returns:
        str: 保存文件的路径
    """
    # 确保目录存在
    os.makedirs(layout_dir, exist_ok=True)
    
    # 准备数据
    name = layout_data.get("name", "新布局")
    grid = layout_data.get("grid", [])
    
    # 检查是否存在layouts.json文件
    layouts_path = os.path.join(layout_dir, "layouts.json")
    if os.path.exists(layouts_path):
        # 加载现有布局
        try:
            with open(layouts_path, "r", encoding="utf-8") as f:
                layouts_data = json.load(f)
                layouts = layouts_data.get("layouts", [])
        except Exception:
            # 如果读取出错，创建新的布局列表
            layouts = []
    else:
        layouts = []
    
    # 查找是否已存在同名布局
    layout_found = False
    for i, layout in enumerate(layouts):
        if layout.get("name") == name:
            # 更新现有布局
            layouts[i] = {
                "name": name,
                "grid": grid
            }
            layout_found = True
            break
    
    # 如果没有找到布局，添加新的
    if not layout_found:
        layouts.append({
            "name": name,
            "grid": grid
        })
    
    # 保存到layouts.json
    with open(layouts_path, "w", encoding="utf-8") as f:
        json.dump({"layouts": layouts}, f, ensure_ascii=False, indent=2)
    
    return layouts_path

def save_layouts_to_single_file(layouts: List[Dict[str, Any]], layout_dir=LAYOUT_DIR):
    """
    将多个レストランレイアウト保存到单一的layouts.json文件
    
    Args:
        layouts: 布局数据列表，每个元素包含name和grid
        layout_dir: 保存目录路径
    
    Returns:
        str: 保存文件的路径
    """
    # 确保目录存在
    os.makedirs(layout_dir, exist_ok=True)
    
    # 准备保存的数据
    save_data = {
        "layouts": layouts
    }
    
    # 保存到文件
    file_path = os.path.join(layout_dir, "layouts.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    
    return file_path

def delete_restaurant_layout(layout_name, layout_dir=LAYOUT_DIR):
    """
    删除レストランレイアウト文件
    
    Args:
        layout_name: 布局名称
        layout_dir: 布局文件目录
    
    Returns:
        bool: 是否成功删除
    """
    # 检查新格式文件
    new_format_path = os.path.join(layout_dir, "layouts.json")
    if os.path.exists(new_format_path):
        try:
            with open(new_format_path, "r", encoding="utf-8") as f:
                layouts_data = json.load(f)
                
            # 过滤掉要删除的布局
            layouts_data["layouts"] = [
                layout for layout in layouts_data["layouts"]
                if layout["name"] != layout_name
            ]
            
            # 保存回文件
            with open(new_format_path, "w", encoding="utf-8") as f:
                json.dump(layouts_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"从新格式文件删除布局失败: {e}")
            return False
    
    # 回退到旧格式
    file_path = os.path.join(layout_dir, f"{layout_name}.json")
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

def build_robot(use_ai, layout, restaurant_name="默认餐厅"):
    """
    构建机器人实例
    """
    if use_ai:
        robot = AIEnhancedRobot(layout, robot_id=1, knowledge_dir=RAG_KB_DIR, restaurant_name=restaurant_name)
    else:
        robot = Robot(layout, robot_id=1, restaurant_name=restaurant_name)
        
    # 设置机器人的目标容忍参数
    robot.GOAL_TOLERANCE = 0  # 必须到达确切位置才算送达
    
    return robot

def make_order(seq, table_id):
    """
    创建订单实例
    """
    return Order(order_id=seq, table_id=table_id, prep_time=0)

def create_rich_layout(grid, height, width, tables, 
                       robot_position: Optional[Tuple[int, int]] = None,
                       highlight_path: Optional[list] = None):
    """
    创建富文本格式的レストランレイアウト
    
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
    """
    获取特定位置对应的桌子ID
    """
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
    创建富文本格式的レストランレイアウト面板
    
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
