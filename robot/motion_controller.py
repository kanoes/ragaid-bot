"""
机器人主体（动作层）
低层动作执行 & 障碍处理

该层只关心『从 A 走到 B 的每一步应该怎么走、遇到障碍怎么办』
不关心接单/路径规划/统计等上层任务
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional, Tuple

from restaurant.restaurant_layout import RestaurantLayout
from robot.plan import PathPlanner
from robot.rag.rag_module import RAGModule

logger = logging.getLogger(__name__)


class MotionController:
    """
    机器人底盘控制器：一步移动 + 障碍应对
    """

    def __init__(
        self,
        layout: RestaurantLayout,
        planner: PathPlanner,
        rag: Optional[RAGModule] = None,
    ) -> None:
        self.layout = layout
        self.planner = planner
        self.rag = rag

    # --------------------------------------------------------------------- #
    # 公共 API
    # --------------------------------------------------------------------- #
    def step(
        self,
        position: Tuple[int, int],
        path: List[Tuple[int, int]],
        goal: Tuple[int, int] | None,
    ) -> Tuple[Tuple[int, int], List[Tuple[int, int]]]:
        """
        执行一个离散时间步：尝试向 `path[1]` 前进

        返回
        ----
        new_pos, new_path
        """
        if not path:
            return position, path

        next_pos = path[1] if len(path) > 1 else position
        if self.layout.is_free(next_pos):
            return next_pos, path[1:]

        # 遇障
        logger.debug("遇到障碍 %s", next_pos)
        new_path = self._handle_obstacle(position, goal, next_pos)
        return position, new_path

    # --------------------------------------------------------------------- #
    # 私有：障碍处理
    # --------------------------------------------------------------------- #
    def _handle_obstacle(
        self,
        pos: Tuple[int, int],
        goal: Tuple[int, int] | None,
        obstacle: Tuple[int, int],
    ) -> List[Tuple[int, int]]:
        """
        优先调用 RAG；否则直接重新规划
        """
        if self.rag and self.rag.is_ready():
            decision = self.rag.make_decision(
                situation_type="obstacle",
                position=pos,
                goal=goal,
                context=obstacle,
            )
            logger.info("RAG 决策: %s", decision)
            if decision in {"绕行", "重新规划"} and goal:
                return self.planner.find_path(pos, goal) or []
            if decision == "等待":
                time.sleep(0.5)
                return []
        # 基础策略：重新规划或放弃
        return self.planner.find_path(pos, goal) if goal else []
