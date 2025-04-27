"""
UIコンポーネント関数
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
from rich.text import Text
from streamlit_plotly_events import plotly_events
import pandas as pd
import time
import os

from .state import (
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
    get_batch_histories,
)

# パフォーマンス最適化設定
ENABLE_CACHING = True  # キャッシュ最適化をあり効にする


def setup_page():
    """
    ページの基本設定
    """
    st.set_page_config(page_title="レストラン配達ロボットシミュレーションシステム", layout="wide")
    st.title("レストラン配達ロボットシミュレーションシステム (Web)")


def render_sidebar(layouts, restaurant):
    """
    サイドバーコンポーネントをレンダリング
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
    HTML+CSSを使用してレストラングリッドをレンダリング、経路のハイライトとテーブル表示をサポート。

    パラメータ:
    - restaurant: Restaurant、レストランインスタンス
    - path: List[Tuple[int, int]]、オプション、ロボット経路
    - table_positions: Dict[str, Tuple[int, int]]、オプション、テーブル座標
    - title: str、タイトル
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
            color = "#ffffff"  # デフォルト空地は白色
            label = ""

            val = restaurant.layout.grid[row][col]

            if pos in path:
                color = "#ff4d4d"  # 経路は赤色
            elif val == 1:
                color = "#333333"  # 壁
            elif val == 3:
                color = "#f5c518"  # キッチン
            elif val == 4:
                color = "#4da6ff"  # 駐車スポット
            elif val == 2 or pos in table_positions.values():
                color = "#00cc66"  # テーブルは緑

            # テーブルの場合、文字を表示
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
    Plotlyを使用してレストランレイアウトをレンダリング、より優れた視覚効果でチェス盤に似た表現。

    パラメータ:
    - _restaurant: Restaurant、レストランインスタンス
    - path: List[Tuple[int, int]]、オプション、ロボット経路
    - title: str、タイトル
    - random_key: str、オプション、強制的に再レンダリングするためのランダムキー
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
        4: "#4da6ff",  # 駐車スポット
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

    # 駐車スポットラベルを設定
    if layout.parking:
        row, col = layout.parking
        labels[row][col] = "停"

    # ヒートマップデータを作成
    fig = go.Figure()

    # ヒートマップを追加 - 色ブロックを表示
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

    # 添加文本注釋 - ラベルを表示
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

    # 添加路径点（如果あり）
    if path:
        path_y, path_x = zip(*path)  # 注意Plotlyの座標系
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

    # 設定グラフレイアウト
    fig.update_layout(
        title=dict(text=title, font=dict(size=20)),
        width=width * 50,  # グリッドサイズに基づいてグラフサイズを調整
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
            range=[height - 0.5, -0.5],  # Y軸を反転させて(0,0)を左上角に
        ),
        # 国際チェス盤スタイルの背景グリッドを追加
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


def render_stats(stats):
    """
    基本統計情報を表示
    """
    st.subheader("今回のシミュレーションデータ")
    
    # 指標を表示 - total_stepsを削除
    metrics = {
        "total_orders": "総注文数",
        "total_time": "総配達時間",
        "avg_waiting_time": "平均注文待ち時間",
        "総配送路程": "総配達距離",
        "レストランレイアウト": "レストランレイアウト",
        "ロボットタイプ": "ロボットタイプ",
    }
    
    if stats:
        # レストランレイアウト名を追加
        if "配送履歴" in stats and stats["配送履歴"] and "レストランレイアウト" in stats["配送履歴"][0]:
            stats["レストランレイアウト"] = stats["配送履歴"][0]["レストランレイアウト"]
            
        # よりコンパクトなレイアウトを使用
        col1, col2 = st.columns(2)
        
        # 左半分
        with col1:
            if "total_orders" in stats:
                st.write(f"**総注文数:** {stats['total_orders']}")
            if "total_time" in stats:
                st.write(f"**総配達時間:** {stats['total_time']:.2f}")
            if "avg_waiting_time" in stats:
                st.write(f"**平均注文待ち時間:** {stats['avg_waiting_time']:.2f}")
                
        # 右半分
        with col2:
            if "総配送路程" in stats:
                st.write(f"**総配達距離:** {stats['総配送路程']}")
            if "レストランレイアウト" in stats:
                st.write(f"**レストランレイアウト:** {stats['レストランレイアウト']}")
            if "ロボットタイプ" in stats:
                st.write(f"**ロボットタイプ:** {stats['ロボットタイプ']}")
        
        st.write("---")
        st.caption("注: 総配達時間と経路長は駐車スポットから出発し、すべての注文を配達して駐車スポットに戻るまでを計算")


@st.cache_data(ttl=300, show_spinner=False, hash_funcs={object: lambda x: id(x)}) if ENABLE_CACHING else lambda f: f
def render_plotly_stats(stats):
    """
    Plotlyを使用して統計データのグラフをレンダリング
    """
    if not stats:
        return
        
    # 基本統計データを準備
    key_metrics = {
        "総注文数": stats.get("total_orders", 0),
        "総配達距離": stats.get("総配送路程", 0),
        "総配達時間": stats.get("total_time", 0),
        "平均注文待ち時間": stats.get("avg_waiting_time", 0)
    }
    
    # 棒グラフを作成
    fig = go.Figure()
    
    # 棒を追加
    fig.add_trace(
        go.Bar(
            x=list(key_metrics.keys()),
            y=list(key_metrics.values()),
            text=[format_value(k, v, key_metrics) for k, v in key_metrics.items()],
            textposition='auto',
            marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        )
    )
    
    # レイアウトを設定
    fig.update_layout(
        title="コアパフォーマンス指標",
        xaxis_title="指標",
        yaxis_title="数値",
        height=400,
        margin=dict(l=40, r=40, t=40, b=40)
    )
    
    # グラフを表示
    st.plotly_chart(fig, use_container_width=True)


