# MyPostMan - API 测试工具

一个基于 Flet 框架开发的跨平台 API 测试工具，支持桌面、Web、Android、iOS 等多平台部署。

## 功能特性

### 核心功能
- **HTTP 请求支持**: GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS
- **请求参数管理**: Headers、Query Params、Body（JSON/Text/Form）
- **响应展示**: 状态码、响应头、响应体（JSON/HTML/XML 格式化）
- **历史记录**: 自动保存请求历史，支持快速回放
- **环境管理**: 支持多套环境配置，快速切换
- **全局变量**: 跨环境共享的全局变量管理
- **请求列表**: 常用请求 URL 管理，支持快速加载
- **变量解析**: 支持 `{{variable_name}}` 格式的变量引用
- **URL 自动解析**: 自动识别 URL 中的查询参数并填充到 Params

### 技术特点
- **跨平台**: 基于 Flet 框架，支持多平台部署
- **数据持久化**: 使用 SQLite 数据库存储所有配置和历史记录
- **异步请求**: 使用线程避免阻塞 UI
- **现代化 UI**: 清晰的界面布局，直观的操作流程
- **模块化架构**: 清晰的项目结构，易于维护和扩展

## 项目结构

```
MyPostMan/
├── src/                          # 源代码目录
│   ├── models/                   # 数据模型和数据库模块
│   │   ├── __init__.py
│   │   ├── models.py             # 数据模型定义
│   │   └── database.py           # 数据库配置和模型
│   ├── managers/                 # 业务逻辑管理器
│   │   ├── __init__.py
│   │   ├── environment_manager.py    # 环境管理器
│   │   ├── global_variable_manager.py # 全局变量管理器
│   │   ├── history_manager.py        # 历史记录管理器
│   │   └── request_list_manager.py   # 请求列表管理器
│   ├── ui/                       # 用户界面模块
│   │   ├── __init__.py
│   │   ├── main_ui.py            # 主界面 UI 构建
│   │   └── ui_components.py      # 可复用 UI 组件
│   ├── services/                 # 服务层模块
│   │   ├── __init__.py
│   │   └── services.py           # HTTP 请求服务
│   ├── assets/                   # 静态资源文件
│   └── main.py                   # 应用入口
├── test/                         # 测试文件目录
│   ├── __init__.py
│   ├── README.md                 # 测试说明文档
│   ├── test_request_list_db.py   # 请求列表数据库测试
│   └── test_variable_resolution.py # 变量解析测试
├── .venv/                        # 虚拟环境
├── mypostman.db                  # SQLite 数据库文件
├── pyproject.toml                # 项目配置
├── README.md                     # 项目说明文档
└── RULES.md                      # 项目开发规范
```

## 模块说明

### 数据模型层 (`models/`)

#### 数据模型 (`models.py`)
- `HttpMethod`: HTTP 请求方法枚举
- `HttpRequest`: HTTP 请求数据模型
- `HttpResponse`: HTTP 响应数据模型
- `HistoryItem`: 历史记录项
- `Environment`: 环境配置数据模型
- `GlobalVariables`: 全局变量数据模型

#### 数据库 (`database.py`)
- `DatabaseManager`: 数据库管理器，负责连接和会话管理
- `EnvironmentModel`: 环境配置数据库模型
- `EnvironmentVariableModel`: 环境变量数据库模型
- `GlobalVariableModel`: 全局变量数据库模型
- `HistoryModel`: 历史记录数据库模型
- `RequestListModel`: 请求列表数据库模型

### 管理器层 (`managers/`)
- `EnvironmentManager`: 环境管理器，管理多套环境配置
- `GlobalVariableManager`: 全局变量管理器，管理跨环境变量
- `HistoryManager`: 历史记录管理器，管理请求历史
- `RequestListManager`: 请求列表管理器，管理常用请求 URL

### 服务层 (`services/`)
- `HttpService`: HTTP 请求服务，处理实际的 HTTP 请求

