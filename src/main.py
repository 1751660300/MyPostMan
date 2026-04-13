"""MyPostMan - API 测试工具

一个类似 Apifox 的跨平台 API 测试工具，基于 Flet 框架开发。
支持 HTTP 请求发送、响应查看、历史记录管理等功能。
"""

import flet as ft
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from ui.main_ui import ApiTestPage


def main(page: ft.Page):
    """应用入口函数"""
    # 初始化主界面
    app = ApiTestPage(page)


if __name__ == "__main__":
    ft.run(main)