def format_value(key, value, metrics):
    """
    値表示の書式設定
    """
    # 単純な処理、metricsの書式設定ツールに依存しない
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)


@st.cache_data(ttl=300, show_spinner=False, hash_funcs={object: lambda x: id(x)}) if ENABLE_CACHING else lambda f: f
def render_plotly_robot_path(_restaurant, path_history, orders=None, title="ロボット経路"):
    """
    ロボット経路の動的グラフをレンダリング
    
    Args:
        _restaurant: Restaurantインスタンス
        path_history: 経路履歴
        orders: 注文リスト
        title: グラフタイトル
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
        4: "#4da6ff",  # 駐車スポット
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

    # 駐車スポットラベルを設定
    if layout.parking:
        row, col = layout.parking
        labels[row][col] = "停"

    # ヒートマップデータを作成
    fig = go.Figure()

    # ヒートマップを追加 - 色ブロックを表示
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

    # テキスト注釋を追加 - ラベルを表示
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

    # 経路点を追加
    if path_history and len(path_history) > 0:
        path_y, path_x = zip(*path_history)  # Plotlyの座標系に注意
        
        # ロボットの出発点と終点
        start_point = path_history[0]
        end_point = path_history[-1]
        
        # 完全な経路を描画
        fig.add_trace(
            go.Scatter(
                x=path_x,
                y=path_y,
                mode="lines",
                line=dict(
                    width=3,
                    color="rgba(255, 0, 0, 0.6)",
                    dash="solid",
                ),
                name="ロボット経路",
            )
        )
        
        # 突出表示出発点
        fig.add_trace(
            go.Scatter(
                x=[start_point[1]],
                y=[start_point[0]],
                mode="markers+text",
                marker=dict(
                    size=16,
                    color="green",
                    symbol="circle",
                    line=dict(width=2, color="darkgreen"),
                ),
                text=["S"],  # アルファベットSで出発点をマーク
                textposition="middle center",
                textfont=dict(size=10, color="white", family="Arial Black"),
                name="出発点",
                hoverinfo="text",
                hovertext="出発点（駐車スポット）",
            )
        )
        
        # 判断終点が出発点と同じかどうか
        is_same_point = start_point == end_point
        
        # 突出表示終点/現在位置
        fig.add_trace(
            go.Scatter(
                x=[end_point[1]],
                y=[end_point[0]],
                mode="markers+text",
                marker=dict(
                    size=16,
                    color="red",
                    symbol="circle",
                    line=dict(width=2, color="darkred"),
                ),
                text=["E" if not is_same_point else "S/E"],  # アルファベットEで終点をマーク
                textposition="middle center",
                textfont=dict(size=10, color="white", family="Arial Black"),
                name="戻り点" if not is_same_point else "出発/戻り点",
                hoverinfo="text",
                hovertext="戻り点（駐車スポット）",
                visible=not is_same_point,  # 出発点と同じ場合は表示しない
            )
        )
        
        # もし注文情報が提供された場合、配送順に基づいて注釋を追加
        if orders:
            # すべてのテーブルの配達点を取得
            table_delivery_points = {}
            for table_id, table_pos in _restaurant.layout.tables.items():
                delivery_pos = _restaurant.layout.get_delivery_point(table_id)
                if delivery_pos:
                    table_delivery_points[table_id] = delivery_pos

            # 尝试按配送顺序排序
            sorted_orders = sorted(orders, key=lambda x: x.get('delivery_sequence', float('inf')))

            # 配送順に基づいて注釋を追加
            for order in sorted_orders:
                table_id = order.get('table_id')
                order_id = order.get('order_id')
                delivery_seq = order.get('delivery_sequence')
                
                # 配送順が注釋された注文のみを注釋
                if delivery_seq and table_id in table_delivery_points:
                    # 配送目標点を使用して注釋
                    delivery_pos = table_delivery_points[table_id]
                    
                    # 配送順を注釋して注文IDを注釋
                    hover_text = f"配送順: #{delivery_seq}<br>注文ID: #{order_id}<br>テーブル: {table_id}"
                    table_markers = go.Scatter(
                        x=[delivery_pos[1]],
                        y=[delivery_pos[0]],
                        mode='markers+text',
                        marker=dict(
                            size=20,
                            color="rgba(255, 165, 0, 0.8)",  # オレンジ半透明
                            symbol="circle",
                            line=dict(width=2, color="orange"),
                        ),
                        text=[f"{delivery_seq}"],  # 数字のみ表示、#記号は表示しない
                        textposition="middle center",
                        textfont=dict(size=12, color="black", family="Arial Black"),
                        name="配送順",  # 簡略図例名
                        hoverinfo='text',
                        hovertext=hover_text,
                        showlegend=(order == sorted_orders[0])  # 最初の点のみ図例を表示
                    )
                    fig.add_trace(table_markers)

    # 設定グラフレイアウト
    fig.update_layout(
        title=dict(
            text=title, 
            font=dict(size=20),
            y=0.97,  # タイトルを少し上に移動
        ),
        width=width * 50,  # グリッドサイズに基づいてグラフサイズを調整
        height=height * 50,
        margin=dict(l=10, r=10, t=60, b=30),  # 上部と下部の余白を増やす
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
            range=[height - 0.5, -0.5],  # Y軸を反転させて(0,0)を左上角に
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",    # 下部に合わせる
            y=0.01,              # y=0.01 は底部に近い
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255,255,255,0.8)",  # 半透明白色背景
            bordercolor="lightgrey",
            borderwidth=1,
        ),
        # 国際チェス盤スタイルの背景グリッドを追加
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


@st.cache_data(ttl=300, show_spinner=False, hash_funcs={object: lambda x: id(x)}) if ENABLE_CACHING else lambda f: f
def render_plotly_stats_extended(stats_data, custom_metrics=None):
    """
    渲染扩展的统计数据可视化，支持自定义指标

    参数:
    - stats_data: dict，统计数据字典
    - custom_metrics: dict，自定义指标配置，格式为{'指标名称': {'color': 颜色, 'format': 格式化函数}}
    """
    if not stats_data:
        return
        
    # 获取累积的历史批次数据
    batch_histories = get_batch_histories()

    st.header("高级统计分析")

    # 默认的指标配置
    default_metrics = {
        "total_orders": {"color": "#00cc66", "format": lambda x: int(x)},
        "total_batches": {"color": "#ff9900", "format": lambda x: int(x)},
        "総配送路程": {"color": "#4da6ff", "format": lambda x: int(x)},
        "平均每批次订单数": {"color": "#f5c518", "format": lambda x: f"{x:.2f}"},
        "平均每订单步数": {"color": "#2196f3", "format": lambda x: f"{x:.2f}"}
    }

    # 合并自定义指标
    metrics = default_metrics.copy()
    if custom_metrics:
        metrics.update(custom_metrics)

    # 准备数据
    data = []

    # 添加基础统计
    data.append(
        {
            "指标": "総注文数",
            "值": stats_data.get("total_orders", 0),
            "颜色": metrics.get("total_orders", {}).get("color", "#00cc66"),
        }
    )
    data.append(
        {
            "指标": "総批次数",
            "值": stats_data.get("total_batches", 0),
            "颜色": metrics.get("total_batches", {}).get("color", "#ff9900"),
        }
    )
    
    # 添加路径长度指标
    data.append(
        {
            "指标": "総配送路程",
            "值": stats_data.get("総配送路程", 0),
            "颜色": metrics.get("総配送路程", {}).get("color", "#4da6ff"),
        }
    )

    # 添加平均值指标
    for key in ["平均每批次订单数", "平均每订单步数", "平均每订单配送时间"]:
        if key in stats_data:
            metric_config = metrics.get(
                key, {"color": "#9467bd", "format": lambda x: f"{x:.2f}"}
            )
            data.append({"指标": key, "值": stats_data[key], "颜色": metric_config["color"]})

    # 添加其他统计指标
    for key, value in stats_data.items():
        if key not in ["total_orders", "total_batches", "総配送路程", "平均每批次订单数", "平均每订单步数", "平均每订单配送时间", "配送履歴"]:
            metric_config = metrics.get(
                key, {"color": "#9467bd", "format": lambda x: x}
            )
            data.append({"指标": key, "值": value, "颜色": metric_config["color"]})

    # 创建图表
    tabs = st.tabs(["配送性能", "雷达图", "历史批次分析"])

    with tabs[0]:
        # 棒グラフ
        fig_bar = go.Figure()
        fig_bar.add_trace(
            go.Bar(
                x=[item["指标"] for item in data],
                y=[item["值"] for item in data],
                marker_color=[item["颜色"] for item in data],
                text=[format_value(item["指标"], item["值"], metrics) for item in data],
                textposition="auto",
            )
        )

        fig_bar.update_layout(
            title="配送性能指標詳細",
            xaxis=dict(title="指標"),
            yaxis=dict(title="数値"),
            height=400,
        )

        st.plotly_chart(fig_bar, use_container_width=True)

    with tabs[1]:
        # レーダーチャート
        fig_radar = go.Figure()

        fig_radar.add_trace(
            go.Scatterpolar(
                r=[item["値"] for item in data],
                theta=[item["指標"] for item in data],
                fill="toself",
                name="統計指標",
                line_color="rgba(255, 0, 0, 0.8)",
                fillcolor="rgba(255, 0, 0, 0.2)",
            )
        )

        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                ),
            ),
            title="配送性能レーダーチャート",
            height=400,
        )

        st.plotly_chart(fig_radar, use_container_width=True)

    with tabs[2]:
        # 批次历史分析
        if batch_histories:  # 優先使用累積的历史批次数据
            # 将历史数据转换为DataFrame进行分析
            history_df = pd.DataFrame(batch_histories)
            
            # 批次订单数分布
            if "orders_count" in history_df.columns:
                st.subheader("批次订单数分布")
                fig_batch = go.Figure()
                fig_batch.add_trace(
                    go.Bar(
                        x=[f"批次 {i+1}" for i in range(len(history_df))],
                        y=history_df["orders_count"],
                        marker_color="#4da6ff",
                        text=history_df["orders_count"],
                        textposition="auto",
                    )
                )
                fig_batch.update_layout(
                    title="各批次订单数量",
                    xaxis=dict(title="批次"),
                    yaxis=dict(title="订单数量"),
                    height=300,
                )
                st.plotly_chart(fig_batch, use_container_width=True)
            
            # 批次路径长度分布
            if "path_length" in history_df.columns:
                st.subheader("批次路径长度分布")
                fig_path = go.Figure()
                fig_path.add_trace(
                    go.Bar(
                        x=[f"批次 {i+1}" for i in range(len(history_df))],
                        y=history_df["path_length"],
                        marker_color="#00cc66",
                        text=history_df["path_length"],
                        textposition="auto",
                    )
                )
                fig_path.update_layout(
                    title="各批次路径长度",
                    xaxis=dict(title="批次"),
                    yaxis=dict(title="路径长度"),
                    height=300,
                )
                st.plotly_chart(fig_path, use_container_width=True)
                
            # 批次配送时间分布
            if "duration" in history_df.columns:
                st.subheader("批次配送时间分布")
                fig_duration = go.Figure()
                fig_duration.add_trace(
                    go.Bar(
                        x=[f"批次 {i+1}" for i in range(len(history_df))],
                        y=history_df["duration"],
                        marker_color="#ff9900",
                        text=[f"{d:.2f}" for d in history_df["duration"]],
                        textposition="auto",
                    )
                )
                fig_duration.update_layout(
                    title="各批次配送时间(秒)",
                    xaxis=dict(title="批次"),
                    yaxis=dict(title="时间(秒)"),
                    height=300,
                )
                st.plotly_chart(fig_duration, use_container_width=True)
        elif "配送履歴" in stats_data and stats_data["配送履歴"]:  # 如果没あり累积数据，使用当前模拟数据
            # 将历史数据转换为DataFrame进行分析
            history_df = pd.DataFrame(stats_data["配送履歴"])
            
            # 批次订单数分布
            if "orders_count" in history_df.columns:
                st.subheader("批次订单数分布")
                fig_batch = go.Figure()
                fig_batch.add_trace(
                    go.Bar(
                        x=[f"批次 {i+1}" for i in range(len(history_df))],
                        y=history_df["orders_count"],
                        marker_color="#4da6ff",
                        text=history_df["orders_count"],
                        textposition="auto",
                    )
                )
                fig_batch.update_layout(
                    title="各批次订单数量",
                    xaxis=dict(title="批次"),
                    yaxis=dict(title="订单数量"),
                    height=300,
                )
                st.plotly_chart(fig_batch, use_container_width=True)
            
            # 批次路径长度分布
            if "path_length" in history_df.columns:
                st.subheader("批次路径长度分布")
                fig_path = go.Figure()
                fig_path.add_trace(
                    go.Bar(
                        x=[f"批次 {i+1}" for i in range(len(history_df))],
                        y=history_df["path_length"],
                        marker_color="#00cc66",
                        text=history_df["path_length"],
                        textposition="auto",
                    )
                )
                fig_path.update_layout(
                    title="各批次路径长度",
                    xaxis=dict(title="批次"),
                    yaxis=dict(title="路径长度"),
                    height=300,
                )
                st.plotly_chart(fig_path, use_container_width=True)
                
            # 批次配送时间分布
            if "duration" in history_df.columns:
                st.subheader("批次配送时间分布")
                fig_duration = go.Figure()
                fig_duration.add_trace(
                    go.Bar(
                        x=[f"批次 {i+1}" for i in range(len(history_df))],
                        y=history_df["duration"],
                        marker_color="#ff9900",
                        text=[f"{d:.2f}" for d in history_df["duration"]],
                        textposition="auto",
                    )
                )
                fig_duration.update_layout(
                    title="各批次配送时间(秒)",
                    xaxis=dict(title="批次"),
                    yaxis=dict(title="时间(秒)"),
                    height=300,
                )
                st.plotly_chart(fig_duration, use_container_width=True)
        else:
            st.info("暂なし批次历史数据")

    return data


def render_layout_editor():
    """
    レストランレイアウトエディタをレンダリングし、ユーザーがレイアウトを作成、編集、削除できるようにする

    戻り値:
        dict: 编辑后的布局信息，如果没あり改变则返回None
    """
    st.header("レストランレイアウトエディタ")

    # 布局参数设置
    col1, col2, col3 = st.columns(3)
    with col1:
        current_height = get_editor_height()
        new_height = st.number_input(
            "高さ", min_value=3, max_value=30, value=current_height, key="editor_height_input"
        )
        if new_height != current_height:
            # 调整高さ时保留现あり数据
            current_grid = get_editor_grid()
            current_width = get_editor_width()
            new_grid = [[0 for _ in range(current_width)] for _ in range(new_height)]
            for i in range(min(new_height, current_height)):
                for j in range(current_width):
                    new_grid[i][j] = current_grid[i][j]
            set_editor_grid(new_grid)
            set_editor_height(new_height)

            # 检查并移除超出范围的特殊位置
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
            # 调整幅时保留现あり数据
            current_grid = get_editor_grid()
            current_height = get_editor_height()
            new_grid = [[0 for _ in range(new_width)] for _ in range(current_height)]
            for i in range(current_height):
                for j in range(min(new_width, current_width)):
                    new_grid[i][j] = current_grid[i][j]
            set_editor_grid(new_grid)
            set_editor_width(new_width)

            # 检查并移除超出范围的特殊位置
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

    # レイアウト編集用の視覚的インターフェースを作成
    st.subheader("编辑布局")
    st.write("グリッドセルをクリックしてタイプを変更")

    # 创建多行列布局，美化界面
    edit_col1, edit_col2 = st.columns([3, 1])
    
    with edit_col2:
        st.write("**要素ツールボックス**")
        # 編集する要素タイプを選択
        element_type = st.radio(
            "选择元素类型", 
            ["墙壁/障碍", "空地", "テーブル", "キッチン", "駐車スポット"],
            captions=["#", ".", "A-Z", "厨", "停"],
            key="element_type_radio"
        )
        
        # 元素类型映射到数值
        type_map = {"墙壁/障碍": 1, "空地": 0, "テーブル": 2, "キッチン": 3, "駐車スポット": 4}
        
        # 显示当前元素的颜色提示
        element_colors = {
            "墙壁/障碍": "#333333",
            "空地": "white",
            "テーブル": "#00cc66",
            "キッチン": "#f5c518",
            "駐車スポット": "#4da6ff"
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
                color: {"black" if element_type != "墙壁/障碍" else "white"};
                font-weight: bold;
            ">
                {element_type}
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # テーブルモードの場合、テーブルIDを入力する必要がある
        table_id = None
        if element_type == "テーブル":
            table_id = st.text_input("テーブルID (1文字のアルファベット A-Z)", max_chars=1, key="table_id_input")
            if table_id and (not table_id.isalpha() or len(table_id) != 1):
                st.warning("テーブルIDは1文字のアルファベット(A-Z)でなければなりません")
                
        # 显示统计信息
        st.write("**レイアウト統計**")
        tables = get_editor_tables()
        kitchen = get_editor_kitchen()
        parking = get_editor_parking()
        
        st.markdown(f"""
        - グリッドサイズ: {get_editor_height()} × {get_editor_width()}
        - テーブル: {len(tables)} 个
        - キッチン: {len(kitchen)} 个
        - 駐車スポット: {"あり" if parking else "なし"}
        """)
        
        # 操作按钮
        st.write("**操作**")
        if st.button("レイアウトをリセット", key="editor_reset_button"):
            # 重置为空白布局
            reset_editor()
            st.rerun()
            
        if st.button("自動で壁を追加", key="editor_add_walls_button"):
            # レイアウトの縁に壁を追加する
            grid = get_editor_grid()
            height = get_editor_height()
            width = get_editor_width()

            # 添加上部と下部の壁
            for j in range(width):
                grid[0][j] = 1
                grid[height - 1][j] = 1

            # 左右の壁を追加
            for i in range(height):
                grid[i][0] = 1
                grid[i][width - 1] = 1

            # 更新网格
            set_editor_grid(grid)
            st.rerun()
    
    with edit_col1:
        # 创建Plotly图表以便交互编辑
        fig = render_interactive_editor_grid()
        
        # 使用 plotly_events 展示图表并监听点击事件
        clicked_point = plotly_events(fig, click_event=True, key="layout_editor_plotly")
        
        if clicked_point:
            # 获取点击的坐标
            try:
                point_data = clicked_point[0]
                row, col = int(point_data["y"]), int(point_data["x"])
                
                # 获取当前状态
                grid = get_editor_grid()
                tables = get_editor_tables()
                kitchen = get_editor_kitchen()
                parking = get_editor_parking()
                height = get_editor_height()
                width = get_editor_width()

                # 根据选择的元素类型进行修改
                if 0 <= row < height and 0 <= col < width:
                    if (
                        element_type == "テーブル"
                        and table_id
                        and table_id.isalpha()
                        and len(table_id) == 1
                    ):
                        # 处理テーブル - 需要存储テーブルID和位置
                        # 先检查该ID是否已被使用
                        table_id_upper = table_id.upper()
                        if table_id_upper in tables and tables[table_id_upper] != (row, col):
                            # 如果已存在此ID但位置不同，找到并清除旧位置
                            old_row, old_col = tables[table_id_upper]
                            if grid[old_row][old_col] == 2:  # 确保旧位置确实是テーブル
                                grid[old_row][old_col] = 0  # 设为空地
                                
                        # 检查该位置是否已あり其他テーブル
                        table_to_remove = None
                        for tid, pos in tables.items():
                            if pos == (row, col) and tid != table_id_upper:
                                table_to_remove = tid
                        if table_to_remove:
                            del tables[table_to_remove]
                                
                        grid[row][col] = type_map[element_type]
                        tables[table_id_upper] = (row, col)
                        set_editor_tables(tables)
                    elif element_type == "キッチン":
                        # 处理キッチン - 可以あり多个キッチン位置
                        grid[row][col] = type_map[element_type]
                        if (row, col) not in kitchen:
                            kitchen.append((row, col))
                        set_editor_kitchen(kitchen)
                    elif element_type == "駐車スポット":
                        # 处理駐車スポット - 只能あり一个
                        # 先清除现あり的駐車スポット
                        if parking:
                            old_row, old_col = parking
                            if grid[old_row][old_col] == 4:
                                grid[old_row][old_col] = 0  # 设为空地

                        grid[row][col] = type_map[element_type]
                        set_editor_parking((row, col))
                    else:
                        # 处理墙壁或空地
                        old_value = grid[row][col]
                        grid[row][col] = type_map[element_type]

                        # 如果将某个特殊位置设为墙壁或空地，需要从相应列表中移除
                        # 检查和清理テーブル
                        if old_value == 2:  # 原来是テーブル
                            tables_to_remove = []
                            for tid, pos in tables.items():
                                if pos == (row, col):
                                    tables_to_remove.append(tid)
                            for tid in tables_to_remove:
                                del tables[tid]
                            set_editor_tables(tables)

                        # 检查和清理キッチン
                        if old_value == 3 and (row, col) in kitchen:  # 原来是キッチン
                            kitchen.remove((row, col))
                            set_editor_kitchen(kitchen)

                        # 检查和清理駐車スポット
                        if old_value == 4 and parking == (row, col):  # 原来是駐車スポット
                            set_editor_parking(None)

                    # 更新网格
                    set_editor_grid(grid)

                    # 强制重新渲染
                    st.rerun()
            except (KeyError, IndexError) as e:
                st.error(f"なし法处理点击: {e}")
    
    # レイアウトを保存按钮
    st.write("")
    save_col1, save_col2 = st.columns([3, 1])
    
    with save_col1:
        st.write("**レイアウトの編集を完了したら、保存をクリック：**")
        
    with save_col2:
        if st.button("レイアウトを保存", key="editor_save_layout_button", type="primary"):
            # 验证布局是否あり效
            is_valid, message = validate_layout_extended()
            if not is_valid:
                st.error(f"布局なし效! {message}")
                return None

            # 返回当前编辑的布局数据
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
    渲染交互式可编辑的Plotlyレストランレイアウト网格，改进版本

    戻り値:
        go.Figure: Plotly图表对象
    """
    grid = get_editor_grid()
    height = get_editor_height()
    width = get_editor_width()
    tables = get_editor_tables()
    kitchen = get_editor_kitchen()
    parking = get_editor_parking()

    # 创建颜色映射
    colormap = {
        0: "white",         # 空地
        1: "#333333",       # 墙壁/障碍
        2: "#00cc66",       # テーブル
        3: "#f5c518",       # キッチン
        4: "#4da6ff",       # 駐車スポット
    }

    # 创建标签映射
    labels = [["" for _ in range(width)] for _ in range(height)]

    # 设置テーブル标签
    for table_id, pos in tables.items():
        row, col = pos
        if 0 <= row < height and 0 <= col < width:  # 防止越界
            labels[row][col] = table_id

    # 设置キッチン标签
    for row, col in kitchen:
        if 0 <= row < height and 0 <= col < width:  # 防止越界
            labels[row][col] = "厨"

    # 设置駐車スポット标签
    if parking:
        row, col = parking
        if 0 <= row < height and 0 <= col < width:  # 防止越界
            labels[row][col] = "停"

    # 创建热力图数据
    fig = go.Figure()

    # 添加热力图 - 显示颜色块
    heatmap_z = np.array(grid)
    colorscale = [
        [0, colormap[0]],      # 空地
        [0.2, colormap[0]],
        [0.2, colormap[1]],    # 墙壁
        [0.4, colormap[1]],
        [0.4, colormap[2]],    # テーブル
        [0.6, colormap[2]],
        [0.6, colormap[3]],    # キッチン
        [0.8, colormap[3]],
        [0.8, colormap[4]],    # 駐車スポット
        [1.0, colormap[4]],
    ]

    # 生成每个单元格的悬停文本
    hover_texts = []
    for i in range(height):
        row_texts = []
        for j in range(width):
            cell_type = grid[i][j]
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
            # 禁用默认的heatmap tooltips
            zhoverformat="none"
        )
    )

    # 添加文本注釋 - 显示标签
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

    # 设置图表布局
    fig.update_layout(
        width=min(800, max(400, width * 35)),  # 更合理的大小调整
        height=min(800, max(400, height * 35)),
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=False,  # 不显示网格线，我们会自己添加
            zeroline=False,
            range=[-0.5, width - 0.5],
            tickvals=list(range(width)),
            ticktext=[str(i) for i in range(width)],
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            showgrid=False,  # 不显示网格线，我们会自己添加
            zeroline=False,
            scaleanchor="x",
            scaleratio=1,
            range=[height - 0.5, -0.5],  # 反转Y轴使(0,0)在左上角
            tickvals=list(range(height)),
            ticktext=[str(i) for i in range(height)],
            tickfont=dict(size=10),
        ),
        # 添加棋盘样式网格
        shapes=[
            # 水平线
            *[dict(
                type="line",
                x0=-0.5, x1=width-0.5,
                y0=i-0.5, y1=i-0.5,
                line=dict(color="lightgrey", width=1)
            ) for i in range(height+1)],
            # 垂直线
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

    # 添加额外的指导性提示
    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.5, y=-0.07,
        text="点击任意单元格应用当前选择的元素类型",
        showarrow=False,
        font=dict(size=12, color="grey"),
    )

    return fig


