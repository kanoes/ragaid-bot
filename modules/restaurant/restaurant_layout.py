from modules.restaurant.restaurant_grid import RestaurantEnvironment
import queue
import os
import warnings

def create_restaurant_layout():
    """
    创建20桌子和厨房区域的标准餐厅布局（向后兼容函数）
    
    返回：配置好的RestaurantEnvironment对象
    """
    # 尝试从utils中导入相关函数
    try:
        from modules.restaurant.utils import load_restaurant_layout, list_restaurant_layouts
        
        # 检查是否有可用的布局文件
        layouts = list_restaurant_layouts()
        if not layouts:
            # 创建一个基本的空餐厅环境
            warnings.warn("没有找到餐厅布局文件，创建一个基本的空餐厅环境")
            return RestaurantEnvironment()
        
        # 使用第一个可用的布局
        try:
            restaurant = load_restaurant_layout(layouts[0])
            return restaurant.environment
        except Exception as e:
            warnings.warn(f"加载默认布局失败: {e}，创建一个基本的空餐厅环境")
            return RestaurantEnvironment()
            
    except ImportError:
        # 如果无法导入，创建一个基本的空餐厅环境
        warnings.warn("无法导入餐厅工具函数，创建一个基本的空餐厅环境")
        return RestaurantEnvironment()

def verify_and_fix_connectivity(restaurant, start, destinations):
    """スタート地点から全目的地への接続性をチェックし、接続されていないパスを修正"""
    print("レストランレイアウトの接続性をチェック中...")
    
    # BFSで接続性をチェック
    height, width = restaurant.height, restaurant.width
    for dest_id, dest in destinations.items():
        if not is_connected(restaurant, start, dest):
            print(f"警告: テーブル番号 {dest_id} の位置 {dest} はキッチンと接続されていません、修正を試みます...")
            create_path(restaurant, start, dest)
    
    print("接続性チェック完了")

def is_connected(restaurant, start, end):
    """2点間が接続されているかをチェック"""
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
    """startからendへの直線パスを作成"""
    x1, y1 = start
    x2, y2 = end
    
    # まず水平方向
    for y in range(min(y1, y2), max(y1, y2) + 1):
        if 0 <= x1 < restaurant.height and 0 <= y < restaurant.width:
            if restaurant.grid[x1][y] == 1:  # 障害物の場合
                restaurant.grid[x1][y] = 0   # 通路に変更
                print(f"  ({x1}, {y}) に通路を作成")
    
    # 次に垂直方向
    for x in range(min(x1, x2), max(x1, x2) + 1):
        if 0 <= x < restaurant.height and 0 <= y2 < restaurant.width:
            if restaurant.grid[x][y2] == 1:  # 障害物の場合
                restaurant.grid[x][y2] = 0   # 通路に変更
                print(f"  ({x}, {y2}) に通路を作成")

def print_restaurant_info(restaurant):
    """レストラン情報の概要を表示"""
    print("===== レストランレイアウト情報 =====")
    print(f"レストランサイズ: {restaurant.height}x{restaurant.width}")
    print(f"テーブル数: {len(restaurant.tables)}")
    print(f"キッチンエリア: {len(restaurant.kitchen)} セル")
    
    # すべてのテーブル位置を表示
    print("\nテーブル位置:")
    for table_id, position in sorted(restaurant.tables.items()):
        print(f"  テーブル番号 {table_id}: 位置 {position}")
    
    # レストラン全体のレイアウトを表示
    print("\nレストランレイアウト:")
    restaurant.display()

def display_full_restaurant(restaurant, kitchen_position=None):
    """レストラン全体のレイアウトを表示し、各セルの座標をテーブル形式でマーク"""
    print("\n===== 詳細レストランレイアウト =====")
    print("  ", end="")
    for j in range(restaurant.width):
        print(f"{j:2d}", end=" ")
    print("\n" + "-" * (restaurant.width * 3 + 3))
    
    for i in range(restaurant.height):
        print(f"{i:2d}|", end="")
        for j in range(restaurant.width):
            cell = (i, j)
            if kitchen_position and cell == kitchen_position:
                print(" K*", end="")  # 特殊厨房位置
            elif restaurant.is_kitchen(cell):
                print(" K ", end="")  # 厨房
            elif restaurant.is_table(cell):
                # 查找桌号
                table_id = None
                for tid, pos in restaurant.tables.items():
                    if pos == cell:
                        table_id = tid
                        break
                
                if table_id:
                    # 确保桌号为两位数字符串
                    table_id_str = str(table_id).zfill(2)
                    print(f"{table_id_str}", end=" ")
                else:
                    print(" T ", end="")  # 未知桌号
            elif restaurant.grid[i][j] == 1:
                print(" W ", end="")  # 障碍物
            else:
                print(" S ", end="")  # 空地
        print()
    print() 