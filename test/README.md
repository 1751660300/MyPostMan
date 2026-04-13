# 测试目录

本目录包含项目的测试文件。

## 测试文件说明

- `test_request_list_db.py`: 测试请求列表数据库功能
- `test_variable_resolution.py`: 测试变量解析功能

## 运行测试

### 运行单个测试

```bash
# 测试请求列表数据库
python test/test_request_list_db.py

# 测试变量解析
python test/test_variable_resolution.py
```

### 运行所有测试

```bash
# Windows
for %f in (test\test_*.py) do python "%f"

# Linux/Mac
for f in test/test_*.py; do python "$f"; done
```

## 添加新测试

创建新的测试文件时，请遵循以下命名规范：
- 文件名以 `test_` 开头
- 放在 `test/` 目录下
- 在文件开头添加路径配置：

```python
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
```
