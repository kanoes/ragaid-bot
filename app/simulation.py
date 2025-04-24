"""
模拟引擎
"""

import random
import time
from .utils import build_robot, make_order
from .constants import logger
from .state import get_next_batch_id


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
            "total_time": 0,     # 总配送时间，目前与总步数相同
            "avg_waiting_time": 0  # 新增：平均订单等待时间
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
        # 获取全局批次ID
        batch_id = get_next_batch_id()
        
        self.stats = {
            "total_steps": 0,
            "total_orders": 0,
            "total_time": 0,     # 总配送时间，目前与总步数相同
            "avg_waiting_time": 0  # 新增：平均订单等待时间
        }
        self.path_histories = []
        self.assigned_orders = []

        # 性能优化：批处理订单，减少UI更新频率
        start_time = time.time()
        
        # 创建一个机器人实例
        bot = build_robot(self.use_ai, self.restaurant.layout, restaurant_name=self.restaurant.name)

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
            order_info = []
            for order in bot.all_assigned_orders:
                order_data = {
                    "order_id": order.order_id, 
                    "table_id": order.table_id
                }
                # 添加配送顺序信息（如果有）
                if hasattr(order, "delivery_sequence") and order.delivery_sequence is not None:
                    order_data["delivery_sequence"] = order.delivery_sequence
                order_info.append(order_data)
                
            self.path_histories.append(
                {
                    "robot_id": bot.robot_id,
                    "path": bot.path_history,
                    "orders": order_info
                }
            )
            
            # 获取机器人统计信息，使用新的统计结构
            robot_stats = bot.stats()
            
            # 复制关键统计数据
            for key in ["total_steps", "total_orders", "total_time", "avg_waiting_time"]:
                if key in robot_stats:
                    self.stats[key] = robot_stats[key]
            
            # 添加机器人类型信息
            self.stats["机器人类型"] = robot_stats.get("机器人类型", "基础机器人")
            
            # 添加总配送路程
            self.stats["总配送路程"] = robot_stats.get("总配送路程", 0)
            
            # 处理配送历史
            simplified_history = []
            for record in robot_stats.get("delivery_history", []):
                simplified_record = {
                    "batch_id": batch_id,
                    "total_time": record.get("total_time", 0),
                    "path_length": record.get("path_length", 0),
                    "avg_waiting_time": record.get("avg_waiting_time", 0),
                    "机器人类型": record.get("机器人类型", "基础机器人"),
                    "餐厅布局": record.get("餐厅布局", self.restaurant.name)
                }
                simplified_history.append(simplified_record)
            
            # 如果没有配送历史记录，创建一个基本记录
            if not simplified_history and self.path_histories:
                simplified_record = {
                    "batch_id": batch_id,
                    "total_time": self.stats.get("total_time", 0), 
                    "path_length": self.stats.get("总配送路程", 0),
                    "avg_waiting_time": self.stats.get("avg_waiting_time", 0),
                    "机器人类型": self.stats.get("机器人类型", "基础机器人"),
                    "餐厅布局": self.restaurant.name
                }
                simplified_history.append(simplified_record)
                
            self.stats["配送历史"] = simplified_history

        # 添加路径统计数据
        if self.path_histories:
            path_lengths = [len(ph["path"]) for ph in self.path_histories]
            self.stats["平均路径长度"] = sum(path_lengths) / len(path_lengths)
            self.stats["最长路径"] = max(path_lengths)
            self.stats["最短路径"] = min(path_lengths)
        
        # 添加分配订单的统计
        self.stats["分配订单总数"] = len(self.assigned_orders)

        return self.stats, self.path_histories
