"""Body 编辑器组件"""

import flet as ft
import json
import threading


class BodyEditor(ft.Container):
    """Body 编辑器组件（类似 Postman）"""

    def __init__(self):
        super().__init__()
        self.expand = True

        # Body 类型选择
        self.body_type_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("none", "无"),
                ft.dropdown.Option("json", "JSON"),
                ft.dropdown.Option("text", "文本"),
                ft.dropdown.Option("x-www-form-urlencoded", "表单"),
            ],
            value="none",
            width=180,
            label="Body 类型",
            on_text_change=self._on_body_type_change,
            text_size=13,
            label_style=ft.TextStyle(size=12, weight=ft.FontWeight.BOLD),
        )

        # Body 输入 - 使用更美观的样式
        self.body_input = ft.TextField(
            multiline=True,
            min_lines=10,
            max_lines=25,
            hint_text='选择 Body 类型后输入内容',
            expand=True,
            text_size=13,
            text_style=ft.TextStyle(font_family="Consolas", size=13),
            border_radius=8,
            filled=True,
            bgcolor=ft.Colors.GREY_50,
        )

        # 工具栏按钮
        self.format_btn = ft.IconButton(
            icon=ft.Icons.FORMAT_PAINT,
            icon_size=20,
            tooltip="格式化/美化 JSON",
            on_click=self._format_json,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_50,
                color=ft.Colors.BLUE,
            ),
        )

        self.copy_btn = ft.IconButton(
            icon=ft.Icons.CONTENT_COPY,
            icon_size=20,
            tooltip="复制内容",
            on_click=self._copy_content,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_50,
                color=ft.Colors.GREEN,
            ),
        )

        self.clear_btn = ft.IconButton(
            icon=ft.Icons.CLEAR_ALL,
            icon_size=20,
            tooltip="清空内容",
            on_click=self._clear_content,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREY_200,
                color=ft.Colors.GREY_700,
            ),
        )

        # 状态提示
        self.status_text = ft.Text(
            "",
            size=11,
            color=ft.Colors.GREY_600,
            visible=False,
        )

        self.content = ft.Column(
            controls=[
                # 工具栏
                ft.Container(
                    content=ft.Row(
                        controls=[
                            self.body_type_dropdown,
                            ft.Container(width=10),
                            self.format_btn,
                            self.copy_btn,
                            self.clear_btn,
                            ft.Container(expand=True),
                            self.status_text,
                        ],
                        spacing=8,
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    padding=ft.padding.symmetric(vertical=8, horizontal=4),
                ),
                # Body 输入区域
                ft.Container(
                    content=self.body_input,
                    expand=True,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=8,
                    padding=4,
                ),
            ],
            expand=True,
            spacing=8,
        )

    def _on_body_type_change(self, e):
        """Body 类型切换时更新提示文本和自动美化"""
        body_type = self.body_type_dropdown.value
        if body_type == "json":
            self.body_input.hint_text = '{\n  "key": "value",\n  "example": "data"\n}'
            # 如果已有内容,自动美化
            if self.body_input.value and self.body_input.value.strip():
                self._auto_format_if_json()
        elif body_type == "text":
            self.body_input.hint_text = "输入纯文本内容"
        elif body_type == "x-www-form-urlencoded":
            self.body_input.hint_text = 'key1=value1&key2=value2'
        else:
            self.body_input.hint_text = "选择 Body 类型后输入内容"

        self._show_status(f"已切换到 {body_type} 模式")
        try:
            if hasattr(self.body_input, 'page') and self.body_input.page:
                self.body_input.update()
        except RuntimeError:
            pass

    def _auto_format_if_json(self):
        """如果是JSON则自动美化"""
        try:
            body = self.body_input.value.strip()
            if body:
                parsed = json.loads(body)
                self.body_input.value = json.dumps(parsed, indent=2, ensure_ascii=False)
                self._show_status("✓ JSON 已自动美化")
                try:
                    if hasattr(self.body_input, 'page') and self.body_input.page:
                        self.body_input.update()
                except RuntimeError:
                    pass
                return True
        except (json.JSONDecodeError, ValueError):
            pass
        return False

    def _format_json(self, e):
        """格式化 JSON"""
        try:
            body = self.body_input.value.strip()
            if body:
                parsed = json.loads(body)
                self.body_input.value = json.dumps(parsed, indent=2, ensure_ascii=False)
                self._show_status("✓ JSON 格式化成功")
                try:
                    if hasattr(self.body_input, 'page') and self.body_input.page:
                        self.body_input.update()
                except RuntimeError:
                    pass
            else:
                self._show_status("⚠ 内容为空", ft.Colors.ORANGE)
        except json.JSONDecodeError as ex:
            self._show_status(f"✗ JSON 格式错误: {str(ex)[:50]}", ft.Colors.RED)
        except Exception as ex:
            self._show_status(f"✗ 格式化失败: {str(ex)}", ft.Colors.RED)

    def _copy_content(self, e):
        """复制内容到剪贴板"""
        if self.body_input.value:
            try:
                if hasattr(self, 'page') and self.page:
                    self.page.clipboard.set(self.body_input.value)
            except RuntimeError:
                pass
            self._show_status("✓ 已复制到剪贴板", ft.Colors.GREEN)
        else:
            self._show_status("⚠ 内容为空", ft.Colors.ORANGE)

    def _clear_content(self, e):
        """清空内容"""
        self.body_input.value = ""
        self._show_status("✓ 已清空内容", ft.Colors.GREEN)
        try:
            if hasattr(self.body_input, 'page') and self.body_input.page:
                self.body_input.update()
        except RuntimeError:
            pass

    def _show_status(self, message: str, color: str = ft.Colors.GREEN):
        """显示状态提示"""
        self.status_text.value = message
        self.status_text.color = color
        self.status_text.visible = True
        try:
            if hasattr(self.status_text, 'page') and self.status_text.page:
                self.status_text.update()
        except RuntimeError:
            pass
        # 3秒后自动隐藏
        def hide_status():
            import time
            time.sleep(3)
            self.status_text.visible = False
            try:
                if hasattr(self.status_text, 'page') and self.status_text.page:
                    self.status_text.page.run_thread(lambda: self.status_text.update())
            except RuntimeError:
                pass

        thread = threading.Thread(target=hide_status)
        thread.daemon = True
        thread.start()

    def get_body(self) -> str:
        return self.body_input.value

    def get_body_type(self) -> str:
        return self.body_type_dropdown.value

    def set_body(self, body: str):
        self.body_input.value = body
        # 如果是JSON类型,自动美化
        if self.body_type_dropdown.value == "json":
            self._auto_format_if_json()
        try:
            if hasattr(self.body_input, 'page') and self.body_input.page:
                self.body_input.update()
        except RuntimeError:
            pass

    def set_body_type(self, body_type: str):
        self.body_type_dropdown.value = body_type
        self._on_body_type_change(None)
        try:
            if hasattr(self.body_type_dropdown, 'page') and self.body_type_dropdown.page:
                self.body_type_dropdown.update()
        except RuntimeError:
            pass
