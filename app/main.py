"""
Streamlit Web App メインページロジック
"""

import gc
import streamlit as st
import pandas as pd
from .constants import logger
from .utils import available_layouts
from .ui import (
    setup_page,
    render_stats,
    render_plotly_restaurant_layout_no_cache,
    render_layout_editor,
    render_plotly_stats,
    render_plotly_robot_path,
    render_rag_test,
)
from .handlers import (
    handle_layout_selection,
    handle_simulation,
    handle_layout_save,
    handle_layout_delete,
)
from .state import (
    init_session_state,
    get_restaurant,
    set_restaurant,
    get_stats,
    set_stats,
    load_layout_to_editor,
    is_editor_loaded,
    set_editor_loaded,
    get_path_histories,
    set_path_histories,
    reset_batch_histories,
    get_batch_histories,
)


def run():
    """
    Streamlitアプリケーションを実行
    """
    # ページの設定とパフォーマンス最適化
    setup_page()
    init_session_state()

    # パフォーマンス最適化：Plotlyレンダリング中のメモリ消費を制限
    if "plotly_performance_tuned" not in st.session_state:
        st.session_state["plotly_performance_tuned"] = True
        # 強制ガベージコレクション
        gc.collect()

    # パフォーマンス最適化：メモリ効率の高い描画設定を使用
    if "performance_config" not in st.session_state:
        st.session_state["performance_config"] = {
            "max_points_per_chart": 1000,  # 各チャートの最大ポイント数を制限
            "use_webgl": True,  # WebGLレンダリングを使用（ブラウザがサポートしている場合）
            "batch_size": 10,  # バッチサイズ
        }

    # 利用可能なレイアウトを取得
    layouts = available_layouts()

    # --- サイドバー レイアウト選択 & パラメータ ---
    # レイアウトドロップダウンをレンダリング、後続の依存するウィジェットが最新のレストランを取得できるようにする
    if layouts:
        selected_layout = st.sidebar.selectbox(
            "レストランレイアウトを選択", layouts, key="layout_select"
        )
    else:
        selected_layout = None

    # 現在のレストランを取得し、切り替え時に即時更新
    restaurant = get_restaurant()
    if selected_layout and (restaurant is None or selected_layout != restaurant.name):
        # デバッグログを追加
        logger.info(f"現在のレストラン: {restaurant.name if restaurant else 'None'}")
        logger.info(f"選択レイアウト: {selected_layout}")
        
        # 新しいレイアウトをロード
        restaurant = handle_layout_selection(selected_layout)
        set_restaurant(restaurant)
        logger.info(f"レストランレイアウトのロード完了: {restaurant.name}")
        
        # 強制ページ更新 - UIの更新を確保
        st.rerun()

    # その他のサイドバーウィジェット
    use_ai = st.sidebar.checkbox("RAGインテリジェントロボットを使用", value=False, key="use_ai")
    num_tables = (
        len(restaurant.layout.tables) if (restaurant and restaurant.layout) else 1
    )
    num_orders = st.sidebar.slider(
        "注文数", 1, max(1, num_tables), 1, key="num_orders"
    )
    sim_button = st.sidebar.button("シミュレーション開始", key="sim_button")

    # --- メインインターフェースタブ ---
    tab1, tab2, tab3, tab4 = st.tabs(["シミュレーター", "データ分析", "レイアウトエディター", "RAGテスト"])

    with tab1:
        # 現在のレイアウトを可視化
        if restaurant:
            # キャッシュなしのバージョンを使用し、毎回最新のレイアウトを表示
            render_plotly_restaurant_layout_no_cache(restaurant)

        # シミュレーション処理
        if sim_button and restaurant:
            stats, path_histories = handle_simulation(restaurant, use_ai, num_orders)
            set_stats(stats)
            set_path_histories(path_histories)

        # 経路の可視化を表示
        path_histories = get_path_histories()
        if path_histories and restaurant:
            st.subheader("配達経路の可視化")
            
            # 割り当てられたすべての注文情報を表示
            if path_histories[0].get("orders"):
                orders = path_histories[0]["orders"]
                st.write(f"**割り当てられたすべての注文 ({len(orders)}件):**")
                order_df = pd.DataFrame(orders)
                st.dataframe(order_df, use_container_width=True)
            
            # 経路を表示
            st.write("**配達経路:**")
            render_plotly_robot_path(
                restaurant,
                path_histories[0]["path"],
                orders=path_histories[0].get("orders", []),
                title=f"ロボット #{path_histories[0]['robot_id']} 配達経路（駐車場から出発して戻る）",
            )

    with tab2:
        # 統計結果を表示
        stats = get_stats()
        if stats:
            # 基本統計
            render_stats(stats)

            # Plotly統計可視化
            render_plotly_stats(stats)
            
            # 履歴データ部分を表示
            batch_histories = get_batch_histories()
            
            # 履歴データ部分
            if batch_histories:  # 累積履歴バッチデータを優先使用
                # 見出しとリセットボタンを配置するためのカラムレイアウトを使用
                col1, col2 = st.columns([6, 1])
                with col1:
                    st.subheader("履歴シミュレーションデータ")
                with col2:
                    st.write("")  # ボタンを揃えるための空行を追加
                    reset_btn = st.button("🔄", key="reset_batch_data", help="履歴データをリセット")
                    if reset_btn:
                        reset_batch_histories()
                        st.success("すべての履歴バッチデータをリセットしました")
                        st.rerun()
                        
                history_df = pd.DataFrame(batch_histories)
                
                # フレンドリーな列名を表示
                display_columns = {
                    "batch_id": "シミュレーション回数",
                    "total_time": "配達完了時間",
                    "path_length": "総配達距離",
                    "avg_waiting_time": "平均注文待ち時間",
                    "機器人类型": "ロボットタイプ",
                    "餐厅布局": "レストランレイアウト"
                }
                
                # 表示する列を選択し、名前を変更
                if history_df.empty:
                    st.info("履歴データがありません")
                else:
                    display_df = history_df[[col for col in display_columns.keys() if col in history_df.columns]]
                    display_df.columns = [display_columns[col] for col in display_df.columns]
                    
                    # 数値列をフォーマット、単位を削除
                    for col in ["配達完了時間", "総配達距離", "平均注文待ち時間"]:
                        if col in display_df.columns:
                            display_df[col] = display_df[col].apply(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
            elif "配送历史" in stats and stats["配送历史"]:  # 累積データがない場合、現在のシミュレーションデータを使用
                col1, col2 = st.columns([6, 1])
                with col1:
                    st.subheader("履歴データ")
                with col2:
                    st.write("")  # ボタンを揃えるための空行を追加
                    reset_btn = st.button("🔄", key="reset_batch_data", help="履歴データをリセット")
                    if reset_btn:
                        reset_batch_histories()
                        st.success("すべての履歴バッチデータをリセットしました")
                        st.rerun()
                        
                history_df = pd.DataFrame(stats["配送历史"])
                
                # フレンドリーな列名を表示
                display_columns = {
                    "batch_id": "シミュレーション回数",
                    "total_time": "配達完了時間",
                    "path_length": "総配達距離",
                    "avg_waiting_time": "平均注文待ち時間",
                    "機器人类型": "ロボットタイプ",
                    "餐厅布局": "レストランレイアウト"
                }
                
                # 表示する列を選択し、名前を変更
                if history_df.empty:
                    st.info("履歴データがありません")
                else:
                    display_df = history_df[[col for col in display_columns.keys() if col in history_df.columns]]
                    display_df.columns = [display_columns[col] for col in display_df.columns]
                    
                    # 数値列をフォーマット、単位を削除
                    for col in ["配達完了時間", "総配達距離", "平均注文待ち時間"]:
                        if col in display_df.columns:
                            display_df[col] = display_df[col].apply(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.subheader("履歴データ")
                st.info("履歴バッチデータがありません")

    with tab3:
        st.header("レストランレイアウト管理")

        # レイアウトリストと削除ボタン
        col1, col2 = st.columns([3, 1])
        with col1:
            if layouts:
                layout_to_edit = st.selectbox(
                    "既存レイアウトを編集", ["新しいレイアウトを作成"] + layouts, key="layout_editor_select"
                )
            else:
                st.info("現在利用可能なレイアウトがありません。新しいレイアウトを作成してください")
                layout_to_edit = "新しいレイアウトを作成"
        with col2:
            if layout_to_edit != "新しいレイアウトを作成" and st.button(
                "選択されたレイアウトを削除", key="delete_layout"
            ):
                if handle_layout_delete(layout_to_edit):
                    st.success(f"レイアウト: {layout_to_edit} を削除しました")
                    # 削除されたレイアウトが現在使用中の場合、クリア
                    if restaurant and restaurant.name == layout_to_edit:
                        set_restaurant(None)
                        st.rerun()

        # 既存レイアウトをロードまたは新しいレイアウトを作成
        if layout_to_edit != "新しいレイアウトを作成" and not is_editor_loaded():
            # 既存レイアウトオブジェクトをエディターにロード
            restaurant_to_edit = handle_layout_selection(layout_to_edit)
            load_layout_to_editor(restaurant_to_edit)
            set_editor_loaded(True)
        elif layout_to_edit == "新しいレイアウトを作成" and is_editor_loaded():
            set_editor_loaded(False)
            st.rerun()

        # エディターをレンダリング
        new_layout = render_layout_editor()

        # レイアウト保存ボタン
        save_col1, save_col2 = st.columns([3, 1])
        with save_col1:
            layout_name = st.text_input(
                "レイアウト名",
                value=layout_to_edit if layout_to_edit != "新しいレイアウトを作成" else "",
                key="layout_name",
            )

        with save_col2:
            st.write("")
            st.write("")
            if st.button("レイアウトを保存", key="save_layout") and layout_name and new_layout:
                # レイアウト名を更新して保存
                new_layout["name"] = layout_name
                saved_restaurant = handle_layout_save(new_layout)
                if saved_restaurant:
                    st.success(f"レイアウト: {layout_name} を保存しました")
                    # 新しいレイアウトを現在のレストランに設定
                    set_restaurant(saved_restaurant)

    # RAGテストタブを追加
    with tab4:
        render_rag_test()
