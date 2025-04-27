"""
レストラン配達ロボットシミュレーションシステム - Appパッケージ
"""

def run():
    """
    Streamlitアプリケーションを起動
    """
    from .main import run as main_run
    main_run()

__all__ = ["run"]