"""
Prompt拼接系统 / user 提示，并抽取关键词式决策
"""

from __future__ import annotations
from typing import Tuple


class PromptHelper:
    """
    构造与解析 Prompt
    """

    @staticmethod
    def build_obstacle_query(robot_id: int, position, goal, obstacle) -> str:
        return (
            f"Robot#{robot_id} encounters an obstacle at {obstacle} while heading "
            f"from {position} to {goal}. Suggest the best action "
            f"(options: reroute, wait, report_unreachable)."
        )

    @staticmethod
    def build_plan_query(robot_id: int, start: Tuple[int, int], goal: Tuple[int, int]) -> str:
        return (
            f"Robot#{robot_id} planning path from {start} to {goal}. "
            "Please suggest improvements or identify potential issues."
        )

    @staticmethod
    def simplify(decision: str) -> str:
        d = decision.lower()
        if "reroute" in d or "new path" in d:
            return "reroute"
        if "wait" in d:
            return "wait"
        if "unreachable" in d:
            return "report_unreachable"
        return decision.strip()
