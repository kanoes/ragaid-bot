# restaurant — 餐厅网格与布局解析

本子包提供 **2‑D 网格餐厅建模** 能力，是机器人寻路与配送的环境基础。

---

## 1. 文件一览

| 文件 | 功能 |
|------|------|
| **`restaurant_layout.py`** | `RestaurantLayout`：<br>• 解析 `layout_lines` ➜ 网格<br>• `is_free()` / `neighbors()` / `display()` |
| **`restaurant.py`** | `Restaurant`：包装 `RestaurantLayout` 并附带名称 |
| **`__init__.py`** | 快捷导出 `Restaurant`, `RestaurantLayout` |
| **`resources/my_restaurant/*.json`** | 预置布局示例 |

---

## 2. 快速使用

### 2.1 加载预置布局

```python
from pathlib import Path
from restaurant import Restaurant, RestaurantLayout

json_file = Path("resources/my_restaurant/default_restaurant.json")
data = json_file.read_text(encoding="utf-8")
layout_lines = json.loads(data)["layout"]

cfg = RestaurantLayout.parse_layout_from_strings("default", layout_lines)
rest = Restaurant("默认餐厅", RestaurantLayout(**cfg))
rest.display()          # ASCII 可视化
```

### 2.2 纯文本行直接创建

```python
layout_lines = [
    "＃ ＃ ＃ ＃",
    "＃ * A *",
    "＃ * 台 *",
    "＃ * * 停",
    "＃ ＃ ＃ ＃",
]

cfg = RestaurantLayout.parse_layout_from_strings("demo", layout_lines)
rest = Restaurant("Demo", RestaurantLayout(**cfg))
rest.display()
```

---

## 3. JSON 布局规范

```jsonc
{
  "name": "small_cafe",
  "layout": [
    "＃ ＃ ＃ ＃ ＃",
    "＃ * A * ＃",
    "＃ * 台 * ＃",
    "＃ * 停 * ＃",
    "＃ ＃ ＃ ＃ ＃"
  ]
}
```

| 符号 | 含义 | 数值 |
|------|------|------|
| `＃` 或 `W` | 墙壁 / 障碍 | 1 |
| `*` 或 `.`  | 空地 | 0 |
| `A‑Z` | 桌子编号 | 2 |
| `台` | 厨房 | 3 |
| `停` 或 `P` | 机器人停靠点 | 4 |

> **空格分隔**：解析器按空格分词，便于视觉对齐；若无空格，也能正常读取。

---

## 4. 常用 API

```python
layout = rest.layout

layout.is_free((x, y))          # 位置是否可通行
layout.neighbors((x, y))        # 上下左右四邻
layout.tables                   # {'A': (2,1), ...}
layout.kitchen                  # [(4,3), ...]
layout.parking                  # (6,2)
layout.display()                # ASCII 网格
```

---

## 5. 设计工具（CLI）

> ⚠ 旧版 `restaurant_designer.py` 已迁出；新的交互式设计器将整合进独立脚本 *todo*。

---

## 6. 扩展方向

| 目标 | 建议实现 |
|------|----------|
| 不规则多边形 / 多层餐厅 | 把网格改为 `networkx` 图；`RestaurantLayout` 负责网格→图转换 |
| 动态障碍 | 在仿真循环中修改 `layout.grid[x][y]` 并实时刷新 |
| 导出 SVG / HTML | 在 `display()` 新增 `to_svg()` 使用 `svgwrite` |
