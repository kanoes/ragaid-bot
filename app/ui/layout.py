"""
レイアウトレンダリングコンポーネント
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
from rich.text import Text

from .base import ENABLE_CACHING


def render_sidebar(layouts, restaurant):
    """
    レストランレイアウトを選択するためのサイドバーをレンダリングします
    """
    if not layouts:
        st.error("レストランレイアウトファイルが見つかりません")
        return None, None, None

    selected = st.sidebar.selectbox("レストランレイアウトを選択", layouts)
    use_ai = st.sidebar.checkbox("RAGインテリジェントロボットを使用", value=False)
    num_orders = st.sidebar.slider(
        "注文数", 1, max(1, len(restaurant.layout.tables)), 1
    )

    sim_button = st.sidebar.button("シミュレーション開始")

    return selected, use_ai, num_orders, sim_button


def render_restaurant_layout(
    restaurant, path=None, table_positions=None, title="レストランレイアウト"
):
    """
    レストラングリッドレイアウトをHTML+CSSでレンダリングします。パスの強調表示とテーブルの表示をサポートします。

    パラメータ:
    - restaurant: Restaurant，レストランインスタンス
    - path: List[Tuple[int, int]]，オプション、ロボットパス
    - table_positions: Dict[str, Tuple[int, int]]，オプション、テーブル座標
    - title: str，タイトル
    """
    path = path or []
    table_positions = table_positions or {}

    st.markdown(f"### {title}")
    st.markdown("⬇️ 現在のレストラングリッドレイアウト：")

    html = f"""
    <div style="display: grid; grid-template-columns: repeat({len(restaurant.layout.grid[0])}, 24px); gap: 1px;">
    """

    for row in range(len(restaurant.layout.grid)):
        for col in range(len(restaurant.layout.grid[0])):
            pos = (row, col)
            color = "#ffffff"  # デフォルトの空地は白色
            label = ""

            val = restaurant.layout.grid[row][col]

            if pos in path:
                color = "#ff4d4d"  # パスは赤色
            elif val == 1:
                color = "#333333"  # 壁
            elif val == 3:
                color = "#f5c518"  # キッチン
            elif val == 4:
                color = "#4da6ff"  # 駐車場
            elif val == 2 or pos in table_positions.values():
                color = "#00cc66"  # テーブルは緑色

            # テーブルの場合、テキストを表示
            for name, tpos in table_positions.items():
                if tpos == pos:
                    label = name
                    break

            html += f"""
            <div style="
                width: 24px;
                height: 24px;
                background-color: {color};
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
                color: black;
                font-weight: bold;
                border: 1px solid #aaa;
            ">{label}</div>
            """

    html += "</div>"

    st.markdown(html, unsafe_allow_html=True)


@st.cache_data(ttl=300, show_spinner=False, hash_funcs={object: lambda x: id(x)}) if ENABLE_CACHING else lambda f: f
def render_plotly_restaurant_layout(_restaurant, path=None, title="レストランレイアウト", random_key=None):
    """
    レストランレイアウトをPlotlyでレンダリングします。より良い視覚効果を提供します。

    パラメータ:
    - _restaurant: Restaurant，レストランインスタンス
    - path: List[Tuple[int, int]]，オプション、ロボットパス
    - title: str，タイトル
    - random_key: str，オプション、強制的に再レンダリングするためのランダムキー
    """
    layout = _restaurant.layout
    grid = layout.grid
    height = layout.height
    width = layout.width

    # カラーマップを作成
    colormap = {
        0: "white",  # 空地
        1: "#333333",  # 壁/障害物
        2: "#00cc66",  # テーブル
        3: "#f5c518",  # キッチン
        4: "#4da6ff",  # 駐車場
    }

    # ラベルマップを作成
    labels = [["" for _ in range(width)] for _ in range(height)]

    # テーブルラベルを設定
    for table_id, pos in layout.tables.items():
        row, col = pos
        labels[row][col] = table_id

    # キッチンラベルを設定
    for row, col in layout.kitchen:
        labels[row][col] = "厨"

    # 駐車場ラベルを設定
    if layout.parking:
        row, col = layout.parking
        labels[row][col] = "停"

    # ヒートマップデータを作成
    fig = go.Figure()

    # ヒートマップ - 色塊を表示
    heatmap_z = np.array(grid)
    colorscale = [
        [0, colormap[0]],
        [0.2, colormap[0]],
        [0.2, colormap[1]],
        [0.4, colormap[1]],
        [0.4, colormap[2]],
        [0.6, colormap[2]],
        [0.6, colormap[3]],
        [0.8, colormap[3]],
        [0.8, colormap[4]],
        [1.0, colormap[4]],
    ]

    fig.add_trace(
        go.Heatmap(
            z=heatmap_z,
            colorscale=colorscale,
            showscale=False,
            hoverinfo="none",
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
                    font=dict(size=14, color="black", family="Arial Black"),
                )

    # パスポイント（存在する場合）
    if path:
        path_y, path_x = zip(*path)  # Plotlyの座標系に注意
        fig.add_trace(
            go.Scatter(
                x=path_x,
                y=path_y,
                mode="lines+markers",
                marker=dict(size=8, color="red"),
                line=dict(width=2, color="red"),
                name="経路",
            )
        )

    # チャートレイアウトを設定
    fig.update_layout(
        title=dict(text=title, font=dict(size=20)),
        width=width * 50,  # グリッドサイズに基づいてチャートサイズを調整
        height=height * 50,
        margin=dict(l=0, r=0, t=40, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=True,
            gridcolor="lightgrey",
            gridwidth=1,
            zeroline=False,
            showticklabels=False,
            range=[-0.5, width - 0.5],
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="lightgrey",
            gridwidth=1,
            zeroline=False,
            showticklabels=False,
            scaleanchor="x",
            scaleratio=1,
            range=[height - 0.5, -0.5],  # Y軸を反転させて(0,0)を左上にする
        ),
        # 国際チェスボードスタイルの背景グリッドを追加
        shapes=[
            # 水平線
            *[dict(
                type="line",
                x0=-0.5, x1=width-0.5,
                y0=i-0.5, y1=i-0.5,
                line=dict(color="lightgrey", width=1)
            ) for i in range(height+1)],
            # 垂直線
            *[dict(
                type="line",
                x0=j-0.5, x1=j-0.5,
                y0=-0.5, y1=height-0.5,
                line=dict(color="lightgrey", width=1)
            ) for j in range(width+1)]
        ]
    )

    st.plotly_chart(fig)

    return fig


def _get_table_style(x, y, tables):
    """
    テーブルのスタイルとラベルを取得
    """
    # 位置からテーブルIDを逆引き
    table_id = None
    for tid, pos in tables.items():
        if pos == (x, y):
            table_id = tid
            break

    if table_id:
        return Text(table_id.center(2), style="black on cyan")
    else:
        return Text("卓", style="black on cyan")


@st.cache_data(ttl=300, show_spinner=False, hash_funcs={object: lambda x: id(x)}) if ENABLE_CACHING else lambda f: f
def render_plotly_robot_path(_restaurant, path_history, orders=None, title="ロボット経路"):
    """
    ロボットパスの動的チャートをレンダリングします
    
    Args:
        _restaurant: Restaurantインスタンス
        path_history: パス履歴
        orders: 注文リスト
        title: チャートタイトル
    """
    layout = _restaurant.layout
    grid = layout.grid
    height = layout.height
    width = layout.width

    # カラーマップを作成
    colormap = {
        0: "white",  # 空地
        1: "#333333",  # 壁/障害物
        2: "#00cc66",  # テーブル
        3: "#f5c518",  # キッチン
        4: "#4da6ff",  # 駐車場
    }

    # ラベルマップを作成
    labels = [["" for _ in range(width)] for _ in range(height)]

    # テーブルラベルを設定
    for table_id, pos in layout.tables.items():
        row, col = pos
        labels[row][col] = table_id

    # キッチンラベルを設定
    for row, col in layout.kitchen:
        labels[row][col] = "厨"

    # 駐車場ラベルを設定
    if layout.parking:
        row, col = layout.parking
        labels[row][col] = "停"

    # ヒートマップデータを作成
    fig = go.Figure()

    # ヒートマップ - 色塊を表示
    heatmap_z = np.array(grid)
    colorscale = [
        [0, colormap[0]],
        [0.2, colormap[0]],
        [0.2, colormap[1]],
        [0.4, colormap[1]],
        [0.4, colormap[2]],
        [0.6, colormap[2]],
        [0.6, colormap[3]],
        [0.8, colormap[3]],
        [0.8, colormap[4]],
        [1.0, colormap[4]],
    ]

    fig.add_trace(
        go.Heatmap(
            z=heatmap_z,
            colorscale=colorscale,
            showscale=False,
            hoverinfo="none",
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
                    font=dict(size=14, color="black", family="Arial Black"),
                )

    # パスポイントを抽出
    if path_history:
        # パスポイントを解包
        path_points = path_history
        if path_points:
            path_y, path_x = zip(*path_points)

            # マーカー付きのパスラインを追加
            fig.add_trace(
                go.Scatter(
                    x=path_x,
                    y=path_y,
                    mode="lines+markers",
                    marker=dict(
                        size=8,
                        color="#ff4d4d",
                        symbol="circle",
                    ),
                    line=dict(
                        width=2,
                        color="#ff4d4d",
                    ),
                    showlegend=False,  # 図例を非表示にする
                )
            )
        
        # オーダー情報が提供されている場合、配送順に基づいてコメントを追加
        if orders:
            # すべてのテーブルの配送点を取得
            table_delivery_points = {}
            for table_id, table_pos in _restaurant.layout.tables.items():
                delivery_pos = _restaurant.layout.get_delivery_point(table_id)
                if delivery_pos:
                    table_delivery_points[table_id] = delivery_pos

            # 配送順に基づいてコメントを追加
            sorted_orders = sorted(orders, key=lambda x: x.get('delivery_sequence', float('inf')))

            for order in sorted_orders:
                table_id = order.get('table_id')
                order_id = order.get('order_id')
                delivery_seq = order.get('delivery_sequence')
                
                # 配送順が存在する場合、順序付きのマーカーを追加
                if delivery_seq is not None and table_id in table_delivery_points:
                    pos = table_delivery_points[table_id]
                    fig.add_trace(
                        go.Scatter(
                            x=[pos[1]],  # 注意座標軸の入れ替え
                            y=[pos[0]],
                            mode="markers+text",
                            marker=dict(
                                size=20,
                                color="rgba(255, 255, 255, 0.8)",
                                symbol="circle",
                                line=dict(width=2, color="blue"),
                            ),
                            text=str(delivery_seq),
                            textposition="middle center",
                            textfont=dict(
                                size=14,
                                color="blue",
                                family="Arial Black",
                            ),
                            name=f"注文 #{order_id} (テーブル {table_id})",
                            showlegend=False,
                        )
                    )

    # チャートレイアウトを設定
    fig.update_layout(
        title=dict(
            text=title, 
            font=dict(size=20),
            y=0.97,  # タイトルを少し上に移動
        ),
        width=width * 50,  # グリッドサイズに基づいてチャートサイズを調整
        height=height * 50,
        margin=dict(l=10, r=10, t=60, b=30),  # 上下の余白を増やす
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=True,
            gridcolor="lightgrey",
            gridwidth=1,
            zeroline=False,
            showticklabels=False,
            range=[-0.5, width - 0.5],
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="lightgrey",
            gridwidth=1,
            zeroline=False,
            showticklabels=False,
            scaleanchor="x",
            scaleratio=1,
            range=[height - 0.5, -0.5],  # Y軸を反転させて(0,0)を左上にする
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",    # 底部に揃える
            y=0.01,              # y=0.01 底部に近づける
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255,255,255,0.8)",  # 半透明の白色背景
            bordercolor="lightgrey",
            borderwidth=1,
        ),
        # 国際チェスボードスタイルの背景グリッドを追加
        shapes=[
            # 水平線
            *[dict(
                type="line",
                x0=-0.5, x1=width-0.5,
                y0=i-0.5, y1=i-0.5,
                line=dict(color="lightgrey", width=1)
            ) for i in range(height+1)],
            # 垂直線
            *[dict(
                type="line",
                x0=j-0.5, x1=j-0.5,
                y0=-0.5, y1=height-0.5,
                line=dict(color="lightgrey", width=1)
            ) for j in range(width+1)]
        ]
    )

    st.plotly_chart(fig)

    return fig


def render_plotly_restaurant_layout_no_cache(_restaurant, path=None, title="レストランレイアウト"):
    """
    キャッシュのないレストランレイアウトレンダリング関数を確保します。最新のレイアウトを再レンダリングします。
    
    パラメータ:
    - _restaurant: Restaurant，レストランインスタンス
    - path: List[Tuple[int, int]]，オプション、ロボットパス
    - title: str，タイトル
    """
    layout = _restaurant.layout
    grid = layout.grid
    height = layout.height
    width = layout.width

    # カラーマップを作成
    colormap = {
        0: "white",  # 空地
        1: "#333333",  # 壁/障害物
        2: "#00cc66",  # テーブル
        3: "#f5c518",  # キッチン
        4: "#4da6ff",  # 駐車場
    }

    # ラベルマップを作成
    labels = [["" for _ in range(width)] for _ in range(height)]

    # テーブルラベルを設定
    for table_id, pos in layout.tables.items():
        row, col = pos
        labels[row][col] = table_id

    # キッチンラベルを設定
    for row, col in layout.kitchen:
        labels[row][col] = "厨"

    # 駐車場ラベルを設定
    if layout.parking:
        row, col = layout.parking
        labels[row][col] = "停"

    # チャートを作成
    fig = go.Figure()

    # チャートデータ
    heatmap_z = np.array(grid)
    colorscale = [
        [0, colormap[0]],
        [0.2, colormap[0]],
        [0.2, colormap[1]],
        [0.4, colormap[1]],
        [0.4, colormap[2]],
        [0.6, colormap[2]],
        [0.6, colormap[3]],
        [0.8, colormap[3]],
        [0.8, colormap[4]],
        [1.0, colormap[4]],
    ]

    fig.add_trace(
        go.Heatmap(
            z=heatmap_z,
            colorscale=colorscale,
            showscale=False,
            hoverinfo="none",
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
                    font=dict(size=14, color="black", family="Arial Black"),
                )

    # パスポイント（存在する場合）
    if path:
        path_y, path_x = zip(*path)  # Plotlyの座標系に注意
        fig.add_trace(
            go.Scatter(
                x=path_x,
                y=path_y,
                mode="lines+markers",
                marker=dict(size=8, color="red"),
                line=dict(width=2, color="red"),
                name="経路",
            )
        )

    # チャートレイアウトを設定
    fig.update_layout(
        title=dict(text=title, font=dict(size=20)),
        width=width * 50,  # グリッドサイズに基づいてチャートサイズを調整
        height=height * 50,
        margin=dict(l=0, r=0, t=40, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=True,
            gridcolor="lightgrey",
            gridwidth=1,
            zeroline=False,
            showticklabels=False,
            range=[-0.5, width - 0.5],
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="lightgrey",
            gridwidth=1,
            zeroline=False,
            showticklabels=False,
            scaleanchor="x",
            scaleratio=1,
            range=[height - 0.5, -0.5],
        ),
        # 国際チェスボードスタイルの背景グリッドを追加
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
        ]
    )

    st.plotly_chart(fig)

    return fig 