def validate_layout_extended():
    """
    验证布局是否あり效，并提供详细的错误信息
    
    戻り値:
        tuple: (is_valid, message) 布局是否あり效及详细信息
    """
    # 检查是否至少あり一个テーブル
    if not get_editor_tables():
        return False, "至少需要一个テーブル"

    # 检查是否至少あり一个キッチン
    if not get_editor_kitchen():
        return False, "至少需要一个キッチン"

    # 检查是否あり駐車スポット
    if not get_editor_parking():
        return False, "需要一个駐車スポット"
        
    # 检查レイアウト名
    if not get_editor_layout_name() or get_editor_layout_name() == "新布局":
        return False, "请提供あり效的レイアウト名"

    return True, "布局あり效"


def get_cell_description(row, col):
    """
    セルの説明テキストを取得し、ホバーツールチップに使用する
    """
    grid = get_editor_grid()
    if row >= len(grid) or col >= len(grid[0]):
        return ""

    cell_type = grid[row][col]
    descriptions = {0: "空地", 1: "墙壁/障碍", 2: "テーブル", 3: "キッチン", 4: "駐車スポット"}

    base_desc = f"({row}, {col}): {descriptions.get(cell_type, '未知')}"

    # 添加额外信息
    if cell_type == 2:  # テーブル
        for tid, pos in get_editor_tables().items():
            if pos == (row, col):
                return f"{base_desc} {tid}"

    return base_desc


