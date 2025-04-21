"""
模拟引擎
"""
import random

from .utils import build_robot, make_order
from .constants import logger

class SimulationEngine:
    """送餐模拟引擎"""
    
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
        
    def run(self, num_orders):
        """
        运行模拟
        
        Args:
            num_orders: 订单数量
            
        Returns:
            dict: 模拟统计结果
        """
        self.stats = {"delivered": 0, "failed": 0}
        
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
                
            #     # 可视化路径
            #     animate_robot_path(
            #         bot.path_history,
            #         title=f"Robot#{bot.robot_id} Order#{order.order_id}",
            #         fps=4,
            #     )
            #     self.stats["delivered"] += 1
            # else:
            #     logger.error(f"订单 #{order.order_id} 无法配送")
            #     self.stats["failed"] += 1
                
        return self.stats 