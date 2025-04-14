# baseline/robot_baseline.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from robot import Robot

class BaselineRobot(Robot):
    """
    基线机器人，直接沿规划路径运动，遇到障碍时停止
    """
    def __init__(self, environment, start, goal):
        super().__init__(environment, start, goal)
    # 直接使用基类的 move() 和 handle_obstacle() 方法 