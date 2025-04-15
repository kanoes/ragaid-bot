# main.py

import time
import threading
import argparse
import os
import json
from restaurant_grid import RestaurantEnvironment
from restaurant_layout import create_restaurant_layout, print_restaurant_info
from baseline.robot_baseline import BaselineRobot
from rag_robot.robot_rag import RagRobot
from visualization import animate_robot_path
from order import OrderManager, Order

def process_kitchen(order_manager, stop_event):
    """
    厨房处理线程，负责模拟厨房准备订单
    """
    while not stop_event.is_set():
        order_manager.process_kitchen_simulation()
        time.sleep(0.5)

def run_baseline_simulation(restaurant, order_manager, robot_count=1):
    """
    使用基线机器人运行订单配送模拟
    """
    print("\n===== 基线机器人仿真开始 =====")
    
    # 创建机器人
    robots = []
    for i in range(robot_count):
        robot = BaselineRobot(restaurant, robot_id=i+1)
        robots.append(robot)
    
    # 启动厨房处理线程
    stop_event = threading.Event()
    kitchen_thread = threading.Thread(target=process_kitchen, args=(order_manager, stop_event))
    kitchen_thread.daemon = True
    kitchen_thread.start()
    
    # 运行模拟
    simulation_time = 0
    max_simulation_time = 60  # 最多模拟60秒
    
    try:
        while simulation_time < max_simulation_time:
            # 每个时间步检查
            print(f"\n当前模拟时间: {simulation_time}秒")
            
            # 检查是否有准备好的订单需要分配
            for robot in robots:
                if robot.is_idle():
                    # 机器人空闲，检查是否有待配送订单
                    next_order = order_manager.get_next_delivery_order()
                    if next_order:
                        # 分配订单给机器人
                        order_manager.assign_order_to_robot(next_order.order_id, robot.robot_id)
                        robot.assign_order(next_order)
            
            # 所有机器人执行一步
            for robot in robots:
                if robot.path:
                    robot.move()
                    
                    # 检查当前订单状态
                    if robot.position == robot.goal and robot.current_order:
                        # 到达目标，完成订单
                        order_manager.complete_order_delivery(robot.current_order.order_id)
            
            # 睡眠一段时间模拟真实环境
            time.sleep(0.5)
            simulation_time += 1
            
            # 如果没有待处理的订单且所有机器人都空闲，提前结束模拟
            if (not order_manager.waiting_orders and 
                not order_manager.preparing_orders and 
                not order_manager.ready_orders and
                all(robot.is_idle() for robot in robots)):
                print("所有订单已处理完成，模拟结束")
                break
    
    finally:
        # 停止厨房处理线程
        stop_event.set()
        kitchen_thread.join(timeout=1)
    
    # 打印统计信息
    print("\n===== 基线机器人仿真结果 =====")
    print("订单统计:")
    stats = order_manager.get_statistics()
    print(f"  总订单数: {stats['total_orders']}")
    print(f"  完成订单数: {stats['completed_orders']}")
    print(f"  失败订单数: {stats['failed_orders']}")
    print(f"  配送成功率: {stats['success_rate']:.2f}%")
    print(f"  平均配送时间: {stats['avg_delivery_time']:.2f}秒")
    
    # 打印每个机器人的路径
    for i, robot in enumerate(robots):
        print(f"\n机器人 #{i+1} 路径:")
        if robot.path_history:
            animate_robot_path(robot.path_history, title=f"基线机器人 #{i+1} 路径")
        else:
            print("  无路径记录")
    
    return stats

