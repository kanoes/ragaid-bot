import time
from enum import Enum

class OrderStatus(Enum):
    """豕ｨ譁・せ繝・・繧ｿ繧ｹ縺ｮ蛻玲嫌蝙・""
    WAITING = 0    # 貅門ｙ蠕・■
    PREPARING = 1  # 繧ｭ繝・メ繝ｳ縺ｧ貅門ｙ荳ｭ
    READY = 2      # 驟埼∝ｾ・■貅門ｙ螳御ｺ・
    DELIVERING = 3 # 驟埼∽ｸｭ
    DELIVERED = 4  # 驟埼＃貂医∩
    FAILED = 5     # 驟埼∝､ｱ謨・

class Order:
    """繝ｬ繧ｹ繝医Λ繝ｳ縺ｮ豕ｨ譁・ｒ陦ｨ縺吶け繝ｩ繧ｹ"""
    def __init__(self, order_id, table_id, prep_time, items=None):
        self.order_id = order_id          # 豕ｨ譁⑩D
        self.table_id = table_id          # 蟇ｾ雎｡繝・・繝悶Ν逡ｪ蜿ｷ
        self.prep_time = prep_time        # 貅門ｙ譎る俣・育ｧ抵ｼ・
        self.items = items or []          # 豕ｨ譁・・縺ｮ譁咏炊繝ｪ繧ｹ繝・
        self.status = OrderStatus.WAITING # 豕ｨ譁・・迴ｾ蝨ｨ縺ｮ繧ｹ繝・・繧ｿ繧ｹ
        self.created_time = time.time()   # 豕ｨ譁・ｽ懈・譎る俣
        self.prep_start_time = None       # 貅門ｙ髢句ｧ区凾髢・
        self.ready_time = None            # 貅門ｙ螳御ｺ・凾髢・
        self.delivery_start_time = None   # 驟埼・幕蟋区凾髢・
        self.delivery_end_time = None     # 驟埼∝ｮ御ｺ・凾髢・
    
    def start_preparing(self):
        """豕ｨ譁・・貅門ｙ繧帝幕蟋・""
        self.status = OrderStatus.PREPARING
        self.prep_start_time = time.time()
        return True
    
    def finish_preparing(self):
        """豕ｨ譁・・貅門ｙ繧貞ｮ御ｺ・""
        self.status = OrderStatus.READY
        self.ready_time = time.time()
        return True
    
    def start_delivery(self):
        """豕ｨ譁・・驟埼√ｒ髢句ｧ・""
        if self.status != OrderStatus.READY:
            return False
        
        self.status = OrderStatus.DELIVERING
        self.delivery_start_time = time.time()
        return True
    
    def complete_delivery(self):
        """豕ｨ譁・・騾√ｒ螳御ｺ・""
        if self.status != OrderStatus.DELIVERING:
            return False
        
        self.status = OrderStatus.DELIVERED
        self.delivery_end_time = time.time()
        return True
    
    def fail_delivery(self):
        """豕ｨ譁・・騾√・螟ｱ謨・""
        self.status = OrderStatus.FAILED
        return True
    
    def get_total_time(self):
        """豕ｨ譁・・邱丞・逅・凾髢薙ｒ蜿門ｾ・""
        if self.delivery_end_time:
            return self.delivery_end_time - self.created_time
        return None
    
    def get_delivery_time(self):
        """豕ｨ譁・・驟埼∵凾髢薙ｒ蜿門ｾ・""
        if self.delivery_start_time and self.delivery_end_time:
            return self.delivery_end_time - self.delivery_start_time
        return None
    
    def is_ready_for_delivery(self):
        """豕ｨ譁・′驟埼∝庄閭ｽ縺九←縺・°繧堤｢ｺ隱・""
        return self.status == OrderStatus.READY
    
    def __str__(self):
        return f"豕ｨ譁・{self.order_id} - 繝・・繝悶Ν{self.table_id} - 繧ｹ繝・・繧ｿ繧ｹ: {self.status.name}"

class OrderManager:
    """繝ｬ繧ｹ繝医Λ繝ｳ縺ｮ蜈ｨ豕ｨ譁・ｒ邂｡逅・""
    def __init__(self):
        self.orders = {}              # 蜈ｨ豕ｨ譁・・霎樊嶌
        self.waiting_orders = []      # 貅門ｙ蠕・■縺ｮ豕ｨ譁・く繝･繝ｼ
        self.preparing_orders = []    # 貅門ｙ荳ｭ縺ｮ豕ｨ譁・Μ繧ｹ繝・
        self.ready_orders = []        # 驟埼∝ｾ・■縺ｮ貅門ｙ螳御ｺ・ｳｨ譁・く繝･繝ｼ
        self.delivering_orders = []   # 驟埼∽ｸｭ縺ｮ豕ｨ譁・Μ繧ｹ繝・
        self.completed_orders = []    # 螳御ｺ・＠縺滓ｳｨ譁・Μ繧ｹ繝・
        self.failed_orders = []       # 驟埼∝､ｱ謨励＠縺滓ｳｨ譁・Μ繧ｹ繝・
        self.next_order_id = 1        # 谺｡縺ｮ豕ｨ譁⑩D
    
    def create_order(self, table_id, prep_time, items=None):
        """譁ｰ縺励＞豕ｨ譁・ｒ菴懈・"""
        order_id = self.next_order_id
        self.next_order_id += 1
        
        order = Order(order_id, table_id, prep_time, items)
        self.orders[order_id] = order
        self.waiting_orders.append(order)
        
        print(f"譁ｰ縺励＞豕ｨ譁・ｒ菴懈・: {order}")
        return order
    
    def start_preparing_next_order(self):
        """繧ｭ繝･繝ｼ縺ｮ谺｡縺ｮ豕ｨ譁・・貅門ｙ繧帝幕蟋・""
        if not self.waiting_orders:
            return None
        
        order = self.waiting_orders.pop(0)
        order.start_preparing()
        self.preparing_orders.append(order)
        
        print(f"豕ｨ譁・・貅門ｙ繧帝幕蟋・ {order}")
        return order
    
    def finish_preparing_order(self, order_id):
        """豕ｨ譁・・貅門ｙ繧貞ｮ御ｺ・""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        if order.status != OrderStatus.PREPARING:
            return False
        
        order.finish_preparing()
        self.preparing_orders.remove(order)
        self.ready_orders.append(order)
        
        print(f"豕ｨ譁・ｺ門ｙ螳御ｺ・ {order}")
        return True
    
    def get_next_delivery_order(self):
        """谺｡縺ｮ驟埼√′蠢・ｦ√↑豕ｨ譁・ｒ蜿門ｾ・""
        if not self.ready_orders:
            return None
        
        return self.ready_orders[0]
    
    def assign_order_to_robot(self, order_id, robot_id):
        """豕ｨ譁・ｒ繝ｭ繝懊ャ繝医↓驟埼∝牡繧雁ｽ薙※"""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        if order.status != OrderStatus.READY:
            return False
        
        order.start_delivery()
        self.ready_orders.remove(order)
        self.delivering_orders.append(order)
        
        print(f"豕ｨ譁・#{order_id} 繧偵Ο繝懊ャ繝・#{robot_id} 縺ｫ驟埼∝牡繧雁ｽ薙※")
        return True
    
    def complete_order_delivery(self, order_id):
        """豕ｨ譁・・騾√ｒ螳御ｺ・""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        if order.status != OrderStatus.DELIVERING:
            return False
        
        order.complete_delivery()
        self.delivering_orders.remove(order)
        self.completed_orders.append(order)
        
        print(f"豕ｨ譁・・騾∝ｮ御ｺ・ {order}")
        print(f"驟埼∵凾髢・ {order.get_delivery_time():.2f}遘・ 邱乗凾髢・ {order.get_total_time():.2f}遘・)
        return True
    
    def fail_order_delivery(self, order_id, reason="荳肴・縺ｪ逅・罰"):
        """豕ｨ譁・・騾√・螟ｱ謨励ｒ繝槭・繧ｯ"""
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
        
        print(f"豕ｨ譁・・騾∝､ｱ謨・ {order} - 逅・罰: {reason}")
        return True
    
    def get_all_orders(self):
        """縺吶∋縺ｦ縺ｮ豕ｨ譁・ｒ蜿門ｾ・""
        return list(self.orders.values())
    
    def get_statistics(self):
        """豕ｨ譁・ｵｱ險域ュ蝣ｱ繧貞叙蠕・""
        total_orders = len(self.orders)
        completed_orders = len(self.completed_orders)
        failed_orders = len(self.failed_orders)
        success_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
        
        avg_delivery_time = 0
        if completed_orders > 0:
            total_delivery_time = sum(order.get_delivery_time() or 0 for order in self.completed_orders)
            avg_delivery_time = total_delivery_time / completed_orders
        
        return {
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "failed_orders": failed_orders,
            "success_rate": success_rate,
            "avg_delivery_time": avg_delivery_time
        }
    
    def process_kitchen_simulation(self):
        """
        繧ｭ繝・メ繝ｳ貅門ｙ繝励Ο繧ｻ繧ｹ縺ｮ繧ｷ繝溘Η繝ｬ繝ｼ繧ｷ繝ｧ繝ｳ
        縺薙・繝｡繧ｽ繝・ラ縺ｯ繝ｫ繝ｼ繝怜・縺ｧ蜻ｼ縺ｳ蜃ｺ縺輔ｌ繧九％縺ｨ繧呈Φ螳・
        """
        # 貅門ｙ荳ｭ縺ｮ豕ｨ譁・′螳御ｺ・＠縺溘°縺ｩ縺・°繧堤｢ｺ隱・
        current_time = time.time()
        completed_preparing = []
        
        for order in self.preparing_orders:
            elapsed_time = current_time - order.prep_start_time
            if elapsed_time >= order.prep_time:
                completed_preparing.append(order.order_id)
        
        # 螳御ｺ・＠縺滓ｺ門ｙ豕ｨ譁・・繧ｹ繝・・繧ｿ繧ｹ繧呈峩譁ｰ
        for order_id in completed_preparing:
            self.finish_preparing_order(order_id)
        
        # 貅門ｙ蠕・■縺ｮ豕ｨ譁・′縺ゅｊ縲∫樟蝨ｨ貅門ｙ荳ｭ縺ｮ豕ｨ譁・′蛻ｶ髯蝉ｻ･荳九・蝣ｴ蜷医∵眠縺励＞豕ｨ譁・ｒ貅門ｙ
        max_simultaneous_preparing = 3  # 譛螟ｧ蜷梧凾貅門ｙ3豕ｨ譁・
        while self.waiting_orders and len(self.preparing_orders) < max_simultaneous_preparing:
            self.start_preparing_next_order()
        
        return len(completed_preparing) 
