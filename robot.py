from path_planner import PathPlanner

class Robot:
    """
    机器人基类，定义基本的路径规划、移动和障碍处理功能
    """
    def __init__(self, environment, start=None, goal=None, robot_id=1):
        self.env = environment
        self.robot_id = robot_id  # 机器人ID
        
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
        
        # 打印初始化信息
        print(f"机器人#{self.robot_id} - 初始化在位置 {self.start}，初始后厨位置 {self.kitchen_position}")
        print(f"环境中共有 {len(kitchen_positions)} 个后厨位置: {kitchen_positions}")

    def plan_path(self):
        """规划从当前位置到目标位置的路径"""
        if self.goal is None:
            print("未设置目标位置")
            return None
            
        self.path = self.planner.find_path(self.position, self.goal)
        if self.path:
            print(f"机器人#{self.robot_id} - 从 {self.position} 到 {self.goal} 的规划路径： {self.path}")
        else:
            print(f"机器人#{self.robot_id} - 未能找到路径！")
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
                        print(f"机器人#{self.robot_id} - 已到达桌号 {self.current_order.table_id} 附近，准备配送")
                        # 如果目标就是桌子旁边，且已经到达，则视为送达成功
                        if self.position == self.goal:
                            self.on_goal_reached()
            else:
                print(f"机器人#{self.robot_id} - 在 {next_position} 处遇到障碍。")
                self.handle_obstacle(next_position)
        else:
            if self.path and len(self.path) == 1 and self.position == self.goal:
                print(f"机器人#{self.robot_id} - 已到达目标位置 {self.goal}")
                self.on_goal_reached()
            else:
                print(f"机器人#{self.robot_id} - 无可用路径。")
    
    def handle_obstacle(self, obstacle_position):
        """
        遇到障碍的处理逻辑，基类默认不做特殊处理
        """
        print(f"机器人#{self.robot_id} - 基线机器人：无法处理障碍，停止运动。")
        if self.current_order:
            self.fail_current_order("遇到无法处理的障碍")
    
    def assign_order(self, order):
        """
        分配订单给机器人
        """
        if not self.idle:
            print(f"机器人#{self.robot_id} - 当前正忙，无法接受新订单")
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
                print(f"机器人#{self.robot_id} - 接受订单 #{order.order_id}，目标桌号: {order.table_id}")
                print(f"桌子位置: {table_position}, 配送目标位置: {self.goal}")
                return self.plan_path()
            else:
                print(f"机器人#{self.robot_id} - 无法找到桌号 {order.table_id} 周围的可通行位置")
                self.current_order = None
                self.idle = True
                return False
        else:
            print(f"机器人#{self.robot_id} - 未找到桌号 {order.table_id} 的位置")
            self.current_order = None
            self.idle = True
            return False
    
    def on_goal_reached(self):
        """当到达目标位置时的回调"""
        if self.current_order:
            # 检查是否临近对应的桌子
            table_position = self.env.get_table_position(self.current_order.table_id)
            is_near_table = self.is_adjacent_to_table(table_position)
            
            print(f"机器人#{self.robot_id} - 到达目标位置 {self.position}")
            
            if is_near_table:
                print(f"机器人#{self.robot_id} - 成功送达订单 #{self.current_order.order_id} 到桌号 {self.current_order.table_id}")
                # 添加到已送达订单列表
                self.delivered_orders.append(self.current_order)
                
                # 标记为已完成订单，但暂时不清除current_order
                # 这样main.py中的检查可以捕获到订单已送达
                # 设置一个delivered_flag标志，表示此订单已经送达
                self.current_order.delivered_flag = True
                
                # 返回后厨
                self.return_to_kitchen()
            else:
                print(f"机器人#{self.robot_id} - 警告：已到达目标位置，但不在桌号 {self.current_order.table_id} 附近")
                self.fail_current_order("配送位置不正确")
        else:
            # 到达后厨
            kitchen_positions = self.env.get_kitchen_positions()
            if self.position in kitchen_positions:
                print(f"机器人#{self.robot_id} - 已返回后厨")
                # 如果有已送达的订单标记，此时可以安全清除
                if hasattr(self, 'current_order') and self.current_order and hasattr(self.current_order, 'delivered_flag'):
                    self.current_order = None
                self.idle = True
    
    def fail_current_order(self, reason="未知原因"):
        """标记当前订单为失败"""
        if self.current_order:
            print(f"机器人#{self.robot_id} - 订单 #{self.current_order.order_id} 配送失败: {reason}")
            self.failed_orders.append(self.current_order)
            self.current_order = None
            
            # 返回后厨
            self.return_to_kitchen()
    
    def return_to_kitchen(self):
        """返回后厨位置"""
        # 获取所有后厨位置
        kitchen_positions = self.env.get_kitchen_positions()
        if not kitchen_positions:
            print(f"机器人#{self.robot_id} - 错误：没有后厨位置")
            self.idle = True
            return False
            
        # 尝试路径规划到所有后厨位置，选择最近的一个
        successful_path = None
        chosen_kitchen = None
        
        print(f"机器人#{self.robot_id} - 尝试返回后厨，当前有 {len(kitchen_positions)} 个后厨位置")
        
        for kitchen_pos in kitchen_positions:
            self.goal = kitchen_pos
            print(f"机器人#{self.robot_id} - 尝试规划到后厨位置 {kitchen_pos}")
            path = self.planner.find_path(self.position, kitchen_pos)
            
            if path:
                # 找到有效路径，使用这个后厨位置
                successful_path = path
                chosen_kitchen = kitchen_pos
                print(f"机器人#{self.robot_id} - 成功找到返回后厨 {kitchen_pos} 的路径")
                break
        
        if successful_path:
            self.path = successful_path
            self.goal = chosen_kitchen
            self.kitchen_position = chosen_kitchen  # 更新当前使用的后厨位置
            print(f"机器人#{self.robot_id} - 开始返回后厨 {chosen_kitchen}")
            self.idle = False  # 返回途中不是空闲状态
            return True
        else:
            # 无法找到返回任何后厨的路径
            print(f"机器人#{self.robot_id} - 无法找到返回任何后厨的路径")
            # 如果已经成功送达了订单但无法返回后厨，仍然清除当前订单
            if hasattr(self, 'current_order') and self.current_order and hasattr(self.current_order, 'delivered_flag'):
                print(f"机器人#{self.robot_id} - 订单已送达，但无法返回后厨")
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
            print(f"机器人#{self.robot_id} - 未设置目标位置，无法开始模拟")
            return False
            
        self.plan_path()
        steps = 0
        
        while self.position != self.goal and self.path is not None:
            print(f"步骤 {steps}：机器人#{self.robot_id} - 当前位置 {self.position}")
            self.env.display(self.path, self.position)
            self.move()
            steps += 1
            
            if steps > max_steps:
                print(f"机器人#{self.robot_id} - 仿真结束：步数过多。")
                if self.current_order:
                    self.fail_current_order("模拟步数超限")
                break
                
        if self.position == self.goal:
            print(f"机器人#{self.robot_id} - 任务完成，在 {steps} 步后到达目标 {self.position}。")
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