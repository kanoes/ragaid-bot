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
import math
from typing import List, Optional, Tuple, Deque
from collections import deque

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

    # 定义到达目标点的容忍半径
    GOAL_TOLERANCE = 0  # 目标点容忍半径（格子数）
    ANGLE_TOLERANCE = 15  # 角度容忍范围（度）

    def __init__(
        self,
        layout: RestaurantLayout,
        robot_id: int = 1,
        start: Optional[Tuple[int, int]] = None,
    ) -> None:
        self.layout = layout
        self.robot_id = robot_id

        # 确保机器人从停靠点出发
        self.parking_spot = layout.parking or (layout.kitchen[0] if layout.kitchen else (0, 0))
        self.position = self.parking_spot
        self.goal: Optional[Tuple[int, int]] = None
        self.path: List[Tuple[int, int]] = []

        self.planner = PathPlanner(layout)
        self.controller = MotionController(layout, self.planner)

        # 订单队列
        self.order_queue: Deque[Order] = deque()
        self.current_order: Optional[Order] = None
        self._stats = {"delivered": 0, "failed": 0, "total_delivery_time": 0}
        self.path_history: list[tuple[int, int]] = [self.position]
        self.returning_to_parking = False
        self.delivery_start_time = None
        self.all_assigned_orders = []

    # ---------------- 订单接口 ---------------- #
    def assign_order(self, order: Order) -> bool:
        """
        接单并加入队列
        """
        table_pos = self.layout.tables.get(order.table_id)
        if not table_pos:
            logger.error("桌号不存在 %s", order.table_id)
            return False

        # 将订单加入队列
        self.order_queue.append(order)
        self.all_assigned_orders.append(order)
        logger.info("Robot #%s 接收订单 #%s 加入队列", self.robot_id, order.order_id)
        
        # 如果当前没有处理中的订单，则立即开始处理
        if not self.current_order and not self.returning_to_parking:
            self._process_next_order()
        
        return True

    def _process_next_order(self) -> bool:
        """
        处理队列中的下一个订单
        """
        if not self.order_queue:
            # 如果没有更多订单且不在停靠点，则返回停靠点
            if self.position != self.parking_spot and not self.returning_to_parking:
                self._return_to_parking()
            return False

        # 优化订单队列
        self._optimize_order_queue()

        # 取出下一个订单
        order = self.order_queue.popleft()
        self.current_order = order

        # 获取桌子对应的送餐点
        delivery_info = self.layout.get_delivery_point(order.table_id)
        if not delivery_info:
            logger.error("桌号 %s 没有指定送餐点", order.table_id)
            self._finish_delivery(success=False)
            return False

        delivery_pos, _ = delivery_info
        if not self.layout.is_free(delivery_pos):
            logger.error("桌号 %s 的送餐点 %s 不可通行", order.table_id, delivery_pos)
            self._finish_delivery(success=False)
            return False

        # 设置目标点
        self.goal = delivery_pos
        
        # 规划路径
        self.path = self.planner.find_path(self.position, self.goal) or []
        if not self.path:
            logger.error("无法规划到达桌子 %s 的路径", order.table_id)
            self._finish_delivery(success=False)
            return False

        # 开始配送
        order.start_delivery()
        
        # 如果是第一次从停靠点出发，记录开始时间
        if self.position == self.parking_spot and self.delivery_start_time is None:
            self.delivery_start_time = order.delivery_start_time
        
        logger.info("机器人 #%s 开始送餐至桌号 %s，目标位置 %s",
                   self.robot_id, order.table_id, self.goal)
        
        return True

    def _optimize_order_queue(self) -> None:
        """
        优化订单队列的配送顺序
        根据从当前位置到各个订单目标位置的距离，按照最近优先原则重新排序
        """
        if len(self.order_queue) <= 1:
            return  # 没有订单或只有一个订单，不需要优化
        
        # 创建一个临时列表来存储订单及其距离
        orders_with_distance = []
        current_pos = self.position
        
        for order in self.order_queue:
            # 获取订单的送餐点
            delivery_info = self.layout.get_delivery_point(order.table_id)
            if not delivery_info:
                continue
                
            delivery_pos, _ = delivery_info
            
            # 计算曼哈顿距离
            distance = abs(current_pos[0] - delivery_pos[0]) + abs(current_pos[1] - delivery_pos[1])
            
            # 将订单和距离加入列表
            orders_with_distance.append((order, distance))
        
        # 按距离排序
        orders_with_distance.sort(key=lambda x: x[1])
        
        # 重建队列
        self.order_queue.clear()
        for order, _ in orders_with_distance:
            self.order_queue.append(order)
            
        logger.info("Robot #%s 优化了订单队列，按距离排序: %s", 
                   self.robot_id, 
                   ", ".join([f"#{order.order_id}({order.table_id})" for order, _ in orders_with_distance]))

    def _return_to_parking(self) -> bool:
        """
        返回停靠点
        """
        self.returning_to_parking = True
        self.goal = self.parking_spot
        self.path = self.planner.find_path(self.position, self.goal) or []
        
        if not self.path:
            logger.error("无法规划返回停靠点的路径")
            self.returning_to_parking = False
            return False
            
        logger.info("Robot #%s 正在返回停靠点", self.robot_id)
        return True
        
    def _is_at_goal(self) -> bool:
        """
        判断机器人是否已经到达目标点（考虑容忍范围）
        """
        if not self.goal:
            return False
            
        # 计算当前位置到目标点的曼哈顿距离
        dist = abs(self.position[0] - self.goal[0]) + abs(self.position[1] - self.goal[1])
        
        # 如果距离在容忍范围内，则认为到达目标
        return dist <= self.GOAL_TOLERANCE

    # ---------------- 模拟循环 ---------------- #
    def tick(self) -> None:
        if not self.path:  # 没有剩余路径，处理下一步
            if self.returning_to_parking:
                # 已到达停靠点，重置状态
                if self._is_at_goal() or self.position == self.parking_spot:
                    self.returning_to_parking = False
                    self._calculate_delivery_cycle_time()
            elif self.current_order:
                # 已到达目标位置，完成当前订单
                if self._is_at_goal() or self.position == self.goal:
                    # 模拟送餐动作
                    logger.info("机器人 #%s 已到达目标位置，完成送餐", self.robot_id)
                    self._finish_delivery(success=True)
                    self._process_next_order()
            else:
                # 没有当前订单，尝试处理下一个
                self._process_next_order()
            return

        prev = self.position
        self.position, self.path = self.controller.step(
            self.position, self.path, self.goal
        )

        # 只有在实际移动时才记录轨迹
        if self.position != prev:
            self.path_history.append(self.position)
            
        # 检查是否已经到达目标点（考虑容忍范围）
        if self.goal and self._is_at_goal():
            # 到达目标，清空剩余路径
            self.path = []

    def _finish_delivery(self, *, success: bool) -> None:
        if not self.current_order:
            return
        if success:
            self.current_order.complete_delivery()
            self._stats["delivered"] += 1
            logger.info("订单 #%s 送达成功", self.current_order.order_id)
        else:
            self.current_order.fail_delivery()
            self._stats["failed"] += 1
            logger.error("订单 #%s 送达失败", self.current_order.order_id)
        self.current_order = None
        self.goal = None
        self.path = []

    def _calculate_delivery_cycle_time(self) -> None:
        """
        计算从停靠点出发到返回停靠点的总时间
        """
        if self.delivery_start_time is not None:
            end_time = self.all_assigned_orders[-1].delivery_end_time if self.all_assigned_orders else None
            if end_time:
                total_time = end_time - self.delivery_start_time
                self._stats["total_delivery_time"] = total_time
                self._stats["total_orders_delivered"] = len(self.all_assigned_orders)
                logger.info(f"Robot #{self.robot_id} 完成配送周期，总时间: {total_time:.2f}秒，送达订单: {len(self.all_assigned_orders)}")
            self.delivery_start_time = None

    # ---------------- 其他 ---------------- #
    def simulate(self, max_step: int = 500) -> None:
        step = 0
        while (self.path or self.current_order or self.order_queue or self.returning_to_parking) and step < max_step:
            self.tick()
            step += 1
        
        # 如果还没有返回停靠点，则返回
        if self.position != self.parking_spot and not self.returning_to_parking:
            self._return_to_parking()
            while self.path and step < max_step:
                self.tick()
                step += 1
                
        logging.debug("simulate finished: %s steps", step)

    def stats(self) -> dict:
        stats = dict(self._stats)
        # 添加额外统计信息
        if self.all_assigned_orders:
            stats["送达订单数"] = len([o for o in self.all_assigned_orders if o.status.name == "DELIVERED"])
            stats["失败订单数"] = len([o for o in self.all_assigned_orders if o.status.name == "FAILED"])
            stats["总路径长度"] = len(self.path_history)
            
        return stats


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
            knowledge_file=os.path.join(knowledge_dir, "restaurant_rule.json") if knowledge_dir else None,
        )
        self.controller = MotionController(layout, self.planner, rag=self.rag)
