"""
Main runner — CLI 入口
"""

from __future__ import annotations

import json
import logging
import os
import random
from typing import List, Optional

from restaurant.restaurant_layout import RestaurantLayout
from restaurant.restaurant import Restaurant
from robot import AIEnhancedRobot, Robot
from robot.planner import Order
# >>> 新增可视化 <<<
from visualization import animate_robot_path

# --------------------------------------------------------------------------- #
# 日志
# --------------------------------------------------------------------------- #
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# 资源路径
# --------------------------------------------------------------------------- #
BASE_DIR = os.path.dirname(__file__)
LAYOUT_DIR = os.path.join(BASE_DIR, "resources", "my_restaurant")
RAG_KB_DIR = os.path.join(BASE_DIR, "resources", "rag_knowledge")

# --------------------------------------------------------------------------- #
# 主入口
# --------------------------------------------------------------------------- #
def run() -> None:
    """
    启动交互式模拟
    """
    layouts = _available_layouts(LAYOUT_DIR)
    if not layouts:
        logger.error("没有找到任何餐厅布局文件")
        return

    logger.info("===== 餐厅送餐机器人模拟系统 =====")
    while True:
        match _main_menu():
            case "1":
                _restaurant_workflow(layouts)
            case "2":
                break
            case _:
                print("无效输入")

# --------------------------------------------------------------------------- #
# 菜单
# --------------------------------------------------------------------------- #
def _available_layouts(layout_dir: str) -> List[str]:
    return sorted(
        os.path.splitext(f)[0] for f in os.listdir(layout_dir) if f.endswith(".json")
    )

def _main_menu() -> str:
    print("\n1. 选择餐厅\n2. 退出")
    return input("请选择 (1-2): ").strip()

def _restaurant_menu() -> str:
    print("\n1. 运行模拟\n2. 返回主菜单")
    return input("请选择 (1-2): ").strip()

# --------------------------------------------------------------------------- #
# 工作流程
# --------------------------------------------------------------------------- #
def _restaurant_workflow(layouts: List[str]) -> None:
    idx = _choose_layout(layouts)
    if idx is None:
        return

    rest = _load_restaurant(layouts[idx])
    if not rest:
        return

    while True:
        if _restaurant_menu() != "1":
            break
        _run_simulation(rest)

def _choose_layout(layouts: List[str]) -> Optional[int]:
    print("\n===== 可用布局 =====")
    for i, name in enumerate(layouts, 1):
        print(f"{i}. {name}")
    try:
        sel = int(input("选择编号(0取消): "))
        return sel - 1 if 1 <= sel <= len(layouts) else None
    except ValueError:
        return None

# --------------------------------------------------------------------------- #
# 加载餐厅
# --------------------------------------------------------------------------- #
def _load_restaurant(layout_name: str) -> Optional[Restaurant]:
    json_path = os.path.join(LAYOUT_DIR, f"{layout_name}.json")
    with open(json_path, encoding="utf-8") as fp:
        data = json.load(fp)

    cfg = RestaurantLayout.parse_layout_from_strings(layout_name, data["layout"])
    rest = Restaurant(data.get("name", layout_name), RestaurantLayout(**cfg))
    rest.display()
    return rest

# --------------------------------------------------------------------------- #
# 构造机器人
# --------------------------------------------------------------------------- #
def _build_robot(use_ai: bool, layout: RestaurantLayout) -> Robot:
    if use_ai:
        return AIEnhancedRobot(layout, robot_id=1, knowledge_dir=RAG_KB_DIR)
    return Robot(layout, robot_id=1)

# --------------------------------------------------------------------------- #
# 单次模拟
# --------------------------------------------------------------------------- #
def _run_simulation(rest: Restaurant) -> None:
    use_ai = input("\n使用 RAG 智能机器人? (y/n): ").lower() == "y"
    bot = _build_robot(use_ai, rest.layout)

    # 随机生成订单
    table_ids = list(rest.layout.tables.keys())
    if not table_ids:
        logger.warning("该餐厅没有桌子")
        return

    num = max(1, int(input("生成几单? (默认1): ") or "1"))
    orders = [_make_order(i + 1, random.choice(table_ids)) for i in range(min(num, len(table_ids)))]

    for od in orders:
        print(f"\n派送 {od}")
        if bot.assign_order(od):
            print("规划路径:", bot.path)          # ← 打印规划出的路径
            bot.simulate()
            print("运动历史:", bot.path_history)  # ← 打印实际走过的点

            # >>> 新增可视化 <<<
            animate_robot_path(
                bot.path_history,
                title=f"Robot#{bot.robot_id} Order#{od.order_id} Path",
                fps=4,
            )
        else:
            print("接单失败")

    _print_stats(bot.stats())

def _make_order(seq: int, table_id: str) -> Order:
    return Order(order_id=seq, table_id=table_id, prep_time=0)

def _print_stats(st: dict) -> None:
    delivered = st["delivered"]
    failed = st["failed"]
    total = delivered + failed
    rate = delivered / total * 100 if total else 0.0
    print("\n===== 统计 =====")
    print(f"成功: {delivered}, 失败: {failed}, 成功率: {rate:.1f}%")
    print("===============")

# --------------------------------------------------------------------------- #
# 直接执行
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    run()
