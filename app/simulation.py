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
        self.stats = {
            "total_steps": 0,
            "total_orders": 0,
            "total_batches": 0,
            "total_delivery_time": 0
        }
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
        self.stats = {
            "total_steps": 0,
            "total_orders": 0,
            "total_batches": 0,
            "total_delivery_time": 0
        }
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
        max_attempts = num_orders * 3
        
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
        
        # 执行模拟
        if self.assigned_orders:
            bot.simulate()
            
            # 记录路径历史
            self.path_histories.append(
                {
                    "robot_id": bot.robot_id,
                    "path": bot.path_history,
                    "orders": [{"order_id": order.order_id, "table_id": order.table_id} for order in bot.all_assigned_orders]
                }
            )
            
            # 获取机器人统计信息，使用新的统计结构
            robot_stats = bot.stats()
            
            # 复制主要统计数据
            for key in ["total_steps", "total_orders", "total_batches", "total_delivery_time"]:
                if key in robot_stats:
                    self.stats[key] = robot_stats[key]
            
            # 复制计算的平均值
            for key in ["平均每批次订单数", "平均每订单步数", "平均每订单配送时间"]:
                if key in robot_stats:
                    self.stats[key] = robot_stats[key]
            
            # 添加机器人类型信息
            self.stats["机器人类型"] = robot_stats.get("机器人类型", "基础机器人")
            
            # 添加总路径长度
            self.stats["总路径长度"] = robot_stats.get("总路径长度", 0)
            
            # 添加配送历史记录
            self.stats["配送历史"] = robot_stats.get("配送历史", [])

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
