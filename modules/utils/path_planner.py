# modules/utils/path_planner.py
import heapq

class PathPlanner:
    """
    A*アルゴリズムによる経路計画の実装
    """
    def __init__(self, environment):
        self.env = environment

    def heuristic(self, a, b):
        # マンハッタン距離をヒューリスティック関数として使用
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def find_path(self, start, goal):
        env = self.env
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        
        # 開始点と目標周辺の状況を表示
        print(f"経路計画開始：{start} から {goal} へ")
        
        # 目標位置の周りに通行可能エリアがあるか確認
        goal_x, goal_y = goal
        goal_neighbors = []
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = goal_x + dx, goal_y + dy
            if 0 <= nx < env.height and 0 <= ny < env.width:
                status = "通行可能" if env.is_free((nx, ny)) else "通行不可"
                goal_neighbors.append(f"({nx}, {ny}): {status}")
        
        print(f"目標位置 {goal} の周囲状況:")
        for n in goal_neighbors:
            print(f"  {n}")
        
        # 目標が完全に封鎖されているかチェック - すべて通行不可の場合、探索範囲を拡大
        all_blocked = True
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = goal_x + dx, goal_y + dy
            if 0 <= nx < env.height and 0 <= ny < env.width and env.is_free((nx, ny)):
                all_blocked = False
                break
                
        # 目標周辺がすべて封鎖されている場合、探索半径を増やして到達可能点を探す
        if all_blocked:
            print(f"警告：目標 {goal} の周囲がすべて封鎖されています。探索範囲を拡大します")
            # 探索半径を2に拡大
            for r in range(2, 4):  # 半径2-3
                for dx in range(-r, r+1):
                    for dy in range(-r, r+1):
                        if abs(dx) + abs(dy) <= r:  # マンハッタン距離がr以下
                            nx, ny = goal_x + dx, goal_y + dy
                            if 0 <= nx < env.height and 0 <= ny < env.width and env.is_free((nx, ny)):
                                print(f"目標から {r} ステップ離れた到達可能点 ({nx}, {ny}) を発見")
                                # この点を一時的な目標として設定
                                temp_goal = (nx, ny)
                                # 標準A*を使用してこの一時的な目標への経路を検索
                                path = self._find_path_internal(start, temp_goal)
                                if path:
                                    print(f"一時的な目標 {temp_goal} への経路が見つかりました")
                                    return path
        
        # 標準A*探索
        return self._find_path_internal(start, goal)
        
    def _find_path_internal(self, start, goal):
        """内部標準A*経路探索"""
        env = self.env
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        
        while open_set:
            current_priority, current = heapq.heappop(open_set)
            if current == goal:
                path = self.reconstruct_path(came_from, current)
                print(f"経路が見つかりました: {path}")
                return path

            for neighbor in env.neighbors(current):
                tentative_g = g_score[current] + 1
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + self.heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score, neighbor))
        
        print(f"{start} から {goal} への経路が見つかりません")
        return None  # 経路が見つからない

    def reconstruct_path(self, came_from, current):
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path 