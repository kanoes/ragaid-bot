import time
import threading
import argparse
import os
import json
import sys
import warnings
import dotenv
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.font_manager import FontProperties

from colorama import Fore, Style, init

# 加载.env文件中的环境变量
dotenv.load_dotenv()

# 配置matplotlib中文字体支持
try:
    # 检查是否存在特定的字体配置环境变量
    font_path = os.environ.get('MATPLOTLIB_FONT', None)
    if font_path and os.path.exists(font_path):
        # 使用指定的字体文件
        font_prop = FontProperties(fname=font_path)
        plt.rcParams['font.family'] = font_prop.get_name()
    else:
        # 尝试使用系统中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
except Exception as e:
    print(f"配置中文字体时出错: {e}")
    print("将使用默认字体")

# 过滤matplotlib中文字体警告
warnings.filterwarnings("ignore", category=UserWarning, module="tkinter")

# 检查是否需要使用英文标题（ASCII模式）
ASCII_MODE = False
if "--ascii" in sys.argv:
    ASCII_MODE = True
    sys.argv.remove("--ascii")
    print("使用ASCII模式（英文标题）运行")

from modules.environment import RestaurantEnvironment, create_restaurant_layout, print_restaurant_info, display_full_restaurant
from modules.robot import Robot
from modules.utils import animate_robot_path, OrderManager, Order

def get_title(zh_title, en_title):
    """根据ASCII模式返回适当的标题"""
    return en_title if ASCII_MODE else zh_title

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
        robot = Robot(restaurant, robot_id=i+1, enable_rag=False)
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
            print(f"\n当前模拟时间: {simulation_time}秒")
            # 检查是否有准备好的订单需要分配
            for robot in robots:
                if robot.is_idle():
                    next_order = order_manager.get_next_delivery_order()
                    if next_order:
                        order_manager.assign_order_to_robot(next_order.order_id, robot.robot_id)
                        robot.assign_order(next_order)
            
            # 所有机器人执行一步
            for robot in robots:
                if robot.path:
                    robot.move()
                    if robot.current_order:
                        if robot.position == robot.goal:
                            order_manager.complete_order_delivery(robot.current_order.order_id)
                        elif hasattr(robot.current_order, 'delivered_flag'):
                            order_manager.complete_order_delivery(robot.current_order.order_id)
                            print(f"手动完成订单 #{robot.current_order.order_id} 状态更新（已送达但未返回后厨）")
            
            time.sleep(0.5)
            simulation_time += 1
            
            # 如果没有待处理的订单且所有机器人均空闲，则提前结束模拟
            if (not order_manager.waiting_orders and 
                not order_manager.preparing_orders and 
                not order_manager.ready_orders and
                not order_manager.delivering_orders and
                all(robot.current_order is None or hasattr(robot.current_order, 'delivered_flag') for robot in robots)):
                print("所有订单已处理完成，模拟结束")
                for robot in robots:
                    if robot.current_order and hasattr(robot.current_order, 'delivered_flag'):
                        order_manager.complete_order_delivery(robot.current_order.order_id)
                        robot.current_order = None
                break
    
    finally:
        stop_event.set()
        kitchen_thread.join(timeout=1)
    
    print("\n===== 基线机器人仿真结果 =====")
    print("订单统计:")
    stats = order_manager.get_statistics()
    print(f"  总订单数: {stats['total_orders']}")
    print(f"  完成订单数: {stats['completed_orders']}")
    print(f"  失败订单数: {stats['failed_orders']}")
    print(f"  配送成功率: {stats['success_rate']:.2f}%")
    print(f"  平均配送时间: {stats['avg_delivery_time']:.2f}秒")
    
    for i, robot in enumerate(robots):
        print(f"\n机器人 #{i+1} 路径:")
        if robot.path_history:
            title = get_title(f"基线机器人 #{i+1} 路径", f"Baseline Robot #{i+1} Path")
            animate_robot_path(robot.path_history, title=title)
        else:
            print("  无路径记录")
    
    return stats

