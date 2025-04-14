# robot.py

from path_planner import PathPlanner

class Robot:
    """
    机器人基类，定义基本的路径规划、移动和障碍处理功能
    """
    def __init__(self, environment, start, goal):
        self.env = environment
        self.start = start
        self.goal = goal
        self.position = start
        self.planner = PathPlanner(environment)
        self.path = []  # 当前规划的路径
        self.path_history = [start]  # 记录每一步坐标以便于可视化

    def plan_path(self):
        self.path = self.planner.find_path(self.position, self.goal)
        if self.path:
            print(f"从 {self.position} 到 {self.goal} 的规划路径： {self.path}")
        else:
            print("未能找到路径！")
    
    def move(self):
        """
        沿路径前进一步
        """
        if self.path and len(self.path) > 1:
            next_position = self.path[1]
            if self.env.is_free(next_position):
                self.position = next_position
                self.path_history.append(next_position)
                self.path.pop(0)
            else:
                print(f"在 {next_position} 处遇到障碍。")
                self.handle_obstacle(next_position)
        else:
            print("已到达目标或无可用路径。")
    
    def handle_obstacle(self, obstacle_position):
        """
        遇到障碍的处理逻辑，基类默认不做特殊处理
        """
        print("基线机器人：无法处理障碍，停止运动。")
    
    def simulate(self):
        """
        模拟机器人执行任务，直至到达目标或超出步数限制
        """
        self.plan_path()
        steps = 0
        while self.position != self.goal and self.path is not None:
            print(f"步骤 {steps}：当前位置 {self.position}")
            self.move()
            steps += 1
            if steps > 50:  # 防止无限循环
                print("仿真结束：步数过多。")
                break
        if self.position == self.goal:
            print(f"任务完成，在 {steps} 步后到达目标 {self.position}。") 