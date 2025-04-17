# visualization — 机器人路径可视化工具

本子包基于 **matplotlib**，为 ragaid‑bot 提供“轨迹动画”与“中文字体配置”功能。  
核心文件：[`visualization/visualization.py`](./visualization.py)

---

## 1. 主要 API

| 函数 | 功能 | 关键参数 |
|------|------|----------|
| `configure_fonts(custom_font=None)` | 配置中文字体，跨平台解决乱码 | `custom_font` – 指定系统字体名；否则按操作系统自动选择（Win → Microsoft YaHei，macOS → PingFang SC，Linux → Noto Sans CJK SC） |
| `animate_robot_path(path_history, title="Robot Path", save_path=None, fps=2)` | 根据坐标序列生成动画，可选保存为 `.gif` / `.mp4` | `path_history` – `[(x, y), …]`；<br>`save_path` 决定是否保存及格式；<br>`fps` – 导出帧率 |

> ⚠️ 在 **无 GUI 环境**（Linux 服务器、CI）下会自动切换到 `Agg` 后端，不弹窗，只保存文件。

---

## 2. 安装依赖

```bash
pip install matplotlib pillow  # pillow 用于 GIF 写入
# 若需 .mp4 导出，请确保系统安装 ffmpeg
```

---

## 3. 基本用法

```python
from visualization import animate_robot_path

# 假设已有机器人运动轨迹
path = [(0, 0), (1, 0), (1, 1), (2, 1), (3, 1)]

# 仅弹窗播放
animate_robot_path(path, title="Demo Path", fps=4)

# 保存为 GIF（无 GUI 环境也能用）
animate_robot_path(
    path,
    title="Save Demo",
    save_path="outputs/demo.gif",
    fps=5,
)

# 保存为 MP4
animate_robot_path(
    path,
    save_path="outputs/demo.mp4",
    fps=6,
)
```

---

## 4. 效果示例

> 下面动图来自实际模拟输出（占位图，仅示例）。

![demo-gif](../docs/demo.gif)

---

## 5. 进阶

* **批量可视化**  
  ```python
  for i, hist in enumerate(all_histories, 1):
      animate_robot_path(hist, save_path=f"results/path_{i}.gif")
  ```
* **自定义字体**  
  在环境变量中指定：  
  ```bash
  export MATPLOTLIB_FONT="Microsoft YaHei"
  ```
  或在代码里：  
  ```python
  from visualization import configure_fonts
  configure_fonts("Source Han Sans CN")
  ```

---

## 6. 目录文件说明

| 文件 | 作用 |
|------|------|
| `visualization.py` | 主模块：动画函数、字体设置 |
| `__init__.py` | `configure_fonts` & `animate_robot_path` 快捷导出 |
| `README.md` | 当前说明文档 |

---
