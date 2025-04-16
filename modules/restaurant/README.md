# 餐厅模拟系统

这个模块提供了一个灵活的餐厅模拟系统，用于测试不同送餐机器人在餐厅环境中的送餐效率。

## 主要功能

- 使用2D网格表示餐厅布局
- 支持自定义餐厅布局和大小
- 灵活的桌子和厨房位置配置
- 可视化显示餐厅布局
- 可扩展的模块化设计
- **新增**: 交互式餐厅设计工具
- **新增**: 简单的JSON格式定义餐厅布局
- **更新**: 使用字母和桌号直观表示餐厅元素

## 使用方法

### 1. 使用预定义布局

```python
from modules.restaurant import load_restaurant_layout

# 使用默认餐厅布局
restaurant = load_restaurant_layout('default_restaurant', '我的标准餐厅')
restaurant.display()

# 使用小型餐厅布局
small_restaurant = load_restaurant_layout('small_restaurant', '我的小型餐厅')
small_restaurant.display()

# 使用JSON定义的布局
cafe = load_restaurant_layout('small_cafe', '小咖啡馆')
cafe.display()
```

### 2. 创建自定义餐厅

```python
from modules.restaurant import create_custom_restaurant

# 创建一个5x5的简单餐厅网格
grid = [
    [1, 1, 1, 1, 1],
    [1, 0, 0, 0, 1],
    [1, 0, 1, 0, 1],
    [1, 0, 0, 0, 1],
    [1, 1, 1, 1, 1]
]
# 添加厨房和桌子
grid[1][1] = 3  # 厨房
grid[3][3] = 2  # 桌子

# 配置桌子和厨房位置
table_positions = {1: (3, 3)}
kitchen_positions = [(1, 1)]

# 创建自定义餐厅
custom_restaurant = create_custom_restaurant(
    "迷你餐厅", 
    grid, 
    table_positions, 
    kitchen_positions
)
custom_restaurant.display()
```

### 3. 使用交互式设计工具创建餐厅

最简单的方法是使用餐厅设计工具，通过直观的命令行界面设计餐厅：

```python
from modules.restaurant.restaurant_designer import design_restaurant

# 启动交互式设计工具
design_restaurant()
```

设计工具会引导您：
1. 设定餐厅大小
2. 使用简单的命令放置墙壁、桌子和厨房
3. 保存设计为JSON文件
4. 随时可查看帮助和统计信息

### 4. 直接创建JSON布局文件

您可以手动创建JSON文件定义餐厅布局。文件应放在`modules/restaurant/layouts/`目录下，命名为`your_layout_name.json`：

```json
{
  "grid": [
    [1, 1, 1, 1, 1],
    [1, 0, 0, 0, 1],
    [1, 0, 2, 0, 1],
    [1, 3, 0, 0, 1],
    [1, 1, 1, 1, 1]
  ],
  "table_positions": {
    "1": [2, 2]
  },
  "kitchen_positions": [
    [3, 1]
  ]
}
```

然后加载此布局：

```python
restaurant = load_restaurant_layout('your_layout_name')
```

## 网格表示

餐厅布局使用2D网格表示，显示时使用以下符号：
- `S`: 空地 (Space) - 机器人可通行区域
- `W`: 障碍物 (Wall) - 墙壁和其他障碍物
- `01`-`99`: 桌子 - 直接显示桌号
- `K`: 厨房 (Kitchen) - 食物准备区域

内部数值表示：
- `0`: 空地
- `1`: 障碍物
- `2`: 桌子
- `3`: 厨房

## 内置布局

系统提供了多个预定义的布局文件：

1. `default_restaurant.py` - 标准餐厅布局，20个桌子
2. `small_restaurant.py` - 小型餐厅布局，10个桌子
3. `small_cafe.json` - 小型咖啡馆布局，9个桌子
4. `fancy_restaurant.json` - 高档餐厅布局，8个桌子

## 设计工具命令

餐厅设计工具提供以下命令：

- 移动: `w`(上), `s`(下), `a`(左), `d`(右)
- 放置: 
  - `0` 或 `s` - 放置空地(S)
  - `1` 或 `w` - 放置障碍物(W)
  - `2` 或 `t` - 放置桌子(显示为桌号)
  - `3` 或 `k` - 放置厨房(K)
- 其他: 
  - `r` - 重置当前位置
  - `q` - 退出
  - `h` - 显示帮助
  - `save` - 保存餐厅布局
  - `clean` - 清除所有桌子和厨房
  - `show` - 显示统计信息

## 示例

可以在 `examples/restaurant_demo.py` 中查看完整示例代码。 