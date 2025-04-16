"""
餐厅送餐机器人模拟系统

主程序入口
"""

import time
import random
import os
import json
from modules.restaurant import (
    list_restaurant_layouts, 
    select_restaurant_layout, 
    Restaurant
)
from modules.robot import Robot, AIEnhancedRobot

# 获取布局文件目录路径
LAYOUTS_DIR = os.path.join(os.path.dirname(__file__), 'modules', 'restaurant', 'layouts')

def main():
    """主程序"""
    print("\n===== 餐厅送餐机器人模拟系统 =====")
    
    # 检查是否有可用的餐厅布局
    layouts = list_restaurant_layouts()
    if not layouts:
        print("错误: 没有找到任何餐厅布局文件!")
        print(f"请先创建餐厅布局JSON文件并放置在{LAYOUTS_DIR}目录中")
        print("布局文件格式示例:")
        print('''{
  "name": "示例餐厅",
  "layout": [
    "WWWWWWWWWW",
    "WSSSSSSSW",
    "WSK01S02W",
    "WSSSSSSSW",
    "WWWWWWWWWW"
  ]
}''')
        print("\n其中W表示墙壁，S表示空地，K表示厨房，01-99表示桌子编号")
        return
    
    # 显示主菜单
    while True:
        print("\n===== 主菜单 =====")
        print("1. 查看可用餐厅布局")
        print("2. 加载餐厅模拟")
        print("3. 退出")
        
        choice = input("\n请选择 (1-3): ").strip()
        
        if choice == "1":
            # 显示所有可用布局文件的内容
            display_available_layouts(layouts)
        elif choice == "2":
            # 加载餐厅布局并启动模拟
            restaurant = select_restaurant_layout()
            if restaurant:
                run_robot_simulation(restaurant)
        else:
            print("感谢使用餐厅送餐机器人模拟系统!")
            break

def display_available_layouts(layouts):
    """直接显示所有可用的布局文件内容"""
    print("\n===== 可用的餐厅布局 =====")
    
    for i, layout_name in enumerate(layouts):
        json_path = os.path.join(LAYOUTS_DIR, f"{layout_name}.json")
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            print(f"\n{i+1}. {layout_name}")
            print("-" * 30)
            
            # 显示名称
            name = data.get('name', layout_name)
            print(f"餐厅名称: {name}")
            
            # 显示原始布局
            if 'layout' in data:
                print("\n原始布局:")
                for line in data['layout']:
                    print(line)
            
            print("-" * 30)
            
        except Exception as e:
            print(f"\n{i+1}. {layout_name} - 无法读取: {e}")
    
    print("\n" + "=" * 40)

def run_robot_simulation(restaurant):
    """运行机器人模拟测试"""
    print(f"\n===== 餐厅 '{restaurant.name}' 模拟测试 =====")
    restaurant.display()
    
    # 获取餐厅中所有桌子的ID
    table_ids = list(restaurant.tables.keys())
    if not table_ids:
        print("错误: 当前餐厅没有任何桌子，无法进行送餐测试")
        return
    
    # 询问用户选择模拟类型
    print("\n请选择模拟类型:")
    print("1. 基础送餐机器人")
    print("2. AI增强型送餐机器人")
    print("3. 对比测试 (两种机器人)")
    
    sim_choice = input("选择 (1-3): ").strip()
    
    # 设置订单数量
    try:
        num_orders = int(input("\n请输入要测试的订单数量 (1-20): ").strip())
        num_orders = max(1, min(20, num_orders))  # 限制在1-20之间
    except ValueError:
        num_orders = 5  # 默认值
        print(f"使用默认订单数量: {num_orders}")
    
    # 生成随机订单
    orders = generate_orders(num_orders, table_ids)
    
    # 根据用户选择运行模拟
    if sim_choice == "1":
        # 基础送餐机器人
        run_single_robot_test(restaurant, orders, use_ai=False)
    elif sim_choice == "2":
        # AI增强型送餐机器人
        run_single_robot_test(restaurant, orders, use_ai=True)
    else:
        # 对比测试
        compare_robots(restaurant, orders)

def generate_orders(num_orders, table_ids):
    """生成随机订单"""
    orders = []
    for _ in range(num_orders):
        table_id = random.choice(table_ids)
        items = random.randint(1, 5)  # 随机1-5个餐品
        
        order = {
            "table_id": table_id,
            "items": items,
            "time": time.time()
        }
        orders.append(order)
    
    return orders