def render_plotly_restaurant_layout_no_cache(_restaurant, path=None, title="レストランレイアウト"):
    """
    なし缓存版本的レストランレイアウト渲染函数，确保每次都重新渲染最新的布局。
    
    参数:
    - _restaurant: Restaurant，餐厅实例
    - path: List[Tuple[int, int]]，可选，机器人路径
    - title: str，标题
    """
    layout = _restaurant.layout
    grid = layout.grid
    height = layout.height
    width = layout.width

    # 创建颜色映射
    colormap = {
        0: "white",  # 空地
        1: "#333333",  # 墙壁/障碍
        2: "#00cc66",  # テーブル
        3: "#f5c518",  # キッチン
        4: "#4da6ff",  # 駐車スポット
    }

    # 创建标签映射
    labels = [["" for _ in range(width)] for _ in range(height)]

    # 设置テーブル标签
    for table_id, pos in layout.tables.items():
        row, col = pos
        labels[row][col] = table_id

    # 设置キッチン标签
    for row, col in layout.kitchen:
        labels[row][col] = "厨"

    # 设置駐車スポット标签
    if layout.parking:
        row, col = layout.parking
        labels[row][col] = "停"

    # 创建热力图数据
    fig = go.Figure()

    # 添加热力图 - 显示颜色块
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

    # 添加文本注釋 - 显示标签
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

    # 添加路径点（如果あり）
    if path:
        path_y, path_x = zip(*path)  # 注意Plotly的坐标系
        fig.add_trace(
            go.Scatter(
                x=path_x,
                y=path_y,
                mode="lines+markers",
                marker=dict(size=8, color="red"),
                line=dict(width=2, color="red"),
                name="路径",
            )
        )

    # 设置图表布局
    fig.update_layout(
        title=dict(text=title, font=dict(size=20)),
        width=width * 50,  # 根据网格大小调整图表大小
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
            range=[height - 0.5, -0.5],  # 反转Y轴使(0,0)在左上角
        ),
        # 添加国际象棋棋盘样式的背景网格
        shapes=[
            # 水平线
            *[dict(
                type="line",
                x0=-0.5, x1=width-0.5,
                y0=i-0.5, y1=i-0.5,
                line=dict(color="lightgrey", width=1)
            ) for i in range(height+1)],
            # 垂直线
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


def render_rag_test():
    """
    RAGテスト画面をレンダリングし、ユーザーが直接RAGモジュールのQA能力をテストできるようにします
    """
    from robot.rag import RAGModule
    import os
    import streamlit as st

    st.header("RAGシステムテスト")

    # OpenAI APIキーの使用
    api_key = os.environ.get("OPENAI_API_KEY", None)

    # RAGモジュールの初期化
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    knowledge_file = os.path.join(current_dir, "robot", "rag", "knowledge", "restaurant_rule.json")

    # セッションステートにRAGモジュールが存在しない場合、初期化
    if "rag_module" not in st.session_state:
        rag = RAGModule(
            api_key=api_key,
            knowledge_file=knowledge_file,
        )
        st.session_state["rag_module"] = rag
    else:
        rag = st.session_state["rag_module"]

    # RAGモジュールの準備状況を確認
    if not rag.is_ready():
        st.warning("ナレッジベースがロードされていない、またはAPIキーが設定されていません。純粋なLLM回答が使用される可能性があります。")
    else:
        st.success(f"ナレッジベースを正常にロードしました: {knowledge_file}")

    # テスト画面の作成
    test_tabs = st.tabs(["QAテスト", "思考レイヤーテスト", "トリガーレイヤーテスト", "意思決定インターフェーステスト"])

    # QAテストタブ
    with test_tabs[0]:
        st.subheader("直接QAテスト")
        query = st.text_input("質問を入力してください：（例：現在ありオーダー3番卓、5番卓、8番卓、配達順序を教えて）", key="qa_query")
        use_rag = st.checkbox("RAG強化回答を使用する", value=True, key="qa_use_rag")

        if st.button("質問を送信", key="qa_submit"):
            if not query:
                st.error("質問内容を入力してください")
            else:
                with st.spinner("思考中..."):
                    try:
                        answer = rag.query_answer(query, use_rag=use_rag)
                        st.success("回答成功")
                        st.info(answer)
                    except Exception as e:
                        st.error(f"エラーが発生しました: {e}")

    # 思考レイヤーテストタブ
    with test_tabs[1]:
        st.subheader("思考レイヤーテスト")
        query = st.text_input("質問を入力してください：（例：現在ありオーダー3番卓、5番卓、8番卓、配達順序を教えて）", key="thinking_query")
        use_rag = st.checkbox("RAG強化回答を使用する", value=True, key="thinking_use_rag")

        if st.button("質問を送信", key="thinking_submit"):
            if not query:
                st.error("質問内容を入力してください")
            else:
                with st.spinner("思考レイヤーで処理中..."):
                    try:
                        raw_response, context_docs = rag.thinking_layer(query, use_rag=use_rag)

                        # 結果表示
                        st.write("#### 思考レイヤー出力")
                        st.write(f"**取得したドキュメント数:** {len(context_docs)} 件")

                        for i, doc in enumerate(context_docs, 1):
                            with st.expander(f"ドキュメント {i}"):
                                st.write(doc)

                        st.write("#### LLMの生レスポンス:")
                        st.info(raw_response)

                        # 意思決定レイヤー処理結果を表示
                        action = rag.decision_layer(raw_response)
                        st.write("#### 意思決定レイヤー簡易結果:")
                        st.success(action)

                    except Exception as e:
                        st.error(f"エラーが発生しました: {e}")

    # トリガーレイヤーテストタブ
    with test_tabs[2]:
        st.subheader("トリガーレイヤーテスト")
        event_type = st.selectbox(
            "イベントタイプを選択してください:",
            ["plan", "obstacle"],
            format_func=lambda x: "経路計画イベント" if x == "plan" else "障害物処理イベント"
        )

        if event_type == "plan":
            robot_id = st.number_input("ロボットID", value=1, min_value=1, step=1)
            start_x = st.number_input("スタートX座標", value=0, step=1)
            start_y = st.number_input("スタートY座標", value=0, step=1)
            goal_x = st.number_input("ゴールX座標", value=10, step=1)
            goal_y = st.number_input("ゴールY座標", value=10, step=1)

            context = {
                'robot_id': robot_id,
                'start': (start_x, start_y),
                'goal': (goal_x, goal_y)
            }
        else:  # obstacle
            robot_id = st.number_input("ロボットID", value=1, min_value=1, step=1)
            pos_x = st.number_input("現在X座標", value=5, step=1)
            pos_y = st.number_input("現在Y座標", value=5, step=1)
            goal_x = st.number_input("ゴールX座標", value=10, step=1)
            goal_y = st.number_input("ゴールY座標", value=10, step=1)
            obstacle_x = st.number_input("障害物X座標", value=6, step=1)
            obstacle_y = st.number_input("障害物Y座標", value=6, step=1)

            context = {
                'robot_id': robot_id,
                'position': (pos_x, pos_y),
                'goal': (goal_x, goal_y),
                'obstacle': (obstacle_x, obstacle_y)
            }

        if st.button("テストを送信", key="trigger_submit"):
            with st.spinner(f"{event_type} イベントをトリガーレイヤーで処理中..."):
                try:
                    result = rag.trigger_layer(event_type, context)

                    # 結果表示
                    st.write("#### トリガーレイヤー結果")
                    st.write(f"**アクション:** {result['action']}")
                    st.write(f"**コンテキスト使用:** {result['context_used']}")
                    st.write(f"**取得ドキュメント数:** {len(result['context_docs'])}")

                    if result['context_docs']:
                        with st.expander("取得されたドキュメント"):
                            for i, doc in enumerate(result['context_docs'], 1):
                                st.write(f"ドキュメント {i}:")
                                st.write(doc)
                                st.write("---")

                    st.write("#### LLMの生レスポンス:")
                    st.info(result['raw_response'])

                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")

    # 意思決定インターフェーステストタブ
    with test_tabs[3]:
        st.subheader("意思決定インターフェーステスト")
        situation_type = st.selectbox(
            "シチュエーションタイプを選択してください:",
            ["plan", "obstacle"],
            format_func=lambda x: "経路計画" if x == "plan" else "障害物処理"
        )

        if situation_type == "plan":
            robot_id = st.number_input("ロボットID", value=1, min_value=1, step=1, key="decision_robot_id")
            start_x = st.number_input("スタートX座標", value=0, step=1, key="decision_start_x")
            start_y = st.number_input("スタートY座標", value=0, step=1, key="decision_start_y")
            goal_x = st.number_input("ゴールX座標", value=10, step=1, key="decision_goal_x")
            goal_y = st.number_input("ゴールY座標", value=10, step=1, key="decision_goal_y")

            kwargs = {
                'robot_id': robot_id,
                'start': (start_x, start_y),
                'goal': (goal_x, goal_y)
            }
        else:  # obstacle
            robot_id = st.number_input("ロボットID", value=1, min_value=1, step=1, key="decision_robot_id")
            pos_x = st.number_input("現在X座標", value=5, step=1, key="decision_pos_x")
            pos_y = st.number_input("現在Y座標", value=5, step=1, key="decision_pos_y")
            goal_x = st.number_input("ゴールX座標", value=10, step=1, key="decision_goal_x")
            goal_y = st.number_input("ゴールY座標", value=10, step=1, key="decision_goal_y")
            obstacle_x = st.number_input("障害物X座標", value=6, step=1, key="decision_obs_x")
            obstacle_y = st.number_input("障害物Y座標", value=6, step=1, key="decision_obs_y")

            kwargs = {
                'robot_id': robot_id,
                'position': (pos_x, pos_y),
                'goal': (goal_x, goal_y),
                'context': (obstacle_x, obstacle_y)
            }

        if st.button("テストを送信", key="decision_submit"):
            with st.spinner(f"意思決定インターフェースをテスト中、シチュエーション: {situation_type}..."):
                try:
                    action = rag.make_decision(situation_type, **kwargs)

                    # 結果表示
                    st.write("#### 意思決定結果")
                    st.success(action)

                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")
