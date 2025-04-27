"""
UIイベント処理関数
"""

import streamlit as st

from restaurant.restaurant_layout import RestaurantLayout
from restaurant.restaurant import Restaurant
from .utils import load_restaurant, save_restaurant_layout, delete_restaurant_layout
from .simulation import SimulationEngine
from .state import append_batch_histories


def handle_layout_selection(layout_name):
    """
    レイアウト選択イベントを処理
    """
    return load_restaurant(layout_name)


def handle_layout_save(layout_data):
    """
    レイアウト保存イベントを処理
    
    Args:
        layout_data: dict, レイアウトデータ

    Returns:
        Restaurant: 作成されたレストランオブジェクト
    """
    if layout_data:
        # ファイルに保存
        save_restaurant_layout(layout_data)

        # 新しいRestaurantLayoutインスタンスを作成
        layout = RestaurantLayout(
            grid=layout_data.get("grid"),
            table_positions=layout_data.get("table_positions"),
            kitchen_positions=layout_data.get("kitchen_positions"),
            parking_position=layout_data.get("parking_position"),
        )

        # Restaurantオブジェクトを作成して返す
        return Restaurant(layout_data.get("name", "新レイアウト"), layout)

    return None


def handle_layout_delete(layout_name):
    """
    レイアウト削除イベントを処理

    Args:
        layout_name: str, 削除するレイアウト名

    Returns:
        bool: 削除に成功したかどうか
    """
    return delete_restaurant_layout(layout_name)


def handle_simulation(restaurant, use_ai, num_orders):
    """
    シミュレーションボタンクリックイベントを処理
    """
    with st.spinner(f"{num_orders}件の注文の配達プロセスをシミュレーション中..."):
        # シミュレーションエンジンを作成
        engine = SimulationEngine(restaurant, use_ai)
        # シミュレーションを実行
        stats, path_histories = engine.run(num_orders)
        
        # 新しい配達履歴がある場合、累積履歴データに追加
        if "配達履歴" in stats and stats["配達履歴"]:
            append_batch_histories(stats["配達履歴"])
            
        return stats, path_histories
