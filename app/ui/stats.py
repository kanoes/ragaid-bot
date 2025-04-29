"""
统计数据可视化组件
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from .base import ENABLE_CACHING
from ..state import get_batch_histories


def render_stats(stats):
    """
    显示基本统计信息
    """
    st.subheader("今回のシミュレーションデータ")
    
    if stats:
        # 添加餐厅布局名
        if "配送履歴" in stats and stats["配送履歴"] and "レストランレイアウト" in stats["配送履歴"][0]:
            stats["レストランレイアウト"] = stats["配送履歴"][0]["レストランレイアウト"]
            
        # 使用更紧凑的布局
        col1, col2 = st.columns(2)
        
        # 左半部分
        with col1:
            if "total_orders" in stats:
                st.write(f"**総注文数:** {stats['total_orders']}")
            if "total_time" in stats:
                st.write(f"**総配達時間:** {stats['total_time']:.2f}")
            if "avg_waiting_time" in stats:
                st.write(f"**平均注文待ち時間:** {stats['avg_waiting_time']:.2f}")
                
        # 右半部分
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
    使用Plotly渲染统计数据图表
    """
    if not stats:
        return
        
    # 准备基本统计数据
    key_metrics = {
        "総注文数": stats.get("total_orders", 0),
        "総配達距離": stats.get("総配送路程", 0),
        "総配達時間": stats.get("total_time", 0),
        "平均注文待ち時間": stats.get("avg_waiting_time", 0)
    }
    
    # 创建柱状图
    fig = go.Figure()
    
    # 添加柱子
    fig.add_trace(
        go.Bar(
            x=list(key_metrics.keys()),
            y=list(key_metrics.values()),
            text=[format_value(k, v, key_metrics) for k, v in key_metrics.items()],
            textposition='auto',
            marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        )
    )
    
    # 设置布局
    fig.update_layout(
        title="コアパフォーマンス指標",
        xaxis_title="指標",
        yaxis_title="数値",
        height=400,
        margin=dict(l=40, r=40, t=40, b=40)
    )
    
    # 显示图表
    st.plotly_chart(fig, use_container_width=True)


def format_value(key, value, metrics):
    """
    格式化值显示
    """
    # 简单处理，不依赖metrics的格式化工具
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)


@st.cache_data(ttl=300, show_spinner=False, hash_funcs={object: lambda x: id(x)}) if ENABLE_CACHING else lambda f: f
def render_plotly_stats_extended(stats_data, custom_metrics=None):
    """
    渲染扩展统计数据的可视化，支持自定义指标

    参数:
    - stats_data: dict，统计数据字典
    - custom_metrics: dict，自定义指标设置，格式: {'指标名': {'color': 颜色, 'format': 格式化函数}}
    """
    if not stats_data:
        return
        
    # 获取累积的批次历史数据
    batch_histories = get_batch_histories()

    st.header("高级统计分析")

    # 默认指标设置
    default_metrics = {
        "total_orders": {"color": "#00cc66", "format": lambda x: int(x)},
        "total_batches": {"color": "#ff9900", "format": lambda x: int(x)},
        "総配送路程": {"color": "#4da6ff", "format": lambda x: int(x)},
        "平均每批次订单数": {"color": "#f5c518", "format": lambda x: f"{x:.2f}"},
        "平均每订单步数": {"color": "#2196f3", "format": lambda x: f"{x:.2f}"}
    }

    # 整合自定义指标
    metrics = default_metrics.copy()
    if custom_metrics:
        metrics.update(custom_metrics)

    # 准备数据
    data = []

    # 基本统计
    data.append(
        {
            "指標": "総注文数",
            "値": stats_data.get("total_orders", 0),
            "色": metrics.get("total_orders", {}).get("color", "#00cc66"),
        }
    )
    data.append(
        {
            "指標": "総批次数",
            "値": stats_data.get("total_batches", 0),
            "色": metrics.get("total_batches", {}).get("color", "#ff9900"),
        }
    )
    
    # 添加配送路程指标
    data.append(
        {
            "指標": "総配送路程",
            "値": stats_data.get("総配送路程", 0),
            "色": metrics.get("總配送路程", {}).get("color", "#4da6ff"),
        }
    )

    # 添加平均值指标
    for key in ["平均每批次订单数", "平均每订单步数", "平均每订单配送时间"]:
        if key in stats_data:
            metric_config = metrics.get(
                key, {"color": "#9467bd", "format": lambda x: f"{x:.2f}"}
            )
            data.append({"指標": key, "値": stats_data[key], "色": metric_config["color"]})

    # 添加其他统计指标
    for key, value in stats_data.items():
        if key not in ["total_orders", "total_batches", "総配送路程", "平均每批次订单数", "平均每订单步数", "平均每订单配送时间", "配送履歴"]:
            metric_config = metrics.get(
                key, {"color": "#9467bd", "format": lambda x: x}
            )
            data.append({"指標": key, "値": value, "色": metric_config["color"]})

    # 创建图表
    tabs = st.tabs(["配送性能", "レーダーチャート", "履歴バッチ分析"])

    with tabs[0]:
        # 柱状图
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
        # 雷达图
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
        if batch_histories:
            # 将历史数据转换为DataFrame进行分析
            history_df = pd.DataFrame(batch_histories)
            
            # 批次订单数分布
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
            
            # 批次配送路程分布
            if "path_length" in history_df.columns:
                st.subheader("バッチ配送路程分布")
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
                    title="各バッチ配送路程",
                    xaxis=dict(title="バッチ"),
                    yaxis=dict(title="配送路程"),
                    height=300,
                )
                st.plotly_chart(fig_path, use_container_width=True)
                
            # 批次配送时间分布
            if "duration" in history_df.columns:
                st.subheader("バッチ配送时间分布")
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
                    title="各バッチ配送时间(秒)",
                    xaxis=dict(title="バッチ"),
                    yaxis=dict(title="时间(秒)"),
                    height=300,
                )
                st.plotly_chart(fig_duration, use_container_width=True)
        elif "配送履歴" in stats_data and stats_data["配送履歴"]:
            # 将历史数据转换为DataFrame进行分析
            history_df = pd.DataFrame(stats_data["配送履歴"])
            
            # 批次订单数分布
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
            
            # 批次配送路程分布
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
                    title="各バッチ配送路程",
                    xaxis=dict(title="バッチ"),
                    yaxis=dict(title="配送距離"),
                    height=300,
                )
                st.plotly_chart(fig_path, use_container_width=True)
                
            # 批次配送时间分布
            if "duration" in history_df.columns:
                st.subheader("バッチ配送时间分布")
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
                    title="各バッチ配送时间(秒)",
                    xaxis=dict(title="バッチ"),
                    yaxis=dict(title="时间(秒)"),
                    height=300,
                )
                st.plotly_chart(fig_duration, use_container_width=True)
        else:
            st.info("バッチ履歴データなし")

    return data 