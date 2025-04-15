# robot.py

from path_planner import PathPlanner

class Robot:
    """
    机器人基类，定义基本的路径规划、移动和障碍处理功能
    """
    def __init__(self, environment, start=None, goal=None, robot_id=1):
        self.env = environment
        self.robot_id = robot_id  # 机器人ID
        
        # 如果未提供起点，默认为环境中第一个后厨位置
        if start is None:
            kitchen_positions = environment.get_kitchen_positions()
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
            self.goal = table_position
            print(f"机器人#{self.robot_id} - 接受订单 #{order.order_id}，目标桌号: {order.table_id}, 位置: {table_position}")
            return self.plan_path()
        else:
            print(f"机器人#{self.robot_id} - 未找到桌号 {order.table_id} 的位置")
            self.current_order = None
            self.idle = True
            return False
    
    def on_goal_reached(self):
        """当到达目标位置时的回调"""
        if self.current_order:
            print(f"机器人#{self.robot_id} - 成功送达订单 #{self.current_order.order_id} 到桌号 {self.current_order.table_id}")
            self.delivered_orders.append(self.current_order)
            self.current_order = None
            
            # 返回后厨
            self.return_to_kitchen()
    
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
        self.goal = self.kitchen_position
        print(f"机器人#{self.robot_id} - 返回后厨")
        path_to_kitchen = self.plan_path()
        
        if path_to_kitchen:
            self.idle = False  # 返回途中不是空闲状态
        else:
            # 无法找到返回后厨的路径
            print(f"机器人#{self.robot_id} - 无法找到返回后厨的路径")
            self.idle = True  # 设为空闲，等待新指令
    
    def is_idle(self):
        """检查机器人是否空闲"""
        # 如果没有当前订单，且位于后厨位置，则认为是空闲状态
        if self.current_order is None and self.position == self.kitchen_position:
            self.idle = True
            return True
        
        # 如果无路径可走，也认为是空闲状态
        if not self.path:
            # 如果正在返回后厨的途中，到达后厨后设为空闲
            if self.position == self.kitchen_position:
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