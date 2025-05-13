"""
エディター関連コンポーネント
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
from streamlit_plotly_events import plotly_events

from ..state import (
    get_editor_height,
    set_editor_height,
    get_editor_width,
    set_editor_width,
    get_editor_grid,
    set_editor_grid,
    get_editor_tables,
    set_editor_tables,
    get_editor_kitchen,
    set_editor_kitchen,
    get_editor_parking,
    set_editor_parking,
    get_editor_layout_name,
    set_editor_layout_name,
    reset_editor,
)


def render_layout_editor():
    """
    レイアウトエディターのインターフェイスをレンダリング
    
    戻り値:
        dict: 編集後のレイアウトデータ。保存されていない場合はNoneを返す
    """
    # シンプルな表形式レイアウトエディターを作成
    st.subheader("レストランレイアウトエディター")
    
    # レイアウトサイズコントロール
    st.write("**グリッドサイズコントロール**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        current_height = get_editor_height()
        new_height = st.number_input(
            "高さ", min_value=3, max_value=30, value=current_height, key="editor_height_input"
        )
        if new_height != current_height:
            # 高さを変更するときに既存のデータを保持
            current_grid = get_editor_grid()
            current_width = get_editor_width()
            new_grid = [[0 for _ in range(current_width)] for _ in range(new_height)]
            for i in range(min(new_height, current_height)):
                for j in range(current_width):
                    new_grid[i][j] = current_grid[i][j]
            set_editor_grid(new_grid)
            set_editor_height(new_height)
            
            # テーブル位置を更新
            tables = get_editor_tables()
            tables = {k: v for k, v in tables.items() if v[0] < new_height}
            set_editor_tables(tables)
            
            kitchen = get_editor_kitchen()
            kitchen = [pos for pos in kitchen if pos[0] < new_height]
            set_editor_kitchen(kitchen)
            
            parking = get_editor_parking()
            if parking and parking[0] >= new_height:
                set_editor_parking(None)
                
            st.rerun()

    with col2:
        current_width = get_editor_width()
        new_width = st.number_input(
            "幅", min_value=3, max_value=30, value=current_width, key="editor_width_input"
        )
        if new_width != current_width:
            # 幅を変更するときに既存のデータを保持
            current_grid = get_editor_grid()
            current_height = get_editor_height()
            new_grid = [[0 for _ in range(new_width)] for _ in range(current_height)]
            for i in range(current_height):
                for j in range(min(new_width, current_width)):
                    new_grid[i][j] = current_grid[i][j]
            set_editor_grid(new_grid)
            set_editor_width(new_width)

            # テーブル位置を更新
            tables = get_editor_tables()
            tables = {k: v for k, v in tables.items() if v[1] < new_width}
            set_editor_tables(tables)

            kitchen = get_editor_kitchen()
            kitchen = [pos for pos in kitchen if pos[1] < new_width]
            set_editor_kitchen(kitchen)

            parking = get_editor_parking()
            if parking and parking[1] >= new_width:
                set_editor_parking(None)

            st.rerun()

    with col3:
        current_name = get_editor_layout_name()
        layout_name = st.text_input("レイアウト名", value=current_name, key="editor_layout_name_input")
        if layout_name != current_name:
            set_editor_layout_name(layout_name)

    # レイアウト編集用の視覚インターフェイスを作成
    st.subheader("レイアウト編集")
    st.write("グリッドセルをクリックしてタイプを変更")

    # レイアウト編集用に多列レイアウトを作成
    edit_col1, edit_col2 = st.columns([3, 1])
    
    with edit_col2:
        st.write("**要素ツールボックス**")
        # 編集する要素タイプを選択
        element_type = st.radio(
            "要素タイプを選択", 
            ["壁/障害物", "空き地", "テーブル", "キッチン", "駐車場"],
            captions=["#", ".", "A-Z", "厨", "停"],
            key="element_type_radio"
        )
        
        # 表示現在の要素の色
        element_colors = {
            "壁/障害物": "#333333",
            "空き地": "white",
            "テーブル": "#00cc66",
            "キッチン": "#f5c518",
            "駐車場": "#4da6ff"
        }
        
        st.markdown(
            f"""
            <div style="
                width: 100%; 
                height: 30px; 
                background-color: {element_colors[element_type]}; 
                border: 1px solid black;
                display: flex;
                align-items: center;
                justify-content: center;
                color: {"black" if element_type != "壁/障害物" else "white"};
                font-weight: bold;
            ">
                {element_type}
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # テーブルモード時、テーブルIDを入力する必要があります
        table_id = None
        if element_type == "テーブル":
            table_id = st.text_input("テーブルID (1つのアルファベット A-Z)", max_chars=1, key="table_id_input")
            if table_id and (not table_id.isalpha() or len(table_id) != 1):
                st.warning("テーブルIDは1つのアルファベット(A-Z)でなければなりません")
                
        # レイアウト統計情報を表示
        st.write("**レイアウト統計**")
        tables = get_editor_tables()
        kitchen = get_editor_kitchen()
        parking = get_editor_parking()
        
        st.markdown(f"""
        - グリッドサイズ: {get_editor_height()} × {get_editor_width()}
        - テーブル: {len(tables)} 個
        - キッチン: {len(kitchen)} 個
        - 駐車場: {"あり" if parking else "なし"}
        """)
        
        # 操作ボタン
        st.write("**操作**")
        if st.button("レイアウトをリセット", key="editor_reset_button"):
            # 空白レイアウトにリセット
            reset_editor()
            st.rerun()
            
        if st.button("自動で壁を追加", key="editor_add_walls_button"):
            # レイアウトの端に壁を追加
            grid = get_editor_grid()
            height = get_editor_height()
            width = get_editor_width()

            # 上下壁を追加
            for j in range(width):
                grid[0][j] = 1
                grid[height - 1][j] = 1

            # 左右壁を追加
            for i in range(height):
                grid[i][0] = 1
                grid[i][width - 1] = 1

            # レイアウトを更新
            set_editor_grid(grid)
            st.rerun()
    
    with edit_col1:
        # Plotlyチャートを使用してインタラクティブ編集を実装
        fig = render_interactive_editor_grid()
        
        # plotly_eventsを使用してチャートを表示し、クリックイベントを監視
        clicked_point = plotly_events(fig, click_event=True, key="layout_editor_plotly")
        
        if clicked_point:
            # クリックされた座標を取得
            try:
                point_data = clicked_point[0]
                row, col = int(point_data["y"]), int(point_data["x"])
                
                # 現在の状態を取得
                grid = get_editor_grid()
                tables = get_editor_tables()
                kitchen = get_editor_kitchen()
                parking = get_editor_parking()
                height = get_editor_height()
                width = get_editor_width()
                
                # 座標が有効範囲内にあることを確認
                if 0 <= row < height and 0 <= col < width:
                    
                    # 特殊要素タイプの処理
                    if element_type == "テーブル":
                        if table_id:
                            # テーブル位置を更新、同一IDは1つのみ
                            for k, v in list(tables.items()):
                                if k == table_id:
                                    tables.pop(k)
                            tables[table_id] = (row, col)
                            grid[row][col] = 2
                            
                            # この位置が以前に他の特殊要素である場合は削除
                            for k, v in list(tables.items()):
                                if v == (row, col) and k != table_id:
                                    tables.pop(k)
                            
                            if (row, col) in kitchen:
                                kitchen.remove((row, col))
                            
                            if parking == (row, col):
                                parking = None
                    
                    elif element_type == "キッチン":
                        # キッチン位置を更新、複数可能
                        if (row, col) not in kitchen:
                            kitchen.append((row, col))
                        grid[row][col] = 3
                        
                        # 他の重複要素を削除
                        for k, v in list(tables.items()):
                            if v == (row, col):
                                tables.pop(k)
                        
                        if parking == (row, col):
                            parking = None
                    
                    elif element_type == "駐車場":
                        # 駐車場を更新、1つのみ
                        parking = (row, col)
                        grid[row][col] = 4
                        
                        # 他の重複要素を削除
                        for k, v in list(tables.items()):
                            if v == (row, col):
                                tables.pop(k)
                        
                        if (row, col) in kitchen:
                            kitchen.remove((row, col))
                    
                    elif element_type == "空き地":
                        # 該当位置のすべての要素を削除
                        grid[row][col] = 0
                        
                        for k, v in list(tables.items()):
                            if v == (row, col):
                                tables.pop(k)
                        
                        if (row, col) in kitchen:
                            kitchen.remove((row, col))
                        
                        if parking == (row, col):
                            parking = None
                    
                    else:  # 壁/障害物
                        grid[row][col] = 1
                        
                        # 重複要素を削除
                        for k, v in list(tables.items()):
                            if v == (row, col):
                                tables.pop(k)
                        
                        if (row, col) in kitchen:
                            kitchen.remove((row, col))
                        
                        if parking == (row, col):
                            parking = None
                    
                    # 状態を更新
                    set_editor_grid(grid)
                    set_editor_tables(tables)
                    set_editor_kitchen(kitchen)
                    set_editor_parking(parking)
                    
                    # 強制的に再レンダリング
                    st.rerun()
            except Exception as e:
                st.error(f"クリックイベントの処理中にエラーが発生: {e}")
        
    # 保存ボタン領域
    save_col1, save_col2 = st.columns([3, 1])
        
    with save_col2:
        if st.button("レイアウトを保存", key="editor_save_layout_button", type="primary"):
            # レイアウトの有効性を検証
            is_valid, message = validate_layout_extended()
            if not is_valid:
                st.error(f"レイアウトが無効です! {message}")
                return None

            # 現在編集中のレイアウトデータを返す
            return {
                "name": get_editor_layout_name(),
                "grid": get_editor_grid(),
                "table_positions": get_editor_tables(),
                "kitchen_positions": get_editor_kitchen(),
                "parking_position": get_editor_parking(),
            }

    return None


