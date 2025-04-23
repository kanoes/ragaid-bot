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
import numpy as np
import time
import random

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
        
        # 新的统计数据结构
        self._stats = {
            "total_steps": 0,            # 总步数（路径长度）
            "total_delivery_time": 0,    # 总配送时间
            "total_orders": 0,           # 总订单数
            "total_batches": 0,          # 总批次数
            "current_batch_orders": 0,   # 当前批次订单数
        }
        # 历史配送记录
        self._delivery_history = []
        
        self.path_history: list[tuple[int, int]] = [self.position]
        self.returning_to_parking = False
        self.delivery_start_time = None
        self.all_assigned_orders = []
        self.is_ai_enhanced = isinstance(self, AIEnhancedRobot)  # 检查是否为智能机器人
        
        # 批处理控制参数
        self.batch_collection_time = 1.0  # 批量收集订单的时间窗口（秒）
        self.last_order_time = None      # 最后一次收到订单的时间
        self.batch_processing = False    # 是否正在批处理模式
        
        # 当前批次信息
        self.current_batch_start_time = None  # 当前批次开始时间
        self.current_batch_orders = []        # 当前批次订单
        self.current_batch_path_length = 0    # 当前批次路径长度

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
        
        # 记录最后收到订单的时间
        self.last_order_time = time.time()
        
        # 如果机器人空闲且未在批处理中，启动批处理定时器
        if not self.current_order and not self.returning_to_parking and not self.batch_processing:
            self.batch_processing = True
            logger.info("Robot #%s 开始订单批处理，等待更多订单...", self.robot_id)
            
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
        
        # 记录当前批次开始
        if not self.current_batch_start_time:
            self.current_batch_start_time = time.time()
            self._stats["total_batches"] += 1
            self.current_batch_orders = []
            self.current_batch_path_length = 0

        # 取出下一个订单
        order = self.order_queue.popleft()
        self.current_order = order
        
        # 添加到当前批次
        self.current_batch_orders.append(order)
        self._stats["current_batch_orders"] += 1

        # 获取桌子对应的送餐点
        delivery_pos = self.layout.get_delivery_point(order.table_id)
        if not delivery_pos:
            logger.error("桌号 %s 没有指定送餐点", order.table_id)
            self._finish_delivery(success=False)
            return False

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
        使用近似TSP（旅行商问题）算法，考虑整体路径长度而非简单距离
        目标：最小化总配送时间和路径长度
        """
        if len(self.order_queue) <= 1:
            return  # 没有订单或只有一个订单，不需要优化
        
        # 获取当前位置和所有订单的送餐点
        current_pos = self.position
        delivery_points = {}
        
        for order in self.order_queue:
            delivery_pos = self.layout.get_delivery_point(order.table_id)
            if delivery_pos:
                delivery_points[order.order_id] = delivery_pos
        
        if not delivery_points:
            return  # 没有有效的送餐点
            
        # 构建距离矩阵（包括从当前位置到各个送餐点，以及送餐点之间的距离）
        points = [current_pos] + list(delivery_points.values())
        n = len(points)
        
        # 计算路径长度函数，使用A*算法获取实际路径长度而非简单曼哈顿距离
        def get_path_length(start, end):
            path = self.planner.find_path(start, end)
            return len(path) if path else float('inf')
        
        # 构建距离矩阵
        distances = [[0 for _ in range(n)] for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i != j:
                    distances[i][j] = get_path_length(points[i], points[j])
        
        # 贪婪算法实现TSP近似解：每次选择最近的未访问点
        # 注意：从当前位置(索引0)开始
        current = 0  # 从当前位置开始
        unvisited = set(range(1, n))  # 索引1开始的送餐点
        tour = [current]
        
        # 贪婪构建路径
        while unvisited:
            nearest = min(unvisited, key=lambda j: distances[current][j])
            tour.append(nearest)
            unvisited.remove(nearest)
            current = nearest
            
        # 重新构建订单队列
        new_queue = []
        
        # 将路径转化为订单 (跳过索引0，那是机器人当前位置)
        for idx in tour[1:]:
            point = points[idx]
            # 找到对应此送餐点的订单
            for order in self.order_queue:
                if delivery_points.get(order.order_id) == point:
                    new_queue.append(order)
                    break
        
        # 更新订单队列
        self.order_queue.clear()
        for order in new_queue:
            self.order_queue.append(order)
            
        # 计算估计的总路径长度
        total_distance = sum(distances[tour[i]][tour[i+1]] for i in range(len(tour)-1))
        
        logger.info("Robot #%s 优化了订单队列，执行顺序: %s（估计总长度: %d）", 
                   self.robot_id, 
                   ", ".join([f"#{order.order_id}({order.table_id})" for order in new_queue]),
                   total_distance)

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
        # 记录步数
        self._stats["total_steps"] += 1
        
        # 检查批处理定时
        if self.batch_processing and self.last_order_time:
            if time.time() - self.last_order_time >= self.batch_collection_time:
                # 批处理时间窗口结束，开始处理订单
                logger.info("Robot #%s 批处理时间窗口结束，开始优化订单队列", self.robot_id)
                self.batch_processing = False
                self._process_next_order()
                
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
            elif not self.batch_processing:
                # 没有当前订单且不在批处理中，尝试处理下一个
                self._process_next_order()
            return

        prev = self.position
        self.position, self.path = self.controller.step(
            self.position, self.path, self.goal
        )

        # 只有在实际移动时才记录轨迹
        if self.position != prev:
            self.path_history.append(self.position)
            self.current_batch_path_length += 1
            
        # 检查是否已经到达目标点（考虑容忍范围）
        if self.goal and self._is_at_goal():
            # 到达目标，清空剩余路径
            self.path = []

    def _finish_delivery(self, *, success: bool) -> None:
        if not self.current_order:
            return
        if success:
            self.current_order.complete_delivery()
            self._stats["total_orders"] += 1
            logger.info("订单 #%s 送达成功", self.current_order.order_id)
        else:
            self.current_order.fail_delivery()
            logger.error("订单 #%s 送达失败", self.current_order.order_id)
        self.current_order = None
        self.goal = None
        self.path = []

    def _calculate_delivery_cycle_time(self) -> None:
        """
        计算从停靠点出发到返回停靠点的总时间和统计数据
        """
        if self.delivery_start_time is not None and self.current_batch_start_time is not None:
            end_time = time.time()
            batch_time = end_time - self.current_batch_start_time
            total_time = end_time - self.delivery_start_time
            
            # 更新统计数据
            self._stats["total_delivery_time"] += total_time
            self._stats["total_steps"] += len(self.path_history) - 1  # 减去初始位置
            
            # 记录本次配送批次的历史
            batch_record = {
                "batch_id": self._stats["total_batches"],
                "start_time": self.current_batch_start_time,
                "end_time": end_time,
                "duration": batch_time,
                "orders_count": self._stats["current_batch_orders"],
                "path_length": len(self.path_history) - 1,
                "is_ai_robot": self.is_ai_enhanced,
                "orders": [{"order_id": o.order_id, "table_id": o.table_id} for o in self.current_batch_orders]
            }
            self._delivery_history.append(batch_record)
            
            logger.info(f"Robot #{self.robot_id} 完成配送周期，总时间: {total_time:.2f}秒，" 
                       f"送达订单: {self._stats['current_batch_orders']}个，"
                       f"路径长度: {len(self.path_history) - 1}")
            
            # 重置当前批次数据
            self.delivery_start_time = None
            self.current_batch_start_time = None
            self.current_batch_orders = []
            self._stats["current_batch_orders"] = 0
            self.current_batch_path_length = 0

    # ---------------- 其他 ---------------- #
    def simulate(self, max_step: int = 500) -> None:
        step = 0
        # 如果处于批处理模式，先等待批处理窗口关闭
        if self.batch_processing:
            self.batch_processing = False
            if self.order_queue:
                logger.info("模拟开始：立即结束批处理窗口，开始送餐")
                self._process_next_order()
        
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
        """
        提供丰富的统计指标
        """
        stats = dict(self._stats)
        
        # 计算平均值
        if stats["total_batches"] > 0:
            stats["平均每批次订单数"] = stats["total_orders"] / stats["total_batches"]
            if stats["total_orders"] > 0:
                stats["平均每订单步数"] = stats["total_steps"] / stats["total_orders"]
        
        if stats["total_delivery_time"] > 0 and stats["total_orders"] > 0:
            stats["平均每订单配送时间"] = stats["total_delivery_time"] / stats["total_orders"]
            
        # 添加路径信息
        stats["总路径长度"] = len(self.path_history) - 1  # 减去初始位置
        
        # 添加机器人类型信息
        stats["机器人类型"] = "智能RAG机器人" if self.is_ai_enhanced else "基础机器人"
        
        # 添加历史配送记录
        stats["配送历史"] = self._delivery_history
            
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