def run_single_robot_test(restaurant, orders, use_ai=False):
    """单个机器人测试"""
    if use_ai:
        robot = AIEnhancedRobot(restaurant)
        print("\n===== 使用AI增强型送餐机器人运行模拟 =====")
    else:
        robot = Robot(restaurant)
        print("\n===== 使用基础送餐机器人运行模拟 =====")
    
    # 显示初始状态
    print("初始餐厅状态:")
    restaurant.display(robot_position=robot.position)
    
    # 处理订单
    print(f"\n开始处理 {len(orders)} 个订单...")
    for i, order in enumerate(orders):
        print(f"\n处理订单 {i+1}/{len(orders)} - 桌号: {order['table_id']}, 物品数: {order['items']}")
        success = robot.take_order(order)
        if success:
            print(f"  订单送达成功! 路径长度: {len(robot.path)}")
        else:
            print(f"  订单送达失败!")
        
        # 显示机器人当前位置
        restaurant.display(path=robot.path, robot_position=robot.position)
    
    # 显示统计信息
    robot.display_stats()

def compare_robots(restaurant, orders):
    """比较两种机器人的性能"""
    print("\n===== 机器人对比测试 =====")
    
    # 运行基础机器人模拟
    basic_robot = Robot(restaurant)
    print("\n[基础机器人测试开始]")
    
    # 显示初始状态
    print("初始餐厅状态:")
    restaurant.display(robot_position=basic_robot.position)
    
    # 处理订单
    for i, order in enumerate(orders):
        print(f"\n处理订单 {i+1}/{len(orders)} - 桌号: {order['table_id']}")
        success = basic_robot.take_order(order)
        if success:
            print(f"  送达成功!")
        else:
            print(f"  送达失败!")
    
    # 显示统计信息
    basic_robot.display_stats()
    basic_stats = basic_robot.stats
    
    # 运行AI增强型机器人模拟
    ai_robot = AIEnhancedRobot(restaurant)
    print("\n[AI增强型机器人测试开始]")
    
    # 显示初始状态
    print("初始餐厅状态:")
    restaurant.display(robot_position=ai_robot.position)
    
    # 处理订单
    for i, order in enumerate(orders):
        print(f"\n处理订单 {i+1}/{len(orders)} - 桌号: {order['table_id']}")
        success = ai_robot.take_order(order)
        if success:
            print(f"  送达成功!")
        else:
            print(f"  送达失败!")
    
    # 显示统计信息
    ai_robot.display_stats()
    ai_stats = ai_robot.stats
    
    # 比较结果
    num_orders = len(orders)
    print("\n===== 性能对比总结 =====")
    print(f"总订单数: {num_orders}")
    print(f"基础机器人成功率: {basic_stats['successful_deliveries']/num_orders*100:.2f}%")
    print(f"AI增强机器人成功率: {ai_stats['successful_deliveries']/num_orders*100:.2f}%")
    
    if basic_stats['successful_deliveries'] > 0 and ai_stats['successful_deliveries'] > 0:
        basic_avg_dist = basic_stats['total_distance'] / basic_stats['successful_deliveries']
        ai_avg_dist = ai_stats['total_distance'] / ai_stats['successful_deliveries']
        
        basic_avg_time = basic_stats['total_time'] / basic_stats['successful_deliveries']
        ai_avg_time = ai_stats['total_time'] / ai_stats['successful_deliveries']
        
        print(f"基础机器人平均路径长度: {basic_avg_dist:.2f}")
        print(f"AI增强机器人平均路径长度: {ai_avg_dist:.2f}")
        print(f"基础机器人平均送达时间: {basic_avg_time:.2f}秒")
        print(f"AI增强机器人平均送达时间: {ai_avg_time:.2f}秒")
        
        if ai_avg_dist < basic_avg_dist:
            print(f"AI增强机器人路径效率提升: {(basic_avg_dist - ai_avg_dist) / basic_avg_dist * 100:.2f}%")
        
        if ai_avg_time < basic_avg_time:
            print(f"AI增强机器人时间效率提升: {(basic_avg_time - ai_avg_time) / basic_avg_time * 100:.2f}%")

if __name__ == "__main__":
    main()
