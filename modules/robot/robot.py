from modules.robot.path_planning import PathPlanner
import time

# 条件付きでRAGアシスタントをインポート
try:
    from modules.rag.rag_assistant import RagAssistant
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("警告: RAGモジュールが利用できません。基本ロボット動作を使用します")

class Robot:
    """
    ロボット基本クラス、基本的な経路計画、移動、障害物処理機能を定義
    enable_ragオプションでスマート意思決定機能を有効化可能
    """
    def __init__(self, environment, start=None, goal=None, robot_id=1, 
                enable_rag=False, api_key=None, knowledge_file=None):
        """
        ロボットを初期化
        
        パラメータ:
            environment: 環境オブジェクト
            start: 開始位置
            goal: 目標位置
            robot_id: ロボットID
            enable_rag: RAG機能を有効にするかどうか
            api_key: OpenAI APIキー（enable_rag=Trueの場合のみ使用）
            knowledge_file: 知識ベースファイルパス（enable_rag=Trueの場合のみ使用）
        """
        self.env = environment
        self.robot_id = robot_id  # ロボットID
        
        # ロボット名を設定
        self.enable_rag = enable_rag and RAG_AVAILABLE
        self.name = "スマートロボット" if self.enable_rag else "基本ロボット"
        
        # すべてのキッチン位置を取得
        kitchen_positions = environment.get_kitchen_positions()
        
        # 開始点が提供されていない場合、環境内の最初のキッチン位置をデフォルトとする
        if start is None:
            if kitchen_positions:
                self.start = kitchen_positions[0]
            else:
                self.start = (0, 0)  # デフォルトの開始点
        else:
            self.start = start
            
        self.goal = goal  # 目標位置はNoneでもよい、後で注文から設定
        self.position = self.start  # 現在位置は最初は開始点
        self.planner = PathPlanner(environment)
        self.path = []  # 現在計画された経路
        self.path_history = [self.start]  # 可視化のために各ステップの座標を記録
        
        # 注文関連の属性
        self.current_order = None  # 現在配送中の注文
        self.delivered_orders = []  # 配送済み注文リスト
        self.failed_orders = []    # 配送失敗注文リスト
        self.idle = True           # ロボットがアイドル状態かどうか
        self.kitchen_position = self.start  # キッチン位置（デフォルトは開始点）
        
        # RAGアシスタントの初期化（有効な場合）
        self.rag_assistant = None
        if self.enable_rag:
            print(f"\n===== {self.name} #{robot_id} のRAG機能を初期化 =====")
            try:
                self.rag_assistant = RagAssistant(
                    api_key=api_key,
                    knowledge_file=knowledge_file
                )
                print(f"RAG機能{('準備完了' if self.rag_assistant.is_ready else '初期化失敗')}")
            except Exception as e:
                print(f"RAGアシスタント初期化エラー: {e}")
                self.enable_rag = False
                self.name = "基本ロボット"  # 基本ロボットにダウングレード
            print("========================================\n")
        
        # 初期化情報を表示
        print(f"{self.name}#{self.robot_id} - 位置 {self.start} で初期化、初期キッチン位置 {self.kitchen_position}")
        print(f"環境内に {len(kitchen_positions)} 個のキッチン位置があります: {kitchen_positions}")

    def plan_path(self):
        """現在位置から目標位置への経路を計画"""
        if self.goal is None:
            print("目標位置が設定されていません")
            return None
            
        self.path = self.planner.find_path(self.position, self.goal)
        if self.path:
            print(f"{self.name}#{self.robot_id} - {self.position} から {self.goal} への計画経路： {self.path}")
        else:
            print(f"{self.name}#{self.robot_id} - 経路が見つかりません！")
        return self.path
    
    def is_adjacent_to_table(self, table_position):
        """現在位置がテーブルに隣接しているかをチェック"""
        if not table_position:
            return False
            
        table_x, table_y = table_position
        x, y = self.position
        
        # テーブルの上下左右4方向にいるかをチェック
        return (abs(x - table_x) == 1 and y == table_y) or (abs(y - table_y) == 1 and x == table_x)
    
    def move(self):
        """
        経路に沿って1ステップ前進
        """
        if self.path and len(self.path) > 1:
            next_position = self.path[1]
            if self.env.is_free(next_position):
                self.position = next_position
                self.path_history.append(next_position)
                self.path.pop(0)
                
                # 配送目標の近くに到達したかどうかをチェック
                if self.current_order:
                    table_position = self.env.get_table_position(self.current_order.table_id)
                    if self.is_adjacent_to_table(table_position):
                        print(f"{self.name}#{self.robot_id} - テーブル番号 {self.current_order.table_id} の近くに到着、配送準備中")
                        # 目標がテーブルの隣で、到達している場合は配送成功とみなす
                        if self.position == self.goal:
                            self.on_goal_reached()
            else:
                print(f"{self.name}#{self.robot_id} - {next_position} で障害物に遭遇。")
                self.handle_obstacle(next_position)
        else:
            if self.path and len(self.path) == 1 and self.position == self.goal:
                print(f"{self.name}#{self.robot_id} - 目標位置 {self.goal} に到着")
                self.on_goal_reached()
            else:
                print(f"{self.name}#{self.robot_id} - 利用可能な経路がありません。")
    
    def handle_obstacle(self, obstacle_position):
        """
        障害物に遭遇した際の処理ロジック
        RAGが有効な場合はスマート意思決定を使用、そうでなければ基本動作を使用
        """
        if self.enable_rag and self.rag_assistant and self.rag_assistant.is_ready:
            return self._handle_obstacle_with_rag(obstacle_position)
        else:
            # 基本ロボットの動作
            print(f"{self.name}#{self.robot_id} - {obstacle_position} で障害物に遭遇、配送停止")
            if self.current_order:
                self.fail_current_order("障害物に遭遇し、配送を続行できません")
            
            # キッチンへの帰還を試みる
            self.return_to_kitchen()
    
    def _handle_obstacle_with_rag(self, obstacle_position):
        """RAG技術を使用して障害物を処理"""
        print(f"\n===== {self.name}#{self.robot_id} - RAGを使用して障害物を処理 =====")
        print(f"障害物の位置: {obstacle_position}")
        
        # その位置が実際に障害物かどうかを確認
        x, y = obstacle_position
        if 0 <= x < self.env.height and 0 <= y < self.env.width:
            grid_value = self.env.grid[x][y]
            print(f"その位置のグリッド値: {grid_value} (0=空きスペース, 1=障害物, 2=テーブル, 3=キッチン)")
        
        # RAGアシスタントで意思決定
        decision = self.rag_assistant.make_decision(
            situation_type="obstacle", 
            robot_id=self.robot_id,
            position=self.position, 
            goal=self.goal, 
            context=obstacle_position
        )
        
        print(f"{self.name}#{self.robot_id} - RAG決定：{decision}")
        
        # 決定に基づいて行動を選択
        if decision == "迂回" or decision == "再計画" or decision == "新しい経路を探索":
            print(f"決定: {decision} - 代替経路を探します")
            # 現在の障害物を回避する経路を探す
            self.find_alternative_path(obstacle_position)
        elif decision == "待機" or decision == "しばらく待ってから再試行":
            print(f"決定: {decision} - 待機してから再試行")
            # 待機をシミュレート
            print(f"{self.name}#{self.robot_id} - しばらく待ってから再試行...")
            time.sleep(0.5)  # 0.5秒の待機をシミュレート
            # 同じ移動を即座に再試行しないように最初のポイントを削除
            if len(self.path) > 1:
                self.path.pop(0)
        elif decision == "到達不能を報告":
            print(f"決定: {decision} - 現在のタスクを放棄")
            print(f"{self.name}#{self.robot_id} - 経路が完全に遮断されており、目標に到達できません")
            if self.current_order:
                self.fail_current_order("経路が遮断されており、目標テーブルに到達できません")
            else:
                # 現在の注文がない場合はキッチンへの帰還を試みる
                self.return_to_kitchen()
        
        print(f"===== 障害物処理完了 =====\n")
    
    def find_alternative_path(self, obstacle_position):
        """
        障害物を回避する代替経路を探す
        """
        # 現在の経路が遮断されているため、代替経路を探す必要がある
        
        # 戦略1: 再計画を試みる
        print(f"{self.name}#{self.robot_id} - 再計画を試みる...")
        new_path = self.planner.find_path(self.position, self.goal)
        
        if new_path:
            self.path = new_path
            print(f"{self.name}#{self.robot_id} - 新しい経路を見つけました: {self.path}")
            return True
        
        # 戦略2: 直接再計画が失敗した場合は、周囲のいくつかの方向に移動してから再計画
        print(f"{self.name}#{self.robot_id} - 直接経路計画が失敗したため、周囲の領域を探索...")
        
        # 現在の位置のすべての隣接位置を取得
        neighbors = self.env.neighbors(self.position)
        
        # 目標からの距離に基づいて隣接位置をソート
        neighbors.sort(key=lambda pos: self.planner.heuristic(pos, self.goal))
        
        # 各隣接位置から目標への経路を計画してみる
        for next_pos in neighbors:
            if next_pos == obstacle_position:
                continue  # 障害物位置をスキップ
            
            temp_path = self.planner.find_path(next_pos, self.goal)
            if temp_path:
                # 隣接位置から目標への経路を見つけた場合は、まずその隣接位置に移動
                self.path = [self.position, next_pos] + temp_path[1:]
                print(f"{self.name}#{self.robot_id} - 迂回経路を見つけました、{next_pos}を経由")
                return True
        
        print(f"{self.name}#{self.robot_id} - 有効な代替経路が見つかりません")
        return False
    
    def assign_order(self, order):
        """
        注文をロボットに割り当てる
        """
        if not self.idle:
            print(f"{self.name}#{self.robot_id} - 現在忙しいため、新しい注文を受け付けられません")
            return False
            
        self.current_order = order
        self.idle = False
            
        # 目標位置を注文に対応するテーブル位置に設定
        table_position = self.env.get_table_position(order.table_id)
        if table_position:
            # テーブル周囲の通行可能な位置を目標にする
            # (テーブル自体は通行不可なので、テーブルの隣の位置を探す)
            table_x, table_y = table_position
            adjacent_positions = [
                (table_x-1, table_y), (table_x+1, table_y),
                (table_x, table_y-1), (table_x, table_y+1)
            ]
            
            # 通行可能な位置をフィルタリング
            valid_positions = [pos for pos in adjacent_positions if self.env.is_free(pos)]
            
            if valid_positions:
                # 最初の利用可能な位置を目標に選択
                self.goal = valid_positions[0]
                print(f"{self.name}#{self.robot_id} - 注文 #{order.order_id} を受け入れました、テーブル番号: {order.table_id}")
                print(f"テーブル位置: {table_position}, 配送目標位置: {self.goal}")
                return self.plan_path()
            else:
                print(f"{self.name}#{self.robot_id} - テーブル番号 {order.table_id} 周囲の通行可能な位置が見つかりません")
                self.current_order = None
                self.idle = True
                return False
        else:
            print(f"{self.name}#{self.robot_id} - テーブル番号 {order.table_id} の位置が見つかりません")
            self.current_order = None
            self.idle = True
            return False
    
    def on_goal_reached(self):
        """目標位置に到着した際のコールバック"""
        if self.current_order:
            # 目標に近いテーブルかどうかをチェック
            table_position = self.env.get_table_position(self.current_order.table_id)
            is_near_table = self.is_adjacent_to_table(table_position)
            
            print(f"{self.name}#{self.robot_id} - 目標位置 {self.position} に到着")
            
            if is_near_table:
                print(f"{self.name}#{self.robot_id} - 注文 #{self.current_order.order_id} をテーブル番号 {self.current_order.table_id} に成功配送")
                # 配送済み注文リストに追加
                self.delivered_orders.append(self.current_order)
                
                # 完了注文としてマークしますが、現在の注文をクリアしない
                # これにより、main.pyのチェックは注文が配送されたことをキャプチャできます
                # 完了フラグを設定して注文が完了したことを示す
                self.current_order.delivered_flag = True
                
                # キッチンへの帰還
                self.return_to_kitchen()
            else:
                print(f"{self.name}#{self.robot_id} - 警告：目標位置に到着しましたが、テーブル番号 {self.current_order.table_id} 近くにありません")
                self.fail_current_order("配送位置が正しくありません")
        else:
            # キッチンに戻る
            kitchen_positions = self.env.get_kitchen_positions()
            if self.position in kitchen_positions:
                print(f"{self.name}#{self.robot_id} - キッチンに戻りました")
                # 配送済み注文がある場合は、ここで安全にクリアできます
                if hasattr(self, 'current_order') and self.current_order and hasattr(self.current_order, 'delivered_flag'):
                    self.current_order = None
                self.idle = True
    
    def fail_current_order(self, reason="不明な理由"):
        """現在の注文を失敗としてマーク"""
        if self.current_order:
            print(f"{self.name}#{self.robot_id} - 注文 #{self.current_order.order_id} 配送失敗: {reason}")
            self.failed_orders.append(self.current_order)
            self.current_order = None
            
            # キッチンへの帰還
            self.return_to_kitchen()
    
    def return_to_kitchen(self):
        """キッチン位置に戻る"""
        # すべてのキッチン位置を取得
        kitchen_positions = self.env.get_kitchen_positions()
        if not kitchen_positions:
            print(f"{self.name}#{self.robot_id} - エラー：キッチン位置がありません")
            self.idle = True
            return False
            
        # すべてのキッチン位置に向かって経路計画を試み、最も近いものを選択
        successful_path = None
        chosen_kitchen = None
        
        print(f"{self.name}#{self.robot_id} - キッチンに戻るために試みます、現在のキッチン位置が {len(kitchen_positions)} 個あります")
        
        for kitchen_pos in kitchen_positions:
            self.goal = kitchen_pos
            print(f"{self.name}#{self.robot_id} - キッチン位置 {kitchen_pos} に向かって経路計画を試みます")
            path = self.planner.find_path(self.position, kitchen_pos)
            
            if path:
                # 有効な経路を見つけた場合は、このキッチン位置を使用
                successful_path = path
                chosen_kitchen = kitchen_pos
                print(f"{self.name}#{self.robot_id} - キッチンに戻る {kitchen_pos} の経路を成功見つけました")
                break
        
        if successful_path:
            self.path = successful_path
            self.goal = chosen_kitchen
            self.kitchen_position = chosen_kitchen  # 現在のキッチン位置を更新
            print(f"{self.name}#{self.robot_id} - キッチンに戻る {chosen_kitchen} を開始")
            self.idle = False  # 戻る途中はアイドル状態ではありません
            return True
        else:
            # 戻るために戻ることができない
            print(f"{self.name}#{self.robot_id} - 戻るために戻ることができない")
            # 配送済み注文がある場合でもキッチンに戻れない場合は、現在の注文をクリア
            if hasattr(self, 'current_order') and self.current_order and hasattr(self.current_order, 'delivered_flag'):
                print(f"{self.name}#{self.robot_id} - 注文が配送されましたが、キッチンに戻れません")
                self.current_order = None
            self.idle = True  # アイドル状態に設定し、新しいコマンドを待つ
            return False
    
    def is_idle(self):
        """ロボットがアイドル状態かどうかをチェック"""
        kitchen_positions = self.env.get_kitchen_positions()
        
        # 現在の注文がなく、キッチン位置にある場合はアイドル状態とみなす
        if self.current_order is None and self.position in kitchen_positions:
            self.idle = True
            return True
        
        # 経路がない場合はアイドル状態とみなす
        if not self.path:
            # キッチンに戻る途中にキッチンに到着した場合はアイドル状態とみなす
            if self.position in kitchen_positions:
                self.idle = True
                return True
                
        return self.idle
    
    def simulate(self, max_steps=50):
        """
        ロボットのタスクをシミュレートし、目標に到着するか、ステップ数の制限を超えるまで実行
        """
        if not self.goal:
            print(f"{self.name}#{self.robot_id} - 目標位置が設定されていません、シミュレーションを開始できません")
            return False
            
        self.plan_path()
        steps = 0
        
        while self.position != self.goal and self.path is not None:
            print(f"ステップ {steps}：{self.name}#{self.robot_id} - 現在位置 {self.position}")
            self.env.display(self.path, self.position)
            self.move()
            steps += 1
            
            if steps > max_steps:
                print(f"{self.name}#{self.robot_id} - シミュレーション終了：ステップ数が多すぎます。")
                if self.current_order:
                    self.fail_current_order("シミュレーションステップ数超過")
                break
                
        if self.position == self.goal:
            print(f"{self.name}#{self.robot_id} - タスク完了、{steps} ステップ後に目標 {self.position} に到着しました。")
            self.on_goal_reached()
            return True
        return False
    
    def get_statistics(self):
        """ロボットの配送統計情報を取得"""
        delivered_count = len(self.delivered_orders)
        failed_count = len(self.failed_orders)
        total_count = delivered_count + failed_count
        
        success_rate = (delivered_count / total_count * 100) if total_count > 0 else 0
        
        avg_delivery_time = 0
        if delivered_count > 0:
            total_delivery_time = sum(order.get_delivery_time() or 0 for order in self.delivered_orders)
            avg_delivery_time = total_delivery_time / delivered_count
        
        return {
            "robot_id": self.robot_id,
            "delivered_orders": delivered_count,
            "failed_orders": failed_count,
            "total_orders": total_count,
            "success_rate": success_rate,
            "avg_delivery_time": avg_delivery_time
        }
    
    def comprehensive_test(self):
        """
        総合テストRAG機能の方法、RAGロボットのみで有効
        """
        if not self.enable_rag or not self.rag_assistant or not self.rag_assistant.is_ready:
            print(f"{self.name}#{self.robot_id} - RAG機能が有効になっていません、総合テストを実行できません")
            return
            
        print(f"\n===== {self.name}#{self.robot_id} - 総合テストを開始 =====")
        
        # 異なる状況下での障害物処理をテスト
        test_positions = [
            (self.position[0] + 1, self.position[1]),  # 前方
            (self.position[0], self.position[1] + 1),  # 右側
            (self.position[0] - 1, self.position[1]),  # 後方
            (self.position[0], self.position[1] - 1),  # 左側
        ]
        
        for pos in test_positions:
            print(f"\n障害物位置テスト: {pos}")
            # 環境境界外の位置をスキップ
            if not (0 <= pos[0] < self.env.height and 0 <= pos[1] < self.env.width):
                print(f"位置 {pos} が環境境界外で、テストをスキップ")
                continue
                
            # 元のグリッド値を保存
            original_value = self.env.grid[pos[0]][pos[1]]
            
            # その位置を一時的に障害物に設定（障害物でない場合）
            if original_value == 0:  # 空地の場合
                self.env.grid[pos[0]][pos[1]] = 1  # 障害物に設定
                
                # 障害物処理をテスト
                print(f"シミュレートして {pos} で障害物に遭遇")
                self._handle_obstacle_with_rag(pos)
                
                # 元のグリッド値を復元
                self.env.grid[pos[0]][pos[1]] = original_value
            else:
                print(f"位置 {pos} 現在値が {original_value}、空地ではないため、テストをスキップ")
        
        print(f"\n===== 総合テスト完了 =====\n")

