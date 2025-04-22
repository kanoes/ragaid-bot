"""
RestaurantLayout – 餐厅平面图数据结构。

数字表示方式
-----------
0     空地
1     墙壁/障碍物
2-99   桌子编号(例如21表示21号桌)
100    厨房
200    停靠点

布局文件直接使用数字矩阵定义，不再需要使用字符标记。
"""

from __future__ import annotations

from typing import List, Tuple, Dict, Optional


class RestaurantLayout:
    """
    二维网格的餐厅布局
    """

    # ----- 构造 -------------------------------------------------------------- #
    def __init__(
        self,
        grid: Optional[List[List[int]]] = None,
        table_positions: Optional[Dict[str, Tuple[int, int]]] = None,
        kitchen_positions: Optional[List[Tuple[int, int]]] = None,
        parking_position: Optional[Tuple[int, int]] = None,
        delivery_points: Optional[Dict[str, Tuple[Tuple[int, int], int]]] = None,
    ) -> None:
        if grid is None:
            self.height: int = 10
            self.width: int = 10
            self.grid: List[List[int]] = [[0] * self.width for _ in range(self.height)]
        else:
            self.grid = grid
            self.height = len(grid)
            self.width = len(grid[0]) if self.height else 0

        self.tables: Dict[str, Tuple[int, int]] = table_positions or {}
        self.kitchen: List[Tuple[int, int]] = kitchen_positions or []
        self.parking: Optional[Tuple[int, int]] = parking_position
        
        # 每个桌子的送餐点和朝向，格式: {桌子ID: ((行, 列), 朝向角度)}
        # 朝向角度: 0-上, 90-右, 180-下, 270-左
        self.delivery_points: Dict[str, Tuple[Tuple[int, int], int]] = delivery_points or {}
        
        # 如果没有预设送餐点，自动为每个桌子生成
        if not self.delivery_points:
            self._generate_delivery_points()

    def _generate_delivery_points(self) -> None:
        """
        为每个桌子自动生成送餐点和朝向
        优先选择北、东、南、西四个方向上最近的空闲点
        """
        directions = [((-1, 0), 0), ((0, 1), 90), ((1, 0), 180), ((0, -1), 270)]  # (偏移量, 角度)
        
        for table_id, table_pos in self.tables.items():
            row, col = table_pos
            
            # 尝试四个方向
            for (dr, dc), angle in directions:
                delivery_pos = (row + dr, col + dc)
                if self.is_free(delivery_pos):
                    self.delivery_points[table_id] = (delivery_pos, angle)
                    break
            
            # 如果四个直接相邻的点都不可用，尝试更远的点
            if table_id not in self.delivery_points:
                for distance in range(2, 4):
                    for (dr, dc), angle in directions:
                        delivery_pos = (row + dr * distance, col + dc * distance)
                        if self.is_free(delivery_pos):
                            self.delivery_points[table_id] = (delivery_pos, angle)
                            break
                    if table_id in self.delivery_points:
                        break

    def is_free(self, pos: Tuple[int, int]) -> bool:
        """
        位置是否可通行（空地 / 厨房 / 停靠点）
        """
        x, y = pos
        return (
            0 <= x < self.height and 0 <= y < self.width and self.grid[x][y] in (0, 4, 100, 200)
        )

    def neighbors(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        返回上下左右可通行的相邻位置
        """
        x, y = pos
        cand = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
        return [p for p in cand if self.is_free(p)]
        
    def get_delivery_point(self, table_id: str) -> Optional[Tuple[Tuple[int, int], int]]:
        """
        获取特定桌子的送餐点和朝向
        
        Args:
            table_id: 桌子ID
            
        Returns:
            Tuple[Tuple[int, int], int]: (送餐点坐标, 朝向角度)
            如果桌子不存在或没有送餐点，返回None
        """
        return self.delivery_points.get(table_id)

    @staticmethod
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
            "#": 1,
            "＃": 1,
            "W": 1,  # 墙壁/障碍
            "*": 0,
            ".": 0,  # 空地
            "台": 100,  # 厨房 (新格式)
            "厨": 100,  # 厨房 (新格式)
            "停": 200,  # 停靠点 (新格式)
            "P": 200,  # 停靠点 (新格式)
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
                    if value == 100:  # 厨房
                        kitchen_positions.append((row, col))
                    elif value == 200:  # 停靠点
                        parking_position = (row, col)
                elif token.isalpha() and len(token) == 1:
                    # 桌子
                    grid[row][col] = 2
                    table_positions[token] = (row, col)
                elif token.isdigit() and 2 <= int(token) <= 99:
                    # 桌子编号 (新格式)
                    table_num = int(token)
                    grid[row][col] = table_num
                    table_positions[str(table_num)] = (row, col)
                else:
                    # 未知符号，当作空地处理
                    grid[row][col] = 0

        return {
            "grid": grid,
            "table_positions": table_positions,
            "kitchen_positions": kitchen_positions,
            "parking_position": parking_position,
        }
    
    @staticmethod
    def parse_layout_from_array(layout_name: str, grid_array: List[List[int]]):
        """
        从数字数组解析餐厅布局（新格式）
        
        数字编码:
        0: 空地
        1: 墙壁/障碍物
        2-99: 桌子编号(例如21表示21号桌)
        100: 厨房
        200: 停靠点
        
        Args:
            layout_name: 布局名称
            grid_array: 布局矩阵数组

        Returns:
            dict: 包含解析后的布局配置
        """
        height = len(grid_array)
        width = len(grid_array[0]) if height > 0 else 0
        grid = [row[:] for row in grid_array]  # 深拷贝网格
        
        table_positions = {}
        kitchen_positions = []
        parking_position = None
        
        # 提取特殊位置
        for row in range(height):
            for col in range(width):
                value = grid[row][col]
                if 2 <= value <= 99:  # 桌子
                    table_positions[str(value)] = (row, col)
                    # 保持值为2以兼容原有逻辑
                    grid[row][col] = 2
                elif value == 100:  # 厨房
                    kitchen_positions.append((row, col))
                    grid[row][col] = 3  # 兼容原有代码
                elif value == 200:  # 停靠点
                    parking_position = (row, col)
                    grid[row][col] = 4  # 兼容原有代码
        
        return {
            "grid": grid,
            "table_positions": table_positions,
            "kitchen_positions": kitchen_positions,
            "parking_position": parking_position,
        }
