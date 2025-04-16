"""
餐厅模拟系统辅助函数

提供了餐厅布局加载、创建和保存等功能
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Union, Optional

from modules.restaurant.restaurant import Restaurant
from modules.restaurant.restaurant_grid import RestaurantEnvironment

# 布局文件目录
LAYOUTS_DIR = os.path.join(os.path.dirname(__file__), 'layouts')
os.makedirs(LAYOUTS_DIR, exist_ok=True)

def list_restaurant_layouts() -> List[str]:
    """
    列出所有可用的餐厅布局文件
    
    Returns:
        List[str]: 布局文件名列表（不含扩展名）
    """
    layouts = []
    
    # 遍历layouts目录
    for filename in os.listdir(LAYOUTS_DIR):
        # 只考虑JSON文件
        if filename.endswith('.json'):
            # 去掉扩展名
            layout_name = os.path.splitext(filename)[0]
            layouts.append(layout_name)
    
    # 按名称排序
    layouts.sort()
    return layouts

def select_restaurant_layout(custom_name: Optional[str] = None) -> Optional[Restaurant]:
    """
    交互式选择并加载餐厅布局
    
    Args:
        custom_name: 自定义餐厅名称 (可选)
        
    Returns:
        Restaurant: 加载的餐厅对象，如果没有可用布局则返回None
    """
    layouts = list_restaurant_layouts()
    
    if not layouts:
        print("\n错误: 没有找到任何餐厅布局文件!")
        print(f"请先创建餐厅布局JSON文件并保存到以下目录:")
        print(f"  {os.path.abspath(LAYOUTS_DIR)}")
        return None
    
    print("\n===== 可用的餐厅布局 =====")
    for i, layout in enumerate(layouts):
        print(f"{i+1}. {layout}")
    
    selected_layout = None
    while True:
        try:
            choice = input("\n请选择要加载的布局 (输入编号): ").strip()
            
            # 如果用户直接输入布局名称
            if choice in layouts:
                selected_layout = choice
                break
                
            # 如果用户输入编号
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(layouts):
                selected_layout = layouts[choice_idx]
                break
            else:
                print(f"请输入1到{len(layouts)}之间的编号")
        except ValueError:
            print("请输入有效的编号")
    
    # 如果用户取消选择
    if selected_layout is None:
        return None
    
    # 如果没有提供自定义名称，询问用户
    if custom_name is None:
        custom_name = input("请输入餐厅名称 (留空使用默认名称): ").strip()
        if not custom_name:
            custom_name = None
    
    print(f"\n正在加载 {selected_layout}...")
    try:
        return load_restaurant_layout(selected_layout, custom_name)
    except Exception as e:
        print(f"加载餐厅布局失败: {e}")
        return None

def load_restaurant_layout(name: str, custom_name: Optional[str] = None) -> Restaurant:
    """
    加载指定名称的餐厅布局
    
    布局可以是JSON格式或文本格式
    
    Args:
        name: 餐厅布局名称 (不含扩展名)
        custom_name: 自定义餐厅名称 (可选)
        
    Returns:
        Restaurant: 加载的餐厅对象
    """
    # 确保文件名不含扩展名
    if name.endswith('.json') or name.endswith('.txt'):
        name = os.path.splitext(name)[0]
    
    # 尝试以不同格式加载文件
    json_path = os.path.join(LAYOUTS_DIR, f"{name}.json")
    txt_path = os.path.join(LAYOUTS_DIR, f"{name}.txt")
    
    if os.path.exists(json_path):
        return load_restaurant_from_json(json_path, custom_name)
    elif os.path.exists(txt_path):
        return load_restaurant_from_txt(txt_path, custom_name)
    else:
        raise FileNotFoundError(f"找不到布局文件: {name} (尝试了 .json 和 .txt 格式)")

def load_restaurant_from_json(filepath: str, custom_name: Optional[str] = None) -> Restaurant:
    """
    从JSON文件加载餐厅布局
    
    Args:
        filepath: JSON文件路径
        custom_name: 自定义餐厅名称（可选）
        
    Returns:
        Restaurant: 加载的餐厅对象
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 获取餐厅名称，优先使用传入的custom_name
    if custom_name:
        name = custom_name
    else:
        # 其次尝试从JSON中读取name
        name = data.get('name')
        # 如果JSON中也没有name，则使用文件名作为餐厅名称
        if name is None:
            name = os.path.splitext(os.path.basename(filepath))[0]
    
    # 检查JSON格式
    if 'layout' in data:
        # 新的简化格式(仅包含layout字符串数组)
        layout_strings = data['layout']
        return create_restaurant_from_layout_string(name, '\n'.join(layout_strings))
    elif all(key in data for key in ['grid', 'table_positions', 'kitchen_positions']):
        # 旧格式(包含grid, table_positions, kitchen_positions)
        grid = data['grid']
        table_positions = {int(k): tuple(v) for k, v in data['table_positions'].items()}
        kitchen_positions = [tuple(pos) for pos in data['kitchen_positions']]
        
        return Restaurant(
            name=name,
            config={
                'grid': grid,
                'table_positions': table_positions,
                'kitchen_positions': kitchen_positions
            }
        )
    else:
        raise ValueError(f"无效的餐厅布局JSON格式: {filepath}")

