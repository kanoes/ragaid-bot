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
        
        while open_set:
            current_priority, current = heapq.heappop(open_set)
            if current == goal:
                return self.reconstruct_path(came_from, current)

            for neighbor in env.neighbors(current):
                tentative_g = g_score[current] + 1
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + self.heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score, neighbor))
        return None  # 找不到路径

    def reconstruct_path(self, came_from, current):
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path 