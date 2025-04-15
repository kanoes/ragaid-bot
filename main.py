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

# .envファイルから環境変数を読み込む
dotenv.load_dotenv()

# matplotlibの日本語フォントサポートを設定
try:
    # 特定のフォント設定環境変数が存在するかチェック
    font_path = os.environ.get('MATPLOTLIB_FONT', None)
    if font_path and os.path.exists(font_path):
        # 指定されたフォントファイルを使用
        font_prop = FontProperties(fname=font_path)
        plt.rcParams['font.family'] = font_prop.get_name()
    else:
        # システムの日本語フォントを試用
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False  # マイナス記号表示の問題を解決
except Exception as e:
    print(f"日本語フォント設定エラー: {e}")
    print("デフォルトフォントを使用します")

# matplotlibの日本語フォント警告をフィルタリング
warnings.filterwarnings("ignore", category=UserWarning, module="tkinter")

# 英語タイトルを使用する必要があるかチェック（ASCIIモード）
ASCII_MODE = False
if "--ascii" in sys.argv:
    ASCII_MODE = True
    sys.argv.remove("--ascii")
    print("ASCIIモード（英語タイトル）で実行中")

from modules.environment import RestaurantEnvironment, create_restaurant_layout, print_restaurant_info, display_full_restaurant
from modules.robot import Robot
from modules.utils import animate_robot_path, OrderManager, Order

def get_title(zh_title, en_title):
    """ASCIIモードに基づいて適切なタイトルを返す"""
    return en_title if ASCII_MODE else zh_title

def process_kitchen(order_manager, stop_event):
    """
    キッチン処理スレッド、キッチンの注文準備をシミュレート
    """
    while not stop_event.is_set():
        order_manager.process_kitchen_simulation()
        time.sleep(0.5)

def run_baseline_simulation(restaurant, order_manager, robot_count=1):
    """
    ベースラインロボットを使用して注文配送シミュレーションを実行
    """
    print("\n===== ベースラインロボットシミュレーション開始 =====")
    
    # ロボットを作成
    robots = []
    for i in range(robot_count):
        robot = Robot(restaurant, robot_id=i+1, enable_rag=False)
        robots.append(robot)
    
    # キッチン処理スレッドを開始
    stop_event = threading.Event()
    kitchen_thread = threading.Thread(target=process_kitchen, args=(order_manager, stop_event))
    kitchen_thread.daemon = True
    kitchen_thread.start()
    
    # シミュレーション実行
    simulation_time = 0
    max_simulation_time = 60  # 最大60秒シミュレーション
    
    try:
        while simulation_time < max_simulation_time:
            print(f"\n現在のシミュレーション時間: {simulation_time}秒")
            # 準備完了した注文の割り当てを確認
            for robot in robots:
                if robot.is_idle():
                    next_order = order_manager.get_next_delivery_order()
                    if next_order:
                        order_manager.assign_order_to_robot(next_order.order_id, robot.robot_id)
                        robot.assign_order(next_order)
            
            # 全ロボットを1ステップ実行
            for robot in robots:
                if robot.path:
                    robot.move()
                    if robot.current_order:
                        if robot.position == robot.goal:
                            order_manager.complete_order_delivery(robot.current_order.order_id)
                        elif hasattr(robot.current_order, 'delivered_flag'):
                            order_manager.complete_order_delivery(robot.current_order.order_id)
                            print(f"注文 #{robot.current_order.order_id} の状態を手動で更新（配達済みがキッチンに戻っていない）")
            
            time.sleep(0.5)
            simulation_time += 1
            
            # 処理待ちの注文がなく、全ロボットがアイドル状態の場合、シミュレーションを早期終了
            if (not order_manager.waiting_orders and 
                not order_manager.preparing_orders and 
                not order_manager.ready_orders and
                not order_manager.delivering_orders and
                all(robot.current_order is None or hasattr(robot.current_order, 'delivered_flag') for robot in robots)):
                print("すべての注文が処理完了、シミュレーション終了")
                for robot in robots:
                    if robot.current_order and hasattr(robot.current_order, 'delivered_flag'):
                        order_manager.complete_order_delivery(robot.current_order.order_id)
                        robot.current_order = None
                break
    
    finally:
        stop_event.set()
        kitchen_thread.join(timeout=1)
    
    print("\n===== ベースラインロボットシミュレーション結果 =====")
    print("注文統計:")
    stats = order_manager.get_statistics()
    print(f"  総注文数: {stats['total_orders']}")
    print(f"  完了注文数: {stats['completed_orders']}")
    print(f"  失敗注文数: {stats['failed_orders']}")
    print(f"  配送成功率: {stats['success_rate']:.2f}%")
    print(f"  平均配送時間: {stats['avg_delivery_time']:.2f}秒")
    
    for i, robot in enumerate(robots):
        print(f"\nロボット #{i+1} の経路:")
        if robot.path_history:
            print(f"経路履歴の長さ: {len(robot.path_history)}")
            title = get_title(f"ベースラインロボット #{i+1} の経路", f"Baseline Robot #{i+1} Path")
            animate_robot_path(robot.path_history, title=title)
        else:
            print("  経路記録なし")
    
    return stats

