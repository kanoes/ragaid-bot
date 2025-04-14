# visualization.py
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

def animate_robot_path(path_history, title="机器人路径动画"):
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