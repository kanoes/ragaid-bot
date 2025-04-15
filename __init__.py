# ragaid-bot
# 使用机器人送餐模拟，比较基础机器人和RAG增强智能机器人的配送效率
# 这是一个用于研究和教学目的的简单模拟项目
from modules.robot import Robot
from modules.environment import RestaurantEnvironment, create_restaurant_layout
from modules.utils import OrderManager, Order, animate_robot_path, PathPlanner

__version__ = "1.0.0" 