def run_rag_simulation(restaurant, order_manager, robot_count=1, api_key=None, knowledge_file=None):
    """
    RAGロボットを使用して注文配送シミュレーションを実行
    パラメータ:
        restaurant: レストラン環境
        order_manager: 注文マネージャー
        robot_count: ロボット数
        api_key: OpenAI APIキー
        knowledge_file: 知識ベースファイルパス
    """
    print("\n===== RAGロボットシミュレーション開始 =====")
    
    # ロボットを作成
    robots = []
    for i in range(robot_count):
        try:
            robot = Robot(restaurant, robot_id=i+1, enable_rag=True, 
                          api_key=api_key, knowledge_file=knowledge_file)
            robots.append(robot)
        except Exception as e:
            print(f"RAGロボットの作成に失敗: {e}")
            print("代わりにベースラインロボットを使用")
            robot = Robot(restaurant, robot_id=i+1, enable_rag=False)
            robots.append(robot)
    
    # キッチン処理スレッドを開始
    stop_event = threading.Event()
    kitchen_thread = threading.Thread(target=process_kitchen, args=(order_manager, stop_event))
    kitchen_thread.daemon = True
    kitchen_thread.start()
    
    simulation_time = 0
    max_simulation_time = 60  # 最大60秒シミュレーション
    
    try:
        while simulation_time < max_simulation_time:
            print(f"\n現在のシミュレーション時間: {simulation_time}秒")
            for robot in robots:
                if robot.is_idle():
                    next_order = order_manager.get_next_delivery_order()
                    if next_order:
                        order_manager.assign_order_to_robot(next_order.order_id, robot.robot_id)
                        path_success = robot.assign_order(next_order)
                        if path_success and robot.enable_rag and simulation_time > 3:
                            print("\nRAG障害物処理総合テストを実行中...")
                            robot.comprehensive_test()
            
            for robot in robots:
                if robot.path:
                    robot.move()
                    if robot.current_order:
                        if robot.position == robot.goal:
                            order_manager.complete_order_delivery(robot.current_order.order_id)
                        elif hasattr(robot.current_order, 'delivered_flag'):
                            order_manager.complete_order_delivery(robot.current_order.order_id)
                            print(f"注文 #{robot.current_order.order_id} の状態を手動で更新（配達済みがキッチンに戻っていない）")
            
            time.sleep(0.5)
            simulation_time += 1
            if (not order_manager.waiting_orders and 
                not order_manager.preparing_orders and 
                not order_manager.ready_orders and
                not order_manager.delivering_orders and
                all(robot.current_order is None or hasattr(robot.current_order, 'delivered_flag') for robot in robots)):
                print("すべての注文が処理完了、シミュレーション終了")
                for robot in robots:
                    if robot.current_order and hasattr(robot.current_order, 'delivered_flag'):
                        order_manager.complete_order_delivery(robot.current_order.order_id)
                        robot.current_order = None
                break
    
    finally:
        stop_event.set()
        kitchen_thread.join(timeout=1)
    
    print(f"\n===== RAGロボットシミュレーション結果 =====")
    print("注文統計:")
    stats = order_manager.get_statistics()
    print(f"  総注文数: {stats['total_orders']}")
    print(f"  完了注文数: {stats['completed_orders']}")
    print(f"  失敗注文数: {stats['failed_orders']}")
    print(f"  配送成功率: {stats['success_rate']:.2f}%")
    print(f"  平均配送時間: {stats['avg_delivery_time']:.2f}秒")
    
    for i, robot in enumerate(robots):
        print(f"\nロボット #{i+1} の経路:")
        if robot.path_history:
            print(f"経路履歴の長さ: {len(robot.path_history)}")
            title = get_title(f"RAGロボット #{i+1} の経路", f"RAG Robot #{i+1} Path")
            animate_robot_path(robot.path_history, title=title)
        else:
            print("  経路記録なし")
    
    return stats

def compare_simulation_results(baseline_stats, rag_stats):
    """
    二種類のロボットのシミュレーション結果を比較
    """
    print("\n===== シミュレーション結果比較 =====")
    print("指標\t\tベースラインロボット\tRAGロボット\t差異")
    print("-" * 60)
    
    completed_diff = rag_stats['completed_orders'] - baseline_stats['completed_orders']
    failed_diff = rag_stats['failed_orders'] - baseline_stats['failed_orders']
    success_rate_diff = rag_stats['success_rate'] - baseline_stats['success_rate']
    time_diff = baseline_stats['avg_delivery_time'] - rag_stats['avg_delivery_time']
    
    print(f"完了注文数\t{baseline_stats['completed_orders']}\t\t{rag_stats['completed_orders']}\t\t{completed_diff:+d}")
    print(f"失敗注文数\t{baseline_stats['failed_orders']}\t\t{rag_stats['failed_orders']}\t\t{failed_diff:+d}")
    print(f"配送成功率\t{baseline_stats['success_rate']:.2f}%\t\t{rag_stats['success_rate']:.2f}%\t\t{success_rate_diff:+.2f}%")
    print(f"平均配送時間\t{baseline_stats['avg_delivery_time']:.2f}秒\t{rag_stats['avg_delivery_time']:.2f}秒\t{time_diff:+.2f}秒")

