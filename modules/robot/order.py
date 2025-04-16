"""
订单管理模块
包含订单状态枚举、订单类和订单管理器类，用于餐厅订单的创建、分配和状态跟踪。
"""
import time
from enum import Enum

class OrderStatus(Enum):
    """订单状态的分类"""
    WAITING = 0    # 准备等待
    PREPARING = 1  # 厨房中准备中
    READY = 2      # 配送等待准备完成
    DELIVERING = 3 # 配送中
    DELIVERED = 4  # 配送完成
    FAILED = 5     # 配送失败

class Order:
    """餐厅的订单类"""
    def __init__(self, order_id, table_id, prep_time, items=None):
        self.order_id = order_id          # 订单ID
        self.table_id = table_id          # 目标桌号
        self.prep_time = prep_time        # 准备时间（秒）
        self.items = items or []          # 订单中的料理列表
        self.status = OrderStatus.WAITING # 订单当前的状态
        self.created_time = time.time()   # 订单创建时间
        self.prep_start_time = None       # 准备开始时间
        self.ready_time = None            # 准备完成时间
        self.delivery_start_time = None   # 配送开始时间
        self.delivery_end_time = None     # 配送完成时间
    
    def start_preparing(self):
        """开始准备订单"""
        self.status = OrderStatus.PREPARING
        self.prep_start_time = time.time()
        return True
    
    def finish_preparing(self):
        """完成订单准备"""
        self.status = OrderStatus.READY
        self.ready_time = time.time()
        return True
    
    def start_delivery(self):
        """开始订单配送"""
        if self.status != OrderStatus.READY:
            return False
        
        self.status = OrderStatus.DELIVERING
        self.delivery_start_time = time.time()
        return True
    
    def complete_delivery(self):
        """完成订单配送"""
        if self.status != OrderStatus.DELIVERING:
            return False
        
        self.status = OrderStatus.DELIVERED
        self.delivery_end_time = time.time()
        return True
    
    def fail_delivery(self):
        """订单配送失败"""
        self.status = OrderStatus.FAILED
        return True
    
    def get_total_time(self):
        """获取订单总处理时间"""
        if self.delivery_end_time:
            return self.delivery_end_time - self.created_time
        return None
    
    def get_delivery_time(self):
        """获取订单配送时间"""
        if self.delivery_start_time and self.delivery_end_time:
            return self.delivery_end_time - self.delivery_start_time
        return None
    
    def is_ready_for_delivery(self):
        """确认订单是否可以配送"""
        return self.status == OrderStatus.READY
    
    def __str__(self):
        return f"订单{self.order_id} - 桌号{self.table_id} - 状态: {self.status.name}"

class OrderManager:
    """餐厅的全部订单管理"""
    def __init__(self):
        self.orders = {}              # 所有订单字典
        self.waiting_orders = []      # 准备等待的订单队列
        self.preparing_orders = []    # 准备中的订单列表
        self.ready_orders = []        # 配送等待的准备完成订单队列
        self.delivering_orders = []   # 配送中的订单列表
        self.completed_orders = []    # 完成的订单列表
        self.failed_orders = []       # 配送失败的订单列表
        self.next_order_id = 1        # 下一个订单ID
    
    def create_order(self, table_id, prep_time, items=None):
        """创建新订单"""
        order_id = self.next_order_id
        self.next_order_id += 1
        
        order = Order(order_id, table_id, prep_time, items)
        self.orders[order_id] = order
        self.waiting_orders.append(order)
        
        print(f"创建新订单: {order}")
        return order
    
    def start_preparing_next_order(self):
        """开始准备队列中的下一个订单"""
        if not self.waiting_orders:
            return None
        
        order = self.waiting_orders.pop(0)
        order.start_preparing()
        self.preparing_orders.append(order)
        
        print(f"开始准备订单: {order}")
        return order
    
    def finish_preparing_order(self, order_id):
        """完成订单准备"""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        if order.status != OrderStatus.PREPARING:
            return False
        
        order.finish_preparing()
        self.preparing_orders.remove(order)
        self.ready_orders.append(order)
        
        print(f"订单准备完成: {order}")
        return True
    
    def get_next_delivery_order(self):
        """获取需要下一个配送的订单"""
        if not self.ready_orders:
            return None
        
        return self.ready_orders[0]
    
    def assign_order_to_robot(self, order_id, robot_id):
        """将订单分配给机器人配送"""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        if order.status != OrderStatus.READY:
            return False
        
        order.start_delivery()
        self.ready_orders.remove(order)
        self.delivering_orders.append(order)
        
        print(f"订单#{order_id} 分配给机器人#{robot_id} 配送")
        return True
    
    def complete_order_delivery(self, order_id):
        """完成订单配送"""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        if order.status != OrderStatus.DELIVERING:
            return False
        
        order.complete_delivery()
        self.delivering_orders.remove(order)
        self.completed_orders.append(order)
        
        print(f"订单配送完成: {order}")
        print(f"配送时间: {order.get_delivery_time():.2f}秒, 总时间: {order.get_total_time():.2f}秒")
        return True
    
    def fail_order_delivery(self, order_id, reason="未知原因"):
        """标记订单配送失败"""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        if order.status not in [OrderStatus.READY, OrderStatus.DELIVERING]:
            return False
        
        order.fail_delivery()
        
        if order in self.ready_orders:
            self.ready_orders.remove(order)
        if order in self.delivering_orders:
            self.delivering_orders.remove(order)
            
        self.failed_orders.append(order)
        
        print(f"订单配送失败: {order} - 原因: {reason}")
        return True
    
    def get_all_orders(self):
        """获取所有订单"""
        return list(self.orders.values())
    
    def get_statistics(self):
        """获取订单统计信息"""
        total_orders = len(self.orders)
        completed_orders = len(self.completed_orders)
        failed_orders = len(self.failed_orders)
        waiting_orders = len(self.waiting_orders) + len(self.preparing_orders) + len(self.ready_orders)
        
        # 计算平均配送时间
        delivery_times = [order.get_delivery_time() for order in self.completed_orders if order.get_delivery_time()]
        avg_delivery_time = sum(delivery_times) / len(delivery_times) if delivery_times else 0
        
        # 计算平均总时间
        total_times = [order.get_total_time() for order in self.completed_orders if order.get_total_time()]
        avg_total_time = sum(total_times) / len(total_times) if total_times else 0
        
        return {
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "failed_orders": failed_orders,
            "waiting_orders": waiting_orders,
            "success_rate": completed_orders / total_orders * 100 if total_orders else 0,
            "avg_delivery_time": avg_delivery_time,
            "avg_total_time": avg_total_time
        }
    
    def process_kitchen_simulation(self):
        """
        厨房准备过程的模拟
        这个方法应该在循环中被调用
        """
        # 检查准备中的订单是否完成
        current_time = time.time()
        completed_preparing = []
        
        for order in self.preparing_orders:
            elapsed_time = current_time - order.prep_start_time
            if elapsed_time >= order.prep_time:
                completed_preparing.append(order.order_id)
        
        # 更新已完成准备的订单状态
        for order_id in completed_preparing:
            self.finish_preparing_order(order_id)
        
        # 如果有等待中的订单且当前准备中的订单数小于上限，开始准备新订单
        max_simultaneous_preparing = 3  # 最多同时准备3个订单
        while self.waiting_orders and len(self.preparing_orders) < max_simultaneous_preparing:
            self.start_preparing_next_order()
        
        return len(completed_preparing) 