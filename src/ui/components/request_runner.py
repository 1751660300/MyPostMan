"""请求运行器组件"""

import flet as ft
from ui.components.key_value import KeyValueRow


class RequestRunner(ft.Container):
    """请求运行器组件（设置请求次数和并发数）"""

    def __init__(self):
        super().__init__()
        self.expand = True

        # 请求次数行
        self.request_count_row = KeyValueRow()
        self.request_count_row.key_input.value = "请求次数"
        self.request_count_row.key_input.read_only = True
        self.request_count_row.key_input.bgcolor = ft.Colors.GREY_100
        self.request_count_row.key_input.width = 150
        self.request_count_row.value_input.value = "1"
        self.request_count_row.value_input.hint_text = "总共发送多少次请求"
        self.request_count_row.value_input.keyboard_type = ft.KeyboardType.NUMBER
        self.request_count_row.desc_input.value = "总共发送多少次请求"
        self.request_count_row.delete_btn.visible = False
        self.request_count_row.enabled_checkbox.visible = False

        # 并发数量行
        self.concurrency_count_row = KeyValueRow()
        self.concurrency_count_row.key_input.value = "并发数量"
        self.concurrency_count_row.key_input.read_only = True
        self.concurrency_count_row.key_input.bgcolor = ft.Colors.GREY_100
        self.concurrency_count_row.key_input.width = 150
        self.concurrency_count_row.value_input.value = "1"
        self.concurrency_count_row.value_input.hint_text = "同时发送多少个请求"
        self.concurrency_count_row.value_input.keyboard_type = ft.KeyboardType.NUMBER
        self.concurrency_count_row.desc_input.value = "同时发送多少个请求（并发执行）"
        self.concurrency_count_row.delete_btn.visible = False
        self.concurrency_count_row.enabled_checkbox.visible = False

        # 进度条
        self.progress_bar = ft.ProgressBar(
            value=0,
            color=ft.Colors.BLUE,
            visible=False,
        )

        # 进度文本
        self.progress_text = ft.Text("", size=13, color=ft.Colors.GREY_700)

        self.content = ft.Column(
            controls=[
                # 表头
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text("参数名", size=12, weight=ft.FontWeight.BOLD, width=150),
                            ft.Text("参数值", size=12, weight=ft.FontWeight.BOLD, expand=2),
                            ft.Text("说明", size=12, weight=ft.FontWeight.BOLD, expand=1),
                        ],
                        spacing=8,
                    ),
                    padding=ft.padding.symmetric(vertical=6, horizontal=4),
                    bgcolor=ft.Colors.GREY_200,
                ),
                # 参数行
                ft.Container(
                    content=ft.Column(
                        controls=[
                            self.request_count_row,
                            self.concurrency_count_row,
                        ],
                        spacing=0,
                    ),
                ),
                ft.Container(height=10),
                # 进度
                self.progress_bar,
                ft.Container(height=5),
                self.progress_text,
            ],
            spacing=0,
        )

    def get_request_count(self) -> int:
        """获取请求次数"""
        try:
            return max(1, int(self.request_count_row.value_input.value or "1"))
        except ValueError:
            return 1

    def get_concurrency_count(self) -> int:
        """获取并发数量"""
        try:
            return max(1, int(self.concurrency_count_row.value_input.value or "1"))
        except ValueError:
            return 1

    def set_progress(self, value: float, text: str = ""):
        """设置进度"""
        self.progress_bar.value = value
        self.progress_text.value = text
        self.progress_bar.visible = value > 0
        try:
            if hasattr(self.progress_bar, 'page') and self.progress_bar.page:
                self.progress_bar.update()
                self.progress_text.update()
        except RuntimeError:
            pass

    def reset_progress(self):
        """重置进度"""
        self.progress_bar.value = 0
        self.progress_bar.visible = False
        self.progress_text.value = ""
        try:
            if hasattr(self.progress_bar, 'page') and self.progress_bar.page:
                self.progress_bar.update()
                self.progress_text.update()
        except RuntimeError:
            pass
