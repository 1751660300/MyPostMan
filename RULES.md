# MyPostMan 项目执行规范

## 一、项目目标

### 1.1 项目概述
MyPostMan 是一个基于 Flet 框架开发的跨平台应用程序，支持桌面、Web、Android、iOS 等多平台部署。

### 1.2 技术栈
- **编程语言**: Python >= 3.10
- **UI 框架**: Flet >= 0.84.0
- **包管理**: uv
- **开发工具**: flet-cli, flet-desktop, flet-web

### 1.3 项目结构
```
MyPostMan/
├── src/                    # 源代码目录
│   ├── assets/             # 静态资源文件
│   └── main.py             # 应用入口
├── .venv/                  # 虚拟环境
├── pyproject.toml          # 项目配置
├── main.py                 # 根目录入口（示例）
└── RULES.md                # 项目规范（本文件）
```

---

## 二、Flet API 规范

### 2.1 应用入口
```python
import flet as ft

def main(page: ft.Page):
    # 应用逻辑
    pass

ft.run(main)
```

### 2.2 页面配置
- 使用 `page.title` 设置页面标题
- 使用 `page.theme_mode` 设置主题模式（`ft.ThemeMode.LIGHT` / `ft.ThemeMode.DARK`）
- 使用 `page.window_width` / `page.window_height` 设置窗口尺寸

### 2.3 控件使用规范
- 所有控件应使用 `ft.` 前缀明确命名
- 事件处理函数应使用语义化命名，如 `on_click_handler`
- 使用 `ft.Container` 进行布局包装，保持结构清晰
- **按钮控件**: `ft.TextButton`、`ft.Button` 等按钮控件直接使用位置参数传递文本，不使用 `text=` 或 `label=` 参数
  ```python
  # 正确写法
  ft.TextButton("清空历史", icon=ft.Icons.DELETE_SWEEP, on_click=handler)
  ft.Button("发送", icon=ft.Icons.SEND, on_click=handler)
  
  # 错误写法
  ft.TextButton(text="清空历史")  # ❌
  ft.TextButton(label="清空历史")  # ❌
  ft.Button("发送")  # ❌ 已废弃，使用 ft.Button 代替
  ```
- **Dropdown 控件**: 使用 `on_text_change` 属性监控值变化（不是 `on_change`）
  ```python
  # 正确写法
  ft.Dropdown(
      options=[ft.dropdown.Option("A"), ft.dropdown.Option("B")],
      value="A",
      on_text_change=handler,
  )
  
  # 错误写法
  ft.Dropdown(..., on_change=handler)  # ❌ 使用 on_text_change
  ```
- **Tab 控件**: 使用 `ft.Tabs` + `ft.TabBar` + `ft.TabBarView` 的标准结构。`ft.Tab` 的初始化参数为 `label`、`icon`、`height`、`icon_margin`。`ft.TabBar` 用于定义 Tab 标签栏，`ft.TabBarView` 用于定义每个 Tab 的内容视图
  ```python
  # 正确写法 - 使用 TabBar + TabBarView 的标准结构
  ft.Tabs(
      length=4,
      selected_index=0,
      expand=True,
      content=ft.Column(
          expand=True,
          controls=[
              ft.TabBar(
                  tab_alignment=ft.TabAlignment.START,
                  tabs=[
                      ft.Tab(label=ft.Text("Params")),
                      ft.Tab(label=ft.Text("Headers")),
                      ft.Tab(label=ft.Text("Body")),
                      ft.Tab(label=ft.Text("Runner")),
                  ],
              ),
              ft.TabBarView(
                  expand=True,
                  controls=[
                      self.params_list,
                      self.headers_list,
                      self.body_editor,
                      self.request_runner,
                  ],
              ),
          ],
      ),
  )

  # 错误写法
  ft.Tab("Headers")  # ❌ label 应使用 ft.Text() 包装
  ft.Tabs(tabs=[tab1, tab2])  # ❌ 没有tabs参数，应使用content包含TabBar和TabBarView
  ft.Tabs(content=ft.Row([tab1, tab2]))  # ❌ 缺少TabBar和TabBarView结构
  ```

### 2.4 SnackBar 使用
- `ft.Page` 没有 `show_snack_bar` 方法
- 正确用法：将 `SnackBar` 添加到 `page.overlay`，然后设置 `open = True`
  ```python
  # 正确写法
  snack_bar = ft.SnackBar(content=ft.Text("提示信息"), duration=2000)
  self.page.overlay.append(snack_bar)
  snack_bar.open = True
  self.page.update()

  # 错误写法
  self.page.show_snack_bar(snack_bar)  # ❌ 方法不存在
  ```

