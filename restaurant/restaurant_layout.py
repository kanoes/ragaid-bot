"""RestaurantLayout – 餐厅平面图数据结构。

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


# ---------------------------------------------------------------------------- #
# 核心类
# ---------------------------------------------------------------------------- #
class RestaurantLayout:
    """二维网格的餐厅布局。"""

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

    # ----- 基础查询 ---------------------------------------------------------- #
    def is_free(self, pos: Tuple[int, int]) -> bool:
        """位置是否可通行（空地 / 厨房 / 停靠点）。"""
        x, y = pos
        return (
            0 <= x < self.height
            and 0 <= y < self.width
            and self.grid[x][y] in (0, 4)
        )

    def neighbors(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """返回上下左右可通行的相邻位置。"""
        x, y = pos
        cand = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
        return [p for p in cand if self.is_free(p)]

    # ----- 信息接口 ---------------------------------------------------------- #
    def print_info(self) -> None:
        """打印尺寸、桌子/厨房/停靠点统计。"""
        print("===== 布局信息 =====")
        print(f"尺寸: {self.width} × {self.height}")
        print(f"桌子数量: {len(self.tables)}")
        print(f"厨房数量: {len(self.kitchen)}")
        if self.parking:
            print(f"停靠点: {self.parking}")

    # ----- 显示 -------------------------------------------------------------- #
    def display(
        self,
        restaurant_name: str = "餐厅",
        path: Optional[List[Tuple[int, int]]] = None,
        robot_position: Optional[Tuple[int, int]] = None,
    ) -> None:
        """打印 ASCII 网格，可选路径与机器人位置。"""
        print(f"\n===== {restaurant_name} =====")
        vis = [["." for _ in range(self.width)] for _ in range(self.height)]

        # 基础填充
        for i in range(self.height):
            for j in range(self.width):
                cell = self.grid[i][j]
                if cell == 1:
                    vis[i][j] = "#"
                elif cell == 3:
                    vis[i][j] = "K"
                elif cell == 4:
                    vis[i][j] = "P"

        # 桌子
        for tid, (r, c) in self.tables.items():
            vis[r][c] = tid

        # 路径
        if path:
            for r, c in path:
                if vis[r][c] == ".":
                    vis[r][c] = "*"

        # 机器人
        if robot_position:
            r, c = robot_position
            vis[r][c] = "R"

        # 输出
        print("+" + "-" * (self.width * 2 + 1) + "+")
        for row in vis:
            print("| " + " ".join(row) + " |")
        print("+" + "-" * (self.width * 2 + 1) + "+")

    def display_full(self, highlight: Optional[Tuple[int, int]] = None) -> None:
        """
        带坐标的详细输出，用于调试
        """
        header = "    " + " ".join(f"{j:2d}" for j in range(self.width))
        print(header)
        print("   " + "-" * (self.width * 3))
        for i in range(self.height):
            line = f"{i:2d}|"
            for j in range(self.width):
                char = "."
                if self.grid[i][j] == 1:
                    char = "#"
                elif self.grid[i][j] == 3:
                    char = "K"
                elif self.grid[i][j] == 4:
                    char = "P"
                for tid, pos in self.tables.items():
                    if pos == (i, j):
                        char = tid
                        break
                if highlight and (i, j) == highlight:
                    char = "*"
                line += f" {char} "
            print(line)

    # --------------------------------------------------------------------- #
    # 静态方法：解析 / 导出
    # --------------------------------------------------------------------- #
    @staticmethod
    def parse_layout_from_strings(
        name: str, lines: List[str]
    ) -> Dict[str, object]:
        """
        将字符串列表解析成布局配置字典
        每行需用空格分隔 token，支持符号见模块说明
        """
        tokens = [ln.split() for ln in lines]
        height = len(tokens)
        width = max(len(row) for row in tokens) if height else 0

        grid = [[0] * width for _ in range(height)]
        table_pos: Dict[str, Tuple[int, int]] = {}
        kitchen_pos: List[Tuple[int, int]] = []
        parking_pos: Optional[Tuple[int, int]] = None

        for i, row in enumerate(tokens):
            for j, tk in enumerate(row):
                if tk == "#":
                    grid[i][j] = 1
                elif tk in {".", "*"}:
                    grid[i][j] = 0
                elif tk == "台":
                    grid[i][j] = 3
                    kitchen_pos.append((i, j))
                elif tk == "停":
                    grid[i][j] = 4
                    if parking_pos is None:
                        parking_pos = (i, j)
                elif tk.isalpha():  # 桌子
                    grid[i][j] = 2
                    table_pos[tk] = (i, j)

        return {
            "grid": grid,
            "table_positions": table_pos,
            "kitchen_positions": kitchen_pos,
            "parking_position": parking_pos,
        }
