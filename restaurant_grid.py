# restaurant_grid.py

class RestaurantEnvironment:
    """
    模拟餐厅环境，使用2D网格表示，0表示可通行区域，1表示障碍物。
    """
    def __init__(self, grid):
        self.grid = grid
        self.height = len(grid)
        self.width = len(grid[0]) if self.height > 0 else 0

    def is_free(self, position):
        x, y = position
        if 0 <= x < self.height and 0 <= y < self.width:
            return self.grid[x][y] == 0
        return False

    def neighbors(self, position):
        """
        返回当前位置的有效邻居（上下左右）
        """
        x, y = position
        potential_moves = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
        return [move for move in potential_moves if self.is_free(move)]
    
    def display(self, path=None):
        """
        打印环境网格，如果提供了路径，则用'*'标记路径点。
        """
        display_grid = [row.copy() for row in self.grid]
        if path:
            for x, y in path:
                display_grid[x][y] = '*'
        for row in display_grid:
            print(' '.join(str(cell) for cell in row))
        print() 