class AIEnhancedRobot(Robot):
    """
    RAG技術で強化されたスマートロボット
    基本ロボットの全機能に加え、より高度な意思決定能力を持ちます
    """
    def __init__(self, environment, start=None, goal=None, robot_id=1, api_key=None, knowledge_file=None):
        """AIロボットを初期化"""
        super().__init__(
            environment=environment, 
            start=start, 
            goal=goal, 
            robot_id=robot_id,
            enable_rag=True,  # RAG機能を有効化
            api_key=api_key, 
            knowledge_file=knowledge_file
        )
        
        # 名前をより明確に
        self.name = "RAG強化ロボット"
        print(f"{self.name}#{self.robot_id} - 初期化完了、スマート意思決定有効")
    
    def handle_obstacle(self, obstacle_position):
        """
        障害物を処理する強化版メソッド
        常にRAGアシスタントを使用し、失敗時のみ基本戦略にフォールバック
        """
        # RAGアシスタントが利用可能な場合は使用
        if self.rag_assistant and self.rag_assistant.is_ready:
            return self._handle_obstacle_with_rag(obstacle_position)
        else:
            # 基本戦略にフォールバック
            print(f"{self.name}#{self.robot_id} - RAGアシスタントが利用できません。基本戦略にフォールバック。")
            return super().handle_obstacle(obstacle_position)
    
    def find_alternative_path(self, obstacle_position):
        """
        障害物を回避する代替経路を探す強化版メソッド
        より広範囲に経路を探索
        """
        print(f"{self.name}#{self.robot_id} - 高度な経路探索アルゴリズムを使用")
        
        # 現在の経路を保存
        original_path = self.path.copy() if self.path else []
        
        # 障害物周辺を迂回する経路を広範囲に探索
        # 現在位置から目標までの直接経路を再計画
        new_path = self.planner.find_path(self.position, self.goal)
        
        if new_path:
            print(f"{self.name}#{self.robot_id} - 新しい経路を見つけました: {len(new_path)} ステップ")
            self.path = new_path
            return True
        else:
            print(f"{self.name}#{self.robot_id} - 現在位置から直接到達できる経路が見つかりません")
            
            # キッチンへの復帰経路を計画
            if self.kitchen_position:
                print(f"{self.name}#{self.robot_id} - キッチンへの帰還経路を検討")
                kitchen_path = self.planner.find_path(self.position, self.kitchen_position)
                if kitchen_path:
                    # 戦略的撤退 - いったんキッチンに戻ってから再計画
                    print(f"{self.name}#{self.robot_id} - 一時的にキッチンに戻ります")
                    self.path = kitchen_path
                    return True
            
            # 元の経路に戻す（現在位置以前は削除）
            if original_path:
                current_index = -1
                for i, pos in enumerate(original_path):
                    if pos == self.position:
                        current_index = i
                        break
                
                if current_index >= 0 and current_index < len(original_path) - 1:
                    print(f"{self.name}#{self.robot_id} - 元の経路に戻って別のアプローチを試みます")
                    self.path = original_path[current_index:]
                    return True
            
            print(f"{self.name}#{self.robot_id} - 使用可能な経路が見つかりません")
            return False 