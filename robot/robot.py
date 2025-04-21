"""
机器人主体（调度层）

分层架构
--------
* PathPlanner             — 规划层（robot.path_planner）
* Order / OrderManager    — 订单层（robot.order）
* MotionController        — 动作层（robot.motion_controller）
* Robot / AIEnhancedRobot — 调度层（本文件）
"""

from __future__ import annotations

import logging
import os
from typing import List, Optional, Tuple

from restaurant.restaurant_layout import RestaurantLayout
from robot.motion_controller import MotionController
from robot.plan import PathPlanner
from robot.order import Order
from robot.rag import RAGModule

logger = logging.getLogger(__name__)


class Robot:
    """
    基础机器人：无 RAG 智能
    """

    def __init__(
        self,
        layout: RestaurantLayout,
        robot_id: int = 1,
        start: Optional[Tuple[int, int]] = None,
    ) -> None:
        self.layout = layout
        self.robot_id = robot_id

        self.position = start or (layout.kitchen[0] if layout.kitchen else (0, 0))
        self.goal: Optional[Tuple[int, int]] = None
        self.path: List[Tuple[int, int]] = []

        self.planner = PathPlanner(layout)
        self.controller = MotionController(layout, self.planner)

        self.current_order: Optional[Order] = None
        self._stats = {"delivered": 0, "failed": 0}
        self.path_history: list[tuple[int, int]] = [self.position]
    
    # ---------------- 移动记录 ---------------- #
    def tick(self) -> None:
        if not self.path:
            return

        prev_pos = self.position
        self.position, self.path = self.controller.step(
            self.position, self.path, self.goal
        )

        if self.position != prev_pos:
            self.path_history.append(self.position)

        if self.position == self.goal:
            self._finish_delivery(success=True)

    def _finish_delivery(self, *, success: bool) -> None:
        ...
        # 保留 path_history；在接新订单时重置
        self.path = []

    # ---------------- 订单接口 ---------------- #
    def assign_order(self, order: Order) -> bool:
        """
        接单并规划路径
        """
        if self.current_order:
            self.path_history = [self.position] 
            logger.info("Robot #%s 忙碌", self.robot_id)
            return False

        table_pos = self.layout.tables.get(order.table_id)
        if not table_pos:
            logger.error("桌号不存在 %s", order.table_id)
            return False

        # 找到靠近桌子的可通行点
        for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            g = (table_pos[0] + dx, table_pos[1] + dy)
            if self.layout.is_free(g):
                self.goal = g
                break
        if not self.goal:
            logger.error("桌子周围无落脚点")
            return False

        self.path = self.planner.find_path(self.position, self.goal) or []
        if not self.path:
            logger.error("无法规划路径")
            return False

        order.start_delivery()
        self.current_order = order
        return True

    # ---------------- 模拟循环 ---------------- #
    def tick(self) -> None:
        if not self.path:           # 没有剩余路径，不动
            return

        prev = self.position
        self.position, self.path = self.controller.step(
            self.position, self.path, self.goal
        )

        # 只有在实际移动时才记录轨迹
        if self.position != prev:
            self.path_history.append(self.position)

        if self.position == self.goal:
            self._finish_delivery(success=True)


    def _finish_delivery(self, *, success: bool) -> None:
        if not self.current_order:
            return
        if success:
            self.current_order.complete_delivery()
            self._stats["delivered"] += 1
        else:
            self.current_order.fail_delivery()
            self._stats["failed"] += 1
        self.current_order = None
        self.goal = None
        self.path = []

    # ---------------- 其他 ---------------- #
    def simulate(self, max_step: int = 500) -> None:
        step = 0
        while self.path and step < max_step:
            self.tick()
            step += 1
        logging.debug("simulate finished: %s steps", step)

    def stats(self) -> dict:
        return dict(self._stats)


class AIEnhancedRobot(Robot):
    """
    带 RAG 智能的机器人
    """

    def __init__(
        self,
        layout: RestaurantLayout,
        robot_id: int = 1,
        api_key: str | None = None,
        knowledge_dir: str | None = None,
        start: Optional[Tuple[int, int]] = None,
    ) -> None:
        super().__init__(layout, robot_id, start)
        self.rag = RAGModule(
            api_key=api_key,
            knowledge_file=os.path.join(knowledge_dir, "restaurant_rule.json"),
        )
        self.controller = MotionController(layout, self.planner, rag=self.rag)
