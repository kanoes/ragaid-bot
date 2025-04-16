import time
import random
import os
import json
import dotenv
from modules.restaurant.layout import RestaurantLayout
from modules.restaurant.restaurant import Restaurant
from modules.robot.robot import Robot, AIEnhancedRobot
from modules.robot.order import Order

dotenv.load_dotenv()

# 设定布局文件目录路径
RESTAURANT_LAYOUT = os.path.join(
    os.path.dirname(__file__), "resources", "my_restaurant"
)
RAG_KNOWLEDGE = os.path.join(
    os.path.dirname(__file__), "resources", "rag_knowledge"
)

def main():
    print("\n===== 餐厅送餐机器人模拟系统 =====")

    # 列出 layouts 目录下所有 JSON 文件名（不含扩展名）
    layouts = sorted([
        os.path.splitext(fname)[0]
        for fname in os.listdir(RESTAURANT_LAYOUT)
        if fname.endswith(".json")
    ])

    if not layouts:
        print("错误: 没有找到任何餐厅布局文件")
        return

    while True:
        print("\n===== 主菜单 =====")
        print("1. 选择餐厅")
        print("2. 退出")

        choice = input("\n请选择 (1-2): ").strip()

        if choice == "1":
            print("\n===== 可用的餐厅布局 =====")
            for i, layout_name in enumerate(layouts):
                json_path = os.path.join(RESTAURANT_LAYOUT, f"{layout_name}.json")
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                name = data.get("name", layout_name)
                print(f"{i+1}. {layout_name}: {name}")

            layout_choice = int(input("\n请选择布局编号 (输入0取消): "))
            if layout_choice == 0:
                continue
            if 1 <= layout_choice <= len(layouts):
                selected_layout = layouts[layout_choice - 1]
                json_path = os.path.join(RESTAURANT_LAYOUT, f"{selected_layout}.json")

                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                name = data.get("name") or selected_layout
                layout_lines = data["layout"]
                config = RestaurantLayout.parse_layout(layout_lines)
                layout = RestaurantLayout(**config)
                restaurant = Restaurant(name, layout)
                restaurant.original_layout = layout_lines

                print("\n成功创建餐厅!")
                restaurant.layout.display(restaurant_name=restaurant.name)

                while True:
                    print("\n===== 餐厅操作 =====")
                    print("1. 运行送餐机器人模拟")
                    print("2. 返回主菜单")

                    op_choice = input("\n请选择 (1-2): ").strip()
                    if op_choice != "1":
                        break

                    print(f"\n===== 餐厅 '{restaurant.name}' 模拟测试 =====")
                    restaurant.layout.display(restaurant_name=restaurant.name)

                    table_ids = list(restaurant.layout.tables.keys())
                    if not table_ids:
                        print("错误: 当前餐厅没有任何桌子，无法进行送餐测试")
                        break

                    print("\n请选择模拟类型:")
                    print("1. 基础送餐机器人")
                    print("2. AI增强型送餐机器人")
                    sim_choice = input("\n选择 (1-2): ").strip()

                    print("\n请选择订单生成方式:")
                    print("1. 随机生成")
                    print("2. 手动指定")
                    order_choice = input("\n选择 (1-2): ").strip()

                    # 生成订单
                    orders = []
                    available_tables = table_ids.copy()  # 可用桌子列表，确保不重复
                    max_orders = len(available_tables)  # 最大订单数量等于桌子数量
                    
                    if order_choice == "1":  # 随机生成
                        print(f"\n当前餐厅有{max_orders}个桌子可用")
                        num_orders = input(f"请输入要生成的订单数量 (1-{max_orders}): ").strip()
                        try:
                            num_orders = int(num_orders)
                            num_orders = max(1, min(num_orders, max_orders))  # 限制在1到最大桌子数之间
                        except ValueError:
                            num_orders = 1
                            print(f"输入无效，默认使用1个订单")
                        
                        # 随机选择不重复的桌子
                        selected_tables = random.sample(available_tables, num_orders)
                        
                        for table_id in selected_tables:
                            prep_time = random.randint(1, 10)  # 随机生成1-10秒的制作时间
                            orders.append({
                                "table_id": table_id,
                                "time": prep_time
                            })
                            
                    else:  # 手动指定
                        print(f"\n当前可用桌号: {', '.join(available_tables)}")
                        print("请按照格式输入订单 (如 'A 5' 表示桌号A的订单，制作时间5秒)")
                        print("每行输入一个订单，输入空行结束")
                        
                        used_tables = set()  # 已使用的桌号
                        
                        while True:
                            if len(orders) >= max_orders:
                                print(f"已达到最大订单数 {max_orders}")
                                break
                                
                            order_input = input(f"订单 {len(orders)+1}/{max_orders} (空行结束): ").strip()
                            if not order_input:
                                break
                                
                            parts = order_input.split()
                            if len(parts) != 2:
                                print("格式错误，请按照'桌号 制作时间'格式输入")
                                continue
                                
                            table_id, time_str = parts
                            
                            # 检查桌号是否存在
                            if table_id not in available_tables:
                                print(f"错误: 桌号 {table_id} 不存在")
                                continue
                            
                            # 检查桌号是否重复
                            if table_id in used_tables:
                                print(f"错误: 桌号 {table_id} 已有订单")
                                continue
                            
                            # 检查时间是否有效
                            try:
                                prep_time = int(time_str)
                                if prep_time <= 0:
                                    print("制作时间必须大于0")
                                    continue
                            except ValueError:
                                print("制作时间必须是正整数")
                                continue
                            
                            # 添加订单
                            orders.append({
                                "table_id": table_id,
                                "time": prep_time
                            })
                            used_tables.add(table_id)  # 标记该桌号已使用

                    if not orders:
                        print("没有创建任何订单，返回菜单")
                        continue

                    # 初始化机器人
                    if sim_choice == "2":
                        print("\n===== 创建AI增强型送餐机器人 =====")
                        knowledge_file = os.path.join(
                            os.path.dirname(__file__),
                            "modules",
                            "rag",
                            "knowledge",
                            "restaurant_rule.json",
                        )
                        if not os.path.exists(knowledge_file):
                            print(f"警告: 知识库文件不存在: {knowledge_file}")
                            print("AI增强型机器人将以基础模式运行")

                        api_key = os.environ.get("OPENAI_API_KEY")
                        if not api_key:
                            print("警告: 未找到OPENAI_API_KEY环境变量，AI功能可能受限")

                        robot = AIEnhancedRobot(
                            environment=restaurant.layout,
                            robot_id=1,
                            api_key=api_key,
                            knowledge_file=knowledge_file,
                        )
                    else:
                        print("\n===== 创建基础送餐机器人 =====")
                        robot = Robot(environment=restaurant.layout, robot_id=1, enable_rag=False)

                    # 显示订单
                    print("\n生成的订单:")
                    for i, order in enumerate(orders):
                        print(f"订单 {i+1}: 桌号 {order['table_id']}, 制作时间 {order['time']}秒")

                    print(f"\n===== 开始送餐模拟 ({len(orders)}个订单) =====")
                    for i, order in enumerate(orders):
                        print(f"\n处理订单 {i+1}/{len(orders)}: 桌号 {order['table_id']}, 制作时间 {order['time']}秒")

                        success = robot.take_order(order)
                        if success:
                            print("机器人开始配送订单...")
                            steps, path = robot.simulate(max_steps=100)
                            print(f"订单配送过程结束，用了 {steps} 步")
                        else:
                            print("订单分配失败，机器人无法处理该订单")

                    robot.display_stats()
                    input("\n按回车键返回...")

                else:
                    print("无效的选择!")
        else:
            print("感谢使用餐厅送餐机器人模拟系统!")
            break

    print("\n" + "=" * 40)

if __name__ == "__main__":
    main()
