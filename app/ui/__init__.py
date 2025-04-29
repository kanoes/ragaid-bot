"""
UI组件模块
"""

from .base import setup_page
from .layout import (
    render_restaurant_layout,
    render_plotly_restaurant_layout,
    render_plotly_restaurant_layout_no_cache,
    render_plotly_robot_path
)
from .stats import (
    render_stats,
    render_plotly_stats
)
from .editors import render_layout_editor
from .rag_test import render_rag_test

__all__ = [
    "setup_page",
    "render_restaurant_layout",
    "render_plotly_restaurant_layout",
    "render_plotly_restaurant_layout_no_cache",
    "render_plotly_robot_path",
    "render_stats",
    "render_plotly_stats",
    "render_layout_editor",
    "render_rag_test"
]