def input_orders():
    """
    ユーザー入力から注文を取得
    """
    order_manager = OrderManager()
    
    print("\n===== 注文入力 =====")
    print("注文情報を入力してください（'完了'と入力して終了）")
    print("形式: テーブル番号 準備時間(秒)")
    
    while True:
        order_input = input("注文> ")
        if order_input.lower() in ['完了', 'done', 'q', 'quit', 'exit']:
            break
        
        try:
            parts = order_input.split()
            if len(parts) >= 2:
                table_id = int(parts[0])
                prep_time = float(parts[1])
                items = parts[2:] if len(parts) > 2 else []
                order_manager.create_order(table_id, prep_time, items)
            else:
                print("形式エラー。形式を使用してください: テーブル番号 準備時間")
        except ValueError:
            print("無効な入力。テーブル番号は整数、準備時間は数値である必要があります。")
    
    return order_manager

def parse_arguments():
    parser = argparse.ArgumentParser(description="レストラン配送ロボットシミュレーション")
    parser.add_argument('--api_key', type=str, help='OpenAI APIキー')
    parser.add_argument('--knowledge', type=str, default='knowledge.json', help='知識ベースファイルパス')
    parser.add_argument('--skip_baseline', action='store_true', help='ベースラインシミュレーションをスキップ')
    parser.add_argument('--ascii', action='store_true', help='ASCIIモードを使用（日本語レンダリングの問題を回避）')
    parser.add_argument('--font', type=str, help='グラフ表示用のフォントを指定')
    return parser.parse_args()

def main():
    """
    メイン関数、レストラン配送シミュレーションを実行
    """
    args = parse_arguments()
    
    if args.font:
        os.environ['MATPLOTLIB_FONT'] = args.font
        print(f"カスタムフォントを使用: {args.font}")
    
    global ASCII_MODE
    ASCII_MODE = args.ascii
    if ASCII_MODE:
        print("ASCIIモード表示を使用、日本語レンダリングの問題を回避")
    
    # 環境変数から直接OpenAI APIキーを読み取る（ユーザー入力やセーブを求めない）
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("エラー: 環境変数にOpenAI APIキーが見つかりません。.envファイルでOPENAI_API_KEYを設定してください")
        sys.exit(1)
    
    # 知識ベースファイルが存在することを確認
    ensure_knowledge_file(args.knowledge)
    
    # レストラン環境を作成
    restaurant = create_restaurant_layout()
    print_restaurant_info(restaurant)
    
    kitchen_pos = restaurant.get_kitchen_positions()[0]
    display_full_restaurant(restaurant, kitchen_pos)
    
    order_manager = input_orders()
    if not order_manager.orders:
        print("注文が入力されていません、プログラム終了")
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
    """知識ベースファイルが存在することを確認し、存在しない場合はサンプル知識ベースを作成"""
    if os.path.exists(knowledge_file_path):
        print(f"知識ベースファイルが存在します: {knowledge_file_path}")
        return
    
    print(f"知識ベースファイルが存在しません、サンプル知識ベースを作成: {knowledge_file_path}")
    dirname = os.path.dirname(knowledge_file_path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    
    example_knowledge = [
        "ロボットが障害物に遭遇した場合、まず障害物の性質を評価する必要があります。一時的な障害物であれば、短時間待ってから再試行できます。永続的な障害物であれば、経路を再計画する必要があります。",
        "レストラン環境では、混雑エリアは通常一時的な障害物であり、ロボットは減速して通過を待つべきです。",
        "短時間に同じ位置で複数回障害物に遭遇した場合、その障害物は永続的である可能性が高いため、代替経路を探すべきです。",
        "ロボットが実行可能な経路を見つけられない場合は、目的地に到達できないことを報告すべきです。",
        "移動中の人や物体に遭遇した場合は、迂回を試みるのではなく、それらが通過するのを待つべきです。",
        "目標が障害物に囲まれている場合、障害物が一時的である可能性があるため、しばらく待ってから近づくことを試みるべきです。",
        "交通量の多いエリアでは、ロボットはできるだけ端を走行し、他の人々の通行を妨げないようにすべきです。",
        "複数回の迂回の試みが失敗した場合、ロボットは経路が長くなっても、完全に異なる経路を検討すべきです。"
    ]
    
    with open(knowledge_file_path, 'w', encoding='utf-8') as f:
        json.dump(example_knowledge, f, ensure_ascii=False, indent=2)
    
    print(f"サンプル知識ベース作成成功、{len(example_knowledge)}個の知識エントリを含む")

if __name__ == "__main__":
    main()
