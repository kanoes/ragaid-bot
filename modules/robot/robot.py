from modules.utils.path_planner import PathPlanner
import time

# 有条件导入RAG助手
try:
    from modules.rag.rag_assistant import RagAssistant
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("警告: RAG模块不可用，将使用基础机器人行为")

class Robot:
    """
    机器人基类，定义基本的路径规划、移动和障碍处理功能
    可以通过enable_rag选项启用智能决策能力
    """
    def __init__(self, environment, start=None, goal=None, robot_id=1, 
                enable_rag=False, api_key=None, knowledge_file=None):
        """
        初始化机器人
        
        参数:
            environment: 环境对象
            start: 起始位置
            goal: 目标位置
            robot_id: 机器人ID
            enable_rag: 是否启用RAG功能
            api_key: OpenAI API密钥（仅在enable_rag=True时使用）
            knowledge_file: 知识库文件路径（仅在enable_rag=True时使用）
        """
        self.env = environment
        self.robot_id = robot_id  # 机器人ID
        
        # 设置机器人名称
        self.enable_rag = enable_rag and RAG_AVAILABLE
        self.name = "智能机器人" if self.enable_rag else "基础机器人"
        
        # 获取所有后厨位置
        kitchen_positions = environment.get_kitchen_positions()
        
        # 如果未提供起点，默认为环境中第一个后厨位置
        if start is None:
            if kitchen_positions:
                self.start = kitchen_positions[0]
            else:
                self.start = (0, 0)  # 默认起点
        else:
            self.start = start
            
        self.goal = goal  # 目标位置可以为None，后续通过订单设置
        self.position = self.start  # 当前位置初始为起点
        self.planner = PathPlanner(environment)
        self.path = []  # 当前规划的路径
        self.path_history = [self.start]  # 记录每一步坐标以便于可视化
        
        # 订单相关属性
        self.current_order = None  # 当前正在配送的订单
        self.delivered_orders = []  # 已配送订单列表
        self.failed_orders = []    # 配送失败订单列表
        self.idle = True           # 机器人是否空闲
        self.kitchen_position = self.start  # 后厨位置（默认为起点）
        
        # 初始化RAG助手（如果启用）
        self.rag_assistant = None
        if self.enable_rag:
            print(f"\n===== 初始化{self.name} #{robot_id} 的RAG功能 =====")
            try:
                self.rag_assistant = RagAssistant(
                    api_key=api_key,
                    knowledge_file=knowledge_file
                )
                print(f"RAG功能{'已就绪' if self.rag_assistant.is_ready else '初始化失败'}")
            except Exception as e:
                print(f"初始化RAG助手时出错: {e}")
                self.enable_rag = False
                self.name = "基础机器人"  # 降级为基础机器人
            print("========================================\n")
        
        # 打印初始化信息
        print(f"{self.name}#{self.robot_id} - 初始化在位置 {self.start}，初始后厨位置 {self.kitchen_position}")
        print(f"环境中共有 {len(kitchen_positions)} 个后厨位置: {kitchen_positions}")

    def plan_path(self):
        """规划从当前位置到目标位置的路径"""
        if self.goal is None:
            print("未设置目标位置")
            return None
            
        self.path = self.planner.find_path(self.position, self.goal)
        if self.path:
            print(f"{self.name}#{self.robot_id} - 从 {self.position} 到 {self.goal} 的规划路径： {self.path}")
        else:
            print(f"{self.name}#{self.robot_id} - 未能找到路径！")
        return self.path
    
    def is_adjacent_to_table(self, table_position):
        """检查当前位置是否紧邻桌子"""
        if not table_position:
            return False
            
        table_x, table_y = table_position
        x, y = self.position
        
        # 检查是否在桌子的上下左右四个位置
        return (abs(x - table_x) == 1 and y == table_y) or (abs(y - table_y) == 1 and x == table_x)
    
    def move(self):
        """
        沿路径前进一步
        """
        if self.path and len(self.path) > 1:
            next_position = self.path[1]
            if self.env.is_free(next_position):
                self.position = next_position
                self.path_history.append(next_position)
                self.path.pop(0)
                
                # 检查是否已经到达配送目标附近
                if self.current_order:
                    table_position = self.env.get_table_position(self.current_order.table_id)
                    if self.is_adjacent_to_table(table_position):
                        print(f"{self.name}#{self.robot_id} - 已到达桌号 {self.current_order.table_id} 附近，准备配送")
                        # 如果目标就是桌子旁边，且已经到达，则视为送达成功
                        if self.position == self.goal:
                            self.on_goal_reached()
            else:
                print(f"{self.name}#{self.robot_id} - 在 {next_position} 处遇到障碍。")
                self.handle_obstacle(next_position)
        else:
            if self.path and len(self.path) == 1 and self.position == self.goal:
                print(f"{self.name}#{self.robot_id} - 已到达目标位置 {self.goal}")
                self.on_goal_reached()
            else:
                print(f"{self.name}#{self.robot_id} - 无可用路径。")
    
    def handle_obstacle(self, obstacle_position):
        """
        遇到障碍的处理逻辑
        如果启用RAG，将使用智能决策；否则使用基础行为
        """
        if self.enable_rag and self.rag_assistant and self.rag_assistant.is_ready:
            return self._handle_obstacle_with_rag(obstacle_position)
        else:
            # 基础机器人行为
            print(f"{self.name}#{self.robot_id} - 在 {obstacle_position} 遇到障碍，停止配送")
            if self.current_order:
                self.fail_current_order("遇到障碍物，无法继续配送")
            
            # 尝试返回后厨
            self.return_to_kitchen()
    
    def _handle_obstacle_with_rag(self, obstacle_position):
        """使用RAG技术处理障碍物"""
        print(f"\n===== {self.name}#{self.robot_id} - 使用RAG处理障碍物 =====")
        print(f"障碍物位置: {obstacle_position}")
        
        # 检查该位置是否真的是障碍
        x, y = obstacle_position
        if 0 <= x < self.env.height and 0 <= y < self.env.width:
            grid_value = self.env.grid[x][y]
            print(f"该位置的网格值: {grid_value} (0=空地, 1=障碍物, 2=桌子, 3=后厨)")
        
        # 使用RAG助手做决策
        decision = self.rag_assistant.make_decision(
            situation_type="obstacle", 
            robot_id=self.robot_id,
            position=self.position, 
            goal=self.goal, 
            context=obstacle_position
        )
        
        print(f"{self.name}#{self.robot_id} - RAG决策：{decision}")
        
        # 根据决策选择行动
        if decision == "绕行" or decision == "重新规划" or decision == "探索新路径":
            print(f"决策: {decision} - 尝试找到替代路径")
            # 尝试找到绕开当前障碍的路径
            self.find_alternative_path(obstacle_position)
        elif decision == "等待" or decision == "等待片刻后重试":
            print(f"决策: {decision} - 等待后再尝试")
            # 模拟等待
            print(f"{self.name}#{self.robot_id} - 等待片刻后再尝试...")
            time.sleep(0.5)  # 模拟等待0.5秒
            # 保持当前路径，但移除第一个点以避免立即再次尝试相同的移动
            if len(self.path) > 1:
                self.path.pop(0)
        elif decision == "报告无法达到":
            print(f"决策: {decision} - 放弃当前任务")
            print(f"{self.name}#{self.robot_id} - 路径完全阻塞，无法到达目标")
            if self.current_order:
                self.fail_current_order("路径被阻塞，无法到达目标桌位")
            else:
                # 如果没有当前订单，尝试返回后厨
                self.return_to_kitchen()
        
        print(f"===== 障碍物处理完成 =====\n")
    
    def find_alternative_path(self, obstacle_position):
        """
        尝试找到绕开障碍物的替代路径
        """
        # 当前位置到目标的路径已被阻塞，需要找替代路径
        
        # 策略1: 尝试直接重新规划
        print(f"{self.name}#{self.robot_id} - 尝试重新规划路径...")
        new_path = self.planner.find_path(self.position, self.goal)
        
        if new_path:
            self.path = new_path
            print(f"{self.name}#{self.robot_id} - 找到新路径: {self.path}")
            return True
        
        # 策略2: 如果直接重规划失败，尝试先向周围几个方向移动，然后再规划
        print(f"{self.name}#{self.robot_id} - 直接路径规划失败，尝试探索周围区域...")
        
        # 获取当前位置的所有邻居
        neighbors = self.env.neighbors(self.position)
        
        # 按照与目标的距离排序邻居
        neighbors.sort(key=lambda pos: self.planner.heuristic(pos, self.goal))
        
        # 尝试从每个邻居位置规划到目标
        for next_pos in neighbors:
            if next_pos == obstacle_position:
                continue  # 跳过障碍位置
            
            temp_path = self.planner.find_path(next_pos, self.goal)
            if temp_path:
                # 找到从邻居到目标的路径，先移动到这个邻居
                self.path = [self.position, next_pos] + temp_path[1:]
                print(f"{self.name}#{self.robot_id} - 找到绕行路径，经过 {next_pos}")
                return True
        
        print(f"{self.name}#{self.robot_id} - 无法找到任何有效的替代路径")
        return False
    
    def assign_order(self, order):
        """
        分配订单给机器人
        """
        if not self.idle:
            print(f"{self.name}#{self.robot_id} - 当前正忙，无法接受新订单")
            return False
            
        self.current_order = order
        self.idle = False
            
        # 设置目标位置为订单对应的桌子位置
        table_position = self.env.get_table_position(order.table_id)
        if table_position:
            # 寻找桌子周围的可通行位置作为目标
            # (桌子本身不可通行，需要找桌子旁边的位置)
            table_x, table_y = table_position
            adjacent_positions = [
                (table_x-1, table_y), (table_x+1, table_y),
                (table_x, table_y-1), (table_x, table_y+1)
            ]
            
            # 过滤出可通行的位置
            valid_positions = [pos for pos in adjacent_positions if self.env.is_free(pos)]
            
            if valid_positions:
                # 选择第一个可用位置作为目标
                self.goal = valid_positions[0]
                print(f"{self.name}#{self.robot_id} - 接受订单 #{order.order_id}，目标桌号: {order.table_id}")
                print(f"桌子位置: {table_position}, 配送目标位置: {self.goal}")
                return self.plan_path()
            else:
                print(f"{self.name}#{self.robot_id} - 无法找到桌号 {order.table_id} 周围的可通行位置")
                self.current_order = None
                self.idle = True
                return False
        else:
            print(f"{self.name}#{self.robot_id} - 未找到桌号 {order.table_id} 的位置")
            self.current_order = None
            self.idle = True
            return False
    
    def on_goal_reached(self):
        """当到达目标位置时的回调"""
        if self.current_order:
            # 检查是否临近对应的桌子
            table_position = self.env.get_table_position(self.current_order.table_id)
            is_near_table = self.is_adjacent_to_table(table_position)
            
            print(f"{self.name}#{self.robot_id} - 到达目标位置 {self.position}")
            
            if is_near_table:
                print(f"{self.name}#{self.robot_id} - 成功送达订单 #{self.current_order.order_id} 到桌号 {self.current_order.table_id}")
                # 添加到已送达订单列表
                self.delivered_orders.append(self.current_order)
                
                # 标记为已完成订单，但暂时不清除current_order
                # 这样main.py中的检查可以捕获到订单已送达
                # 设置一个delivered_flag标志，表示此订单已经送达
                self.current_order.delivered_flag = True
                
                # 返回后厨
                self.return_to_kitchen()
            else:
                print(f"{self.name}#{self.robot_id} - 警告：已到达目标位置，但不在桌号 {self.current_order.table_id} 附近")
                self.fail_current_order("配送位置不正确")
        else:
            # 到达后厨
            kitchen_positions = self.env.get_kitchen_positions()
            if self.position in kitchen_positions:
                print(f"{self.name}#{self.robot_id} - 已返回后厨")
                # 如果有已送达的订单标记，此时可以安全清除
                if hasattr(self, 'current_order') and self.current_order and hasattr(self.current_order, 'delivered_flag'):
                    self.current_order = None
                self.idle = True
    
    def fail_current_order(self, reason="未知原因"):
        """标记当前订单为失败"""
        if self.current_order:
            print(f"{self.name}#{self.robot_id} - 订单 #{self.current_order.order_id} 配送失败: {reason}")
            self.failed_orders.append(self.current_order)
            self.current_order = None
            
            # 返回后厨
            self.return_to_kitchen()
    
    def return_to_kitchen(self):
        """返回后厨位置"""
        # 获取所有后厨位置
        kitchen_positions = self.env.get_kitchen_positions()
        if not kitchen_positions:
            print(f"{self.name}#{self.robot_id} - 错误：没有后厨位置")
            self.idle = True
            return False
            
        # 尝试路径规划到所有后厨位置，选择最近的一个
        successful_path = None
        chosen_kitchen = None
        
        print(f"{self.name}#{self.robot_id} - 尝试返回后厨，当前有 {len(kitchen_positions)} 个后厨位置")
        
        for kitchen_pos in kitchen_positions:
            self.goal = kitchen_pos
            print(f"{self.name}#{self.robot_id} - 尝试规划到后厨位置 {kitchen_pos}")
            path = self.planner.find_path(self.position, kitchen_pos)
            
            if path:
                # 找到有效路径，使用这个后厨位置
                successful_path = path
                chosen_kitchen = kitchen_pos
                print(f"{self.name}#{self.robot_id} - 成功找到返回后厨 {kitchen_pos} 的路径")
                break
        
        if successful_path:
            self.path = successful_path
            self.goal = chosen_kitchen
            self.kitchen_position = chosen_kitchen  # 更新当前使用的后厨位置
            print(f"{self.name}#{self.robot_id} - 开始返回后厨 {chosen_kitchen}")
            self.idle = False  # 返回途中不是空闲状态
            return True
        else:
            # 无法找到返回任何后厨的路径
            print(f"{self.name}#{self.robot_id} - 无法找到返回任何后厨的路径")
            # 如果已经成功送达了订单但无法返回后厨，仍然清除当前订单
            if hasattr(self, 'current_order') and self.current_order and hasattr(self.current_order, 'delivered_flag'):
                print(f"{self.name}#{self.robot_id} - 订单已送达，但无法返回后厨")
                self.current_order = None
            self.idle = True  # 设为空闲，等待新指令
            return False
    
    def is_idle(self):
        """检查机器人是否空闲"""
        kitchen_positions = self.env.get_kitchen_positions()
        
        # 如果没有当前订单，且位于后厨位置，则认为是空闲状态
        if self.current_order is None and self.position in kitchen_positions:
            self.idle = True
            return True
        
        # 如果无路径可走，也认为是空闲状态
        if not self.path:
            # 如果正在返回后厨的途中，到达后厨后设为空闲
            if self.position in kitchen_positions:
                self.idle = True
                return True
                
        return self.idle
    
    def simulate(self, max_steps=50):
        """
        模拟机器人执行任务，直至到达目标或超出步数限制
        """
        if not self.goal:
            print(f"{self.name}#{self.robot_id} - 未设置目标位置，无法开始模拟")
            return False
            
        self.plan_path()
        steps = 0
        
        while self.position != self.goal and self.path is not None:
            print(f"步骤 {steps}：{self.name}#{self.robot_id} - 当前位置 {self.position}")
            self.env.display(self.path, self.position)
            self.move()
            steps += 1
            
            if steps > max_steps:
                print(f"{self.name}#{self.robot_id} - 仿真结束：步数过多。")
                if self.current_order:
                    self.fail_current_order("模拟步数超限")
                break
                
        if self.position == self.goal:
            print(f"{self.name}#{self.robot_id} - 任务完成，在 {steps} 步后到达目标 {self.position}。")
            self.on_goal_reached()
            return True
        return False
    
    def get_statistics(self):
        """获取机器人的配送统计信息"""
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
        综合测试RAG功能的方法，仅在RAG机器人中有效
        """
        if not self.enable_rag or not self.rag_assistant or not self.rag_assistant.is_ready:
            print(f"{self.name}#{self.robot_id} - 未启用RAG功能，无法执行综合测试")
            return
            
        print(f"\n===== {self.name}#{self.robot_id} - 开始综合测试 =====")
        
        # 测试不同情况下的障碍物处理
        test_positions = [
            (self.position[0] + 1, self.position[1]),  # 正前方
            (self.position[0], self.position[1] + 1),  # 右侧
            (self.position[0] - 1, self.position[1]),  # 后方
            (self.position[0], self.position[1] - 1),  # 左侧
        ]
        
        for pos in test_positions:
            print(f"\n测试障碍物位置: {pos}")
            # 跳过环境边界外的位置
            if not (0 <= pos[0] < self.env.height and 0 <= pos[1] < self.env.width):
                print(f"位置 {pos} 超出环境边界，跳过测试")
                continue
                
            # 保存原始网格值
            original_value = self.env.grid[pos[0]][pos[1]]
            
            # 将该位置临时设为障碍物（如果不是障碍物）
            if original_value == 0:  # 如果是空地
                self.env.grid[pos[0]][pos[1]] = 1  # 设为障碍物
                
                # 测试障碍物处理
                print(f"模拟在 {pos} 处遇到障碍物")
                self._handle_obstacle_with_rag(pos)
                
                # 恢复原始网格值
                self.env.grid[pos[0]][pos[1]] = original_value
            else:
                print(f"位置 {pos} 当前值为 {original_value}，不是空地，跳过测试")
        
        print(f"\n===== 综合测试完成 =====\n") 