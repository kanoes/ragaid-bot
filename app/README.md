# app 模块说明

`app/` 目录包含 Streamlit 前端应用的代码，负责用户界面展示、状态管理和交互逻辑。

## 目录结构

```text
app/
├─ constants.py     # 全局常量定义
├─ handlers.py      # UI 事件处理函数
├─ main.py          # 应用入口与页面渲染
├─ simulation.py    # 模拟引擎核心逻辑
├─ state.py         # 会话状态管理封装
├─ ui.py            # 可复用 UI 组件
└─ utils.py         # 辅助工具函数
```

## 核心文件说明

- **constants.py**：定义布局路径、颜色、参数名称等全局常量
- **handlers.py**：处理按钮点击、参数变更等 UI 事件，与模拟引擎交互并更新状态
- **main.py**：Streamlit 应用入口，负责页面结构、Tab 切换和整体流程控制
- **simulation.py**：实现订单生成、路径规划、机器人调度等模拟流程，输出可视化数据
- **state.py**：基于 `st.session_state` 封装状态读写，保证组件间数据一致性
- **ui.py**：自定义表单、按钮、图表等组件，以及页面布局管理
- **utils.py**：通用函数，如参数校验、数据格式转换等

## 改进建议

- 暂无
