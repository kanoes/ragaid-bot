"""
Restaurant – 餐厅业务对象

该类只是一个“外观”层，持有 `RestaurantLayout` 实例并向外暴露简易接口
方便上层代码（Robot / Simulator / UI）调用，而不直接操作布局细节
"""

from restaurant.restaurant_layout import RestaurantLayout


class Restaurant:
    """
    餐厅对象，包含名称与布局。
    """

    def __init__(self, name: str, layout: RestaurantLayout) -> None:
        """
        Parameters
        ----------
        name : str
            餐厅名称
        layout : RestaurantLayout
            餐厅平面图对象，由外部先行创建后注入
        """
        self.name: str = name
        self.layout: RestaurantLayout = layout


    # --------------------------------------------------------------------- #
    # 魔术方法
    # --------------------------------------------------------------------- #
    def __repr__(self) -> str:  # pragma: no cover
        return f"<Restaurant {self.name!r} ({self.layout.width}×{self.layout.height})>"
