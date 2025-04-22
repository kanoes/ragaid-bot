"""
RestaurantLayout – 餐厅平面图数据结构。

标记约定
--------
符号  值  含义
"#"   1   障碍物 / 墙
"."   0   空地
"*"   0   空地（与 "." 等价，兼容旧示例）
"台"  3   厨房
"停"  4   机器人停靠点
字母  2   桌子（A、B、C …）
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

    def is_free(self, pos: Tuple[int, int]) -> bool:
        """
        位置是否可通行（空地 / 厨房 / 停靠点）
        """
        x, y = pos
        return (
            0 <= x < self.height and 0 <= y < self.width and self.grid[x][y] in (0, 4)
        )

    def neighbors(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        返回上下左右可通行的相邻位置
        """
        x, y = pos
        cand = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
        return [p for p in cand if self.is_free(p)]

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
            "台": 3,  # 厨房
            "停": 4,
            "P": 4,  # 停靠点
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
            "parking_position": parking_position,
        }
