"""
机器人主体（调度层）
路径规划 & 订单管理组件

* PathPlanner ：A* 算法，负责在 `RestaurantLayout` 上寻找最短路径
* Order / OrderManager ：订单生命周期、状态管理

该文件合并“路径规划 + 订单调度”两类功能，是因为它们都属于
“planning（计划层）”—— 跟 Robot 的动作执行层分离。
"""

from __future__ import annotations

import heapq
import logging
import time
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple

from restaurant.restaurant_layout import RestaurantLayout

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


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


# --------------------------------------------------------------------------- #
# 订单状态与类
# --------------------------------------------------------------------------- #
class OrderStatus(Enum):
    """
    订单状态枚举
    """

    WAITING = auto()
    PREPARING = auto()
    READY = auto()
    DELIVERING = auto()
    DELIVERED = auto()
    FAILED = auto()


class Order:
    """
    餐厅订单实体，记录生命周期时间戳
    """

    def __init__(
        self,
        order_id: int,
        table_id: str,
        prep_time: int,
        items: Optional[List[str]] = None,
    ) -> None:
        self.order_id = order_id
        self.table_id = table_id
        self.prep_time = prep_time
        self.items = items or []

        self.status = OrderStatus.WAITING
        self.created_time = time.time()

        # 时间戳
        self.prep_start_time: Optional[float] = None
        self.ready_time: Optional[float] = None
        self.delivery_start_time: Optional[float] = None
        self.delivery_end_time: Optional[float] = None

    # ---- 状态流转 ----------------------------------------------------------
    def start_preparing(self) -> None:
        self.status = OrderStatus.PREPARING
        self.prep_start_time = time.time()

    def finish_preparing(self) -> None:
        self.status = OrderStatus.READY
        self.ready_time = time.time()

    def start_delivery(self) -> bool:
        if self.status != OrderStatus.READY:
            return False
        self.status = OrderStatus.DELIVERING
        self.delivery_start_time = time.time()
        return True

    def complete_delivery(self) -> bool:
        if self.status != OrderStatus.DELIVERING:
            return False
        self.status = OrderStatus.DELIVERED
        self.delivery_end_time = time.time()
        return True

    def fail_delivery(self) -> None:
        self.status = OrderStatus.FAILED
        self.delivery_end_time = time.time()

    # ---- 统计 --------------------------------------------------------------
    def total_time(self) -> Optional[float]:
        return (self.delivery_end_time or 0) - self.created_time if self.delivery_end_time else None

    def delivery_time(self) -> Optional[float]:
        if self.delivery_start_time and self.delivery_end_time:
            return self.delivery_end_time - self.delivery_start_time
        return None

    # ---- misc --------------------------------------------------------------
    def __repr__(self) -> str:  # pragma: no cover
        return f"<Order#{self.order_id} {self.table_id} {self.status.name}>"


# --------------------------------------------------------------------------- #
# 订单管理器
# --------------------------------------------------------------------------- #
class OrderManager:
    """
    集中管理所有订单的状态队列
    """

    MAX_SIMULTANEOUS_PREPARING = 3

    def __init__(self) -> None:
        self._orders: Dict[int, Order] = {}
        self._next_id = 1

        # 队列
        self.waiting: List[Order] = []
        self.preparing: List[Order] = []
        self.ready: List[Order] = []
        self.delivering: List[Order] = []
        self.completed: List[Order] = []
        self.failed: List[Order] = []

    # ---- 创建与状态迁移 -----------------------------------------------------
    def create(self, table_id: str, prep_time: int, items: Optional[List[str]] = None) -> Order:
        """
        新建订单并加入 waiting 队列
        """
        order = Order(self._next_id, table_id, prep_time, items)
        self._next_id += 1
        self._orders[order.order_id] = order
        self.waiting.append(order)
        logger.info("创建订单 %s", order)
        return order

    def _move(self, order: Order, src: List[Order], dst: List[Order]) -> None:
        if order in src:
            src.remove(order)
        dst.append(order)

    # ---- 厨房模拟循环 ------------------------------------------------------
    def tick_kitchen(self) -> None:
        """
        模拟一次厨房时间片推进：准备完成 -> READY
        """
        now = time.time()

        # 检查准备完成
        finished = [
            od for od in self.preparing if now - (od.prep_start_time or now) >= od.prep_time
        ]
        for od in finished:
            od.finish_preparing()
            self._move(od, self.preparing, self.ready)
            logger.debug("订单准备完成 %s", od)

        # 启动新准备
        while (
            self.waiting
            and len(self.preparing) < self.MAX_SIMULTANEOUS_PREPARING
        ):
            od = self.waiting.pop(0)
            od.start_preparing()
            self.preparing.append(od)
            logger.debug("开始准备 %s", od)

    # ---- 配送相关 ----------------------------------------------------------
    def next_ready_order(self) -> Optional[Order]:
        """
        取队首可配送订单，不弹出
        """
        return self.ready[0] if self.ready else None

    def assign_to_robot(self, order: Order) -> bool:
        """
        将订单指派给机器人
        """
        if order not in self.ready:
            return False
        order.start_delivery()
        self._move(order, self.ready, self.delivering)
        return True

    def complete_delivery(self, order: Order) -> bool:
        """
        完成配送
        """
        if order not in self.delivering:
            return False
        order.complete_delivery()
        self._move(order, self.delivering, self.completed)
        return True

    def fail_delivery(self, order: Order) -> None:
        """
        配送失败
        """
        order.fail_delivery()
        if order in self.ready:
            self._move(order, self.ready, self.failed)
        elif order in self.delivering:
            self._move(order, self.delivering, self.failed)

    # ---- 统计 --------------------------------------------------------------
    def stats(self) -> Dict[str, float]:
        """
        统计订单相关指标
        """
        total = len(self._orders)
        delivery_times = [od.delivery_time() for od in self.completed if od.delivery_time()]
        total_times = [od.total_time() for od in self.completed if od.total_time()]
        return {
            "total_orders": total,
            "completed": len(self.completed),
            "failed": len(self.failed),
            "success_rate": len(self.completed) / total * 100 if total else 0.0,
            "avg_delivery_time": sum(delivery_times) / len(delivery_times) if delivery_times else 0.0,
            "avg_total_time": sum(total_times) / len(total_times) if total_times else 0.0,
        }

    # ---- misc --------------------------------------------------------------
    def __getitem__(self, order_id: int) -> Order:
        """
        获取指定订单
        """
        return self._orders[order_id]
