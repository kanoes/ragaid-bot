# restaurant_layout.py

from restaurant_grid import RestaurantEnvironment

def create_restaurant_layout():
    """
    创建一个带有20张桌子和后厨区域的餐厅布局
    
    餐厅布局为20x20的网格:
    - 0表示可通行区域
    - 1表示障碍物（墙壁、装饰等）
    - 2表示桌子位置
    - 3表示后厨区域
    
    返回：配置好的RestaurantEnvironment对象
    """
    # 创建一个20x20的空网格
    height = 20
    width = 20
    grid = [[0 for _ in range(width)] for _ in range(height)]
    
    # 添加外墙
    for i in range(height):
        grid[i][0] = 1  # 左墙
        grid[i][width-1] = 1  # 右墙
    
    for j in range(width):
        grid[0][j] = 1  # 上墙
        grid[height-1][j] = 1  # 下墙
    
    # 添加后厨区域（左上角）
    kitchen_positions = []
    for i in range(2, 5):
        for j in range(2, 7):
            grid[i][j] = 3
            kitchen_positions.append((i, j))
    
    # 在后厨区域添加一个出口
    grid[5][4] = 0  # 后厨出口
    
    # 添加中央装饰/障碍物
    for i in range(8, 12):
        for j in range(8, 12):
            grid[i][j] = 1
    
    # 添加部分内部墙壁/隔断
    for i in range(5, 15):
        grid[i][15] = 1
    
    for j in range(5, 15):
        grid[5][j] = 1
    
    # 在隔断上添加通道
    grid[5][10] = 0
    grid[10][15] = 0
    
    # 定义桌子位置
    table_positions = {
        1: (3, 10),
        2: (3, 12),
        3: (3, 14),
        4: (7, 3),
        5: (7, 6),
        6: (7, 9),
        7: (7, 12),
        8: (10, 3),
        9: (10, 6),
        10: (12, 9),
        11: (12, 12),
        12: (14, 3),
        13: (14, 6),
        14: (14, 9),
        15: (14, 12),
        16: (16, 10),
        17: (16, 12),
        18: (16, 14),
        19: (16, 17),
        20: (12, 17)
    }
    
    # 创建餐厅环境
    restaurant = RestaurantEnvironment(grid)
    
    # 添加桌子
    for table_id, position in table_positions.items():
        restaurant.add_table(table_id, position)
    
    # 确保后厨区域正确设置
    for pos in kitchen_positions:
        restaurant.add_kitchen(pos)
    
    return restaurant

def print_restaurant_info(restaurant):
    """打印餐厅信息摘要"""
    print("===== 餐厅布局信息 =====")
    print(f"餐厅大小: {restaurant.height}x{restaurant.width}")
    print(f"桌子数量: {len(restaurant.tables)}")
    print(f"后厨区域: {len(restaurant.kitchen)} 个单元格")
    
    # 打印所有桌子的位置
    print("\n桌子位置:")
    for table_id, position in sorted(restaurant.tables.items()):
        print(f"  桌号 {table_id}: 位置 {position}")
    
    # 显示整个餐厅布局
    print("\n餐厅布局:")
    restaurant.display() 