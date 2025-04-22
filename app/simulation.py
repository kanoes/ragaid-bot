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

        # 性能优化：批处理订单，减少UI更新频率
        start_time = time.time()

        for i in range(num_orders):
            # 随机选择桌子
            table_id = random.choice(list(self.restaurant.layout.tables.keys()))
            order = make_order(i + 1, table_id)

            # 创建机器人并分配订单
            bot = build_robot(self.use_ai, self.restaurant.layout)
            success = bot.assign_order(order)

            if success:
                logger.info(f"订单 #{order.order_id} 分配到 Robot#{bot.robot_id}")
                bot.simulate()

                # 记录路径历史
                self.path_histories.append(
                    {
                        "order_id": order.order_id,
                        "robot_id": bot.robot_id,
                        "table_id": order.table_id,
                        "path": bot.path_history,
                    }
                )

                self.stats["delivered"] += 1
            else:
                logger.error(f"订单 #{order.order_id} 无法配送")
                self.stats["failed"] += 1

        # 添加路径统计数据
        if self.path_histories:
            path_lengths = [len(ph["path"]) for ph in self.path_histories]
            self.stats["平均路径长度"] = sum(path_lengths) / len(path_lengths)
            self.stats["最长路径"] = max(path_lengths)
            self.stats["最短路径"] = min(path_lengths)

        # 添加性能统计
        end_time = time.time()
        self.stats["模拟时间(秒)"] = round(end_time - start_time, 2)

        return self.stats, self.path_histories
