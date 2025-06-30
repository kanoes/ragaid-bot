"""
ロボット本体（スケジューリング層）

階層構造
--------
* PathPlanner             — 計画層（robot.path_planner）
* Order / OrderManager    — 注文層（robot.order）
* MotionController        — アクション層（robot.motion_controller）
* Robot / AIEnhancedRobot — スケジューリング層（本ファイル）
* RobotStatistics         - 統計層（本ファイル）
"""

from __future__ import annotations

import logging
import os
from typing import List, Optional, Tuple, Deque, Dict, Any, Protocol, runtime_checkable
from collections import deque
import time

from restaurant.restaurant_layout import RestaurantLayout
from robot.motion_controller import MotionController
from robot.plan import PathPlanner, IPathPlanner
from robot.order import Order
from robot.rag import RAGModule

logger = logging.getLogger(__name__)


@runtime_checkable
class IRobot(Protocol):
    """
    ロボットインターフェース
    すべてのロボットが実装する必要があるメソッドを定義
    """
    
    def assign_order(self, order: Order) -> bool:
        """注文を受け付けてキューに追加"""
        ...
    
    def tick(self) -> None:
        """シミュレーションの1ステップを実行"""
        ...
    
    def simulate(self, max_step: int) -> None:
        """指定ステップまでシミュレーション実行"""
        ...
    
    def stats(self) -> dict:
        """統計情報を取得"""
        ...


