from importlib.metadata import PackageNotFoundError, version

# ---------------- 版本 ---------------- #
try:
    __version__: str = version("ragaid_bot")  # 如果已打包发布
except PackageNotFoundError:
    __version__ = "0.0.0.dev"                 # 本地开发环境

# ---------------- 便捷 re‑export -------- #
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