### UI 层 (`ui/`)
- `ApiTestPage`: 主界面，包含所有 UI 元素和交互逻辑
- `DynamicKeyValueList`: 动态键值对列表组件
- `ResponsePanel`: 响应展示面板组件
- `BodyEditor`: Body 编辑器组件
- `RequestRunner`: 请求运行器组件
- `KeyValueRow`: 键值对输入行组件

## 安装和运行

### 环境要求
- Python >= 3.10

### 安装依赖
```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
.venv\Scripts\python.exe -m pip install -e .
```

### 运行应用
```bash
# 桌面应用
.venv\Scripts\python.exe src\main.py

# 或使用 uv
uv run flet run

# Web 应用
uv run flet run --web
```

## 构建应用

### Windows
```bash
flet build windows -v
```

### Web
```bash
flet build web -v
```

### Android
```bash
flet build apk -v
```

### macOS
```bash
flet build macos -v
```

### iOS
```bash
flet build ipa -v
```

### Linux
```bash
flet build linux -v
```

## 使用指南

### 发送 HTTP 请求
1. 选择请求方法（GET/POST/PUT/DELETE 等）
2. 输入请求 URL（如包含查询参数，会自动解析到 Params）
3. 在 Tabs 中配置 Headers、Params 或 Body
4. 点击"发送"按钮
5. 在底部查看响应结果

### 环境管理
1. 在侧边栏选择环境或点击"管理环境"
2. 点击"添加环境"创建新环境
3. 为环境配置变量（如 `base_url`, `token` 等）
4. 切换环境后，请求中使用的 `{{变量名}}` 会自动解析

### 全局变量管理
1. 点击侧边栏的"全局变量"按钮
2. 添加跨环境共享的变量
3. 全局变量在所有环境中都可用
4. 环境变量优先级高于全局变量

### 请求列表管理
1. 在侧边栏"请求列表"区域查看常用请求
2. 点击"+"按钮添加当前请求到列表
3. 点击"粘贴"按钮从剪贴板批量导入 URL
4. 点击列表项快速加载请求配置

### 变量使用
在 URL、Headers、Params、Body 中使用 `{{变量名}}` 格式：
- URL: `{{base_url}}/api/users`
- Header: `Authorization: Bearer {{token}}`
- Body: `{"user": "{{username}}"}`

### URL 自动解析
- 在 URL 输入框中输入包含查询参数的 URL 时，系统会自动解析参数并填充到 Params 标签页
- 例如：输入 `/api/users?page=1&size=10` 会自动在 Params 中添加 `page: 1` 和 `size: 10`

### 历史记录
- 所有请求自动保存在侧边栏
- 点击历史记录可快速回放
- 支持清空历史记录

## 依赖说明

- `flet>=0.84.0`: UI 框架
- `requests>=2.31.0`: HTTP 请求库
- `sqlalchemy>=2.0.0`: ORM 数据库操作
- `pyyaml>=6.0`: YAML 解析支持

## 数据存储

所有数据存储在 SQLite 数据库文件 `mypostman.db` 中：
- **环境配置**: `environments` 表
- **环境变量**: `environment_variables` 表
- **全局变量**: `global_variables` 表
- **历史记录**: `history` 表
- **请求列表**: `request_list` 表

## 架构设计

### 分层架构
```
┌─────────────────────────────────────┐
│         UI Layer (ui/)              │  ← 用户界面层
├─────────────────────────────────────┤
│      Manager Layer (managers/)      │  ← 业务逻辑层
├─────────────────────────────────────┤
│      Service Layer (services/)      │  ← 服务层
├─────────────────────────────────────┤
│       Model Layer (models/)         │  ← 数据模型层
└─────────────────────────────────────┘
```

### 设计原则
- **单一职责**: 每个模块只负责一个功能
- **依赖倒置**: 高层模块不依赖低层模块，都依赖抽象
- **接口隔离**: 每个模块都有清晰的接口定义
- **开闭原则**: 对扩展开放，对修改关闭

## 开发规范

项目开发规范详见 [RULES.md](RULES.md)

## 许可证

MIT License
