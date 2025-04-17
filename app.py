"""
Streamlit Web App for 送餐机器人模拟系统
调用 main_runner 核心逻辑，简化界面层代码
"""
import os
import random
import logging
import contextlib
from io import StringIO

import streamlit as st

from main_runner import _available_layouts, _load_restaurant, _build_robot, _make_order
from visualization import animate_robot_path

# ---------- 配置日志 ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- 常量 ----------
BASE_DIR = os.path.dirname(__file__)
LAYOUT_DIR = os.path.join(BASE_DIR, "resources", "my_restaurant")

# ---------- Streamlit App ----------

def main():
    st.set_page_config(page_title="餐厅送餐机器人模拟系统", layout="wide")
    st.title("餐厅送餐机器人模拟系统 (Web)")

    # 侧边栏：布局选择 + 参数配置
    layouts = _available_layouts(LAYOUT_DIR)
    if not layouts:
        st.error("未找到任何餐厅布局文件")
        return

    selected = st.sidebar.selectbox("选择餐厅布局", layouts)
    use_ai = st.sidebar.checkbox("使用 RAG 智能机器人", value=False)
    # 临时加载餐厅用于获取桌子数
    rest = _load_restaurant(selected)
    num_orders = st.sidebar.slider("订单数量", 1, max(1, len(rest.layout.tables)), 1)

    # 主界面展示餐厅 ASCII 布局
    st.header(f"餐厅: {rest.name}")
    buf = StringIO()
    with contextlib.redirect_stdout(buf):
        rest.layout.display(restaurant_name=rest.name)
    st.text(buf.getvalue())

    # “开始模拟”按钮
    if st.sidebar.button("开始模拟"):
        stats = {"delivered": 0, "failed": 0}
        for i in range(num_orders):
            order = _make_order(i + 1, random.choice(list(rest.layout.tables.keys())))
            # 分配并模拟
            bot = _build_robot(use_ai, rest.layout)
            success = bot.assign_order(order)
            if success:
                bot.simulate()
                # 可视化路径
                animate_robot_path(
                    bot.path_history,
                    title=f"Robot#{bot.robot_id} Order#{order.order_id}",
                    fps=4,
                )
                stats["delivered"] += 1
            else:
                stats["failed"] += 1

        # 展示统计结果
        st.header("统计结果")
        col1, col2, col3 = st.columns(3)
        col1.metric("成功配送", stats["delivered"])
        col2.metric("配送失败", stats["failed"])
        rate = stats["delivered"] / (stats["delivered"] + stats["failed"]) * 100
        col3.metric("成功率", f"{rate:.1f}%")


if __name__ == "__main__":
    main()
