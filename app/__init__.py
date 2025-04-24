"""
餐厅送餐机器人模拟系统 - App 包
"""

def run():
    """
    启动Streamlit应用
    """
    from .main import run as main_run
    main_run()

__all__ = ["run"] 