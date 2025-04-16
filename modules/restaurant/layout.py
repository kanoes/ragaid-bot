from typing import List, Tuple, Dict, Optional

class RestaurantLayout:
    """
    基于 2D 网格描述餐厅平面图，支持如下标记（区分各功能区域）：
      - 障碍物: "#"，对应格子值为 1
      - 空地: "*"，对应格子值为 0
      - 桌子: 字母（如 "A", "B"），对应格子值为 2
      - 厨房: "台"，对应格子值为 3
      - 停留点: "停"，对应格子值为 4
    """

    def __init__(self,
                 grid: Optional[List[List[int]]] = None,
                 table_positions: Optional[Dict[str, Tuple[int, int]]] = None,
                 kitchen_positions: Optional[List[Tuple[int, int]]] = None,
                 parking_position: Optional[Tuple[int, int]] = None) -> None:
        if grid is None:
            # 默认创建 10x10 空网格（全部空地）
            self.height = 10
            self.width = 10
            self.grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
        else:
            self.grid = grid
            self.height = len(grid)
            self.width = len(grid[0]) if self.height > 0 else 0

        self.tables: Dict[str, Tuple[int, int]] = table_positions or {}
        self.kitchen: List[Tuple[int, int]] = kitchen_positions or []
        self.parking: Optional[Tuple[int, int]] = parking_position

    def get_kitchen_positions(self) -> List[Tuple[int, int]]:
        """
        获取餐厅中所有厨房的位置
        
        返回:
            List[Tuple[int, int]]: 厨房位置列表，每个位置为(行,列)坐标
        """
        return self.kitchen
        
    def get_table_position(self, table_id: str) -> Optional[Tuple[int, int]]:
        """
        获取指定桌号的位置
        
        参数:
            table_id: 桌子标识符
            
        返回:
            Optional[Tuple[int, int]]: 桌子位置，如果不存在则返回None
        """
        return self.tables.get(table_id)
        
    def is_free(self, position: Tuple[int, int]) -> bool:
        """
        检查指定位置是否为空闲区域（可通行）
        
        参数:
            position: 要检查的位置坐标(行,列)
            
        返回:
            bool: 如果位置是空闲的返回True，否则返回False
        """
        x, y = position
        if 0 <= x < self.height and 0 <= y < self.width:
            # 值为0表示空地，值为3表示厨房，值为4表示停留点，这些都是可通行区域
            return self.grid[x][y] in [0, 3, 4]
        return False
        
    def neighbors(self, position: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        获取指定位置的邻居节点（上下左右四个方向）
        
        参数:
            position: 当前位置坐标(行,列)
            
        返回:
            List[Tuple[int, int]]: 可通行的邻居位置列表
        """
        x, y = position
        neighbors = []
        
        # 上下左右四个方向
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.height and 0 <= ny < self.width and self.is_free((nx, ny)):
                neighbors.append((nx, ny))
                
        return neighbors

    @staticmethod
    def parse_layout(layout_lines: List[str]) -> Dict:
        """
        解析布局字符串列表。要求每行是以空格分隔的标记。

        返回的配置字典格式：
            {
              "grid": List[List[int]],
              "table_positions": Dict[str, Tuple[int, int]],
              "kitchen_positions": List[Tuple[int, int]],
              "parking_position": Optional[Tuple[int, int]]
            }
        """
        height = len(layout_lines)
        # 将每行按空格分隔为 tokens，每个 token 为一个单元格的标记
        token_rows = [line.split() for line in layout_lines]
        width = max(len(row) for row in token_rows) if height > 0 else 0

        # 初始化整个网格为全空地（值为 0）
        grid = [[0 for _ in range(width)] for _ in range(height)]
        table_positions: Dict[str, Tuple[int, int]] = {}
        kitchen_positions: List[Tuple[int, int]] = []
        parking_position: Optional[Tuple[int, int]] = None

        for i, row in enumerate(token_rows):
            for j, token in enumerate(row):
                token = token.strip()  # 去除多余空白
                # 障碍物： "#"
                if token == "#":
                    grid[i][j] = 1
                # 空地： "*"
                elif token == "*":
                    grid[i][j] = 0
                # 停留点： "停"
                elif token == "停":
                    if parking_position is None:
                        parking_position = (i, j)
                    grid[i][j] = 4
                # 厨房： "台"
                elif token == "台":
                    kitchen_positions.append((i, j))
                    grid[i][j] = 3
                # 桌子：单个英文字母（假定为 A-Z 或 a-z）
                elif token.isalpha():
                    table_positions[token] = (i, j)
                    grid[i][j] = 2
                else:
                    # 遇到未知标记，默认视为空地
                    grid[i][j] = 0

        return {
            "grid": grid,
            "table_positions": table_positions,
            "kitchen_positions": kitchen_positions,
            "parking_position": parking_position
        }

    def display(self, restaurant_name: str = "餐厅", path: List[Tuple[int, int]] = None, robot_position: Tuple[int, int] = None) -> None:
        """
        打印餐厅平面图
        
        参数:
            restaurant_name: 餐厅名称，用于显示
            path: 可选，机器人路径点列表
            robot_position: 可选，机器人当前位置
        """
        print(f"\n===== 餐厅: {restaurant_name} =====")
        
        # 获取布局网格
        grid = self.grid
        height = self.height
        width = self.width
        
        # 创建可视化用的字符网格
        visual_grid = [[' ' for _ in range(width)] for _ in range(height)]
        
        # 填充基础元素
        for i in range(height):
            for j in range(width):
                cell_type = grid[i][j]
                if cell_type == 0:  # 空地
                    visual_grid[i][j] = '.'
                elif cell_type == 1:  # 障碍物
                    visual_grid[i][j] = '#'
                elif cell_type == 3:  # 厨房
                    visual_grid[i][j] = 'K'
                elif cell_type == 4:  # 停留点
                    visual_grid[i][j] = 'P'
        
        # 填充桌子
        for table_id, pos in self.tables.items():
            row, col = pos
            if 0 <= row < height and 0 <= col < width:
                visual_grid[row][col] = table_id
        
        # 添加路径（如果有）
        if path:
            for pos in path:
                row, col = pos
                if 0 <= row < height and 0 <= col < width and visual_grid[row][col] == '.':
                    visual_grid[row][col] = '*'
        
        # 添加机器人位置（如果有）
        if robot_position:
            row, col = robot_position
            if 0 <= row < height and 0 <= col < width:
                visual_grid[row][col] = 'R'
        
        # 打印网格
        print("+" + "-" * (width * 2 + 1) + "+")
        for row in visual_grid:
            print("| " + " ".join(row) + " |")
        print("+" + "-" * (width * 2 + 1) + "+")
        
        # 打印图例
        print("\n图例: ")
        print("  . - 空地")
        print("  # - 障碍物/墙壁")
        print("  K - 厨房")
        print("  字母/数字 - 桌子")
        if path:
            print("  * - 机器人路径")
        if robot_position:
            print("  R - 机器人当前位置")