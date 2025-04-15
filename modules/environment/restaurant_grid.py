class RestaurantEnvironment:
    """
    レストラン環境をシミュレーション、2Dグリッドで表現：
    0は通行可能エリア、1は障害物、2はテーブル、3はキッチンエリア
    """
    def __init__(self, grid=None, table_positions=None, kitchen_positions=None):
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
    
    def get_table_position(self, table_id):
        """指定されたテーブル番号の位置を取得"""
        return self.tables.get(table_id)
    
    def get_kitchen_positions(self):
        """すべてのキッチン位置を取得"""
        return list(self.kitchen)

    def neighbors(self, position):
        """
        現在位置の有効な隣接マス（上下左右）を返す
        """
        x, y = position
        potential_moves = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
        return [move for move in potential_moves if self.is_free(move)]
    
    def display(self, path=None, robot_position=None):
        """
        環境グリッドを表示、異なるタイプのマスを異なる記号で表現：
        - '·' は空きスペース
        - '█' は障害物
        - '◇' はテーブル
        - '▣' はキッチン
        - '*' は経路
        - 'R' はロボットの現在位置
        """
        display_grid = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                if self.grid[i][j] == 0:
                    row.append('·')  # 空きスペース
                elif self.grid[i][j] == 1:
                    row.append('█')  # 障害物
                elif self.grid[i][j] == 2:
                    row.append('◇')  # テーブル
                elif self.grid[i][j] == 3:
                    row.append('▣')  # キッチン
                else:
                    row.append(str(self.grid[i][j]))
            display_grid.append(row)
            
        # 経路をマーク
        if path:
            for x, y in path:
                if display_grid[x][y] in ['·']:  # 空きスペースにのみ経路をマーク
                    display_grid[x][y] = '*'
        
        # ロボット位置をマーク
        if robot_position:
            x, y = robot_position
            display_grid[x][y] = 'R'
            
        # グリッドを表示
        for row in display_grid:
            print(' '.join(row))
        print() 