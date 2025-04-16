# ragaid-bot
# ロボットによる配膳シミュレーションを使用し、基本ロボットとRAG強化型スマートロボットの配送効率を比較
# これは研究と教育目的のためのシンプルなシミュレーションプロジェクトです
from modules.robot import Robot, AIEnhancedRobot
from modules.restaurant import RestaurantEnvironment, create_restaurant_layout
from modules.utils import animate_robot_path
from modules.order import OrderManager, Order

__version__ = "1.0.0" 