def render_interactive_editor_grid():
    """
    インタラクティブに編集可能なPlotlyレストランレイアウトグリッドをレンダリング、強化版

    戻り値:
        go.Figure: Plotlyチャートオブジェクト
    """
    grid = get_editor_grid()
    height = get_editor_height()
    width = get_editor_width()
    tables = get_editor_tables()
    kitchen = get_editor_kitchen()
    parking = get_editor_parking()

    # カラーマップ
    colormap = {
        0: "white",         # 空き地
        1: "#333333",       # 壁/障害物
        2: "#00cc66",       # テーブル
        3: "#f5c518",       # キッチン
        4: "#4da6ff",       # 駐車場
    }

    # ラベルマップ
    labels = [["" for _ in range(width)] for _ in range(height)]

    # テーブルラベル
    for table_id, pos in tables.items():
        row, col = pos
        if 0 <= row < height and 0 <= col < width:  # 範囲外を防ぐ
            labels[row][col] = table_id

    # キッチンラベル
    for row, col in kitchen:
        if 0 <= row < height and 0 <= col < width:  # 範囲外を防ぐ
            labels[row][col] = "厨"

    # 駐車場ラベル
    if parking:
        row, col = parking
        if 0 <= row < height and 0 <= col < width:  # 範囲外を防ぐ
            labels[row][col] = "停"

    # チャートを作成
    fig = go.Figure()

    # ヒートマップデータ
    heatmap_z = np.array(grid)
    colorscale = [
        [0, colormap[0]],      # 空き地
        [0.2, colormap[0]],
        [0.2, colormap[1]],    # 壁/障害物
        [0.4, colormap[1]],
        [0.4, colormap[2]],    # テーブル
        [0.6, colormap[2]],
        [0.6, colormap[3]],    # キッチン
        [0.8, colormap[3]],
        [0.8, colormap[4]],    # 駐車場
        [1.0, colormap[4]],
    ]

    # 各セルのホバーテキストを生成
    hover_texts = []
    for i in range(height):
        row_texts = []
        for j in range(width):
            cell_desc = get_cell_description(i, j)
            row_texts.append(cell_desc)
        hover_texts.append(row_texts)

    fig.add_trace(
        go.Heatmap(
            z=heatmap_z,
            colorscale=colorscale,
            showscale=False,
            hoverinfo="text",
            hovertext=hover_texts,
            # デフォルトのheatmapツールチップを無効にする
            zhoverformat="none"
        )
    )

    # テキスト注釈 - ラベルを表示
    for i in range(height):
        for j in range(width):
            if labels[i][j]:
                fig.add_annotation(
                    x=j,
                    y=i,
                    text=labels[i][j],
                    showarrow=False,
                    font=dict(
                        size=16, 
                        color="black", 
                        family="Arial Black"
                    ),
                )

    # チャートレイアウトを設定
    fig.update_layout(
        width=min(800, max(400, width * 35)),
        height=min(800, max(400, height * 35)),
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            range=[-0.5, width - 0.5],
            tickvals=list(range(width)),
            ticktext=[str(i) for i in range(width)],
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            scaleanchor="x",
            scaleratio=1,
            range=[height - 0.5, -0.5],
            tickvals=list(range(height)),
            ticktext=[str(i) for i in range(height)],
            tickfont=dict(size=10),
        ),
        shapes=[
            *[dict(
                type="line",
                x0=-0.5, x1=width-0.5,
                y0=i-0.5, y1=i-0.5,
                line=dict(color="lightgrey", width=1)
            ) for i in range(height+1)],
            *[dict(
                type="line",
                x0=j-0.5, x1=j-0.5,
                y0=-0.5, y1=height-0.5,
                line=dict(color="lightgrey", width=1)
            ) for j in range(width+1)]
        ],
        hoverlabel=dict(
            bgcolor="white",
            font_size=14,
            font_family="Arial"
        )
    )

    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.5, y=-0.07,
        text="クリックして任意のセルに現在選択されている要素タイプを適用",
        showarrow=False,
        font=dict(size=12, color="grey"),
    )

    return fig