class RobotStatistics:
    """
    ロボット統計データを収集・管理するクラス
    """
    
    def __init__(self, robot_type: str, restaurant_name: str) -> None:
        """
        統計クラスの初期化
        
        Args:
            robot_type: ロボットタイプ（"基本ロボット"または"インテリジェントRAGロボット"）
            restaurant_name: レストラン名
        """
        self.robot_type = robot_type
        self.restaurant_name = restaurant_name
        
        # 基本統計データ
        self._stats = {
            "total_steps": 0,            # 総ステップ数（経路長）
            "total_time": 0,             # 総配達時間
            "total_orders": 0,           # 総注文数
            "avg_waiting_time": 0,       # 平均注文待ち時間
        }
        
        # 配達履歴
        self._delivery_history = []
        
        # パス履歴
        self.path_history: list[tuple[int, int]] = []
    
    def add_position(self, position: Tuple[int, int]) -> None:
        """パス履歴に位置を追加"""
        self.path_history.append(position)
    
    def record_step(self) -> None:
        """ステップ数を増加"""
        self._stats["total_steps"] += 1
    
    def record_order_completion(self) -> int:
        """注文完了を記録し、配達順序番号を返す"""
        self._stats["total_orders"] += 1
        return self._stats["total_orders"]
    
    def calculate_delivery_cycle(
        self, 
        batch_id: int,
        start_time: float,
        batch_start_time: float,
        speed: float,
        batch_orders: List[Order]
    ) -> None:
        """
        配達サイクルの統計情報を計算
        
        Args:
            batch_id: バッチID
            start_time: 配達開始時間
            batch_start_time: バッチ開始時間
            speed: ロボット速度
            batch_orders: バッチ内の注文リスト
        """
        end_time = time.time()
        
        # 本バッチの時間を計算
        batch_time = 0
        if batch_start_time is not None:
            batch_time = end_time - batch_start_time
        else:
            # バッチ開始時間がない場合、配送開始時間を使用
            batch_time = end_time - start_time
        
        # 総配達路程を計算
        path_length = len(self.path_history) - 1  # 初期位置を除く
        
        # 経路長と速度を使用して時間を計算
        calculated_time = path_length / speed
        
        # 統計データを更新
        self._stats["total_steps"] += path_length
        self._stats["total_time"] = calculated_time  # 計算時間を使用
        
        # 本バッチの平均注文待ち時間を計算
        avg_batch_waiting_time = 0
        if batch_orders:
            total_waiting_time = 0
            for i, order in enumerate(batch_orders):
                # 注文待ち時間 = 注文到着時間 = 開始から現在注文の配送時間
                # 配送順序に従って計算、前の注文待ち時間が短く、後の待ち時間が長い
                order_delivery_time = calculated_time * (i+1) / len(batch_orders)
                total_waiting_time += order_delivery_time
            
            # 平均注文待ち時間 = 総待ち時間 / 注文数
            avg_batch_waiting_time = total_waiting_time / len(batch_orders)
            
            # 総体平均注文待ち時間を更新（累積移動平均を使用）
            if self._stats["total_orders"] > 0:
                prev_weight = self._stats["total_orders"] - len(batch_orders)
                new_weight = len(batch_orders)
                self._stats["avg_waiting_time"] = (
                    (self._stats["avg_waiting_time"] * prev_weight + avg_batch_waiting_time * new_weight) /
                    self._stats["total_orders"]
                )
            else:
                self._stats["avg_waiting_time"] = avg_batch_waiting_time
        
        # 注文情報を準備、配送順序を含む
        order_info = []
        for order in batch_orders:
            order_data = {
                "order_id": order.order_id,
                "table_id": order.table_id
            }
            # 配送順序情報を追加（ある場合）
            if hasattr(order, "delivery_sequence") and order.delivery_sequence is not None:
                order_data["delivery_sequence"] = order.delivery_sequence
            order_info.append(order_data)
        
        # 本配送バッチの履歴を記録
        batch_record = {
            "batch_id": batch_id,
            "total_time": calculated_time,  # 計算時間を使用
            "path_length": path_length,
            "avg_waiting_time": avg_batch_waiting_time,
            "ロボットタイプ": self.robot_type,
            "orders": order_info,
            "レストランレイアウト": self.restaurant_name
        }
        self._delivery_history.append(batch_record)
        
        logger.info(f"配送サイクル完了、総配送時間: {batch_time:.2f}秒、" 
                   f"配送注文: {len(batch_orders)}個、"
                   f"経路長: {path_length}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        統計情報を取得
        
        Returns:
            Dict[str, Any]: 統計情報を含む辞書
        """
        stats = dict(self._stats)
        
        # 経路情報を追加
        stats["総配送路程"] = len(self.path_history) - 1  # 初期位置を除く
        
        # ロボットタイプ情報を追加
        stats["ロボットタイプ"] = self.robot_type
        
        # 配送履歴を追加
        stats["配送履歴"] = self._delivery_history
        
        # 将来の拡張用に他のデータフィールドを予約
        stats["他のデータ"] = {
            "エネルギー消費": 0,       # 予約：ロボットエネルギー消費
            "障害物処理回数": 0,   # 予約：障害物に遭遇する回数
            "待機操作回数": 0,     # 予約：待機操作の回数
            "経路再計画回数": 0,   # 予約：経路を再計画する回数
            "混雑区域": [],       # 予約：レストラン混雑区域
        }
        
        return stats


class Robot(IRobot):
    """
    基本ロボット：RAG知能なし
    """

    # 目標点到達の許容半径を定義
    GOAL_TOLERANCE = 0  # 目標点許容半径（マス数）

    def __init__(
        self,
        layout: RestaurantLayout,
        robot_id: int = 1,
        restaurant_name: str = "デフォルトレストラン",
        start: Optional[Tuple[int, int]] = None,
        planner: Optional[IPathPlanner] = None,
    ) -> None:
        self.layout = layout
        self.robot_id = robot_id
        self.speed = 1.0  # ロボット速度、単位：マス/時間単位
        self.restaurant_name = restaurant_name

        # ロボットが駐車スポットから出発することを確保
        self.parking_spot = layout.parking or (layout.kitchen[0] if layout.kitchen else (0, 0))
        self.position = self.parking_spot
        self.goal: Optional[Tuple[int, int]] = None
        self.path: List[Tuple[int, int]] = []

        # 経路計画器の初期化（依存性の注入）
        self.planner = planner or PathPlanner(layout)
        self.controller = MotionController(layout, self.planner)

        # 注文キュー
        self.order_queue: Deque[Order] = deque()
        self.current_order: Optional[Order] = None
        
        # 統計管理クラスを初期化
        self.is_ai_enhanced = isinstance(self, AIEnhancedRobot)
        robot_type = "インテリジェントRAGロボット" if self.is_ai_enhanced else "基本ロボット"
        self._stats = RobotStatistics(robot_type, restaurant_name)
        self._stats.add_position(self.position)  # 初期位置を記録
        
        self.returning_to_parking = False
        self.delivery_start_time = None
        self.all_assigned_orders = []
        
        # バッチ処理制御パラメータ
        self.batch_collection_time = 1.0  # 注文を一括収集する時間ウィンドウ（秒）
        self.last_order_time = None      # 最後に注文を受けた時間
        self.batch_processing = False    # バッチ処理モードかどうか
        
        # 現在のバッチ情報
        self.current_batch_start_time = None  # 現在のバッチ開始時間
        self.current_batch_orders = []        # 現在のバッチ注文
        self.current_batch_id = 0             # 現在のバッチID

    # ---------------- 注文インターフェース ---------------- #
    def assign_order(self, order: Order) -> bool:
        """
        注文を受け付けてキューに追加
        """
        table_pos = self.layout.tables.get(order.table_id)
        if not table_pos:
            logger.error("テーブル番号が存在しません %s", order.table_id)
            return False

        # 注文をキューに追加
        self.order_queue.append(order)
        self.all_assigned_orders.append(order)
        logger.info("ロボット #%s が注文 #%s をキューに追加", self.robot_id, order.order_id)
        
        # 最後に注文を受けた時間を記録
        self.last_order_time = time.time()
        
        # ロボットがアイドル状態でバッチ処理中でない場合、バッチ処理タイマーを開始
        if not self.current_order and not self.returning_to_parking and not self.batch_processing:
            self.batch_processing = True
            logger.info("ロボット #%s が注文バッチ処理を開始、追加の注文を待機中...", self.robot_id)
            
        return True

    def _process_next_order(self) -> bool:
        """
        キュー内の次の注文を処理
        """
        if not self.order_queue:
            # 注文がなく駐車スポットにいない場合、駐車スポットに戻る
            if self.position != self.parking_spot and not self.returning_to_parking:
                self._return_to_parking()
            return False

        # 注文キューを最適化
        self._optimize_order_queue()
        
        # 現在のバッチ開始を記録
        if not self.current_batch_start_time:
            self.current_batch_start_time = time.time()
            self.current_batch_id += 1
            self.current_batch_orders = []

        # 次の注文を取り出す
        order = self.order_queue.popleft()
        self.current_order = order
        
        # 現在のバッチに追加
        self.current_batch_orders.append(order)
        
        # テーブルに対応する配達ポイントを取得
        delivery_pos = self.layout.get_delivery_point(order.table_id)
        if not delivery_pos:
            logger.error("テーブル番号 %s に指定された配達ポイントがありません", order.table_id)
            self._finish_delivery(success=False)
            return False

        if not self.layout.is_free(delivery_pos):
            logger.error("テーブル番号 %s の配達ポイント %s は通行できません", order.table_id, delivery_pos)
            self._finish_delivery(success=False)
            return False

        # 目標点を設定
        self.goal = delivery_pos
        
        # 経路計画
        self.path = self.planner.find_path(self.position, self.goal) or []
        if not self.path:
            logger.error("テーブル %s への経路を計画できません", order.table_id)
            self._finish_delivery(success=False)
            return False

        # インテリジェントロボットの場合、RAGの計画層をトリガーして提案を記録
        if self.is_ai_enhanced and getattr(self, 'rag', None):
            rag_result = self.rag.trigger_layer(
                'plan',
                {'robot_id': self.robot_id, 'start': self.position, 'goal': self.goal}
            )
            logger.info(
                f"RAG 計画提案: action={rag_result['action']}, "
                f"context_docs={rag_result['context_docs']}, "
                f"raw_response={rag_result['raw_response']}"
            )

        # 配達開始
        order.start_delivery()
        
        # 初めて駐車スポットから出発する場合、開始時間を記録
        if self.position == self.parking_spot and self.delivery_start_time is None:
            self.delivery_start_time = time.time()
        
        logger.info("ロボット #%s がテーブル番号 %s への配達を開始、目標位置 %s",
                   self.robot_id, order.table_id, self.goal)
        
        return True

    def _optimize_order_queue(self) -> None:
        """
        注文キューの配達順序を最適化
        近似TSP（巡回セールスマン問題）アルゴリズムを使用し、単純な距離ではなく
        全体の経路長を考慮します。
        目標：総配達時間と経路長を最小化
        """
        if len(self.order_queue) <= 1:
            return  # 注文がないか1つしかない場合、最適化不要
        
        # 現在位置とすべての注文の配達ポイントを取得
        current_pos = self.position
        delivery_points = {}
        
        for order in self.order_queue:
            delivery_pos = self.layout.get_delivery_point(order.table_id)
            if delivery_pos:
                delivery_points[order.order_id] = delivery_pos
        
        if not delivery_points:
            return  # 有効な配達ポイントがない
            
        # 距離行列を構築（現在位置から各配達ポイント、および配達ポイント間の距離を含む）
        points = [current_pos] + list(delivery_points.values())
        n = len(points)
        
        # 経路長計算関数、単純なマンハッタン距離ではなくA*アルゴリズムで実際の経路長を取得
        def get_path_length(start, end):
            path = self.planner.find_path(start, end)
            return len(path) if path else float('inf')
        
        # 距離行列の構築
        distances = [[0 for _ in range(n)] for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i != j:
                    distances[i][j] = get_path_length(points[i], points[j])
        
        # 貪欲法によるTSP近似解：毎回最も近い未訪問点を選択
        # 注意：現在位置（インデックス0）から開始
        current = 0  # 現在位置から開始
        unvisited = set(range(1, n))  # インデックス1以降の配達ポイント
        tour = [current]
        
        # 貪欲に経路を構築
        while unvisited:
            nearest = min(unvisited, key=lambda j: distances[current][j])
            tour.append(nearest)
            unvisited.remove(nearest)
            current = nearest
            
        # 注文キューの再構築
        new_queue = []
        
        # 経路を注文に変換（インデックス0はスキップ、それはロボットの現在位置）
        for idx in tour[1:]:
            point = points[idx]
            # この配達ポイントに対応する注文を探す
            for order in self.order_queue:
                if delivery_points.get(order.order_id) == point:
                    new_queue.append(order)
                    break
        
        # 注文キューを更新
        self.order_queue.clear()
        for order in new_queue:
            self.order_queue.append(order)
            
        # 推定の総配達路程を計算
        total_distance = sum(distances[tour[i]][tour[i+1]] for i in range(len(tour)-1))
        
        logger.info("Robot #%s 注文キューを最適化、実行順序: %s（推定総長: %d）", 
                   self.robot_id, 
                   ", ".join([f"#{order.order_id}({order.table_id})" for order in new_queue]),
                   total_distance)

    def _return_to_parking(self) -> bool:
        """
        駐車スポットに戻る
        """
        self.returning_to_parking = True
        self.goal = self.parking_spot
        self.path = self.planner.find_path(self.position, self.goal) or []
        
        if not self.path:
            logger.error("駐車スポットに戻る経路を計画できません")
            self.returning_to_parking = False
            return False
            
        logger.info("Robot #%s が駐車スポットに戻る途中です", self.robot_id)
        return True
        
    def _is_at_goal(self) -> bool:
        """
        ロボットが目標点に到達したかどうかを判断（許容範囲を考慮）
        """
        if not self.goal:
            return False
            
        # 現在位置から目標点までのマンハッタン距離を計算
        dist = abs(self.position[0] - self.goal[0]) + abs(self.position[1] - self.goal[1])
        
        # 距離が許容範囲内にある場合、目標に到達したと見なす
        return dist <= self.GOAL_TOLERANCE

    # ---------------- シミュレーションループ ---------------- #
    def tick(self) -> None:
        # ステップ数を記録
        self._stats.record_step()
        
        # バッチ処理タイマーをチェック
        if self.batch_processing and self.last_order_time:
            if time.time() - self.last_order_time >= self.batch_collection_time:
                # バッチ処理時間ウィンドウが終了、注文を処理
                logger.info("Robot #%s バッチ処理時間ウィンドウが終了、注文キューを最適化", self.robot_id)
                self.batch_processing = False
                self._process_next_order()
                
        if not self.path:  # 残り経路がない場合、次のステップを処理
            if self.returning_to_parking:
                # 駐車スポットに到着、状態をリセット
                if self._is_at_goal() or self.position == self.parking_spot:
                    self.returning_to_parking = False
                    self._calculate_delivery_cycle_time()
            elif self.current_order:
                # 目標位置に到着、現在の注文を完了
                if self._is_at_goal() or self.position == self.goal:
                    # シミュレーションの配達動作
                    logger.info("ロボット #%s が目標位置に到着、配達完了", self.robot_id)
                    self._finish_delivery(success=True)
                    self._process_next_order()
            elif not self.batch_processing:
                # 現在注文がなくバッチ処理中でない場合、次を処理
                self._process_next_order()
            return

        prev = self.position
        self.position, self.path = self.controller.step(
            self.position, self.path, self.goal
        )

        # 実際に移動したときに軌跡を記録
        if self.position != prev:
            self._stats.add_position(self.position)
            
        # 目標点に到着したかどうかをチェック（許容範囲を考慮）
        if self.goal and self._is_at_goal():
            # 目標に到着、残り経路をクリア
            self.path = []

    def _finish_delivery(self, *, success: bool) -> None:
        if not self.current_order:
            return
        if success:
            # 配送完了番号を追加
            self.current_order.delivery_sequence = self._stats.record_order_completion()
            self.current_order.complete_delivery()
            logger.info("注文 #%s (テーブル: %s) 配送成功、配送順序: #%d", 
                       self.current_order.order_id, 
                       self.current_order.table_id,
                       self.current_order.delivery_sequence)
        else:
            self.current_order.fail_delivery()
            logger.error("注文 #%s 配送失敗", self.current_order.order_id)
        self.current_order = None
        self.goal = None
        self.path = []

    def _calculate_delivery_cycle_time(self) -> None:
        """
        駐車スポットから戻るまでの総配達時間と統計データを計算
        """
        if self.delivery_start_time is not None:
            # 統計クラスに処理を委譲
            self._stats.calculate_delivery_cycle(
                batch_id=self.current_batch_id,
                start_time=self.delivery_start_time,
                batch_start_time=self.current_batch_start_time,
                speed=self.speed,
                batch_orders=self.current_batch_orders
            )
            
            # 現在のバッチデータをリセット
            self.delivery_start_time = None
            self.current_batch_start_time = None
            self.current_batch_orders = []

    # ---------------- 他の ---------------- #
    def simulate(self, max_step: int = 500) -> None:
        step = 0
        # 配送開始時間（まだ設定されていない場合）を記録
        if self.delivery_start_time is None:
            self.delivery_start_time = time.time()
            
        # バッチ処理モードの場合、先にバッチ処理ウィンドウを閉じるのを待つ
        if self.batch_processing:
            self.batch_processing = False
            if self.order_queue:
                logger.info("シミュレーション開始：即時にバッチ処理ウィンドウを終了、配達を開始")
                self._process_next_order()
        
        while (self.path or self.current_order or self.order_queue or self.returning_to_parking) and step < max_step:
            self.tick()
            step += 1
        
        # バッチ処理モードが終了しても駐車スポットに戻れない場合、駐車スポットに戻る
        if self.position != self.parking_spot and not self.returning_to_parking:
            self._return_to_parking()
            while self.path and step < max_step:
                self.tick()
                step += 1
        
        # シミュレーション終了時に駐車スポットに戻れない場合、配送サイクルを記録
        if not self.returning_to_parking and self.delivery_start_time is not None:
            self._calculate_delivery_cycle_time()
                
        logging.debug("simulate finished: %s steps", step)

    def stats(self) -> dict:
        """
        豊富な統計指標を提供
        """
        return self._stats.get_stats()
    
    @property
    def path_history(self) -> list[tuple[int, int]]:
        """
        パス履歴を取得
        """
        return self._stats.path_history


class AIEnhancedRobot(Robot):
    """
    インテリジェントロボット
    """

    def __init__(
        self,
        layout: RestaurantLayout,
        robot_id: int = 1,
        api_key: str | None = None,
        knowledge_dir: str | None = None,
        start: Optional[Tuple[int, int]] = None,
        planner: Optional[IPathPlanner] = None,
    ) -> None:
        # 基底クラスの初期化
        super().__init__(layout, robot_id, start=start, planner=planner)
        
        # RAGモジュールの初期化
        self.rag = RAGModule(
            api_key=api_key,
            knowledge_file=os.path.join(knowledge_dir, "restaurant_rule.json") if knowledge_dir else None,
        )
        
        # RAG対応のコントローラーに置き換え
        self.controller = MotionController(layout, self.planner, rag=self.rag)
