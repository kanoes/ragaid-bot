import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib
import platform
import os

# matplotlibの日本語表示をサポートするための設定
def configure_matplotlib_fonts(custom_font=None):
    if custom_font:
        # ユーザー指定のフォントを使用
        font_family = [custom_font]
    else:
        # 異なるOSに応じてデフォルトフォントを選択
        system = platform.system()
        if system == 'Windows':
            # Windowsシステム、Microsoft YaHeiなどを使用
            font_family = ['Microsoft YaHei', 'SimHei', 'SimSun']
        elif system == 'Darwin':
            # macOSシステム、PingFang SCなどを使用
            font_family = ['PingFang SC', 'Hiragino Sans GB', 'STHeiti']
        else:
            # Linuxシステム、Noto Sans CJK SCなどを使用
            font_family = ['Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'Source Han Sans CN']
    
    # フォントを設定
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = font_family
    plt.rcParams['axes.unicode_minus'] = False  # マイナス記号表示の問題を解決

# 環境変数にカスタムフォント設定があるかチェック
custom_font = os.environ.get('MATPLOTLIB_FONT', None)
# インポート時にフォントが設定されていることを確認
configure_matplotlib_fonts(custom_font)

def animate_robot_path(path_history, title="ロボット経路アニメーション"):
    """
    ロボットの経路を可視化
    
    パラメータ:
        path_history: ロボットが通過した座標のリスト
        title: グラフのタイトル
    """
    # 経路履歴が空または短すぎるかチェック
    if not path_history:
        print(f"警告：経路履歴が空のため、アニメーションを生成できません")
        return
    
    if len(path_history) < 2:
        print(f"警告：経路履歴が短すぎます（{len(path_history)}ポイントのみ）、アニメーションを生成できません")
        return
    
    # path_historyの各要素が有効な座標点であることを確認
    try:
        xs, ys = zip(*path_history)
    except Exception as e:
        print(f"警告：経路履歴を解析できません、無効なデータが含まれている可能性があります: {e}")
        return
    
    # すべての座標が数値であることを確認
    if not all(isinstance(x, (int, float)) for x in xs) or not all(isinstance(y, (int, float)) for y in ys):
        print(f"警告：経路に非数値座標が含まれています")
        return
    
    fig, ax = plt.subplots()
    # 背景経路を描画（参照線）
    ax.plot(xs, ys, 'k--', alpha=0.3)
    robot_dot, = ax.plot([], [], 'bo', markersize=8)
    
    # グラフの範囲を設定
    ax.set_xlim(min(xs) - 1, max(xs) + 1)
    ax.set_ylim(min(ys) - 1, max(ys) + 1)
    ax.set_title(title)
    ax.set_xlabel("X軸")
    ax.set_ylabel("Y軸")
    
    def init():
        robot_dot.set_data([], [])
        return (robot_dot,)
    
    def update(frame):
        if 0 <= frame < len(xs):
            robot_dot.set_data([xs[frame]], [ys[frame]])  # 単一値をリストでラップ
        return (robot_dot,)
    
    # init_funcパラメータを使用し、blit=Trueの場合は各フレームが反復可能オブジェクトを返すことを確認
    anim = FuncAnimation(fig, update, frames=len(xs), init_func=init, interval=500, blit=True)
    plt.show()