def run_rag_simulation(restaurant, order_manager, robot_count=1, api_key=None, config_file=None, knowledge_file=None):
    """
    使用RAG机器人运行订单配送模拟
    
    参数:
        restaurant: 餐厅环境
        order_manager: 订单管理器
        robot_count: 机器人数量
        api_key: OpenAI API密钥
        config_file: 配置文件路径
        knowledge_file: 知识库文件路径
    """
    print("\n===== RAG机器人仿真开始 =====")
    
    # 创建机器人
    robots = []
    for i in range(robot_count):
        try:
            robot = RagRobot(restaurant, robot_id=i+1, api_key=api_key, 
                             config_file=config_file, knowledge_file=knowledge_file)
            robots.append(robot)
        except Exception as e:
            print(f"创建RAG机器人失败: {e}")
            print("使用基线机器人替代")
            robot = BaselineRobot(restaurant, robot_id=i+1)
            robots.append(robot)
    
    # 启动厨房处理线程
    stop_event = threading.Event()
    kitchen_thread = threading.Thread(target=process_kitchen, args=(order_manager, stop_event))
    kitchen_thread.daemon = True
    kitchen_thread.start()
    
    # 运行模拟
    simulation_time = 0
    max_simulation_time = 60  # 最多模拟60秒
    
    try:
        while simulation_time < max_simulation_time:
            # 每个时间步检查
            print(f"\n当前模拟时间: {simulation_time}秒")
            
            # 检查是否有准备好的订单需要分配
            for robot in robots:
                if robot.is_idle():
                    # 机器人空闲，检查是否有待配送订单
                    next_order = order_manager.get_next_delivery_order()
                    if next_order:
                        # 分配订单给机器人
                        order_manager.assign_order_to_robot(next_order.order_id, robot.robot_id)
                        robot.assign_order(next_order)
            
            # 所有机器人执行一步
            for robot in robots:
                if robot.path:
                    robot.move()
                    
                    # 检查当前订单状态
                    if robot.position == robot.goal and robot.current_order:
                        # 到达目标，完成订单
                        order_manager.complete_order_delivery(robot.current_order.order_id)
            
            # 睡眠一段时间模拟真实环境
            time.sleep(0.5)
            simulation_time += 1
            
            # 如果没有待处理的订单且所有机器人都空闲，提前结束模拟
            if (not order_manager.waiting_orders and 
                not order_manager.preparing_orders and 
                not order_manager.ready_orders and
                all(robot.is_idle() for robot in robots)):
                print("所有订单已处理完成，模拟结束")
                break
    
    finally:
        # 停止厨房处理线程
        stop_event.set()
        kitchen_thread.join(timeout=1)
    
    # 打印统计信息
    print(f"\n===== RAG机器人仿真结果 =====")
    print("订单统计:")
    stats = order_manager.get_statistics()
    print(f"  总订单数: {stats['total_orders']}")
    print(f"  完成订单数: {stats['completed_orders']}")
    print(f"  失败订单数: {stats['failed_orders']}")
    print(f"  配送成功率: {stats['success_rate']:.2f}%")
    print(f"  平均配送时间: {stats['avg_delivery_time']:.2f}秒")
    
    # 打印每个机器人的路径
    for i, robot in enumerate(robots):
        print(f"\n机器人 #{i+1} 路径:")
        if robot.path_history:
            animate_robot_path(robot.path_history, title=f"RAG机器人 #{i+1} 路径")
        else:
            print("  无路径记录")
    
    return stats

def compare_simulation_results(baseline_stats, rag_stats):
    """
    比较两种机器人的模拟结果
    """
    print("\n===== 模拟结果比较 =====")
    print("指标\t\t基线机器人\tRAG机器人\t差异")
    print("-" * 60)
    
    # 计算各项指标的差异
    completed_diff = rag_stats['completed_orders'] - baseline_stats['completed_orders']
    failed_diff = rag_stats['failed_orders'] - baseline_stats['failed_orders']
    success_rate_diff = rag_stats['success_rate'] - baseline_stats['success_rate']
    time_diff = baseline_stats['avg_delivery_time'] - rag_stats['avg_delivery_time']
    
    # 打印比较结果
    print(f"完成订单数\t{baseline_stats['completed_orders']}\t\t{rag_stats['completed_orders']}\t\t{completed_diff:+d}")
    print(f"失败订单数\t{baseline_stats['failed_orders']}\t\t{rag_stats['failed_orders']}\t\t{failed_diff:+d}")
    print(f"配送成功率\t{baseline_stats['success_rate']:.2f}%\t\t{rag_stats['success_rate']:.2f}%\t\t{success_rate_diff:+.2f}%")
    print(f"平均配送时间\t{baseline_stats['avg_delivery_time']:.2f}秒\t{rag_stats['avg_delivery_time']:.2f}秒\t{time_diff:+.2f}秒")

