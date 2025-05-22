"""
机器人主体（动作层）
低层动作执行 & 障碍处理

该层只关心『从 A 走到 B 的每一步应该怎么走、遇到障碍怎么办』
不关心接单/路径规划/统计等上层任务
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional, Tuple, Protocol, runtime_checkable

from restaurant.restaurant_layout import RestaurantLayout
from robot.plan import IPathPlanner
from robot.rag.rag_module import RAGModule

logger = logging.getLogger(__name__)


@runtime_checkable
class IObstacleHandler(Protocol):
    """
    障碍处理策略接口
    """
    
    def handle_obstacle(
        self, 
        pos: Tuple[int, int],
        goal: Tuple[int, int] | None,
        obstacle: Tuple[int, int]
    ) -> List[Tuple[int, int]]:
        """
        处理遇到的障碍
        
        Args:
            pos: 当前位置
            goal: 目标位置
            obstacle: 障碍物位置
            
        Returns:
            新的路径，空列表表示需要等待或无法到达
        """
        ...


class DefaultObstacleHandler(IObstacleHandler):
    """
    默认障碍处理策略：仅尝试重新规划路径
    """
    
    def __init__(self, planner: IPathPlanner) -> None:
        self.planner = planner
    
    def handle_obstacle(
        self, 
        pos: Tuple[int, int],
        goal: Tuple[int, int] | None,
        obstacle: Tuple[int, int]
    ) -> List[Tuple[int, int]]:
        """基础策略：重新规划或放弃"""
        return self.planner.find_path(pos, goal) if goal else []


class RAGObstacleHandler(IObstacleHandler):
    """
    基于RAG的智能障碍处理策略
    """
    
    def __init__(self, planner: IPathPlanner, rag: RAGModule) -> None:
        self.planner = planner
        self.rag = rag
    
    def handle_obstacle(
        self, 
        pos: Tuple[int, int],
        goal: Tuple[int, int] | None,
        obstacle: Tuple[int, int]
    ) -> List[Tuple[int, int]]:
        """调用RAG决策层处理障碍"""
        decision = self.rag.make_decision(
            situation_type="obstacle",
            position=pos,
            goal=goal,
            context=obstacle,
        )
        logger.info("RAG 决策: %s", decision)
        
        # 英文动作关键字处理
        if decision == "reroute" and goal:
            # 重新规划路径
            return self.planner.find_path(pos, goal) or []
        if decision == "wait":
            # 等待一段时间后再尝试
            time.sleep(0.5)
            return []
        if decision == "report_unreachable":
            # 标记为不可达，返回空路径
            return []
            
        # 默认行为：尝试重新规划
        return self.planner.find_path(pos, goal) if goal else []


class MotionController:
    """
    机器人底盘控制器：一步移动 + 障碍应对
    """

    def __init__(
        self,
        layout: RestaurantLayout,
        planner: IPathPlanner,
        rag: Optional[RAGModule] = None,
    ) -> None:
        self.layout = layout
        self.planner = planner
        self.rag = rag
        
        # 根据是否有RAG选择合适的障碍处理器
        if rag and rag.is_ready():
            self.obstacle_handler = RAGObstacleHandler(planner, rag)
        else:
            self.obstacle_handler = DefaultObstacleHandler(planner)

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
        new_path = self.obstacle_handler.handle_obstacle(position, goal, next_pos)
        return position, new_path
