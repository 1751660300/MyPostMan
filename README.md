# MyPostMan - API 测试工具

一个类似 Apifox/Postman 的跨平台 API 测试工具，基于 Flet 框架开发。

## ✨ 特性

### 核心功能
- 🌐 **多平台支持**: 桌面、Web、Android、iOS
- 📝 **HTTP 请求**: GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS
- 🔧 **请求管理**: Headers、Query Params、Body（JSON/Text/Form）
- 📊 **响应展示**: 状态码、响应头、响应体（JSON 格式化）
- 🔖 **多Tab支持**: 同时打开多个请求，独立编辑

### 高级功能
- 📚 **历史记录**: 自动保存请求历史，支持分页和搜索
- 🌍 **环境管理**: 多套环境配置，快速切换
- 🔍 **搜索功能**: 历史记录和请求列表支持关键字搜索
- 🔄 **全局变量**: 跨环境共享的变量管理
- 🎬 **登录录制**: 自动捕获认证信息（Token/Cookie），支持重放验证

### 🆕 执行计划功能
- 📋 **执行计划**: 创建和管理多个请求的执行序列
- ⚙️ **步骤配置**: 
  - 参数映射（使用上一步结果、全局变量、环境变量）
  - 自定义方法（Python代码处理响应数据）
  - 超时和重试设置
- ▶️ **执行监控**: 实时显示执行进度和每步详细结果
- ⏰ **定时任务**: 支持 Cron 表达式、间隔执行、一次性执行
- 📈 **执行历史**: 查看每次执行的详细记录和统计信息

## 📁 项目结构

```
MyPostMan/
├── src/
│   ├── main.py                    # 应用入口
│   ├── ui/                        # 界面模块
│   │   ├── main_ui.py             # 主界面
│   │   ├── dialogs/               # 对话框组件
│   │   │   ├── step_editor_dialog.py      # 步骤编辑器
│   │   │   ├── schedule_config_dialog.py  # 定时配置
│   │   │   └── plan_detail_dialog.py      # 计划详情
│   │   ├── panels/                # 面板组件
│   │   │   ├── execution_plan_panel.py    # 执行计划列表
│   │   │   ├── execution_monitor_panel.py # 执行监控
│   │   │   ├── execution_history_panel.py # 执行历史
│   │   │   └── scheduled_tasks_panel.py   # 定时任务管理
│   │   └── components/            # 可复用组件
│   │       ├── body_editor.py     # Body编辑器
│   │       ├── key_value.py       # 键值对组件
│   │       ├── request_runner.py  # 请求运行器
│   │       └── response_panel.py  # 响应面板
│   ├── managers/                  # 管理器
│   │   ├── request_list_manager.py # 请求列表管理
│   │   ├── history_manager.py     # 历史记录管理
│   │   ├── environment_manager.py # 环境管理
│   │   ├── global_variable_manager.py # 全局变量管理
│   │   ├── execution_plan_manager.py  # 执行计划管理
│   │   └── scheduler_manager.py       # 调度器管理
│   ├── services/                  # 服务层
│   │   ├── services.py            # HTTP请求服务
│   │   ├── execution_engine.py    # 执行引擎
│   │   ├── script_sandbox.py      # 脚本沙箱
│   │   └── execution_context.py   # 执行上下文
│   └── models/                    # 数据模型
│       ├── models.py              # 数据模型定义
│       ├── database.py            # 数据库操作
│       └── execution_plan.py      # 执行计划模型
├── .venv/                         # 虚拟环境
├── pyproject.toml                 # 项目配置
└── README.md                      # 项目说明
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 使用 uv 安装（推荐）
uv sync

# 或使用 pip
pip install flet requests sqlalchemy pyyaml
```

### 2. 运行应用

```bash
# 桌面应用
.venv\Scripts\python.exe src\main.py

# 或激活虚拟环境后运行
.venv\Scripts\activate
python src\main.py
```

## 📖 使用说明

### 发送请求

1. 在 URL 输入框中输入请求地址
2. 选择请求方法（GET/POST/PUT/DELETE等）
3. 在 Params/Headers/Body Tab 中配置请求参数
4. 点击"发送"按钮

### 管理请求

- **添加到请求列表**: 点击请求列表的 ➕ 按钮
- **搜索请求**: 在请求列表搜索框中输入关键字
- **清空列表**: 点击请求列表标题旁的 🗑️ 按钮

### 历史记录

- 自动保存所有请求历史
- 支持分页浏览（每页20条）
- 支持搜索（URL、方法、状态码）
- 点击历史记录可快速打开请求

### 环境管理

- 创建多套环境配置（开发/测试/生产）
- 每个环境可定义独立变量
- 快速切换环境

### 全局变量

- 在所有环境中都可用的变量
- 支持添加、编辑、删除

### 登录录制 🎬

自动捕获登录过程中的认证信息，无需手动复制粘贴：