def load_restaurant_from_txt(filepath: str, custom_name: Optional[str] = None) -> Restaurant:
    """
    从文本文件加载餐厅布局
    
    Args:
        filepath: 文本文件路径
        custom_name: 自定义餐厅名称 (可选)
        
    Returns:
        Restaurant: 加载的餐厅对象
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 获取餐厅名称
    name = os.path.splitext(os.path.basename(filepath))[0]
    
    return create_restaurant_from_layout_string(name, content, custom_name)

def create_restaurant_from_layout_string(name: str, layout_string: str, custom_name: Optional[str] = None) -> Restaurant:
    """
    从文本布局字符串创建餐厅对象
    
    Args:
        name: 餐厅名称
        layout_string: 包含餐厅布局的字符串，每行代表餐厅的一行
        custom_name: 自定义餐厅名称 (可选)
        
    Returns:
        Restaurant: 创建的餐厅对象
    """
    # 解析布局字符串
    layout_lines = layout_string.strip().split('\n')
    return parse_layout_from_raw_strings(name, layout_lines, custom_name)

def parse_layout_from_raw_strings(name: str, layout_lines: List[str], custom_name: Optional[str] = None) -> Restaurant:
    """
    从原始字符串数组解析餐厅布局
    
    支持以下字符：
    - S 或空格或. : 空地
    - W 或 # : 墙壁
    - K : 厨房
    - P : 机器人停靠点
    - 01-99 : 桌子编号
    
    Args:
        name: 餐厅名称
        layout_lines: 包含餐厅布局的字符串数组，每个元素代表餐厅的一行
        custom_name: 自定义餐厅名称 (可选)
        
    Returns:
        Restaurant: 创建的餐厅对象
    """
    # 计算最大宽度
    max_width = max(len(line) for line in layout_lines)
    height = len(layout_lines)
    
    # 创建网格, 1表示墙壁，0表示空地
    grid = [[0 for _ in range(max_width)] for _ in range(height)]
    
    # 记录桌子和厨房位置
    table_positions = {}
    kitchen_positions = []
    parking_position = None
    
    # 桌子编号正则表达式，匹配01到99的数字
    table_pattern = re.compile(r'([0-9]{2})')
    
    # 解析每一行
    for i, line in enumerate(layout_lines):
        j = 0
        while j < len(line):
            char = line[j].upper()
            
            # 检查是否为桌子编号(两位数字)
            match = None
            if j < len(line) - 1:
                match = table_pattern.match(line[j:j+2])
            
            if match:
                # 找到桌子编号
                table_id = int(match.group(1))
                grid[i][j] = 0  # 桌子下面是空地
                grid[i][j+1] = 0
                table_positions[table_id] = (i, j)
                j += 2  # 跳过两个字符
            else:
                # 处理单个字符
                if char == 'S' or char == ' ' or char == '.':
                    grid[i][j] = 0  # 空地
                elif char == 'W' or char == '#':
                    grid[i][j] = 1  # 墙壁
                elif char == 'K':
                    grid[i][j] = 0  # 厨房下面是空地
                    kitchen_positions.append((i, j))
                elif char == 'P':
                    grid[i][j] = 0  # 停靠点下面是空地
                    if parking_position is None:  # 只记录第一个P点
                        parking_position = (i, j)
                else:
                    # 默认为空地
                    grid[i][j] = 0
                j += 1
    
    # 创建并返回餐厅对象
    config = {
        'grid': grid,
        'table_positions': table_positions,
        'kitchen_positions': kitchen_positions
    }
    
    # 添加停靠点信息
    if parking_position:
        config['parking_position'] = parking_position
    
    # 使用自定义名称（如果有）
    final_name = custom_name if custom_name else name
    
    return Restaurant(final_name, config)

def save_restaurant_to_json(restaurant: Restaurant, filename: str) -> str:
    """
    将餐厅对象保存为JSON格式
    
    Args:
        restaurant: 要保存的餐厅对象
        filename: 保存的文件名 (不含扩展名)
        
    Returns:
        str: 保存的文件路径
    """
    # 生成字符串布局表示
    layout = create_restaurant_layout(restaurant)
    
    # 准备JSON数据
    data = {
        'name': restaurant.name,
        'layout': layout
    }
    
    # 确保文件扩展名正确
    if not filename.endswith('.json'):
        filename = f"{filename}.json"
    
    # 保存到文件
    filepath = os.path.join(LAYOUTS_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    return filepath

def save_restaurant_to_txt(restaurant: Restaurant, filename: str) -> str:
    """
    将餐厅对象保存为文本格式
    
    Args:
        restaurant: 要保存的餐厅对象
        filename: 保存的文件名 (不含扩展名)
        
    Returns:
        str: 保存的文件路径
    """
    # 生成字符串布局表示
    layout = create_restaurant_layout(restaurant)
    
    # 确保文件扩展名正确
    if not filename.endswith('.txt'):
        filename = f"{filename}.txt"
    
    # 保存到文件
    filepath = os.path.join(LAYOUTS_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(layout))
    
    return filepath

def create_restaurant_layout(restaurant: Restaurant) -> List[str]:
    """
    从餐厅对象创建字符串布局表示
    
    Args:
        restaurant: 餐厅对象
        
    Returns:
        List[str]: 字符串布局数组，每个元素代表一行
    """
    grid = restaurant.grid
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0
    
    # 创建一个与网格大小相同的字符数组，初始化为空地
    char_grid = [['S' for _ in range(width)] for _ in range(height)]
    
    # 填充墙壁
    for i in range(height):
        for j in range(width):
            if grid[i][j] == 1:
                char_grid[i][j] = 'W'
    
    # 填充厨房
    for pos in restaurant.kitchen:
        i, j = pos
        if 0 <= i < height and 0 <= j < width:
            char_grid[i][j] = 'K'
    
    # 填充停靠点
    if hasattr(restaurant.environment, 'parking') and restaurant.environment.parking:
        i, j = restaurant.environment.parking
        if 0 <= i < height and 0 <= j < width:
            char_grid[i][j] = 'P'
    
    # 填充桌子 (将桌号格式化为两位数)
    for table_id, pos in restaurant.tables.items():
        i, j = pos
        if 0 <= i < height and 0 <= j < width:
            table_str = f"{table_id:02d}"
            # 只设置第一个位置，保持两位数字
            if j + 1 < width:
                char_grid[i][j] = table_str[0]
                char_grid[i][j+1] = table_str[1]
            else:
                # 如果超出边界，只放第一位
                char_grid[i][j] = table_str[0]
    
    # 将每行字符转换为字符串
    return [''.join(row) for row in char_grid]

def create_custom_restaurant(name: str, grid: List[List[int]], 
                            table_positions: Dict[int, Tuple[int, int]], 
                            kitchen_positions: List[Tuple[int, int]],
                            parking_position: Optional[Tuple[int, int]] = None) -> Restaurant:
    """
    创建自定义餐厅
    
    Args:
        name: 餐厅名称
        grid: 餐厅网格 (0=空地, 1=墙壁)
        table_positions: 桌子位置映射 {桌号: (行,列)}
        kitchen_positions: 厨房位置列表 [(行,列), ...]
        parking_position: 机器人停靠点位置 (行,列) (可选)
        
    Returns:
        Restaurant: 创建的餐厅对象
    """
    config = {
        'grid': grid,
        'table_positions': table_positions,
        'kitchen_positions': kitchen_positions
    }
    
    if parking_position:
        config['parking_position'] = parking_position
        
    return Restaurant(name, config)

def print_restaurant_info(restaurant: Restaurant) -> None:
    """
    打印餐厅信息
    
    Args:
        restaurant: 餐厅对象
    """
    print(f"餐厅名称: {restaurant.name}")
    print(f"餐厅尺寸: {len(restaurant.grid[0])}x{len(restaurant.grid)} (宽x高)")
    print(f"桌子数量: {len(restaurant.tables)}")
    print(f"厨房数量: {len(restaurant.kitchen)}")
    
def display_full_restaurant(restaurant: Restaurant) -> None:
    """
    显示完整的餐厅布局信息
    
    打印餐厅基本信息，显示布局，并列出所有桌子和厨房的位置
    
    Args:
        restaurant: 餐厅对象
    """
    print_restaurant_info(restaurant)
    print("\n餐厅布局:")
    restaurant.display()
    
    print("\n桌子位置:")
    for table_id, pos in sorted(restaurant.tables.items()):
        print(f"  桌号 {table_id}: 位置 {pos}")
    
    print("\n厨房位置:")
    for i, pos in enumerate(restaurant.kitchen):
        print(f"  厨房 {i+1}: 位置 {pos}")

def create_environment(restaurant: Restaurant, seed: Optional[int] = None) -> RestaurantEnvironment:
    """
    为指定餐厅创建环境
    
    Args:
        restaurant: 餐厅对象
        seed: 随机种子 (可选)
        
    Returns:
        RestaurantEnvironment: 创建的环境对象
    """
    return RestaurantEnvironment(restaurant, seed=seed) 