def run_rag_simulation(restaurant, order_manager, robot_count=1, api_key=None, knowledge_file=None):
    """
    使用RAG机器人运行订单配送模拟
    参数:
        restaurant: 餐厅环境
        order_manager: 订单管理器
        robot_count: 机器人数量
        api_key: OpenAI API密钥
        knowledge_file: 知识库文件路径
    """
    print("\n===== RAG机器人仿真开始 =====")
    
    # 创建机器人
    robots = []
    for i in range(robot_count):
        try:
            robot = Robot(restaurant, robot_id=i+1, enable_rag=True, 
                          api_key=api_key, knowledge_file=knowledge_file)
            robots.append(robot)
        except Exception as e:
            print(f"创建RAG机器人失败: {e}")
            print("使用基线机器人替代")
            robot = Robot(restaurant, robot_id=i+1, enable_rag=False)
            robots.append(robot)
    
    # 启动厨房处理线程
    stop_event = threading.Event()
    kitchen_thread = threading.Thread(target=process_kitchen, args=(order_manager, stop_event))
    kitchen_thread.daemon = True
    kitchen_thread.start()
    
    simulation_time = 0
    max_simulation_time = 60  # 最多模拟60秒
    
    try:
        while simulation_time < max_simulation_time:
            print(f"\n当前模拟时间: {simulation_time}秒")
            for robot in robots:
                if robot.is_idle():
                    next_order = order_manager.get_next_delivery_order()
                    if next_order:
                        order_manager.assign_order_to_robot(next_order.order_id, robot.robot_id)
                        path_success = robot.assign_order(next_order)
                        if path_success and robot.enable_rag and simulation_time > 3:
                            print("\n执行RAG障碍物处理综合测试...")
                            robot.comprehensive_test()
            
            for robot in robots:
                if robot.path:
                    robot.move()
                    if robot.current_order:
                        if robot.position == robot.goal:
                            order_manager.complete_order_delivery(robot.current_order.order_id)
                        elif hasattr(robot.current_order, 'delivered_flag'):
                            order_manager.complete_order_delivery(robot.current_order.order_id)
                            print(f"手动完成订单 #{robot.current_order.order_id} 状态更新（已送达但未返回后厨）")
            
            time.sleep(0.5)
            simulation_time += 1
            if (not order_manager.waiting_orders and 
                not order_manager.preparing_orders and 
                not order_manager.ready_orders and
                not order_manager.delivering_orders and
                all(robot.current_order is None or hasattr(robot.current_order, 'delivered_flag') for robot in robots)):
                print("所有订单已处理完成，模拟结束")
                for robot in robots:
                    if robot.current_order and hasattr(robot.current_order, 'delivered_flag'):
                        order_manager.complete_order_delivery(robot.current_order.order_id)
                        robot.current_order = None
                break
    
    finally:
        stop_event.set()
        kitchen_thread.join(timeout=1)
    
    print(f"\n===== RAG机器人仿真结果 =====")
    print("订单统计:")
    stats = order_manager.get_statistics()
    print(f"  总订单数: {stats['total_orders']}")
    print(f"  完成订单数: {stats['completed_orders']}")
    print(f"  失败订单数: {stats['failed_orders']}")
    print(f"  配送成功率: {stats['success_rate']:.2f}%")
    print(f"  平均配送时间: {stats['avg_delivery_time']:.2f}秒")
    
    for i, robot in enumerate(robots):
        print(f"\n机器人 #{i+1} 路径:")
        if robot.path_history:
            title = get_title(f"RAG机器人 #{i+1} 路径", f"RAG Robot #{i+1} Path")
            animate_robot_path(robot.path_history, title=title)
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
    
    completed_diff = rag_stats['completed_orders'] - baseline_stats['completed_orders']
    failed_diff = rag_stats['failed_orders'] - baseline_stats['failed_orders']
    success_rate_diff = rag_stats['success_rate'] - baseline_stats['success_rate']
    time_diff = baseline_stats['avg_delivery_time'] - rag_stats['avg_delivery_time']
    
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
                items = parts[2:] if len(parts) > 2 else []
                order_manager.create_order(table_id, prep_time, items)
            else:
                print("格式错误。请使用格式: 桌号 准备时间")
        except ValueError:
            print("无效输入。桌号必须是整数，准备时间必须是数字。")
    
    return order_manager

