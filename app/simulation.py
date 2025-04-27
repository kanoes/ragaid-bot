"""
シミュレーションエンジン
"""

import random
import time
from .utils import build_robot, make_order
from .constants import logger
from .state import get_next_batch_id


class SimulationEngine:
    """
    配達シミュレーションエンジン
    """

    def __init__(self, restaurant, use_ai=False):
        """
        シミュレーションエンジンの初期化

        Args:
            restaurant: レストランインスタンス
            use_ai: AI強化ロボットを使用するかどうか
        """
        self.restaurant = restaurant
        self.use_ai = use_ai
        self.stats = {
            "total_steps": 0,
            "total_orders": 0,
            "total_time": 0,     # 総配達時間（現在は総ステップ数と同じ）
            "avg_waiting_time": 0  # 追加：注文の平均待ち時間
        }
        self.path_histories = []
        self.assigned_orders = []

    def run(self, num_orders):
        """
        シミュレーションの実行

        Args:
            num_orders: 注文数

        Returns:
            dict: シミュレーション統計結果
        """
        # グローバルバッチIDを取得
        batch_id = get_next_batch_id()
        
        self.stats = {
            "total_steps": 0,
            "total_orders": 0,
            "total_time": 0,     
            "avg_waiting_time": 0  
        }
        self.path_histories = []
        self.assigned_orders = []

        # パフォーマンス最適化：注文をバッチ処理し、UI更新頻度を減らす
        start_time = time.time()
        
        # ロボットインスタンスを作成
        bot = build_robot(self.use_ai, self.restaurant.layout, restaurant_name=self.restaurant.name)

        # 割り当て済み注文のテーブルを追跡
        assigned_tables = set()
        
        # 利用可能な全テーブルを取得
        available_tables = list(self.restaurant.layout.tables.keys())
        if not available_tables:
            logger.error("レストランに利用可能なテーブルがありません")
            return self.stats, self.path_histories
            
        # 全ての注文を生成して割り当てる
        orders_created = 0
        attempts = 0
        max_attempts = num_orders * 3
        
        while orders_created < num_orders and attempts < max_attempts:
            attempts += 1
            
            # テーブルをランダムに選択、重複を避ける
            available_tables_list = [t for t in available_tables if t not in assigned_tables]
            if not available_tables_list:
                logger.info("全てのテーブルに注文が割り当てられており、これ以上作成できません")
                break
                
            table_id = random.choice(available_tables_list)
            order = make_order(orders_created + 1, table_id)
            
            # ロボットに注文を割り当て
            success = bot.assign_order(order)
            
            if success:
                logger.info(f"注文 #{order.order_id} を Robot#{bot.robot_id} に割り当てました, テーブル番号: {table_id}")
                self.assigned_orders.append(order)
                assigned_tables.add(table_id)
                orders_created += 1
        
        # シミュレーション実行
        if self.assigned_orders:
            bot.simulate()
            
            # 経路履歴を記録
            order_info = []
            for order in bot.all_assigned_orders:
                order_data = {
                    "order_id": order.order_id, 
                    "table_id": order.table_id
                }
                # 配達順序情報を追加（あれば）
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
            
            # ロボット統計情報を取得（新しい統計構造を使用）
            robot_stats = bot.stats()
            
            # 主要な統計データをコピー
            for key in ["total_steps", "total_orders", "total_time", "avg_waiting_time"]:
                if key in robot_stats:
                    self.stats[key] = robot_stats[key]
            
            # ロボットタイプ情報を追加
            self.stats["ロボットタイプ"] = robot_stats.get("ロボットタイプ", "基本ロボット")
            
            # 総配達距離を追加
            self.stats["総配達距離"] = robot_stats.get("総配達距離", 0)
            
            # 配達履歴を処理
            simplified_history = []
            for record in robot_stats.get("delivery_history", []):
                simplified_record = {
                    "batch_id": batch_id,
                    "total_time": record.get("total_time", 0),
                    "path_length": record.get("path_length", 0),
                    "avg_waiting_time": record.get("avg_waiting_time", 0),
                    "ロボットタイプ": record.get("ロボットタイプ", "基本ロボット"),
                    "レストランレイアウト": record.get("レストランレイアウト", self.restaurant.name)
                }
                simplified_history.append(simplified_record)
            
            # 配達履歴が存在しない場合、基本情報を作成
            if not simplified_history and self.path_histories:
                simplified_record = {
                    "batch_id": batch_id,
                    "total_time": self.stats.get("total_time", 0), 
                    "path_length": self.stats.get("総配達距離", 0),
                    "avg_waiting_time": self.stats.get("avg_waiting_time", 0),
                    "ロボットタイプ": self.stats.get("ロボットタイプ", "基本ロボット"),
                    "レストランレイアウト": self.restaurant.name
                }
                simplified_history.append(simplified_record)
                
            self.stats["配達履歴"] = simplified_history

        # 経路統計データを追加
        if self.path_histories:
            path_lengths = [len(ph["path"]) for ph in self.path_histories]
            self.stats["平均経路長"] = sum(path_lengths) / len(path_lengths)
            self.stats["最長経路"] = max(path_lengths)
            self.stats["最短経路"] = min(path_lengths)
        
        # 割り当て注文数の統計を追加
        self.stats["割り当て注文総数"] = len(self.assigned_orders)

        return self.stats, self.path_histories
