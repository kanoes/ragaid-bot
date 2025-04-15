# restaurant_grid.py

class RestaurantEnvironment:
    """
    模拟餐厅环境，使用2D网格表示：
    0表示可通行区域，1表示障碍物，2表示桌子，3表示后厨区域
    """
    def __init__(self, grid=None, table_positions=None, kitchen_positions=None):
        # 如果没有提供网格，创建一个默认空网格
        if grid is None:
            self.height = 10
            self.width = 10
            self.grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
        else:
            self.grid = grid
            self.height = len(grid)
            self.width = len(grid[0]) if self.height > 0 else 0
        
        # 桌子字典，键为桌号，值为位置坐标
        self.tables = {}
        if table_positions:
            for table_id, position in table_positions.items():
                self.add_table(table_id, position)
        
        # 后厨区域
        self.kitchen = set()
        if kitchen_positions:
            for position in kitchen_positions:
                self.add_kitchen(position)

    def is_free(self, position):
        x, y = position
        if 0 <= x < self.height and 0 <= y < self.width:
            # 只有值为0的区域可以通行
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
            self.grid[x][y] = 2  # 标记为桌子
            self.tables[table_id] = position
            return True
        return False
    
    def add_kitchen(self, position):
        x, y = position
        if 0 <= x < self.height and 0 <= y < self.width:
            self.grid[x][y] = 3  # 标记为后厨
            self.kitchen.add(position)
            return True
        return False
    
    def get_table_position(self, table_id):
        """获取指定桌号的位置"""
        return self.tables.get(table_id)
    
    def get_kitchen_positions(self):
        """获取所有后厨位置"""
        return list(self.kitchen)

    def neighbors(self, position):
        """
        返回当前位置的有效邻居（上下左右）
        """
        x, y = position
        potential_moves = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
        return [move for move in potential_moves if self.is_free(move)]
    
    def display(self, path=None, robot_position=None):
        """
        打印环境网格，使用不同的符号表示不同类型的格子：
        - '·' 表示空地
        - '█' 表示障碍物
        - '◇' 表示桌子
        - '▣' 表示后厨
        - '*' 表示路径
        - 'R' 表示机器人当前位置
        """
        display_grid = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                if self.grid[i][j] == 0:
                    row.append('·')  # 空地
                elif self.grid[i][j] == 1:
                    row.append('█')  # 障碍物
                elif self.grid[i][j] == 2:
                    row.append('◇')  # 桌子
                elif self.grid[i][j] == 3:
                    row.append('▣')  # 后厨
                else:
                    row.append(str(self.grid[i][j]))
            display_grid.append(row)
            
        # 标记路径
        if path:
            for x, y in path:
                if display_grid[x][y] in ['·']:  # 只在空地上标记路径
                    display_grid[x][y] = '*'
        
        # 标记机器人位置
        if robot_position:
            x, y = robot_position
            display_grid[x][y] = 'R'
            
        # 打印网格
        for row in display_grid:
            print(' '.join(row))
        print() 