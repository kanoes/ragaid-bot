from modules.environment.restaurant_grid import RestaurantEnvironment
import queue

def create_restaurant_layout():
    """
    20テーブルとキッチンエリアを持つレストランレイアウトを作成
    
    レストランレイアウトは20x20のグリッド:
    - 0は通行可能エリア
    - 1は障害物（壁、装飾など）
    - 2はテーブル位置
    - 3はキッチンエリア
    
    戻り値：設定済みのRestaurantEnvironmentオブジェクト
    """
    # 20x20の空グリッドを作成
    height = 20
    width = 20
    grid = [[0 for _ in range(width)] for _ in range(height)]
    
    # 外壁を追加
    for i in range(height):
        grid[i][0] = 1  # 左壁
        grid[i][width-1] = 1  # 右壁
    
    for j in range(width):
        grid[0][j] = 1  # 上壁
        grid[height-1][j] = 1  # 下壁
    
    # キッチンエリアを追加（左上）
    kitchen_positions = []
    for i in range(2, 5):
        for j in range(2, 7):
            grid[i][j] = 3
            kitchen_positions.append((i, j))
    
    # キッチンエリアに出口を追加
    grid[5][4] = 0  # メインキッチン出口
    grid[3][7] = 0  # 追加キッチン出口
    
    # 中央の装飾/障害物を追加
    for i in range(8, 12):
        for j in range(8, 12):
            grid[i][j] = 1
    
    # 一部の内壁/仕切りを追加（十分な通路を確保）
    for i in range(5, 15):
        if i != 7 and i != 10 and i != 12:  # 複数の通路を追加
            grid[i][15] = 1
    
    for j in range(5, 15):
        if j != 7 and j != 10 and j != 13:  # 複数の通路を追加
            grid[5][j] = 1
    
    # 仕切りに通路を追加
    grid[5][10] = 0
    grid[10][15] = 0
    
    # テーブル位置を定義
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
    
    # 各テーブルの周りに空きスペースがあることを確認（ロボット配送用）
    for position in table_positions.values():
        x, y = position
        # テーブルの周りに少なくとも1つの空きスペースがあることを確認
        has_empty = False
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < height and 0 <= ny < width and grid[nx][ny] == 0:
                has_empty = True
                break
        
        # 空きスペースがない場合、強制的に作成
        if not has_empty:
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < height and 0 <= ny < width and grid[nx][ny] == 1:
                    grid[nx][ny] = 0  # 障害物を空きスペースに変更
                    break
    
    # レストラン環境を作成
    restaurant = RestaurantEnvironment(grid)
    
    # テーブルを追加
    for table_id, position in table_positions.items():
        restaurant.add_table(table_id, position)
    
    # キッチンエリアが正しく設定されていることを確認
    for pos in kitchen_positions:
        restaurant.add_kitchen(pos)
    
    # 接続性チェックと修正
    verify_and_fix_connectivity(restaurant, kitchen_positions[0], table_positions)
    
    return restaurant

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
                print(" K ", end="")
            elif restaurant.is_kitchen(cell):
                print(" ▣ ", end="")
            elif restaurant.is_table(cell):
                # テーブル番号を見つける
                table_id = None
                for tid, pos in restaurant.tables.items():
                    if pos == cell:
                        table_id = tid
                        break
                
                if table_id:
                    if table_id < 10:
                        print(f" {table_id} ", end="")
                    else:
                        print(f"{table_id} ", end="")
                else:
                    print(" T ", end="")
            elif restaurant.grid[i][j] == 1:
                print(" █ ", end="")
            else:
                print("   ", end="")
        print()
    print() 