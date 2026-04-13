"""MyPostMan 应用启动入口"""

import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 导入并运行应用
from src.main import main

if __name__ == "__main__":
    import flet as ft
    ft.run(main)