from importlib.metadata import PackageNotFoundError, version

# ---------------- バージョン ---------------- #
try:
    __version__: str = version("ragaid_bot")  # パッケージ化されている場合
except PackageNotFoundError:
    __version__ = "0.0.0.dev"                 # ローカル開発環境

# ---------------- 便利な re‑export -------- #
from .restaurant import Restaurant, RestaurantLayout          # noqa: E402
from .robot import AIEnhancedRobot, Robot                     # noqa: E402
from .robot.rag import RAGModule                              # noqa: E402

__all__ = [
    "__version__",
    "Restaurant",
    "RestaurantLayout",
    "Robot",
    "AIEnhancedRobot",
    "RAGModule",
]
