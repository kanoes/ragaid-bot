import time
from enum import Enum

class OrderStatus(Enum):
    """注文ステータスの列挙型"""
    WAITING = 0    # 準備待ち
    PREPARING = 1  # キッチンで準備中
    READY = 2      # 配送待ち準備完了
    DELIVERING = 3 # 配送中
    DELIVERED = 4  # 配達済み
    FAILED = 5     # 配送失敗

class Order:
    """レストランの注文を表すクラス"""
    def __init__(self, order_id, table_id, prep_time, items=None):
        self.order_id = order_id          # 注文ID
        self.table_id = table_id          # 対象テーブル番号
        self.prep_time = prep_time        # 準備時間（秒）
        self.items = items or []          # 注文内の料理リスト
        self.status = OrderStatus.WAITING # 注文の現在のステータス
        self.created_time = time.time()   # 注文作成時間
        self.prep_start_time = None       # 準備開始時間
        self.ready_time = None            # 準備完了時間
        self.delivery_start_time = None   # 配送開始時間
        self.delivery_end_time = None     # 配送完了時間
    
    def start_preparing(self):
        """注文の準備を開始"""
        self.status = OrderStatus.PREPARING
        self.prep_start_time = time.time()
        return True
    
    def finish_preparing(self):
        """注文の準備を完了"""
        self.status = OrderStatus.READY
        self.ready_time = time.time()
        return True
    
    def start_delivery(self):
        """注文の配送を開始"""
        if self.status != OrderStatus.READY:
            return False
        
        self.status = OrderStatus.DELIVERING
        self.delivery_start_time = time.time()
        return True
    
    def complete_delivery(self):
        """注文配送を完了"""
        if self.status != OrderStatus.DELIVERING:
            return False
        
        self.status = OrderStatus.DELIVERED
        self.delivery_end_time = time.time()
        return True
    
    def fail_delivery(self):
        """注文配送の失敗"""
        self.status = OrderStatus.FAILED
        return True
    
    def get_total_time(self):
        """注文の総処理時間を取得"""
        if self.delivery_end_time:
            return self.delivery_end_time - self.created_time
        return None
    
    def get_delivery_time(self):
        """注文の配送時間を取得"""
        if self.delivery_start_time and self.delivery_end_time:
            return self.delivery_end_time - self.delivery_start_time
        return None
    
    def is_ready_for_delivery(self):
        """注文が配送可能かどうかを確認"""
        return self.status == OrderStatus.READY
    
    def __str__(self):
        return f"注文#{self.order_id} - テーブル{self.table_id} - ステータス: {self.status.name}"

class OrderManager:
    """レストランの全注文を管理"""
    def __init__(self):
        self.orders = {}              # 全注文の辞書
        self.waiting_orders = []      # 準備待ちの注文キュー
        self.preparing_orders = []    # 準備中の注文リスト
        self.ready_orders = []        # 配送待ちの準備完了注文キュー
        self.delivering_orders = []   # 配送中の注文リスト
        self.completed_orders = []    # 完了した注文リスト
        self.failed_orders = []       # 配送失敗した注文リスト
        self.next_order_id = 1        # 次の注文ID
    
    def create_order(self, table_id, prep_time, items=None):
        """新しい注文を作成"""
        order_id = self.next_order_id
        self.next_order_id += 1
        
        order = Order(order_id, table_id, prep_time, items)
        self.orders[order_id] = order
        self.waiting_orders.append(order)
        
        print(f"新しい注文を作成: {order}")
        return order
    
    def start_preparing_next_order(self):
        """キューの次の注文の準備を開始"""
        if not self.waiting_orders:
            return None
        
        order = self.waiting_orders.pop(0)
        order.start_preparing()
        self.preparing_orders.append(order)
        
        print(f"注文の準備を開始: {order}")
        return order
    
    def finish_preparing_order(self, order_id):
        """注文の準備を完了"""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        if order.status != OrderStatus.PREPARING:
            return False
        
        order.finish_preparing()
        self.preparing_orders.remove(order)
        self.ready_orders.append(order)
        
        print(f"注文準備完了: {order}")
        return True
    
    def get_next_delivery_order(self):
        """次の配送が必要な注文を取得"""
        if not self.ready_orders:
            return None
        
        return self.ready_orders[0]
    
    def assign_order_to_robot(self, order_id, robot_id):
        """注文をロボットに配送割り当て"""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        if order.status != OrderStatus.READY:
            return False
        
        order.start_delivery()
        self.ready_orders.remove(order)
        self.delivering_orders.append(order)
        
        print(f"注文 #{order_id} をロボット #{robot_id} に配送割り当て")
        return True
    
    def complete_order_delivery(self, order_id):
        """注文配送を完了"""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        if order.status != OrderStatus.DELIVERING:
            return False
        
        order.complete_delivery()
        self.delivering_orders.remove(order)
        self.completed_orders.append(order)
        
        print(f"注文配送完了: {order}")
        print(f"配送時間: {order.get_delivery_time():.2f}秒, 総時間: {order.get_total_time():.2f}秒")
        return True
    
    def fail_order_delivery(self, order_id, reason="不明な理由"):
        """注文配送の失敗をマーク"""
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
        
        print(f"注文配送失敗: {order} - 理由: {reason}")
        return True
    
    def get_all_orders(self):
        """すべての注文を取得"""
        return list(self.orders.values())
    
    def get_statistics(self):
        """注文統計情報を取得"""
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
        キッチン準備プロセスのシミュレーション
        このメソッドはループ内で呼び出されることを想定
        """
        # 準備中の注文が完了したかどうかを確認
        current_time = time.time()
        completed_preparing = []
        
        for order in self.preparing_orders:
            elapsed_time = current_time - order.prep_start_time
            if elapsed_time >= order.prep_time:
                completed_preparing.append(order.order_id)
        
        # 完了した準備注文のステータスを更新
        for order_id in completed_preparing:
            self.finish_preparing_order(order_id)
        
        # 準備待ちの注文があり、現在準備中の注文が制限以下の場合、新しい注文を準備
        max_simultaneous_preparing = 3  # 最大同時準備3注文
        while self.waiting_orders and len(self.preparing_orders) < max_simultaneous_preparing:
            self.start_preparing_next_order()
        
        return len(completed_preparing) 