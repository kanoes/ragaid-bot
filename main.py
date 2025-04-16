import time
import random
import os
import json
from modules.restaurant.layout import RestaurantLayout
from modules.restaurant.restaurant import Restaurant
from modules.robot.robot import Robot, AIEnhancedRobot
from modules.robot.order import Order

# 设定布局文件目录路径
LAYOUTS_DIR = os.path.join(
    os.path.dirname(__file__), "modules", "restaurant", "my_restaurant"
)


def list_restaurant_layouts(layouts_dir: str) -> list:
    """列出 layouts 目录下所有 JSON 文件（不含扩展名）"""
    return sorted(
        [
            os.path.splitext(fname)[0]
            for fname in os.listdir(layouts_dir)
            if fname.endswith(".json")
        ]
    )


def load_restaurant_from_json(filepath: str, custom_name=None):
    """从 JSON 文件加载餐厅布局。"""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    name = (
        custom_name
        or data.get("name")
        or os.path.splitext(os.path.basename(filepath))[0]
    )
    if "layout" not in data:
        raise ValueError(f"JSON 文件格式错误: {filepath}")
    # 直接使用 JSON 文件中的布局（layout 字段应为字符串列表）
    layout_lines = data["layout"]
    config = RestaurantLayout.parse_layout(layout_lines)
    layout = RestaurantLayout(**config)
    restaurant = Restaurant(name, layout)
    # 保存原始布局用于保存
    restaurant.original_layout = layout_lines
    return restaurant


def load_restaurant_layout(layouts_dir: str, name: str, custom_name=None):
    """根据名称加载餐厅布局，仅支持 JSON 文件。返回一个 Restaurant 对象。"""
    name = os.path.splitext(name)[0]
    json_path = os.path.join(layouts_dir, f"{name}.json")
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"找不到布局文件: {name}")
    return load_restaurant_from_json(json_path, custom_name)


def display_layout_template(layouts_dir: str, name: str):
    """直接打印 layouts 目录下 JSON 文件中存储的 layout 字段内容"""
    json_path = os.path.join(layouts_dir, f"{name}.json")
    if not os.path.exists(json_path):
        print(f"模板文件 {name}.json 不存在.")
        return None
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "layout" in data:
        return data["layout"]
    else:
        print("该 JSON 文件中没有找到 layout 字段.")
        return None


def select_restaurant_layout(layouts_dir: str):
    """交互式选择餐厅布局并创建餐厅对象。"""
    layouts = list_restaurant_layouts(layouts_dir)
    if not layouts:
        print("没有找到可用的餐厅布局文件!")
        return None

    print("\n===== 可用的餐厅布局 =====")
    for i, layout_name in enumerate(layouts):
        json_path = os.path.join(layouts_dir, f"{layout_name}.json")
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        name = data.get("name", layout_name)
        print(f"{i+1}. {layout_name}: {name}")

    try:
        choice = int(input("\n请选择布局编号 (输入0取消): "))
        if choice == 0:
            return None
        if 1 <= choice <= len(layouts):
            selected_layout = layouts[choice - 1]

            # 打印布局模板
            display_layout_template(layouts_dir, selected_layout)

            # 加载餐厅布局并创建餐厅对象
            restaurant = load_restaurant_layout(layouts_dir, selected_layout)
            return restaurant
        else:
            print("无效的选择!")
            return None
    except ValueError:
        print("请输入有效的数字!")
        return None
    except Exception as e:
        print(f"加载布局时出错: {str(e)}")
        return None