### 2.5 状态管理
- 使用控件的 `data` 属性存储简单状态
- 复杂状态应使用类或全局变量管理
- 状态变更后必须更新控件 `value` 并调用 `page.update()`

### 2.6 对话框使用规范
- 显示对话框使用 `page.show_dialog(dialog)` 方法
- 关闭对话框使用 `page.pop_dialog()` 方法
- 不要使用 `dialog.open = True` 和 `page.update()` 的方式
  ```python
  # 正确写法 - 显示对话框
  dialog = ft.AlertDialog(title=ft.Text("标题"), content=ft.Text("内容"))
  self.page.dialog = dialog
  self.page.show_dialog(dialog)

  # 正确写法 - 关闭对话框
  def _close_dialog(self):
      self.page.pop_dialog()

  # 错误写法
  dialog.open = True  # ❌ 对话框可能无法正确显示
  self.page.update()
  ```

### 2.7 控件更新注意事项
- 控件在被添加到页面之前不能调用 `update()` 方法
- 在 `__init__` 中构建UI时，如果控件还未添加到页面，不要调用 `update()`
- 可以在控件添加到页面后的后续操作中再调用 `update()`
  ```python
  # 错误写法 - 控件未添加到页面就调用 update()
  def _build_sidebar(self):
      self.my_dropdown = ft.Dropdown(...)
      self.my_dropdown.update()  # ❌ RuntimeError: Control must be added to the page first
      return ft.Container(...)

  # 正确写法 - 先不更新，等添加到页面后再更新
  def _build_sidebar(self):
      self.my_dropdown = ft.Dropdown(...)
      # 不调用 update()
      return ft.Container(...)

  def _on_some_event(self, e):
      self.my_dropdown.value = "new_value"
      self.my_dropdown.update()  # ✅ 此时控件已添加到页面
  ```

### 2.8 闭包变量捕获规范
- 在嵌套函数中使用外部变量时，应直接使用变量名，不要创建中间引用
- 特别是在事件处理函数中删除列表项时，应使用闭包正确捕获容器对象
  ```python
  # 正确写法 - 使用闭包捕获 row_container
  def add_variable_row():
      row_container = ft.Row(controls=[...])

      def remove_row(e):
          if row_container in parent.controls:
              parent.controls.remove(row_container)
              parent.update()

      remove_btn.on_click = remove_row
      return row_container

  # 错误写法 - 使用未定义的中间变量
  def add_variable_row():
      row = ft.Row(controls=[...])

      def remove_row(e):
          if remove_row_ref in parent.controls:  # ❌ remove_row_ref 未定义
              parent.controls.remove(remove_row_ref)
              parent.update()

      remove_btn.on_click = remove_row
      remove_row_ref = row  # ❌ 赋值在函数定义之后，无法捕获
      return row
  ```

### 2.9 Alignment 使用规范
- `ft.Alignment` 是大写开头的类，不是小写 `ft.alignment`
- 正确写法使用 `ft.Alignment.CENTER_RIGHT`、`ft.Alignment.CENTER_LEFT` 等
- 错误写法 `ft.alignment.center_left` 会导致 AttributeError
  ```python
  # 正确写法
  ft.Container(
      content=widget,
      alignment=ft.Alignment.CENTER_RIGHT,
  )

  # 错误写法
  ft.Container(
      content=widget,
      alignment=ft.alignment.center_left,  # ❌ AttributeError
  )
  ```

### 2.10 布局规范
- 使用 `ft.SafeArea` 确保安全区域适配
- 使用 `ft.Row` / `ft.Column` 进行行列布局
- 使用 `ft.Expand` 控制弹性空间分配

---

## 三、Python 代码规范

### 3.1 命名规范
- **模块/文件**: 小写下划线分隔，如 `user_manager.py`
- **类**: 大驼峰命名，如 `UserController`
- **函数/变量**: 小写下划线分隔，如 `get_user_info()`
- **常量**: 全大写下划线分隔，如 `MAX_RETRIES = 3`

### 3.2 代码格式
- 使用 4 个空格缩进
- 每行代码不超过 120 字符
- 函数/类定义间空 2 行
- 逻辑代码段间空 1 行

### 3.3 类型注解
```python
def calculate_total(items: list[dict], tax_rate: float) -> float:
    """计算总金额"""
    subtotal = sum(item["price"] for item in items)
    return subtotal * (1 + tax_rate)
```

### 3.4 文档字符串
- 所有模块、类、公共函数应包含文档字符串
- 使用三引号，首行简述功能，后续补充细节

