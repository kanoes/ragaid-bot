"""
状態管理
"""

import streamlit as st


def init_session_state():
    """
    セッション状態の初期化
    """
    if "restaurant" not in st.session_state:
        st.session_state["restaurant"] = None

    if "stats" not in st.session_state:
        st.session_state["stats"] = None
        
    if "batch_histories" not in st.session_state:
        st.session_state["batch_histories"] = []
        
    if "current_batch_id" not in st.session_state:
        st.session_state["current_batch_id"] = 0

    # レイアウトエディター状態の初期化
    if "editor_height" not in st.session_state:
        st.session_state["editor_height"] = 10

    if "editor_width" not in st.session_state:
        st.session_state["editor_width"] = 10

    if "editor_grid" not in st.session_state:
        st.session_state["editor_grid"] = [[0 for _ in range(10)] for _ in range(10)]

    if "editor_tables" not in st.session_state:
        st.session_state["editor_tables"] = {}

    if "editor_kitchen" not in st.session_state:
        st.session_state["editor_kitchen"] = []

    if "editor_parking" not in st.session_state:
        st.session_state["editor_parking"] = None

    if "editor_layout_name" not in st.session_state:
        st.session_state["editor_layout_name"] = "新しいレイアウト"

    if "editor_loaded" not in st.session_state:
        st.session_state["editor_loaded"] = False


def get_restaurant():
    """
    現在のレストランインスタンスを取得
    """
    return st.session_state.get("restaurant")


def set_restaurant(restaurant):
    """
    現在のレストランインスタンスを設定
    """
    st.session_state["restaurant"] = restaurant


def get_stats():
    """
    シミュレーション統計結果を取得
    """
    return st.session_state.get("stats")


def set_stats(stats):
    """
    シミュレーション統計結果を設定
    """
    st.session_state["stats"] = stats


def get_path_histories():
    """
    経路履歴を取得
    """
    return st.session_state.get("path_histories", [])


def set_path_histories(path_histories):
    """
    経路履歴を設定
    """
    st.session_state["path_histories"] = path_histories


def get_batch_histories():
    """
    全てのバッチ履歴データを取得
    """
    return st.session_state.get("batch_histories", [])


def set_batch_histories(batch_histories):
    """
    バッチ履歴データを設定
    """
    st.session_state["batch_histories"] = batch_histories


def append_batch_histories(new_batch_histories):
    """
    新しいバッチ履歴データを既存履歴に追加
    
    Args:
        new_batch_histories: 新しいバッチ履歴データリスト
    """
    if new_batch_histories:
        current_histories = get_batch_histories()
        st.session_state["batch_histories"] = current_histories + new_batch_histories


def reset_batch_histories():
    """
    バッチ履歴データとバッチIDをリセット
    """
    st.session_state["batch_histories"] = []
    st.session_state["current_batch_id"] = 0


# レイアウトエディター状態管理関数
def get_editor_height():
    """
    エディターの高さを取得
    """
    return st.session_state.get("editor_height")


def set_editor_height(height):
    """
    エディターの高さを設定
    """
    st.session_state["editor_height"] = height


def get_editor_width():
    """
    エディターの幅を取得
    """
    return st.session_state.get("editor_width")


def set_editor_width(width):
    """
    エディターの幅を設定
    """
    st.session_state["editor_width"] = width


def get_editor_grid():
    """
    エディターグリッドを取得
    """
    return st.session_state.get("editor_grid")


def set_editor_grid(grid):
    """
    エディターグリッドを設定
    """
    st.session_state["editor_grid"] = grid


def get_editor_tables():
    """
    エディターのテーブル位置を取得
    """
    return st.session_state.get("editor_tables")


def set_editor_tables(tables):
    """
    エディターのテーブル位置を設定
    """
    st.session_state["editor_tables"] = tables


def get_editor_kitchen():
    """
    エディターのキッチン位置を取得
    """
    return st.session_state.get("editor_kitchen")


def set_editor_kitchen(kitchen):
    """
    エディターのキッチン位置を設定
    """
    st.session_state["editor_kitchen"] = kitchen


def get_editor_parking():
    """
    エディターの駐車位置を取得
    """
    return st.session_state.get("editor_parking")


def set_editor_parking(parking):
    """
    エディターの駐車位置を設定
    """
    st.session_state["editor_parking"] = parking


def get_editor_layout_name():
    """
    エディターのレイアウト名を取得
    """
    return st.session_state.get("editor_layout_name")


def set_editor_layout_name(name):
    """
    エディターのレイアウト名を設定
    """
    st.session_state["editor_layout_name"] = name


def is_editor_loaded():
    """
    エディターがレイアウトを読み込んだかどうかを確認
    """
    return st.session_state.get("editor_loaded", False)


def set_editor_loaded(loaded):
    """
    エディターの読み込み状態を設定
    """
    st.session_state["editor_loaded"] = loaded


def reset_editor():
    """
    エディター状態をリセット
    """
    height = get_editor_height()
    width = get_editor_width()

    st.session_state["editor_grid"] = [[0 for _ in range(width)] for _ in range(height)]
    st.session_state["editor_tables"] = {}
    st.session_state["editor_kitchen"] = []
    st.session_state["editor_parking"] = None


def get_editor_state():
    """
    完全なエディター状態を取得
    
    注意: この関数は現在使用されていませんが、将来の拡張ポイントとして保持されています。
    エディター状態のエクスポートやシリアライズ（例えば永続ストレージやAPIインターフェース用）に使用可能です。
    """
    return {
        "editor_height": get_editor_height(),
        "editor_width": get_editor_width(),
        "editor_grid": get_editor_grid(),
        "editor_tables": get_editor_tables(),
        "editor_kitchen": get_editor_kitchen(),
        "editor_parking": get_editor_parking(),
        "editor_layout_name": get_editor_layout_name(),
    }


def load_layout_to_editor(restaurant):
    """
    レストランのレイアウトをエディターにロードする
    """
    if restaurant and restaurant.layout:
        set_editor_height(restaurant.layout.height)
        set_editor_width(restaurant.layout.width)
        set_editor_grid(restaurant.layout.grid)
        set_editor_tables(restaurant.layout.tables)
        set_editor_kitchen(restaurant.layout.kitchen)
        set_editor_parking(restaurant.layout.parking)
        set_editor_layout_name(restaurant.name)
        set_editor_loaded(True)
        return True
    return False


def get_next_batch_id():
    """
    次のバッチIDを取得し、カウンターを増加
    """
    if "current_batch_id" not in st.session_state:
        st.session_state["current_batch_id"] = 0
    
    st.session_state["current_batch_id"] += 1
    return st.session_state["current_batch_id"]


def get_current_batch_id():
    """
    現在のバッチIDを取得
    """
    if "current_batch_id" not in st.session_state:
        st.session_state["current_batch_id"] = 0
    
    return st.session_state["current_batch_id"]


def reset_batch_id():
    """
    バッチIDカウンターをリセット
    """
    st.session_state["current_batch_id"] = 0