def parse_arguments():
    parser = argparse.ArgumentParser(description="餐厅配送机器人模拟")
    parser.add_argument('--api_key', type=str, help='OpenAI API 密钥')
    parser.add_argument('--knowledge', type=str, default='knowledge.json', help='知识库文件路径')
    parser.add_argument('--skip_baseline', action='store_true', help='跳过基线模拟')
    parser.add_argument('--ascii', action='store_true', help='使用ASCII模式（避免中文渲染问题）')
    parser.add_argument('--font', type=str, help='指定用于图表显示的字体')
    return parser.parse_args()

def main():
    """
    主函数，运行餐厅配送模拟
    """
    args = parse_arguments()
    
    if args.font:
        os.environ['MATPLOTLIB_FONT'] = args.font
        print(f"使用自定义字体: {args.font}")
    
    global ASCII_MODE
    ASCII_MODE = args.ascii
    if ASCII_MODE:
        print("使用ASCII模式显示，避免中文渲染问题")
    
    # 直接从环境变量读取OpenAI API密钥（不再请求用户输入或保存）
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("错误: 未在环境变量中找到OpenAI API密钥，请在.env文件中设置OPENAI_API_KEY")
        sys.exit(1)
    
    # 确保知识库文件存在
    ensure_knowledge_file(args.knowledge)
    
    # 创建餐厅环境
    restaurant = create_restaurant_layout()
    print_restaurant_info(restaurant)
    
    kitchen_pos = restaurant.get_kitchen_positions()[0]
    display_full_restaurant(restaurant, kitchen_pos)
    
    order_manager = input_orders()
    if not order_manager.orders:
        print("没有输入订单，程序结束")
        return
    
    baseline_stats = None
    if not args.skip_baseline:
        baseline_order_manager = OrderManager()
        for order in order_manager.orders.values():
            baseline_order_manager.create_order(order.table_id, order.prep_time, order.items)
        baseline_stats = run_baseline_simulation(restaurant, baseline_order_manager)
    
    rag_order_manager = OrderManager()
    for order in order_manager.orders.values():
        rag_order_manager.create_order(order.table_id, order.prep_time, order.items)
    
    rag_stats = run_rag_simulation(restaurant, rag_order_manager,
                                   api_key=api_key,
                                   knowledge_file=args.knowledge)
    
    if baseline_stats:
        compare_simulation_results(baseline_stats, rag_stats)

def ensure_knowledge_file(knowledge_file_path):
    """确保知识库文件存在，如果不存在则创建示例知识库"""
    if os.path.exists(knowledge_file_path):
        print(f"知识库文件已存在: {knowledge_file_path}")
        return
    
    print(f"知识库文件不存在，创建示例知识库: {knowledge_file_path}")
    dirname = os.path.dirname(knowledge_file_path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    
    example_knowledge = [
        "当机器人遇到障碍物时，应该先评估障碍物的性质。如果是临时障碍，可以短暂等待后重试；如果是永久性障碍，应该重新规划路径。",
        "在餐厅环境中，拥挤区域通常是临时性障碍，机器人应该减速并等待通行。",
        "如果短时间内多次遇到同一位置的障碍物，说明该障碍物可能是永久性的，应该尝试寻找替代路径。",
        "当机器人无法找到任何可行路径时，应该报告无法到达目标。",
        "如果遇到移动的人或物体，应该等待其通过，而不是尝试绕行。",
        "如果目标周围被障碍物包围，应该等待一段时间后再尝试接近，因为障碍物可能是临时的。",
        "在通行量大的区域，机器人应该尽量靠边行驶，避免阻碍其他人的通行。",
        "当多次尝试绕行都失败时，机器人应该考虑完全不同的路径，即使路径更长。"
    ]
    
    with open(knowledge_file_path, 'w', encoding='utf-8') as f:
        json.dump(example_knowledge, f, ensure_ascii=False, indent=2)
    
    print(f"示例知识库创建成功，包含 {len(example_knowledge)} 条知识条目")

if __name__ == "__main__":
    main()
