# restaurant_layout.py

from restaurant_grid import RestaurantEnvironment
import queue

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
    
    # 在后厨区域添加出口
    grid[5][4] = 0  # 主要后厨出口
    grid[3][7] = 0  # 额外的后厨出口
    
    # 添加中央装饰/障碍物
    for i in range(8, 12):
        for j in range(8, 12):
            grid[i][j] = 1
    
    # 添加部分内部墙壁/隔断（但确保有足够通道）
    for i in range(5, 15):
        if i != 7 and i != 10 and i != 12:  # 添加多个通道
            grid[i][15] = 1
    
    for j in range(5, 15):
        if j != 7 and j != 10 and j != 13:  # 添加多个通道
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
    
    # 确保每张桌子周围有空位，用于机器人配送
    for position in table_positions.values():
        x, y = position
        # 确保桌子周围至少有一个空位
        has_empty = False
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < height and 0 <= ny < width and grid[nx][ny] == 0:
                has_empty = True
                break
        
        # 如果没有空位，强制创建一个
        if not has_empty:
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < height and 0 <= ny < width and grid[nx][ny] == 1:
                    grid[nx][ny] = 0  # 将障碍物改为空位
                    break
    
    # 创建餐厅环境
    restaurant = RestaurantEnvironment(grid)
    
    # 添加桌子
    for table_id, position in table_positions.items():
        restaurant.add_table(table_id, position)
    
    # 确保后厨区域正确设置
    for pos in kitchen_positions:
        restaurant.add_kitchen(pos)
    
    # 连通性检查并修复
    verify_and_fix_connectivity(restaurant, kitchen_positions[0], table_positions)
    
    return restaurant

def verify_and_fix_connectivity(restaurant, start, destinations):
    """检查从起点到所有目的地的连通性，并修复不连通的路径"""
    print("正在检查餐厅布局连通性...")
    
    # 使用BFS检查连通性
    height, width = restaurant.height, restaurant.width
    for dest_id, dest in destinations.items():
        if not is_connected(restaurant, start, dest):
            print(f"警告: 桌号 {dest_id} 在位置 {dest} 与后厨不连通，尝试修复...")
            create_path(restaurant, start, dest)
    
    print("连通性检查完成")

def is_connected(restaurant, start, end):
    """检查两点之间是否连通"""
    visited = set()
    q = queue.Queue()
    q.put(start)
    visited.add(start)
    
    while not q.empty():
        current = q.get()
        if current == end:
            return True
        
        for neighbor in restaurant.neighbors(current):
            if neighbor not in visited:
                visited.add(neighbor)
                q.put(neighbor)
    
    return False

def create_path(restaurant, start, end):
    """创建从start到end的直线路径"""
    x1, y1 = start
    x2, y2 = end
    
    # 先水平方向
    for y in range(min(y1, y2), max(y1, y2) + 1):
        if 0 <= x1 < restaurant.height and 0 <= y < restaurant.width:
            if restaurant.grid[x1][y] == 1:  # 如果是障碍物
                restaurant.grid[x1][y] = 0   # 改为通道
                print(f"  在 ({x1}, {y}) 处创建通道")
    
    # 再垂直方向
    for x in range(min(x1, x2), max(x1, x2) + 1):
        if 0 <= x < restaurant.height and 0 <= y2 < restaurant.width:
            if restaurant.grid[x][y2] == 1:  # 如果是障碍物
                restaurant.grid[x][y2] = 0   # 改为通道
                print(f"  在 ({x}, {y2}) 处创建通道")

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

def display_full_restaurant(restaurant, kitchen_position=None):
    """显示整个餐厅布局，并用表格形式标记每个单元格的坐标"""
    print("\n===== 详细餐厅布局 =====")
    print("  ", end="")
    for j in range(restaurant.width):
        print(f"{j:2d}", end=" ")
    print("\n" + "-" * (restaurant.width * 3 + 3))
    
    for i in range(restaurant.height):
        print(f"{i:2d}|", end="")
        for j in range(restaurant.width):
            cell = (i, j)
            if kitchen_position and cell == kitchen_position:
                print(" K ", end="")
            elif restaurant.is_kitchen(cell):
                print(" ▣ ", end="")
            elif restaurant.is_table(cell):
                # 查找桌号
                table_id = None
                for tid, pos in restaurant.tables.items():
                    if pos == cell:
                        table_id = tid
                        break
                if table_id is not None:
                    print(f"{table_id:2d}", end=" ")
                else:
                    print(" ◇ ", end="")
            elif restaurant.is_free(cell):
                print(" · ", end="")
            else:
                print(" █ ", end="")
        print()
    print() 