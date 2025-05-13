"""
Restaurant – レストランビジネスオブジェクト

このクラスは単なる「ファサード」層で、`RestaurantLayout`インスタンスを保持し、
シンプルなインターフェースを外部に公開します。上位コード（Robot / Simulator / UI）が
レイアウトの詳細を直接操作せずに呼び出すことができます。
"""

from restaurant.restaurant_layout import RestaurantLayout


class Restaurant:
    """
    レストランオブジェクト。名前とレイアウトを含みます。
    """

    def __init__(self, name: str, layout: RestaurantLayout) -> None:
        """
        Parameters
        ----------
        name : str
            レストラン名
        layout : RestaurantLayout
            レストラン図面オブジェクト。外部で先に作成して注入
        """
        self.name: str = name
        self.layout: RestaurantLayout = layout

    # --------------------------------------------------------------------- #
    # マジックメソッド
    # --------------------------------------------------------------------- #
    def __repr__(self) -> str:  # pragma: no cover
        return f"<Restaurant {self.name!r} ({self.layout.width}×{self.layout.height})>"
