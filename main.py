# main.py

from restaurant_grid import RestaurantEnvironment
from baseline.robot_baseline import BaselineRobot
from rag_robot.robot_rag import RagRobot
from visualization import animate_robot_path

def main():
    # 定义一个5x5网格的餐厅环境（0表示通行，1表示障碍）
    grid = [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 0, 0, 1, 0],
        [0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0]
    ]
    env = RestaurantEnvironment(grid)
    
    start = (0, 0)
    goal = (4, 4)
    
    print("===== 基线机器人仿真 =====")
    baseline_robot = BaselineRobot(env, start, goal)
    baseline_robot.simulate()
    print("基线机器人路径动画：")
    animate_robot_path(baseline_robot.path_history, title="基线机器人路径")
    
    print("===== RAG机器人仿真 =====")
    rag_robot = RagRobot(env, start, goal)
    rag_robot.simulate()
    print("RAG机器人路径动画：")
    animate_robot_path(rag_robot.path_history, title="RAG机器人路径")

if __name__ == "__main__":
    main() 