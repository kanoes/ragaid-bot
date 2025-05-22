"""
Restaurant – レストランビジネスオブジェクト

このクラスは単なる「ファサード」層で、`RestaurantLayout`インスタンスを保持し、
シンプルなインターフェースを外部に公開します。上位コード（Robot / Simulator / UI）が
レイアウトの詳細を直接操作せずに呼び出すことができます。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from restaurant.restaurant_layout import RestaurantLayout


@runtime_checkable
class IRestaurant(Protocol):
    """
    レストランインターフェース。
    すべてのレストラン実装が満たすべきインターフェースを定義。
    """
    
    @property
    def name(self) -> str:
        """レストラン名を取得"""
        ...
        
    @property
    def layout(self) -> RestaurantLayout:
        """レストランレイアウトを取得"""
        ...


class Restaurant(IRestaurant):
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
        self._name: str = name
        self._layout: RestaurantLayout = layout

    # --------------------------------------------------------------------- #
    # プロパティ
    # --------------------------------------------------------------------- #
    @property
    def name(self) -> str:
        """レストラン名を取得"""
        return self._name
        
    @property
    def layout(self) -> RestaurantLayout:
        """レストランレイアウトを取得"""
        return self._layout
        
    # --------------------------------------------------------------------- #
    # マジックメソッド
    # --------------------------------------------------------------------- #
    def __repr__(self) -> str:  # pragma: no cover
        return f"<Restaurant {self.name!r} ({self.layout.width}×{self.layout.height})>"
