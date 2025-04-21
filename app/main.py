"""
Streamlit Web App 主页面逻辑
"""
from .constants import logger
from .utils import available_layouts
from .ui import setup_page, render_sidebar, render_restaurant_layout, render_stats
from .handlers import handle_layout_selection, handle_simulation
from .state import init_session_state, get_restaurant, set_restaurant, get_stats, set_stats

def run():
    """
    运行Streamlit应用
    """
    # 配置页面
    setup_page()
    
    # 初始化会话状态
    init_session_state()
    
    # 获取可用布局
    layouts = available_layouts()
    
    # 获取当前餐厅或加载新餐厅
    restaurant = get_restaurant()
    if restaurant is None and layouts:
        restaurant = handle_layout_selection(layouts[0])
        set_restaurant(restaurant)
        
    # 渲染侧边栏
    selected, use_ai, num_orders, sim_button = render_sidebar(layouts, restaurant)
    
    # 处理布局切换
    if selected and (restaurant is None or selected != restaurant.name):
        restaurant = handle_layout_selection(selected)
        set_restaurant(restaurant)
        logger.info(f"加载餐厅布局: {selected}")
    
    # 渲染餐厅布局
    if restaurant:
        render_restaurant_layout(restaurant)
    
    # 处理模拟按钮点击
    if sim_button and restaurant:
        stats = handle_simulation(restaurant, use_ai, num_orders)
        set_stats(stats)
    
    # 显示统计结果
    stats = get_stats()
    if stats:
        render_stats(stats) 