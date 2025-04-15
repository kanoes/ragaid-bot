# path_planner.py
import heapq

class PathPlanner:
    """
    实现 A* 算法进行路径规划
    """
    def __init__(self, environment):
        self.env = environment

    def heuristic(self, a, b):
        # 采用曼哈顿距离作为启发式函数
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def find_path(self, start, goal):
        env = self.env
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        
        # 打印起点和目标附近的情况
        print(f"开始路径规划：从 {start} 到 {goal}")
        
        # 检查目标位置周围是否有可通行区域
        goal_x, goal_y = goal
        goal_neighbors = []
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = goal_x + dx, goal_y + dy
            if 0 <= nx < env.height and 0 <= ny < env.width:
                status = "可通行" if env.is_free((nx, ny)) else "不可通行"
                goal_neighbors.append(f"({nx}, {ny}): {status}")
        
        print(f"目标位置 {goal} 周围状态:")
        for n in goal_neighbors:
            print(f"  {n}")
        
        # 检查目标是否被完全封锁 - 如果都不可通行，尝试扩大搜索范围
        all_blocked = True
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = goal_x + dx, goal_y + dy
            if 0 <= nx < env.height and 0 <= ny < env.width and env.is_free((nx, ny)):
                all_blocked = False
                break
                
        # 如果目标周围全部被阻塞，增加搜索半径尝试找到更远的可达点
        if all_blocked:
            print(f"警告：目标 {goal} 周围全部被阻塞，尝试扩大搜索范围")
            # 尝试扩大搜索半径到2
            for r in range(2, 4):  # 半径2-3
                for dx in range(-r, r+1):
                    for dy in range(-r, r+1):
                        if abs(dx) + abs(dy) <= r:  # 曼哈顿距离不超过r
                            nx, ny = goal_x + dx, goal_y + dy
                            if 0 <= nx < env.height and 0 <= ny < env.width and env.is_free((nx, ny)):
                                print(f"发现距离目标 {r} 步远的可达点 ({nx}, {ny})")
                                # 将此点作为临时目标
                                temp_goal = (nx, ny)
                                # 使用标准A*寻找到这个临时目标的路径
                                path = self._find_path_internal(start, temp_goal)
                                if path:
                                    print(f"找到通往临时目标 {temp_goal} 的路径")
                                    return path
        
        # 标准A*搜索
        return self._find_path_internal(start, goal)
        
    def _find_path_internal(self, start, goal):
        """内部标准A*路径搜索"""
        env = self.env
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        
        while open_set:
            current_priority, current = heapq.heappop(open_set)
            if current == goal:
                path = self.reconstruct_path(came_from, current)
                print(f"找到路径: {path}")
                return path

            for neighbor in env.neighbors(current):
                tentative_g = g_score[current] + 1
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + self.heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score, neighbor))
        
        print(f"无法找到从 {start} 到 {goal} 的路径")
        return None  # 找不到路径

    def reconstruct_path(self, came_from, current):
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path 