def input_orders():
    """
    从用户输入获取订单
    """
    order_manager = OrderManager()
    
    print("\n===== 订单输入 =====")
    print("请输入订单信息 (输入'完成'结束)")
    print("格式: 桌号 准备时间(秒)")
    
    while True:
        order_input = input("订单> ")
        if order_input.lower() in ['完成', 'done', 'q', 'quit', 'exit']:
            break
        
        try:
            parts = order_input.split()
            if len(parts) >= 2:
                table_id = int(parts[0])
                prep_time = float(parts[1])
                
                items = []
                if len(parts) > 2:
                    items = parts[2:]
                
                order_manager.create_order(table_id, prep_time, items)
            else:
                print("格式错误。请使用格式: 桌号 准备时间")
        except ValueError:
            print("无效输入。桌号必须是整数，准备时间必须是数字。")
    
    return order_manager

def ask_for_openai_key():
    """询问用户提供OpenAI API密钥"""
    print("\n===== OpenAI API配置 =====")
    print("需要OpenAI API密钥来使用RAG功能")
    print("您可以在 https://platform.openai.com/api-keys 获取密钥")
    
    api_key = input("请输入OpenAI API密钥 (或按Enter跳过): ").strip()
    
    if api_key:
        # 询问是否保存到配置文件
        save_to_file = input("是否保存此密钥到配置文件? (y/n): ").lower() == 'y'
        if save_to_file:
            config_dir = "rag_robot"
            os.makedirs(config_dir, exist_ok=True)
            config_path = os.path.join(config_dir, "config.json")
            
            # 读取现有配置(如果有)
            config = {}
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                except Exception as e:
                    print(f"读取现有配置文件出错: {e}")
            
            # 更新API密钥
            config["api_key"] = api_key
            
            # 写入配置文件
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)
                print(f"API密钥已保存到 {config_path}")
            except Exception as e:
                print(f"保存配置文件出错: {e}")
    
    return api_key

def main():
    """
    主函数，运行餐厅配送模拟
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="餐厅配送机器人模拟")
    parser.add_argument("--api-key", type=str, help="OpenAI API密钥")
    parser.add_argument("--config", type=str, default="rag_robot/config.json",
                        help="配置文件路径")
    parser.add_argument("--knowledge", type=str, default="rag_robot/knowledge.json",
                        help="知识库文件路径")
    args = parser.parse_args()
    
    # 获取API密钥
    api_key = args.api_key
    if not api_key:
        if os.path.exists(args.config):
            try:
                with open(args.config, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    api_key = config.get("api_key")
            except Exception as e:
                print(f"读取配置文件出错: {e}")
        
        if not api_key:
            api_key = ask_for_openai_key()
    
    # 创建餐厅环境
    restaurant = create_restaurant_layout()
    print_restaurant_info(restaurant)
    
    # 输入订单
    order_manager = input_orders()
    
    if not order_manager.orders:
        print("没有输入订单，程序结束")
        return
    
    # 运行基线机器人模拟
    baseline_order_manager = OrderManager()
    # 复制订单到新的订单管理器
    for order in order_manager.orders.values():
        baseline_order_manager.create_order(order.table_id, order.prep_time, order.items)
    
    baseline_stats = run_baseline_simulation(restaurant, baseline_order_manager)
    
    # 运行RAG机器人模拟
    rag_order_manager = OrderManager()
    # 复制订单到新的订单管理器
    for order in order_manager.orders.values():
        rag_order_manager.create_order(order.table_id, order.prep_time, order.items)
    
    rag_stats = run_rag_simulation(restaurant, rag_order_manager,
                                   api_key=api_key,
                                   config_file=args.config,
                                   knowledge_file=args.knowledge)
    
    # 比较两种机器人的表现
    compare_simulation_results(baseline_stats, rag_stats)

if __name__ == "__main__":
    main() 