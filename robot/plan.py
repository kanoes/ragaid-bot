"""
路径规划组件

PathPlanner类：基于A*算法，负责在 `RestaurantLayout` 上寻找最短路径
"""

from __future__ import annotations

import heapq
import logging
from typing import Dict, List, Optional, Tuple

from restaurant.restaurant_layout import RestaurantLayout

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# 路径规划 – A* 实现
# --------------------------------------------------------------------------- #
class PathPlanner:
    """
    基于 A* 的网格路径规划器
    """

    def __init__(self, layout: RestaurantLayout) -> None:
        self.layout = layout

    # ---- A* ----------------------------------------------------------------
    @staticmethod
    def _heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> int:
        """
        曼哈顿距离启发函数
        """
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def find_path(
        self,
        start: Tuple[int, int],
        goal: Tuple[int, int],
        allow_expand: bool = True,
    ) -> Optional[List[Tuple[int, int]]]:
        """
        搜索从 *start* 到 *goal* 的路径
        若目标四邻域被完全阻塞且 `allow_expand=True`
        将在 2–3 曼哈顿距离半径内寻找最近可达点作为临时目标
        """
        logger.debug("路径规划: %s -> %s", start, goal)

        # 若四邻域可达直接 A*
        if any(
            self.layout.is_free((goal[0] + dx, goal[1] + dy))
            for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0))
        ):
            return self._a_star(start, goal)

        if not allow_expand:
            logger.warning("目标被围堵且不允许扩圈搜索")
            return None

        logger.warning("目标周围被封锁，扩大搜索半径")
        for radius in range(2, 4):  # 半径 2~3
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) + abs(dy) > radius:
                        continue
                    nx, ny = goal[0] + dx, goal[1] + dy
                    if self.layout.is_free((nx, ny)):
                        path = self._a_star(start, (nx, ny))
                        if path:
                            logger.info("找到临时目标 %s 的替代路径", (nx, ny))
                            return path
        logger.error("在扩圈后仍无法找到路径")
        return None

    # ---- internal ----------------------------------------------------------
    def _a_star(
        self, start: Tuple[int, int], goal: Tuple[int, int]
    ) -> Optional[List[Tuple[int, int]]]:
        layout = self.layout
        open_heap: List[Tuple[int, Tuple[int, int]]] = []
        heapq.heappush(open_heap, (0, start))
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        g_score: Dict[Tuple[int, int], int] = {start: 0}

        while open_heap:
            _, current = heapq.heappop(open_heap)
            if current == goal:
                return self._reconstruct(came_from, current)

            for nb in layout.neighbors(current):
                tentative = g_score[current] + 1
                if tentative < g_score.get(nb, float("inf")):
                    came_from[nb] = current
                    g_score[nb] = tentative
                    f_score = tentative + self._heuristic(nb, goal)
                    heapq.heappush(open_heap, (f_score, nb))

        logger.warning("A* 失败: %s -> %s", start, goal)
        return None

    @staticmethod
    def _reconstruct(
        came_from: Dict[Tuple[int, int], Tuple[int, int]],
        current: Tuple[int, int],
    ) -> List[Tuple[int, int]]:
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path
