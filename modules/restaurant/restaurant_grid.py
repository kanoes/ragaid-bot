class RestaurantEnvironment:
    """
    レストラン環境をシミュレーション、2Dグリッドで表現：
    0は通行可能エリア、1は障害物、2はテーブル、3はキッチンエリア、4は機器人の停靠点
    """
    def __init__(self, grid=None, table_positions=None, kitchen_positions=None, parking_position=None):
        # グリッドが提供されていない場合、デフォルトの空グリッドを作成
        if grid is None:
            self.height = 10
            self.width = 10
            self.grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
        else:
            self.grid = grid
            self.height = len(grid)
            self.width = len(grid[0]) if self.height > 0 else 0
        
        # テーブル辞書、キーはテーブル番号、値は位置座標
        self.tables = {}
        if table_positions:
            for table_id, position in table_positions.items():
                self.add_table(table_id, position)
        
        # キッチンエリア
        self.kitchen = set()
        if kitchen_positions:
            for position in kitchen_positions:
                self.add_kitchen(position)
                
        # 機器人の停靠点
        self.parking = None
        if parking_position:
            self.add_parking(parking_position)
        else:
            # グリッドから停靠点を探す
            for i in range(self.height):
                for j in range(self.width):
                    if self.grid[i][j] == 4:
                        self.parking = (i, j)
                        break

    def is_free(self, position):
        x, y = position
        if 0 <= x < self.height and 0 <= y < self.width:
            # 値が0のエリアのみ通行可能
            return self.grid[x][y] == 0
        return False
    
    def is_table(self, position):
        x, y = position
        if 0 <= x < self.height and 0 <= y < self.width:
            return self.grid[x][y] == 2
        return False
    
    def is_kitchen(self, position):
        x, y = position
        if 0 <= x < self.height and 0 <= y < self.width:
            return self.grid[x][y] == 3
        return False
        
    def is_parking(self, position):
        x, y = position
        if 0 <= x < self.height and 0 <= y < self.width:
            return self.grid[x][y] == 4
        return False

    def add_table(self, table_id, position):
        x, y = position
        if 0 <= x < self.height and 0 <= y < self.width:
            self.grid[x][y] = 2  # テーブルとしてマーク
            self.tables[table_id] = position
            return True
        return False
    
    def add_kitchen(self, position):
        x, y = position
        if 0 <= x < self.height and 0 <= y < self.width:
            self.grid[x][y] = 3  # キッチンとしてマーク
            self.kitchen.add(position)
            return True
        return False
        
    def add_parking(self, position):
        x, y = position
        if 0 <= x < self.height and 0 <= y < self.width:
            self.grid[x][y] = 4  # 停靠点としてマーク
            self.parking = position
            return True
        return False
    
    def get_table_position(self, table_id):
        """指定されたテーブル番号の位置を取得"""
        return self.tables.get(table_id)
    
    def get_kitchen_positions(self):
        """すべてのキッチン位置を取得"""
        return list(self.kitchen)
        
    def get_parking_position(self):
        """機器人の停靠点を取得"""
        return self.parking

    def neighbors(self, position):
        """
        現在位置の有効な隣接マス（上下左右）を返す
        """
        x, y = position
        potential_moves = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
        return [move for move in potential_moves if self.is_free(move) or self.is_kitchen(move) or self.is_parking(move)]
    
    def display(self, path=None, robot_position=None):
        """
        環境グリッドを表示、異なるタイプのマスを異なる記号で表現：
        - 'S' は空きスペース (Space)
        - 'W' は障害物 (Wall)
        - '01'-'99' はテーブル番号
        - 'K' はキッチン (Kitchen)
        - 'P' は機器人の停靠点 (Parking)
        - '*' は経路
        - 'R' はロボットの現在位置
        """
        display_grid = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                if self.grid[i][j] == 0:
                    row.append('S')  # 空きスペース (Space)
                elif self.grid[i][j] == 1:
                    row.append('W')  # 障害物 (Wall)
                elif self.grid[i][j] == 2:
                    # 寻找该位置对应的桌号
                    table_id = None
                    for tid, pos in self.tables.items():
                        if pos == (i, j):
                            table_id = tid
                            break
                    
                    if table_id is not None:
                        # 确保桌号为两位数的字符串格式
                        table_id_str = str(table_id).zfill(2)
                        row.append(table_id_str)  # 桌号
                    else:
                        row.append('??')  # 未知桌号
                elif self.grid[i][j] == 3:
                    row.append('K')  # キッチン (Kitchen)
                elif self.grid[i][j] == 4:
                    row.append('P')  # 機器人の停靠点 (Parking)
                else:
                    row.append(str(self.grid[i][j]))
            display_grid.append(row)
            
        # 経路をマーク
        if path:
            for x, y in path:
                if display_grid[x][y] in ['S', 'K', 'P']:  # 空地、厨房、停靠点にのみ経路をマーク
                    display_grid[x][y] = '*'
        
        # ロボット位置をマーク
        if robot_position:
            x, y = robot_position
            display_grid[x][y] = 'R'
            
        # グリッドを表示
        for row in display_grid:
            print(' '.join(row))
        print() 