def validate_layout_extended():
    """
    レイアウトが有効かどうかを検証し、詳細なエラーメッセージを提供
    
    戻り値:
        tuple: (is_valid, message) レイアウトが有効かどうかと詳細情報
    """
    # テーブルが少なくとも1つあるかどうかを確認
    if not get_editor_tables():
        return False, "少なくとも1つのテーブルが必要です"

    # キッチンが少なくとも1つあるかどうかを確認
    if not get_editor_kitchen():
        return False, "少なくとも1つのキッチンが必要です"

    # 駐車場が少なくとも1つあるかどうかを確認
    if not get_editor_parking():
        return False, "少なくとも1つの駐車場が必要です"
        
    # レイアウト名を確認
    if not get_editor_layout_name() or get_editor_layout_name() == "新レイアウト":
        return False, "有効なレイアウト名を提供してください"

    return True, "レイアウトが有効です"


def get_cell_description(row, col):
    """
    セルの説明テキストを取得し、ホバーツールチップに使用
    """
    grid = get_editor_grid()
    if row >= len(grid) or col >= len(grid[0]):
        return ""

    cell_type = grid[row][col]
    descriptions = {0: "空き地", 1: "壁/障害物", 2: "テーブル", 3: "キッチン", 4: "駐車場"}

    base_desc = f"({row}, {col}): {descriptions.get(cell_type, '未知')}"

    # 追加情報を追加
    if cell_type == 2:  # テーブル
        for tid, pos in get_editor_tables().items():
            if pos == (row, col):
                return f"{base_desc} {tid}"

    return base_desc 