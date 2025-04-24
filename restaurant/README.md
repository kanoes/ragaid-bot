# restaurant — 餐厅网格与布局解析

`restaurant` 子包提供 2D 网格餐厅建模能力，是机器人寻路与配送的环境基础。

---

## 目录结构

```text
restaurant/
├─ restaurant_layout.py    # 解析布局、空闲检测、邻居查询、可视化等
├─ restaurant.py           # 包装布局并附带名称
├─ layouts.json            # 多个预置布局示例
├─ README.md               # 本说明文档
└─ __init__.py             # 包入口
```

---

## 布局格式说明

- 数字矩阵：`layouts.json` 中以整数表示，编码规则：
  - 0：空地
  - 1：墙壁/障碍
  - 2-99：桌子编号
  - 100：厨房
  - 200：停靠点

---

## 常用 API

```python
layout = rest.layout
layout.is_free((x, y))         # 是否可通行
layout.neighbors((x, y))       # 上下左右可通行邻居列表
layout.tables                  # 桌子位置字典，如 {'A': (1,2)}
layout.kitchen                 # 厨房坐标列表
layout.parking                 # 停靠点坐标
layout.display()               # ASCII 网格输出
```

## 改进建议

- 在 `restaurant_layout.py` 中加入对动态障碍以及更多种突发情况