### 3.5 异常处理
```python
try:
    result = risky_operation()
except SpecificError as e:
    log_error(e)
    handle_gracefully()
```

---

## 四、开发工作流

### 4.1 运行应用
```bash
# 桌面应用
.venv\Scripts\python.exe src\main.py

# 或使用虚拟环境激活后运行
.venv\Scripts\activate
python src\main.py
```

### 4.2 构建应用
```bash
# Windows
flet build windows -v

# Web
flet build web -v

# Android
flet build apk -v
```

### 4.3 依赖管理
- 所有依赖声明在 `pyproject.toml` 的 `dependencies` 中
- 开发依赖放在 `[dependency-groups]` 中
- 使用虚拟环境安装依赖：`.venv\Scripts\python.exe -m pip install <package>`

### 4.4 命令注意事项
- Windows 环境下 `uv` 命令可能不可用，使用 `pip` 替代
- 虚拟环境路径使用绝对路径：`.venv\Scripts\python.exe`

---

## 五、版本控制规范

- 暂时不涉及

---

## 六、测试规范

### 6.1 测试文件位置
- 测试文件放在 `tests/` 目录
- 命名格式: `test_<模块名>.py`

### 6.2 测试要求
- 核心功能必须编写单元测试
- 使用 `pytest` 框架
- 测试覆盖率目标: >= 80%

---

## 七、安全规范

- 不在代码中硬编码敏感信息
- 使用环境变量或配置文件管理密钥
- 定期更新依赖版本修复安全漏洞

---

## 八、代码审查

- 所有代码合并前需经过审查
- 检查项: 代码质量、安全性、性能、可维护性
- 使用 `/review` 命令触发代码审查

---

## 九、文档更新准则

- 解决所有bug都需要在本文档记录为开发规范

## 十、项目功能模块

### 10.1 已实现功能

#### MyPostMan API 测试工具
- **HTTP 请求支持**: GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS
- **请求参数管理**: Headers、Query Params、Body（JSON/Text/Form）
- **响应展示**: 状态码、响应头、响应体（JSON 格式化）
- **历史记录**: 自动保存请求历史，支持快速回放

### 10.2 模块结构
```
src/
├── main.py              # 应用入口
├── main_ui.py           # 主界面 UI 构建
├── models.py            # 数据模型（HttpRequest/HttpResponse/HistoryItem）
├── services.py          # HTTP 请求服务
├── history_manager.py   # 历史记录管理
├── ui_components.py     # 可复用 UI 组件
└── assets/              # 静态资源
```

### 10.3 依赖说明
- `requests`: 用于发送 HTTP 请求
- `flet`: UI 框架
- `sqlalchemy`: ORM 数据库操作
- `threading`: Python 标准库，用于异步请求（避免阻塞 UI）

### 10.4 数据库使用规范
- 使用 SQLite 作为本地存储数据库
- 使用 SQLAlchemy ORM 进行数据库操作
- 数据库文件名为 `mypostman.db`
- 所有数据操作必须使用事务，确保数据一致性
- 数据库会话使用后必须关闭，使用 `try...finally` 模式
  ```python
  # 正确写法
  session = self.db.get_session()
  try:
      # 数据库操作
      session.query(Model).all()
      session.commit()
  except Exception:
      session.rollback()
      raise
  finally:
      session.close()
  ```

### 10.5 环境管理功能
- **环境配置**: 支持创建多套环境配置（如开发、测试、生产）
- **环境变量**: 每个环境可以定义独立的变量键值对
- **环境切换**: 通过侧边栏下拉框快速切换环境
- **数据持久化**: 环境配置保存到 SQLite 数据库

### 10.6 全局变量管理功能
- **全局变量**: 在所有环境中都可用的变量
- **变量管理**: 支持添加、编辑、删除全局变量
- **数据持久化**: 全局变量保存到 SQLite 数据库

### 10.7 历史记录功能
- **请求历史**: 自动保存请求历史记录
- **数据持久化**: 历史记录保存到 SQLite 数据库
- **容量限制**: 默认保留最近 100 条记录

### 10.8 变量解析规则
- **变量格式**: 使用 `{{variable_name}}` 格式引用变量
- **解析优先级**: 环境变量 > 全局变量（环境变量会覆盖同名全局变量）
- **应用范围**: URL、Headers、Params、Body 都支持变量解析
- **示例**:
  - URL: `{{base_url}}/api/users`
  - Header: `Authorization: Bearer {{token}}`
  - Body: `{"user": "{{username}}"}`

---


*本规范文档应随项目迭代持续更新*
