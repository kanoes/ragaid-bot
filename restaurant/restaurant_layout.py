"""
RestaurantLayout – レストラン平面図データ構造。

数値表現方式
-----------
0     空地
1     壁/障害物
2-99   テーブル番号（例えば21は21番テーブル）
100    キッチン
200    駐車ポイント

レイアウトファイルは直接数値マトリックスで定義され、文字マーカーを使用する必要はありません。
"""

from __future__ import annotations

from typing import List, Tuple, Dict, Optional


class RestaurantLayout:
    """
    二次元グリッドのレストランレイアウト
    """

    # ----- 構築 -------------------------------------------------------------- #
    def __init__(
        self,
        grid: Optional[List[List[int]]] = None,
        table_positions: Optional[Dict[str, Tuple[int, int]]] = None,
        kitchen_positions: Optional[List[Tuple[int, int]]] = None,
        parking_position: Optional[Tuple[int, int]] = None,
        delivery_points: Optional[Dict[str, Tuple[int, int]]] = None,
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
        
        # 各テーブルの配膳ポイント、フォーマット: {テーブルID: (行, 列)}
        self.delivery_points: Dict[str, Tuple[int, int]] = delivery_points or {}
        
        # 配膳ポイントが事前設定されていない場合、自動的に各テーブルに生成
        if not self.delivery_points:
            self._generate_delivery_points()

    def _generate_delivery_points(self) -> None:
        """
        各テーブルの配膳ポイントを自動生成
        北、東、南、西の四方向で最も近い空きポイントを優先
        """
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]  # 上、右、下、左
        
        for table_id, table_pos in self.tables.items():
            row, col = table_pos
            
            # 四方向を試す
            for dr, dc in directions:
                delivery_pos = (row + dr, col + dc)
                if self.is_free(delivery_pos):
                    self.delivery_points[table_id] = delivery_pos
                    break
            
            # 四つの隣接ポイントが使用できない場合、より遠いポイントを試す
            if table_id not in self.delivery_points:
                for distance in range(2, 4):
                    for dr, dc in directions:
                        delivery_pos = (row + dr * distance, col + dc * distance)
                        if self.is_free(delivery_pos):
                            self.delivery_points[table_id] = delivery_pos
                            break
                    if table_id in self.delivery_points:
                        break

    def is_free(self, pos: Tuple[int, int]) -> bool:
        """
        位置が通行可能かどうか（空地 / キッチン / 駐車ポイント）
        """
        x, y = pos
        return (
            0 <= x < self.height and 0 <= y < self.width and self.grid[x][y] in (0, 4, 100, 200)
        )

    def neighbors(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        上下左右の通行可能な隣接位置を返す
        """
        x, y = pos
        cand = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
        return [p for p in cand if self.is_free(p)]
        
    def get_delivery_point(self, table_id: str) -> Optional[Tuple[int, int]]:
        """
        特定テーブルの配膳ポイントを取得
        
        Args:
            table_id: テーブルID
            
        Returns:
            Tuple[int, int]: 配膳ポイントの座標
            テーブルが存在しないか配膳ポイントがない場合はNoneを返す
        """
        return self.delivery_points.get(table_id)
    
    @staticmethod
    def parse_layout_from_array(layout_name: str, grid_array: List[List[int]]):
        """
        数値配列からレストランレイアウトを解析（新フォーマット）
        
        数値コード:
        0: 空地
        1: 壁/障害物
        2-99: テーブル番号（例えば21は21番テーブル）
        100: キッチン
        200: 駐車ポイント
        
        Args:
            layout_name: レイアウト名
            grid_array: レイアウトマトリックス配列

        Returns:
            dict: 解析後のレイアウト設定を含む
        """
        height = len(grid_array)
        width = len(grid_array[0]) if height > 0 else 0
        grid = [row[:] for row in grid_array]  # ディープコピー
        
        table_positions = {}
        kitchen_positions = []
        parking_position = None
        
        # 特殊位置を抽出
        for row in range(height):
            for col in range(width):
                value = grid[row][col]
                if value == 101:  # 壁/障害物
                    grid[row][col] = 1
                elif 1 <= value <= 99:  # テーブル
                    table_positions[str(value)] = (row, col)
                    grid[row][col] = 2
                elif value == 100:  # キッチン
                    kitchen_positions.append((row, col))
                    grid[row][col] = 3
                elif value == 200:  # 駐車ポイント
                    parking_position = (row, col)
                    grid[row][col] = 4
        
        return {
            "grid": grid,
            "table_positions": table_positions,
            "kitchen_positions": kitchen_positions,
            "parking_position": parking_position,
        }
