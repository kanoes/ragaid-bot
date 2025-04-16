from modules.restaurant.layout import RestaurantLayout
from typing import Any, List, Tuple, Optional

class Restaurant:
    """
    餐厅类，用于创建餐厅对象，该对象包含餐厅的基本信息和自定义布局。

    使用方法：
      1. 外部先创建一个继承或实现了 RestaurantLayout 接口的布局对象。
      2. 将餐厅名称和该布局对象传入 Restaurant 的构造函数，从而实例化一个餐厅对象。
    """

    def __init__(self, name: str, layout: RestaurantLayout) -> None:
        """
        初始化餐厅对象

        参数：
          name (str): 餐厅名称。
          layout (RestaurantLayout): 由外部创建的餐厅布局实例，允许用户自由选择或配置不同布局。

        示例：
          >>> from modules.restaurant.some_layout import SomeRestaurantLayout
          >>> layout = SomeRestaurantLayout(config)
          >>> restaurant = Restaurant("我的餐厅", layout)
        """
        self.name = name
        self.layout = layout
        