"""
統計データの可視化コンポーネント
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from .base import ENABLE_CACHING
from ..state import get_batch_histories


def render_stats(stats):
    """
    基本統計情報を表示
    """
    st.subheader("今回のシミュレーションデータ")
    
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
    Plotlyを使用して統計データをグラフ化
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
    値の表示をフォーマット
    """
    # metricsに依存しない単純な処理
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)


@st.cache_data(ttl=300, show_spinner=False, hash_funcs={object: lambda x: id(x)}) if ENABLE_CACHING else lambda f: f
def render_plotly_stats_extended(stats_data, custom_metrics=None):
    """
    拡張統計データの可視化をレンダリングし、カスタム指標をサポート

    パラメータ:
    - stats_data: dict、統計データの辞書
    - custom_metrics: dict、カスタム指標設定、形式: {'指標名': {'color': 色, 'format': フォーマット関数}}
    """
    if not stats_data:
        return
        
    # 累積バッチ履歴データを取得
    batch_histories = get_batch_histories()

    st.header("高度統計分析")

    # デフォルト指標設定
    default_metrics = {
        "total_orders": {"color": "#00cc66", "format": lambda x: int(x)},
        "total_batches": {"color": "#ff9900", "format": lambda x: int(x)},
        "總配送路程": {"color": "#4da6ff", "format": lambda x: int(x)},
        "平均每批次订单数": {"color": "#f5c518", "format": lambda x: f"{x:.2f}"},
        "平均每订单步数": {"color": "#2196f3", "format": lambda x: f"{x:.2f}"}
    }

    # カスタム指標を統合
    metrics = default_metrics.copy()
    if custom_metrics:
        metrics.update(custom_metrics)

    # データを準備
    data = []

    # 基本統計
    data.append(
        {
            "指標": "総注文数",
            "値": stats_data.get("total_orders", 0),
            "色": metrics.get("total_orders", {}).get("color", "#00cc66"),
        }
    )
    data.append(
        {
            "指標": "総バッチ数",
            "値": stats_data.get("total_batches", 0),
            "色": metrics.get("total_batches", {}).get("color", "#ff9900"),
        }
    )
    
    # 配達距離指標を追加
    data.append(
        {
            "指標": "総配達距離",
            "値": stats_data.get("総配送路程", 0),
            "色": metrics.get("總配送路程", {}).get("color", "#4da6ff"),
        }
    )

    # 平均値指標を追加
    for key in ["バッチあたりの平均注文数", "注文あたりの平均ステップ数", "注文あたりの平均配達時間"]:
        if key in stats_data:
            metric_config = metrics.get(
                key, {"color": "#9467bd", "format": lambda x: f"{x:.2f}"}
            )
            data.append({"指標": key, "値": stats_data[key], "色": metric_config["color"]})

    # 他の統計指標を追加
    for key, value in stats_data.items():
        if key not in ["total_orders", "total_batches", "總配送路程", "バッチあたりの平均注文数", "注文あたりの平均ステップ数", "注文あたりの平均配達時間", "配送履歴"]:
            metric_config = metrics.get(
                key, {"color": "#9467bd", "format": lambda x: x}
            )
            data.append({"指標": key, "値": value, "色": metric_config["color"]})

    # チャートを作成
    tabs = st.tabs(["配送性能", "レーダーチャート", "履歴バッチ分析"])

    with tabs[0]:
        # 棒グラフ
        fig_bar = go.Figure()
        fig_bar.add_trace(
            go.Bar(
                x=[item["指標"] for item in data],
                y=[item["値"] for item in data],
                marker_color=[item["色"] for item in data],
                text=[format_value(item["指標"], item["値"], metrics) for item in data],
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
        # バッチ履歴分析
        if batch_histories:
            # 履歴データをDataFrameに変換して分析
            history_df = pd.DataFrame(batch_histories)
            
            # バッチ注文数分布
            if "orders_count" in history_df.columns:
                st.subheader("バッチ注文数分布")
                fig_batch = go.Figure()
                fig_batch.add_trace(
                    go.Bar(
                        x=[f"バッチ {i+1}" for i in range(len(history_df))],
                        y=history_df["orders_count"],
                        marker_color="#4da6ff",
                        text=history_df["orders_count"],
                        textposition="auto",
                    )
                )
                fig_batch.update_layout(
                    title="各バッチ注文数量",
                    xaxis=dict(title="バッチ"),
                    yaxis=dict(title="注文数量"),
                    height=300,
                )
                st.plotly_chart(fig_batch, use_container_width=True)
            
            # バッチ配送距離分布
            if "path_length" in history_df.columns:
                st.subheader("バッチ配送距離分布")
                fig_path = go.Figure()
                fig_path.add_trace(
                    go.Bar(
                        x=[f"バッチ {i+1}" for i in range(len(history_df))],
                        y=history_df["path_length"],
                        marker_color="#00cc66",
                        text=history_df["path_length"],
                        textposition="auto",
                    )
                )
                fig_path.update_layout(
                    title="各バッチ配送距離",
                    xaxis=dict(title="バッチ"),
                    yaxis=dict(title="配送距離"),
                    height=300,
                )
                st.plotly_chart(fig_path, use_container_width=True)
                
            # バッチ配送時間分布
            if "duration" in history_df.columns:
                st.subheader("バッチ配送時間分布")
                fig_duration = go.Figure()
                fig_duration.add_trace(
                    go.Bar(
                        x=[f"バッチ {i+1}" for i in range(len(history_df))],
                        y=history_df["duration"],
                        marker_color="#ff9900",
                        text=[f"{d:.2f}" for d in history_df["duration"]],
                        textposition="auto",
                    )
                )
                fig_duration.update_layout(
                    title="各バッチ配送時間(秒)",
                    xaxis=dict(title="バッチ"),
                    yaxis=dict(title="時間(秒)"),
                    height=300,
                )
                st.plotly_chart(fig_duration, use_container_width=True)
        elif "配送履歴" in stats_data and stats_data["配送履歴"]:
            # 履歴データをDataFrameに変換して分析
            history_df = pd.DataFrame(stats_data["配送履歴"])
            
            # バッチ注文数分布
            if "orders_count" in history_df.columns:
                st.subheader("バッチ注文数分布")
                fig_batch = go.Figure()
                fig_batch.add_trace(
                    go.Bar(
                        x=[f"バッチ {i+1}" for i in range(len(history_df))],
                        y=history_df["orders_count"],
                        marker_color="#4da6ff",
                        text=history_df["orders_count"],
                        textposition="auto",
                    )
                )
                fig_batch.update_layout(
                    title="各バッチ注文数量",
                    xaxis=dict(title="バッチ"),
                    yaxis=dict(title="注文量"),
                    height=300,
                )
                st.plotly_chart(fig_batch, use_container_width=True)
            
            # バッチ配送距離分布
            if "path_length" in history_df.columns:
                st.subheader("バッチ配送距離分布")
                fig_path = go.Figure()
                fig_path.add_trace(
                    go.Bar(
                        x=[f"バッチ {i+1}" for i in range(len(history_df))],
                        y=history_df["path_length"],
                        marker_color="#00cc66",
                        text=history_df["path_length"],
                        textposition="auto",
                    )
                )
                fig_path.update_layout(
                    title="各バッチ配送距離",
                    xaxis=dict(title="バッチ"),
                    yaxis=dict(title="配送距離"),
                    height=300,
                )
                st.plotly_chart(fig_path, use_container_width=True)
                
            # バッチ配送時間分布
            if "duration" in history_df.columns:
                st.subheader("バッチ配送時間分布")
                fig_duration = go.Figure()
                fig_duration.add_trace(
                    go.Bar(
                        x=[f"バッチ {i+1}" for i in range(len(history_df))],
                        y=history_df["duration"],
                        marker_color="#ff9900",
                        text=[f"{d:.2f}" for d in history_df["duration"]],
                        textposition="auto",
                    )
                )
                fig_duration.update_layout(
                    title="各バッチ配送時間(秒)",
                    xaxis=dict(title="バッチ"),
                    yaxis=dict(title="時間(秒)"),
                    height=300,
                )
                st.plotly_chart(fig_duration, use_container_width=True)
        else:
            st.info("バッチ履歴データなし")

    return data 