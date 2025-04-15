# baseline/robot_baseline.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from robot import Robot

class BaselineRobot(Robot):
    """
    基线机器人，直接沿规划路径运动，遇到障碍时停止
    """
    def __init__(self, environment, start=None, goal=None, robot_id=1):
        super().__init__(environment, start, goal, robot_id)
        self.name = "基线机器人"
    
    def handle_obstacle(self, obstacle_position):
        """
        基线机器人的障碍处理：简单地停止并失败
        """
        print(f"{self.name}#{self.robot_id} - 在 {obstacle_position} 遇到障碍，停止配送")
        if self.current_order:
            self.fail_current_order("遇到障碍物，无法继续配送")
        
        # 尝试返回后厨
        self.return_to_kitchen()
    # 直接使用基类的 move() 和 handle_obstacle() 方法 