import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib
import platform
import os

# 配置matplotlib支持中文显示
def configure_matplotlib_fonts(custom_font=None):
    if custom_font:
        # 使用用户指定的字体
        font_family = [custom_font]
    else:
        # 根据不同操作系统选择默认字体
        system = platform.system()
        if system == 'Windows':
            # Windows系统，尝试使用微软雅黑
            font_family = ['Microsoft YaHei', 'SimHei', 'SimSun']
        elif system == 'Darwin':
            # macOS系统，尝试使用苹方字体
            font_family = ['PingFang SC', 'Hiragino Sans GB', 'STHeiti']
        else:
            # Linux系统，尝试使用思源黑体
            font_family = ['Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'Source Han Sans CN']
    
    # 设置字体
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = font_family
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 检查环境变量中是否有自定义字体设置
custom_font = os.environ.get('MATPLOTLIB_FONT', None)
# 确保在导入时就配置好字体
configure_matplotlib_fonts(custom_font)

def animate_robot_path(path_history, title="机器人路径动画"):
    """
    可视化机器人路径
    
    参数:
        path_history: 机器人走过的坐标列表
        title: 图形标题
    """
    xs, ys = zip(*path_history)
    
    fig, ax = plt.subplots()
    # 绘制背景路径（参考线）
    ax.plot(xs, ys, 'k--', alpha=0.3)
    robot_dot, = ax.plot([], [], 'bo', markersize=8)
    
    # 设置图形范围
    ax.set_xlim(min(xs) - 1, max(xs) + 1)
    ax.set_ylim(min(ys) - 1, max(ys) + 1)
    ax.set_title(title)
    ax.set_xlabel("X 轴")
    ax.set_ylabel("Y 轴")
    
    def update(frame):
        robot_dot.set_data(xs[frame], ys[frame])
        return robot_dot,
    
    anim = FuncAnimation(fig, update, frames=len(xs), interval=500, blit=True)
    plt.show() 