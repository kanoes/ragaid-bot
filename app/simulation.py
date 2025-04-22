"""
模拟引擎
"""

import random
import time
from .utils import build_robot, make_order
from .constants import logger


class SimulationEngine:
    """
    送餐模拟引擎
    """

    def __init__(self, restaurant, use_ai=False):
        """
        初始化模拟引擎

        Args:
            restaurant: 餐厅实例
            use_ai: 是否使用AI增强机器人
        """
        self.restaurant = restaurant
        self.use_ai = use_ai
        self.stats = {"delivered": 0, "failed": 0}
        self.path_histories = []
        self.assigned_orders = []

    def run(self, num_orders):
        """
        运行模拟

        Args:
            num_orders: 订单数量

        Returns:
            dict: 模拟统计结果
        """
        self.stats = {"delivered": 0, "failed": 0}
        self.path_histories = []
        self.assigned_orders = []

        # 性能优化：批处理订单，减少UI更新频率
        start_time = time.time()
        
        # 创建一个机器人实例
        bot = build_robot(self.use_ai, self.restaurant.layout)

        # 跟踪已分配订单的桌子
        assigned_tables = set()
        
        # 获取所有可用桌子
        available_tables = list(self.restaurant.layout.tables.keys())
        if not available_tables:
            logger.error("餐厅没有可用桌子")
            return self.stats, self.path_histories
            
        # 生成并分配所有订单
        orders_created = 0
        attempts = 0
        max_attempts = num_orders * 3  # 防止死循环
        
        while orders_created < num_orders and attempts < max_attempts:
            attempts += 1
            
            # 随机选择桌子，确保不重复
            available_tables_list = [t for t in available_tables if t not in assigned_tables]
            if not available_tables_list:
                logger.info("所有桌子都已被分配订单，无法创建更多订单")
                break
                
            table_id = random.choice(available_tables_list)
            order = make_order(orders_created + 1, table_id)
            
            # 将订单分配给机器人
            success = bot.assign_order(order)
            
            if success:
                logger.info(f"订单 #{order.order_id} 分配到 Robot#{bot.robot_id}, 桌号: {table_id}")
                self.assigned_orders.append(order)
                assigned_tables.add(table_id)
                orders_created += 1
            else:
                logger.error(f"订单 #{order.order_id} 无法配送")
                self.stats["failed"] += 1
        
        # 执行模拟
        if self.assigned_orders:
            bot.simulate()
            
            # 记录路径历史
            self.path_histories.append(
                {
                    "robot_id": bot.robot_id,
                    "path": bot.path_history,
                    "orientation": getattr(bot, "orientation", 90),  # 保存机器人的朝向
                    "orders": [{"order_id": order.order_id, "table_id": order.table_id} for order in bot.all_assigned_orders]
                }
            )
            
            # 获取机器人统计信息
            robot_stats = bot.stats()
            self.stats["delivered"] = robot_stats["delivered"]
            self.stats["failed"] = robot_stats.get("failed", 0)
            
            # 添加配送周期时间统计
            if "total_delivery_time" in robot_stats:
                self.stats["配送周期时间(秒)"] = round(robot_stats["total_delivery_time"], 2)
                self.stats["配送订单数量"] = robot_stats.get("total_orders_delivered", 0)
                if self.stats["配送订单数量"] > 0:
                    self.stats["平均每单配送时间(秒)"] = round(
                        robot_stats["total_delivery_time"] / self.stats["配送订单数量"], 2
                    )

        # 添加路径统计数据
        if self.path_histories:
            path_lengths = [len(ph["path"]) for ph in self.path_histories]
            self.stats["平均路径长度"] = sum(path_lengths) / len(path_lengths)
            self.stats["最长路径"] = max(path_lengths)
            self.stats["最短路径"] = min(path_lengths)

        # 添加性能统计
        end_time = time.time()
        self.stats["模拟时间(秒)"] = round(end_time - start_time, 2)
        
        # 添加分配订单的统计
        self.stats["分配订单总数"] = len(self.assigned_orders)

        return self.stats, self.path_histories
