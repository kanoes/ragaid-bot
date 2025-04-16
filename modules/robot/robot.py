from modules.robot.path_planner import PathPlanner
from modules.robot.order import Order
from modules.rag.rag_assistant import RagAssistant
import random
import time
import sys

class Robot:
    """
    机器人基础类，定义基本路径规划、移动、障碍物处理功能
    enable_rag选项可以启用智能决策功能
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
        self.enable_rag = enable_rag
        self.name = "智能机器人" if self.enable_rag else "基础机器人"
        
        # 获取所有厨房位置
        kitchen_positions = environment.get_kitchen_positions()
        
        # 如果没有提供起始点，默认使用环境中的第一个厨房位置
        if start is None:
            if kitchen_positions:
                self.start = kitchen_positions[0]
            else:
                self.start = (0, 0)  # 默认起始点
        else:
            self.start = start
            
        self.goal = goal  # 目标位置可以为None，后续从订单中设置
        self.position = self.start  # 当前位置初始为起始点
        self.planner = PathPlanner(environment)
        self.path = []  # 当前规划的路径
        self.path_history = [self.start]  # 记录每一步的坐标以便可视化
        
        # 订单相关属性
        self.current_order = None  # 当前配送中的订单
        self.delivered_orders = []  # 已配送订单列表
        self.failed_orders = []    # 配送失败订单列表
        self.idle = True           # 机器人是否空闲
        self.kitchen_position = self.start  # 厨房位置（默认为起始点）
        
        # 初始化统计信息
        self._stats = {
            "successful_deliveries": 0,
            "failed_deliveries": 0,
            "total_distance": 0,
            "total_time": 0
        }
        
        # 初始化RAG助手（如果启用）
        self.rag_assistant = None
        if self.enable_rag:
            print(f"\n===== 初始化{self.name} #{robot_id}的RAG功能 =====")
            try:
                self.rag_assistant = RagAssistant(
                    api_key=api_key,
                    knowledge_file=knowledge_file
                )
                print(f"RAG功能{'准备就绪' if self.rag_assistant.is_ready else '初始化失败'}")
            except Exception as e:
                print(f"RAG助手初始化错误: {e}")
                self.enable_rag = False
                self.name = "基础机器人"  # 降级为基础机器人
            print("========================================\n")
        
        # 显示初始化信息
        print(f"{self.name}#{self.robot_id} - 在位置{self.start}初始化，初始厨房位置{self.kitchen_position}")
        print(f"环境中有{len(kitchen_positions)}个厨房位置: {kitchen_positions}")

    def plan_path(self):
        """规划从当前位置到目标位置的路径"""
        if self.goal is None:
            print("未设置目标位置")
            return None
            
        self.path = self.planner.find_path(self.position, self.goal)
        if self.path:
            print(f"{self.name}#{self.robot_id} - 从{self.position}到{self.goal}的规划路径：{self.path}")
        else:
            print(f"{self.name}#{self.robot_id} - 未找到路径！")
        return self.path
    
    def is_adjacent_to_table(self, table_position):
        """检查当前位置是否与桌子相邻"""
        if not table_position:
            return False
            
        table_x, table_y = table_position
        x, y = self.position
        
        # 检查是否在桌子的上下左右四个方向
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
                
                # 检查是否接近配送目标
                if self.current_order:
                    table_position = self.env.get_table_position(self.current_order.table_id)
                    if self.is_adjacent_to_table(table_position):
                        print(f"{self.name}#{self.robot_id} - 已接近桌号{self.current_order.table_id}，准备配送")
                        # 如果目标是桌子旁边并且已到达，则认为配送成功
                        if self.position == self.goal:
                            self.on_goal_reached()
            else:
                print(f"{self.name}#{self.robot_id} - 在{next_position}遇到障碍物。")
                self.handle_obstacle(next_position)
        else:
            if self.path and len(self.path) == 1 and self.position == self.goal:
                print(f"{self.name}#{self.robot_id} - 已到达目标位置{self.goal}")
                self.on_goal_reached()
            else:
                print(f"{self.name}#{self.robot_id} - 没有可用路径。")
    
    def handle_obstacle(self, obstacle_position):
        """
        处理遇到障碍物的逻辑
        如果启用了RAG则使用智能决策，否则使用基础行为
        """
        if self.enable_rag and self.rag_assistant and self.rag_assistant.is_ready:
            return self._handle_obstacle_with_rag(obstacle_position)
        else:
            # 基础机器人行为
            print(f"{self.name}#{self.robot_id} - 在{obstacle_position}遇到障碍物，停止配送")
            if self.current_order:
                self.fail_current_order("遇到障碍物，无法继续配送")
            
            # 尝试返回厨房
            self.return_to_kitchen()
    
    def _handle_obstacle_with_rag(self, obstacle_position):
        """使用RAG技术处理障碍物"""
        print(f"\n===== {self.name}#{self.robot_id} - 使用RAG处理障碍物 =====")
        print(f"障碍物位置: {obstacle_position}")
        
        # 确认该位置是否确实是障碍物
        x, y = obstacle_position
        if 0 <= x < self.env.height and 0 <= y < self.env.width:
            grid_value = self.env.grid[x][y]
            print(f"该位置的网格值: {grid_value} (0=空闲空间, 1=障碍物, 2=桌子, 3=厨房)")
        
        # 使用RAG助手进行决策
        decision = self.rag_assistant.make_decision(
            situation_type="obstacle", 
            robot_id=self.robot_id,
            position=self.position, 
            goal=self.goal, 
            context=obstacle_position
        )
        
        print(f"{self.name}#{self.robot_id} - RAG决策：{decision}")
        
        # 根据决策选择行动
        if decision == "绕行" or decision == "重新规划" or decision == "寻找新路径":
            print(f"决策: {decision} - 寻找替代路径")
            # 寻找绕过当前障碍物的路径
            self.find_alternative_path(obstacle_position)
        elif decision == "等待" or decision == "稍等后重试":
            print(f"决策: {decision} - 等待后重试")
            # 模拟等待
            print(f"{self.name}#{self.robot_id} - 稍等后重试...")
            time.sleep(0.5)  # 模拟0.5秒等待
            # 删除第一个点以避免立即重试相同的移动
            if len(self.path) > 1:
                self.path.pop(0)
        elif decision == "报告无法到达":
            print(f"决策: {decision} - 放弃当前任务")
            print(f"{self.name}#{self.robot_id} - 路径完全被阻断，无法到达目标")
            if self.current_order:
                self.fail_current_order("路径被阻断，无法到达目标桌子")
            else:
                # 如果没有当前订单，尝试返回厨房
                self.return_to_kitchen()
        
        print(f"===== 障碍物处理完成 =====\n")
    
    def find_alternative_path(self, obstacle_position):
        """
        寻找绕过障碍物的替代路径
        """
        # 移除障碍物位置
        if obstacle_position in self.path:
            self.path.remove(obstacle_position)
        
        # 重新规划路径
        new_path = self.planner.find_path(self.position, self.goal)
        if new_path:
            print(f"{self.name}#{self.robot_id} - 找到新路径: {new_path}")
            self.path = new_path
        else:
            print(f"{self.name}#{self.robot_id} - 找不到替代路径，尝试返回厨房")
            if self.current_order:
                self.fail_current_order("无法找到到达目标的替代路径")
            self.return_to_kitchen()
    
    def assign_order(self, order):
        """
        分配订单给机器人
        
        参数:
            order: 要配送的订单对象
            
        返回:
            bool: 分配是否成功
        """
        # 检查机器人是否空闲
        if not self.idle:
            print(f"{self.name}#{self.robot_id} - 当前正忙，无法接受新订单")
            return False
        
        # 保存当前订单
        self.current_order = order
        self.idle = False
        
        # 设置配送目标（桌子位置）
        table_position = self.env.get_table_position(order.table_id)
        if not table_position:
            print(f"{self.name}#{self.robot_id} - 错误: 找不到桌号 {order.table_id} 的位置")
            self.fail_current_order("找不到目标桌子位置")
            return False
        
        # 确定目标位置（通常是桌子附近的位置）
        # 这里我们选择桌子旁边的空闲位置作为目标
        table_x, table_y = table_position
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:  # 四个方向
            potential_goal = (table_x + dx, table_y + dy)
            if self.env.is_free(potential_goal):
                self.goal = potential_goal
                break
        else:
            # 如果没有找到空闲位置，报告错误
            print(f"{self.name}#{self.robot_id} - 错误: 桌号 {order.table_id} 周围没有可到达的位置")
            self.fail_current_order("目标桌子周围没有可到达的位置")
            return False
        
        # 规划路径并开始配送
        print(f"{self.name}#{self.robot_id} - 接受订单 #{order.order_id} 配送到桌号 {order.table_id}")
        print(f"目标桌子位置: {table_position}, 配送目标位置: {self.goal}")
        path = self.plan_path()
        if not path:
            print(f"{self.name}#{self.robot_id} - 无法规划到目标桌子的路径，取消订单")
            self.fail_current_order("无法规划到目标桌子的路径")
            return False
        
        # 开始配送
        order.start_delivery()
        return True
    
    def on_goal_reached(self):
        """
        到达目标时的处理
        """
        if self.current_order:
            print(f"{self.name}#{self.robot_id} - 已到达桌号 {self.current_order.table_id}，完成配送")
            # 标记订单为已配送
            self.current_order.complete_delivery()
            # 将订单添加到已配送列表
            self.delivered_orders.append(self.current_order)
            # 添加统计数据
            elapsed = self.current_order.get_delivery_time()
            if elapsed:
                print(f"配送用时: {elapsed:.2f}秒")
                # 更新机器人的统计信息
                self.stats["total_time"] += elapsed
                self.stats["total_distance"] += len(self.path_history)
                self.stats["successful_deliveries"] += 1
                
            # 清除当前订单和目标
            self.current_order = None
            self.goal = None
        
        # 返回厨房
        self.return_to_kitchen()
    
    def fail_current_order(self, reason="未知原因"):
        """标记当前订单配送失败"""
        if self.current_order:
            print(f"{self.name}#{self.robot_id} - 订单 #{self.current_order.order_id} 配送失败: {reason}")
            self.current_order.fail_delivery()
            self.failed_orders.append(self.current_order)
            self.current_order = None
            self.stats["failed_deliveries"] += 1
    
    def return_to_kitchen(self):
        """返回厨房位置"""
        # 清除当前目标和路径
        self.goal = self.kitchen_position
        self.path = []
        
        print(f"{self.name}#{self.robot_id} - 返回厨房位置 {self.kitchen_position}")
        
        # 规划返回厨房的路径
        path = self.planner.find_path(self.position, self.kitchen_position)
        if path:
            self.path = path
            print(f"{self.name}#{self.robot_id} - 规划返回厨房的路径: {path}")
            
            # 模拟返回厨房
            steps = 0
            max_steps = 100  # 防止无限循环
            
            while self.path and steps < max_steps:
                self.move()
                steps += 1
                if self.position == self.kitchen_position:
                    print(f"{self.name}#{self.robot_id} - 已返回厨房")
                    break
            
            if steps >= max_steps:
                print(f"{self.name}#{self.robot_id} - 警告: 返回厨房所需步数超过最大限制")
            
            # 重置闲置状态
            self.idle = True
        else:
            print(f"{self.name}#{self.robot_id} - 无法规划返回厨房的路径，不移动")
            # 强制返回厨房
            self.position = self.kitchen_position
            self.path_history.append(self.position)
            self.idle = True
            print(f"{self.name}#{self.robot_id} - 已重置到厨房位置")
    
    def is_idle(self):
        """检查机器人是否空闲"""
        return self.idle
    
    @property
    def stats(self):
        """获取机器人的统计信息"""
        if not hasattr(self, "_stats"):
            self._stats = {
                "successful_deliveries": 0,
                "failed_deliveries": 0,
                "total_distance": 0,
                "total_time": 0
            }
        return self._stats
    
    def simulate(self, max_steps=50):
        """
        模拟机器人移动
        
        参数:
            max_steps: 最大模拟步数
        """
        steps = 0
        while self.path and steps < max_steps:
            print(f"\n步骤 {steps+1}: 当前位置 {self.position}")
            self.move()
            steps += 1
            
            # 如果到达目标或者无路可走，结束模拟
            if (self.position == self.goal) or (not self.path):
                break
        
        print(f"\n模拟结束，共执行 {steps} 步")
        print(f"最终位置: {self.position}")
        print(f"路径历史: {self.path_history}")
        
        return steps, self.path_history
    
    def display_stats(self):
        """显示机器人的统计信息"""
        print(f"\n===== {self.name} #{self.robot_id} 统计信息 =====")
        print(f"成功配送数: {self.stats['successful_deliveries']}")
        print(f"失败配送数: {self.stats['failed_deliveries']}")
        
        total_deliveries = self.stats['successful_deliveries'] + self.stats['failed_deliveries']
        if total_deliveries > 0:
            success_rate = self.stats['successful_deliveries'] / total_deliveries * 100
            print(f"配送成功率: {success_rate:.2f}%")
        
        if self.stats['successful_deliveries'] > 0:
            avg_distance = self.stats['total_distance'] / self.stats['successful_deliveries']
            avg_time = self.stats['total_time'] / self.stats['successful_deliveries']
            print(f"平均路径长度: {avg_distance:.2f}")
            print(f"平均配送时间: {avg_time:.2f}秒")
    
    def comprehensive_test(self):
        """执行全面测试，评估机器人性能"""
        print(f"\n===== {self.name} #{self.robot_id} 全面测试 =====")
        
        # 重置统计信息
        self._stats = {
            "successful_deliveries": 0,
            "failed_deliveries": 0,
            "total_distance": 0,
            "total_time": 0
        }
        
        # 获取环境中的所有桌子
        all_tables = list(self.env.tables.keys())
        if not all_tables:
            print("环境中没有桌子，无法进行测试")
            return
        
        
        # 创建测试订单
        test_orders = []
        for i in range(5):  # 测试5个订单
            table_id = random.choice(all_tables)
            order = Order(i+1, table_id, 0)  # 准备时间设为0
            test_orders.append(order)
        
        # 执行测试
        for order in test_orders:
            print(f"\n处理测试订单 #{order.order_id} 到桌号 {order.table_id}")
            success = self.assign_order(order)
            if success:
                # 模拟配送过程
                steps, _ = self.simulate(max_steps=100)
                print(f"订单处理完成，用了 {steps} 步")
            else:
                print(f"订单分配失败")
        
        # 显示最终统计
        self.display_stats()
        
        return self.stats

    def take_order(self, order):
        """
        处理订单，兼容main.py中的调用
        
        参数:
            order: 字典格式的订单 {'table_id': xxx, 'items': xxx, 'time': xxx, ...}
            
        返回:
            bool: 订单处理是否成功
        """
        # 直接从当前模块导入，避免循环导入
        # 获取当前模块
        current_module = sys.modules[__name__]
        
        # 将字典格式转换为Order对象
        if isinstance(order, dict):
            table_id = order.get('table_id')
            items = order.get('items', 1)
            # 从'time'字段获取准备时间，这与main.py中使用的字段名一致
            prep_time = order.get('time', 0) or order.get('prep_time', 0)
            
            # 导入Order类（如果当前模块没有，则从robot.order导入）
            if hasattr(current_module, 'Order'):
                OrderClass = current_module.Order
            else:
                from modules.robot.order import Order as OrderClass
                
            order_obj = OrderClass(
                order_id=self.stats['successful_deliveries'] + self.stats['failed_deliveries'] + 1,
                table_id=table_id,
                prep_time=prep_time,  # 传递准备时间
                items=[f"物品{i+1}" for i in range(items)]
            )
        else:
            # 如果已经是Order对象，直接使用
            order_obj = order
            
        # 分配订单
        return self.assign_order(order_obj)

class AIEnhancedRobot(Robot):
    """
    AI增强型机器人，继承自基础机器人类，但默认启用RAG功能
    """
    def __init__(self, environment, start=None, goal=None, robot_id=1, api_key=None, knowledge_file=None):
        """
        初始化AI增强型机器人
        
        所有参数与Robot类相同，但默认启用RAG功能
        """
        # 调用父类构造函数，强制启用RAG
        super().__init__(
            environment=environment,
            start=start,
            goal=goal, 
            robot_id=robot_id,
            enable_rag=True,  # 总是启用RAG
            api_key=api_key,
            knowledge_file=knowledge_file
        )
        
        # 如果RAG不可用，发出警告
        if not self.enable_rag:
            print(f"警告: RAG功能不可用，AI增强型机器人将以基础模式运行")
    
    def handle_obstacle(self, obstacle_position):
        """重写障碍物处理方法以优先使用AI决策"""
        # 始终尝试使用智能决策，但如果不可用则回退到基础行为
        if self.rag_assistant and self.rag_assistant.is_ready:
            return self._handle_obstacle_with_rag(obstacle_position)
        else:
            print(f"{self.name}#{self.robot_id} - RAG不可用，使用基础障碍物处理")
            # 调用父类方法
            return super().handle_obstacle(obstacle_position)
    
    def find_alternative_path(self, obstacle_position):
        """增强版的替代路径寻找算法"""
        # 使用更复杂的逻辑寻找替代路径
        print(f"{self.name}#{self.robot_id} - 使用增强型寻路算法...")
        
        # 移除障碍物位置
        if obstacle_position in self.path:
            self.path.remove(obstacle_position)
        
        # 优先尝试几种不同的绕行策略
        strategies = [
            "直接重规划",  # 直接重新规划路径
            "后退一步",    # 后退一步再规划
            "扩大搜索范围"  # 扩大搜索范围寻找路径
        ]
        
        for strategy in strategies:
            print(f"尝试策略: {strategy}")
            
            if strategy == "直接重规划":
                new_path = self.planner.find_path(self.position, self.goal)
                if new_path:
                    print(f"直接重规划成功")
                    self.path = new_path
                    return True
                    
            elif strategy == "后退一步":
                # 如果路径历史中有至少两个点，尝试后退一步
                if len(self.path_history) >= 2:
                    prev_position = self.path_history[-2]
                    if self.env.is_free(prev_position):
                        print(f"后退到位置 {prev_position}")
                        self.position = prev_position
                        self.path_history.append(prev_position)
                        new_path = self.planner.find_path(self.position, self.goal)
                        if new_path:
                            print(f"后退后重规划成功")
                            self.path = new_path
                            return True
            
            elif strategy == "扩大搜索范围":
                # 这个策略在PathPlanner中已实现，这里只需直接调用
                new_path = self.planner.find_path(self.position, self.goal)
                if new_path:
                    print(f"扩大搜索范围后找到路径")
                    self.path = new_path
                    return True
        
        # 如果所有策略都失败，回退到基础行为
        print(f"{self.name}#{self.robot_id} - 所有绕行策略失败，返回厨房")
        if self.current_order:
            self.fail_current_order("无法找到安全的替代路径")
        self.return_to_kitchen()
        return False 