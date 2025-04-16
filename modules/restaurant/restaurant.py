from modules.restaurant.restaurant_grid import RestaurantEnvironment

class Restaurant:
    """
    餐厅类，用于创建和管理不同布局的餐厅环境
    """
    def __init__(self, name, config=None):
        """
        初始化餐厅
        
        参数:
            name (str): 餐厅名称
            config (dict): 餐厅配置信息，包括以下键:
                - grid: 网格布局
                - table_positions: 桌子位置
                - kitchen_positions: 厨房位置
                - parking_position: 机器人停靠点位置（可选）
                - height: 高度（可选）
                - width: 宽度（可选）
        """
        self.name = name
        
        if config is None:
            # 默认使用空餐厅
            self.environment = RestaurantEnvironment()
        else:
            grid = config.get('grid')
            table_positions = config.get('table_positions', {})
            kitchen_positions = config.get('kitchen_positions', [])
            parking_position = config.get('parking_position')
            
            # 创建餐厅环境
            self.environment = RestaurantEnvironment(
                grid=grid,
                table_positions=table_positions,
                kitchen_positions=kitchen_positions,
                parking_position=parking_position
            )
    
    @classmethod
    def from_layout(cls, name, layout_module):
        """
        从布局模块创建餐厅
        
        参数:
            name (str): 餐厅名称
            layout_module: 布局模块，必须包含get_config()函数
            
        返回:
            Restaurant: 新创建的餐厅实例
        """
        config = layout_module.get_config()
        return cls(name, config)
    
    def display(self, path=None, robot_position=None):
        """显示餐厅布局"""
        print(f"===== 餐厅: {self.name} =====")
        self.environment.display(path, robot_position)
    
    def display_full(self, kitchen_position=None):
        """显示详细餐厅布局"""
        from modules.restaurant.restaurant_layout import display_full_restaurant
        print(f"===== 餐厅: {self.name} - 详细视图 =====")
        display_full_restaurant(self.environment, kitchen_position)
        
    def print_info(self):
        """打印餐厅信息"""
        from modules.restaurant.restaurant_layout import print_restaurant_info
        print(f"===== 餐厅: {self.name} - 信息 =====")
        print_restaurant_info(self.environment)
        
    @property
    def tables(self):
        """获取所有桌子位置"""
        return self.environment.tables
        
    @property
    def kitchen(self):
        """获取厨房位置"""
        return self.environment.kitchen
        
    @property
    def parking(self):
        """获取机器人停靠点位置"""
        return self.environment.parking
        
    @property
    def grid(self):
        """获取餐厅网格"""
        return self.environment.grid
        
    @property
    def height(self):
        """获取餐厅高度"""
        return self.environment.height
        
    @property
    def width(self):
        """获取餐厅宽度"""
        return self.environment.width 