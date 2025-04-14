import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from robot import Robot

class RagRobot(Robot):
    """
    RAG 机器人，通过简单的知识库来模拟 RAG 处理障碍的决策，并重新规划路径
    """
    def __init__(self, environment, start, goal, knowledge_base=None):
        super().__init__(environment, start, goal)
        self.knowledge_base = knowledge_base if knowledge_base else {
            "obstacle": "检测到障碍，尝试重新规划替代路径。"
        }

    def handle_obstacle(self, obstacle_position):
        print(f"RAG机器人：在 {obstacle_position} 处遇到障碍。")
        decision = self.rag_decision(obstacle_position)
        print(f"RAG决策：{decision}")
        # 根据决策结果，再次规划路径
        self.plan_path()

    def rag_decision(self, situation):
        if "obstacle" in self.knowledge_base:
            return self.knowledge_base["obstacle"]
        return "无可用恢复策略。" 