1. **点击侧边栏“登录录制”按钮**
2. **输入登录页面 URL**
3. **点击“开始录制”**
   - 系统会打开浏览器
   - 自动拦截网络请求
   - 捕获 Token/Cookie
4. **在浏览器中完成登录**
5. **查看捕获的数据**
   - 显示所有捕获的认证信息
   - 可点击“重放请求”验证有效性
6. **保存到环境或全局变量**
   - 选择保存位置
   - 输入变量名
   - 后续请求使用 `{{variable_name}}` 引用

#### 安装要求

**自动录制模式（推荐）**：
```bash
pip install playwright
playwright install chromium
```

**手动模式（备选）**：
- 无需额外安装
- 手动从浏览器开发者工具复制 Token/Cookie
- 详见 [LOGIN_RECORDER_SETUP.md](LOGIN_RECORDER_SETUP.md)

#### 功能特点

- ✅ 自动拦截 HTTP 请求和响应
- ✅ 智能识别 Token 和 Cookie
- ✅ 支持重放验证（确保捕获的数据有效）
- ✅ 一键保存到环境/全局变量
- ✅ 降级方案：Playwright 未安装时自动切换到手动模式

### 执行计划

#### 创建执行计划
1. 点击侧边栏“执行计划”
2. 点击“新建计划”按钮
3. 输入计划名称和描述
4. 选择执行模式（串行/并行）
5. 添加请求步骤

#### 配置步骤
每个步骤支持：
- **参数映射**：使用表格配置，支持三种来源
  - 前置步骤结果（只能选择当前步骤之前的步骤）
  - 全局变量
  - 环境变量（执行时动态读取当前环境）
- **自定义方法**：编写 Python 代码处理响应数据
  ```python
  def process(response):
      """处理响应"""
      if response['status_code'] == 200:
          data = json.loads(response['data'])
          return {
              'user_id': data['id'],
              'token': data['token']
          }
      return {'error': '请求失败'}
  ```
- **超时设置**：单个步骤的超时时间
- **重试次数**：失败时的自动重试次数

#### 执行监控
- 实时进度条显示
- 每步执行状态（等待/执行中/成功/失败）
- 点击步骤查看详细结果：
  - 请求信息（方法、URL、Headers）
  - 响应信息（状态码、耗时、响应体）
  - 自定义方法输出
  - 错误信息（如果有）

#### 定时任务
支持三种调度类型：
- **Cron 表达式**：`0 9 * * *` （每天9点执行）
- **间隔执行**：每隔 N 秒/分/时执行
- **一次性执行**：指定时间执行一次

在定时任务管理页面可以：
- 查看所有已配置的定时任务
- 启用/禁用定时任务
- 删除定时任务
- 查看下次执行时间

#### 执行历史
- 自动记录每次执行的结果
- 显示执行状态（完成/失败/停止）
- 统计信息：总步骤数、成功数、失败数、耗时
- 按时间倒序排列

## 🔧 开发

### 运行测试

```bash
pytest tests/
```

### 构建应用

```bash
# Windows
flet build windows -v

# Web
flet build web -v

# Android
flet build apk -v
```

## 📋 依赖

| 包 | 版本 | 说明 |
|---|------|------|
| flet | >=0.84.0 | UI框架 |
| requests | >=2.31.0 | HTTP请求 |
| sqlalchemy | >=2.0.0 | 数据库ORM |
| pyyaml | >=6.0 | YAML解析 |

## 📝 功能详情

### HTTP 请求支持

- ✅ GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS
- ✅ 自定义请求头
- ✅ 查询参数
- ✅ 请求体（JSON/Text/Form）
- ✅ SSL 证书验证控制

### 请求参数管理

- ✅ Headers 管理
- ✅ Query Params 管理
- ✅ Body 编辑（支持 JSON 格式化）
- ✅ 变量替换（`{{variable}}` 格式）

### 响应展示

- ✅ 状态码显示（带颜色标识）
- ✅ 响应时间
- ✅ 响应头查看
- ✅ 响应体（JSON 格式化）

### 历史记录

- ✅ 自动保存
- ✅ 分页浏览
- ✅ 关键字搜索
- ✅ 快速回放
- ✅ 数据持久化（SQLite）

### 多Tab支持

- ✅ 同时打开多个请求
- ✅ 独立编辑
- ✅ Tab重命名
- ✅ 保存/关闭Tab

### 执行计划

- ✅ 创建和管理执行计划
- ✅ 串行/并行执行模式
- ✅ 步骤间参数映射
  - 前置步骤结果引用
  - 全局变量引用
  - 环境变量动态读取
- ✅ 自定义方法处理响应
- ✅ 超时和重试配置
- ✅ 实时执行监控
- ✅ 步骤详情查看
- ✅ 定时任务调度
  - Cron 表达式
  - 间隔执行
  - 一次性执行
- ✅ 执行历史记录
- ✅ 执行统计信息

## 🐛 问题反馈

如有问题或建议，请提交 Issue。

## 📄 许可证

MIT License
