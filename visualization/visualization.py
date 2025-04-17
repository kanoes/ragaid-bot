"""
可视化模块：Robot 运动路径动画

主要函数
--------
configure_fonts(custom_font: str | None = None) -> None
    设置 matplotlib 字体，支持跨平台多语言
animate_robot_path(
    path_history: list[tuple[int, int]],
    title: str = "Robot Path",
    save_path: str | None = None,
    fps: int = 2,
) -> None
    以 matplotlib 动画显示 (并可选保存) 机器人移动路径
"""

from __future__ import annotations

import logging
import os
import platform
from pathlib import Path
from typing import List, Tuple

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter, FFMpegWriter

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# 后端自动切换：无 DISPLAY 时使用 Agg
# --------------------------------------------------------------------------- #
if not os.environ.get("DISPLAY") and platform.system() != "Windows":
    matplotlib.use("Agg")


# --------------------------------------------------------------------------- #
# 字体配置
# --------------------------------------------------------------------------- #
def configure_fonts(custom_font: str | None = None) -> None:
    """
    根据操作系统或自定义字体配置 matplotlib
    """
    if custom_font:
        font_family = [custom_font]
    else:
        system = platform.system()
        font_family = (
            ["Microsoft YaHei", "SimHei"]
            if system == "Windows"
            else ["PingFang SC", "Hiragino Sans GB"]
            if system == "Darwin"
            else ["Noto Sans CJK SC", "WenQuanYi Micro Hei"]
        )

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": font_family,
            "axes.unicode_minus": False,
        }
    )


# 环境变量可覆盖字体
configure_fonts(os.getenv("MATPLOTLIB_FONT"))


# --------------------------------------------------------------------------- #
# 动画函数
# --------------------------------------------------------------------------- #
def animate_robot_path(
    path_history: List[Tuple[int, int]],
    title: str = "Robot Path",
    *,
    save_path: str | None = None,
    fps: int = 2,
) -> None:
    """
    展示并可选保存机器人移动路径动画

    Parameters
    ----------
    path_history : list[(x, y)]
        按时间顺序记录的坐标列表
    title : str
        图表标题。
    save_path : str | None
        若提供，自动保存为 mp4 或 gif，依据文件扩展名 (`.mp4` / `.gif`)
    fps : int
        导出帧率
    """
    if len(path_history) < 2:
        logger.warning("Path history too short (%s points); animation skipped.", len(path_history))
        return

    xs, ys = zip(*path_history)

    fig, ax = plt.subplots()
    ax.plot(xs, ys, "k--", alpha=0.3)
    dot, = ax.plot([], [], "bo", markersize=8)

    ax.set_xlim(min(xs) - 1, max(xs) + 1)
    ax.set_ylim(min(ys) - 1, max(ys) + 1)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title(title)

    def init():
        dot.set_data([], [])
        return (dot,)

    def update(frame: int):
        dot.set_data(xs[frame], ys[frame])
        return (dot,)

    anim = FuncAnimation(fig, update, frames=len(xs), init_func=init, blit=True, interval=1000 / fps)

    # 保存文件（根据扩展名自动选择 writer）
    if save_path:
        path = Path(save_path)
        writer = (
            PillowWriter(fps=fps)
            if path.suffix.lower() == ".gif"
            else FFMpegWriter(fps=fps, codec="libx264")
        )
        anim.save(path, writer=writer)
        logger.info("Animation saved to %s", path.resolve())

    # 只有在可交互后端时才 show
    if matplotlib.get_backend().lower() not in {"agg", "template"}:
        plt.show()