def main():
    """主程序"""
    print("\n===== 餐厅送餐机器人模拟系统 =====")

    # 检查是否有可用的餐厅布局
    layouts = list_restaurant_layouts(LAYOUTS_DIR)
    if not layouts:
        print("错误: 没有找到任何餐厅布局文件")
        print(f"请先创建餐厅布局JSON文件并放置在{LAYOUTS_DIR}目录中")
        return

    # 显示主菜单
    while True:
        print("\n===== 主菜单 =====")
        print("1. 选择餐厅")
        print("2. 退出")

        choice = input("\n请选择 (1-2): ").strip()

        if choice == "1":
            # 选择餐厅布局并创建餐厅对象
            restaurant = select_restaurant_layout(LAYOUTS_DIR)

            if restaurant:
                print("\n成功创建餐厅!")
                restaurant.layout.display(restaurant_name=restaurant.name)

                # 询问用户是否要进行模拟测试
                while True:
                    print("\n===== 餐厅操作 =====")
                    print("1. 运行送餐机器人模拟")
                    print("2. 返回主菜单")

                    op_choice = input("\n请选择 (1-2): ").strip()

                    if op_choice == "1":
                        run_robot_simulation(restaurant)
                    else:
                        break
        else:
            print("感谢使用餐厅送餐机器人模拟系统!")
            break

    print("\n" + "=" * 40)


def generate_orders(num_orders, table_ids):
    """生成随机订单"""
    orders = []
    for _ in range(num_orders):
        table_id = random.choice(table_ids)
        items = random.randint(1, 5)  # 随机1-5个餐品

        order = {"table_id": table_id, "items": items, "time": time.time()}
        orders.append(order)

    return orders


def run_robot_simulation(restaurant):
    """运行机器人模拟测试"""
    print(f"\n===== 餐厅 '{restaurant.name}' 模拟测试 =====")
    restaurant.layout.display(restaurant_name=restaurant.name)

    # 获取餐厅中所有桌子的ID
    table_ids = list(restaurant.layout.tables.keys())
    if not table_ids:
        print("错误: 当前餐厅没有任何桌子，无法进行送餐测试")
        return

    # 询问用户选择模拟类型
    print("\n请选择模拟类型:")
    print("1. 基础送餐机器人")
    print("2. AI增强型送餐机器人")

    sim_choice = input("选择 (1-2): ").strip()

    # 设置订单数量
    try:
        num_orders = int(input("\n请输入要测试的订单数量 (1-20): ").strip())
        num_orders = max(1, min(20, num_orders))  # 限制在1-20之间
    except ValueError:
        num_orders = 5  # 默认值
        print(f"使用默认订单数量: {num_orders}")

    # 生成随机订单
    orders = generate_orders(num_orders, table_ids)

    # 创建对应类型的机器人
    if sim_choice == "2":
        # 创建AI增强型机器人
        print("\n===== 创建AI增强型送餐机器人 =====")
        # 获取知识库文件路径
        knowledge_file = os.path.join(
            os.path.dirname(__file__),
            "modules",
            "rag",
            "knowledge",
            "restaurant_rule.json",
        )
        # 检查知识库文件是否存在
        if not os.path.exists(knowledge_file):
            print(f"警告: 知识库文件不存在: {knowledge_file}")
            print("AI增强型机器人将以基础模式运行")

        # 获取OpenAI API密钥
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("警告: 未找到OPENAI_API_KEY环境变量，AI功能可能受限")

        # 创建AI增强型机器人
        robot = AIEnhancedRobot(
            environment=restaurant.layout,
            robot_id=1,
            api_key=api_key,
            knowledge_file=knowledge_file,
        )
    else:
        # 创建基础机器人
        print("\n===== 创建基础送餐机器人 =====")
        robot = Robot(
            environment=restaurant.layout, robot_id=1, enable_rag=False  # 不启用RAG功能
        )

    # 显示订单信息
    print("\n生成的订单:")
    for i, order in enumerate(orders):
        print(f"订单 {i+1}: 桌号 {order['table_id']}, 物品数量 {order['items']}")

    # 处理每个订单
    print(f"\n===== 开始送餐模拟 ({len(orders)}个订单) =====")
    for i, order in enumerate(orders):
        print(
            f"\n处理订单 {i+1}/{len(orders)}: 桌号 {order['table_id']}, 物品数量 {order['items']}"
        )

        # 分配订单给机器人
        success = robot.take_order(order)
        if success:
            # 模拟机器人配送过程
            print(f"机器人开始配送订单...")
            steps, path = robot.simulate(max_steps=100)
            print(f"订单配送过程结束，用了 {steps} 步")
        else:
            print(f"订单分配失败，机器人无法处理该订单")

    # 显示机器人的配送统计信息
    robot.display_stats()

    input("\n按回车键返回...")


if __name__ == "__main__":
    main()
