"""
定数定義
"""

import os
import logging

from rich.style import Style

# ---------- ログの設定 ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- 定数 ----------
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
LAYOUT_DIR = os.path.join(BASE_DIR, "restaurant")
RAG_KB_DIR = os.path.join(BASE_DIR, "robot", "rag", "knowledge")

# ---------- レストランレイアウトスタイル定数 ----------
EMPTY_STYLE = Style(bgcolor="black", color="white")
WALL_STYLE = Style(bgcolor="grey37", color="white")
TABLE_STYLE = Style(bgcolor="cyan", color="black", bold=True)
KITCHEN_STYLE = Style(bgcolor="yellow", color="black", bold=True)
PARKING_STYLE = Style(bgcolor="green", color="black", bold=True)
ERROR_STYLE = Style(bgcolor="red", color="white", bold=True)
