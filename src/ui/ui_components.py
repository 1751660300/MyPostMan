"""UI 组件模块 - 定义各种界面组件"""

import flet as ft
from typing import Callable


class KeyValueRow(ft.Container):
    """键值对输入行组件（类似 Postman）"""

    def __init__(self, on_delete: Callable | None = None):
        super().__init__()
        
        # 启用/禁用复选框
        self.enabled_checkbox = ft.Checkbox(
            value=True,
            tooltip="启用/禁用此参数",
            width=30,
        )
        
        # Key 输入
        self.key_input = ft.TextField(
            hint_text="Key",
            width=150,
            text_size=13,
            height=36,
            dense=True,
        )
        
        # Value 输入
        self.value_input = ft.TextField(
            hint_text="Value",
            expand=2,
            text_size=13,
            height=36,
            dense=True,
        )
        
        # Description 输入
        self.desc_input = ft.TextField(
            hint_text="Description",
            expand=1,
            text_size=13,
            height=36,
            dense=True,
        )
        
        # 删除按钮
        self.delete_btn = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_size=18,
            tooltip="删除此行",
            width=36,
            on_click=lambda e: self._handle_delete(),
        )
        self.on_delete_callback = on_delete

        self.content = ft.Row(
            controls=[
                self.enabled_checkbox,
                self.key_input,
                self.value_input,
                self.desc_input,
                self.delete_btn,
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.padding = ft.padding.symmetric(vertical=2, horizontal=4)

    def _handle_delete(self):
        if self.on_delete_callback:
            self.on_delete_callback(self)

    def is_enabled(self) -> bool:
        return self.enabled_checkbox.value

    def get_key(self) -> str:
        return self.key_input.value.strip()

    def get_value(self) -> str:
        return self.value_input.value.strip()

    def get_description(self) -> str:
        return self.desc_input.value.strip()

    def is_empty(self) -> bool:
        return not self.get_key() and not self.get_value()


class DynamicKeyValueList(ft.Container):
    """动态键值对列表组件（类似 Postman 表格样式）"""

    def __init__(self, default_data: dict[str, str] = None):
        super().__init__()
        self.expand = True

        # 数据区域
        self.data_area = ft.Column(
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        # 添加行按钮
        self.add_row_btn = ft.TextButton(
            "添加参数",
            icon=ft.Icons.ADD,
            on_click=lambda e: self._add_row(),
        )

        self.content = ft.Column(
            controls=[
                # 表头
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(width=30),  # 复选框占位
                            ft.Text("Key", size=12, weight=ft.FontWeight.BOLD, width=150),
                            ft.Text("Value", size=12, weight=ft.FontWeight.BOLD, expand=2),
                            ft.Text("Description", size=12, weight=ft.FontWeight.BOLD, expand=1),
                            ft.Container(width=36),  # 删除按钮占位
                        ],
                        spacing=8,
                    ),
                    padding=ft.padding.symmetric(vertical=6, horizontal=4),
                    bgcolor=ft.Colors.GREY_200,
                ),
                # 数据行
                self.data_area,
                # 添加按钮
                ft.Container(
                    content=self.add_row_btn,
                    padding=ft.padding.only(top=5),
                ),
            ],
            spacing=0,
        )

        # 如果有默认数据，先添加默认数据
        if default_data:
            for key, value in default_data.items():
                row = KeyValueRow(on_delete=self._remove_row)
                row.key_input.value = key
                row.value_input.value = value
                self.data_area.controls.append(row)
        
        # 补充空行（确保至少有3行）
        while len(self.data_area.controls) < 3:
            row = KeyValueRow(on_delete=self._remove_row)
            self.data_area.controls.append(row)

    def _add_row(self):
        """添加一行键值输入"""
        row = KeyValueRow(on_delete=self._remove_row)
        self.data_area.controls.append(row)
        try:
            if hasattr(self.data_area, 'page') and self.data_area.page:
                self.data_area.update()
        except RuntimeError:
            pass

    def _remove_row(self, row: KeyValueRow):
        """删除指定行"""
        if row in self.data_area.controls:
            self.data_area.controls.remove(row)
            # 确保至少有3行
            while len(self.data_area.controls) < 3:
                self._add_row()
            try:
                if hasattr(self.data_area, 'page') and self.data_area.page:
                    self.data_area.update()
            except RuntimeError:
                pass

    def get_data(self) -> dict[str, str]:
        """获取所有非空且启用的键值对"""
        data = {}
        for control in self.data_area.controls:
            if isinstance(control, KeyValueRow) and not control.is_empty() and control.is_enabled():
                data[control.get_key()] = control.get_value()
        return data

    def set_data(self, data: dict[str, str]):
        """设置键值对数据"""
        self.data_area.controls.clear()
        for key, value in data.items():
            row = KeyValueRow(on_delete=self._remove_row)
            row.key_input.value = key
            row.value_input.value = value
            self.data_area.controls.append(row)
        # 补充空行
        while len(self.data_area.controls) < 3:
            row = KeyValueRow(on_delete=self._remove_row)
            self.data_area.controls.append(row)
        # 只有在组件已添加到页面时才update
        try:
            if hasattr(self.data_area, 'page') and self.data_area.page:
                self.data_area.update()
        except RuntimeError:
            # 组件还未添加到页面，不需要update
            pass


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
        import json
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
        import json
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
            # 组件还未添加到页面，不需要update
            pass
        # 3秒后自动隐藏
        import threading
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
        
        # HTTPS 行（使用独立布局）
        self.https_key_input = ft.TextField(
            value="启用 HTTPS",
            read_only=True,
            bgcolor=ft.Colors.GREY_100,
            width=150,
            text_size=13,
            height=36,
            dense=True,
        )
        self.https_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("是", "是"),
                ft.dropdown.Option("否", "否"),
            ],
            value="是",
            expand=2,
            text_size=13,
            height=36,
            dense=True,
        )
        self.https_desc_input = ft.TextField(
            value="是否使用 HTTPS 协议",
            read_only=True,
            bgcolor=ft.Colors.GREY_100,
            expand=1,
            text_size=13,
            height=36,
            dense=True,
        )
        
        # SSL 认证行（使用独立布局）
        self.ssl_key_input = ft.TextField(
            value="SSL 认证",
            read_only=True,
            bgcolor=ft.Colors.GREY_100,
            width=150,
            text_size=13,
            height=36,
            dense=True,
        )
        self.ssl_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("认证", "认证"),
                ft.dropdown.Option("不认证", "不认证"),
            ],
            value="不认证",
            expand=2,
            text_size=13,
            height=36,
            dense=True,
        )
        self.ssl_desc_input = ft.TextField(
            value="是否验证 SSL 证书",
            read_only=True,
            bgcolor=ft.Colors.GREY_100,
            expand=1,
            text_size=13,
            height=36,
            dense=True,
        )
        
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
                            # HTTPS 行
                            ft.Container(
                                content=ft.Row(
                                    controls=[
                                        ft.Container(
                                            content=self.https_key_input,
                                            width=150,
                                        ),
                                        self.https_dropdown,
                                        ft.Container(
                                            content=self.https_desc_input,
                                            expand=1,
                                        ),
                                    ],
                                    spacing=8,
                                    alignment=ft.MainAxisAlignment.START,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                padding=ft.padding.symmetric(vertical=2, horizontal=4),
                            ),
                            # SSL 认证行
                            ft.Container(
                                content=ft.Row(
                                    controls=[
                                        ft.Container(
                                            content=self.ssl_key_input,
                                            width=150,
                                        ),
                                        self.ssl_dropdown,
                                        ft.Container(
                                            content=self.ssl_desc_input,
                                            expand=1,
                                        ),
                                    ],
                                    spacing=8,
                                    alignment=ft.MainAxisAlignment.START,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                padding=ft.padding.symmetric(vertical=2, horizontal=4),
                            ),
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
    
    def _toggle_https(self, e):
        """切换 HTTPS 状态（已废弃，保留兼容）"""
        pass  # Dropdown 值自动更新
    
    def _toggle_ssl_verify(self, e):
        """切换 SSL 认证状态（已废弃，保留兼容）"""
        pass  # Dropdown 值自动更新

    def is_https(self) -> bool:
        """是否启用 HTTPS"""
        return self.https_dropdown.value == "是"

    def is_ssl_verify(self) -> bool:
        """是否验证 SSL 证书"""
        return self.ssl_dropdown.value == "认证"

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


class ResponsePanel(ft.Container):
    """响应展示面板组件"""

    def __init__(self):
        super().__init__()
        self.expand = True
        self.padding = 15

        # 状态信息
        self.status_text = ft.Text("", size=15, weight=ft.FontWeight.BOLD)
        self.time_text = ft.Text("", size=13, color=ft.Colors.GREY_700)

        # 响应类型信息
        self.response_type_text = ft.Text("", size=12, color=ft.Colors.BLUE)

        # Tab 切换内容
        self.body_text = ft.Text("", size=13, font_family="Consolas")
        self.headers_text = ft.Text("", size=13, font_family="Consolas")
        self.cookies_text = ft.Text("", size=13, font_family="Consolas")

        # HTML 预览（使用 WebView 或文本展示）
        self.html_preview = ft.TextField(
            multiline=True,
            read_only=True,
            text_size=12,
            text_style=ft.TextStyle(font_family="Consolas", size=12),
            expand=True,
            visible=False,
        )

        # 使用 TabBar + TabBarView
        self.tabs = ft.Tabs(
            length=3,
            selected_index=0,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        tab_alignment=ft.TabAlignment.START,
                        tabs=[
                            ft.Tab(label=ft.Text("Body")),
                            ft.Tab(label=ft.Text("Headers")),
                            ft.Tab(label=ft.Text("Cookies")),
                        ],
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            self._create_body_tab(),
                            self._create_scrollable(self.headers_text),
                            self._create_scrollable(self.cookies_text),
                        ],
                    ),
                ],
            ),
        )

        self.content = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Row(
                        controls=[
                            self.status_text,
                            self.response_type_text,
                            self.time_text,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=10,
                    bgcolor=ft.Colors.GREY_50,
                    border_radius=6,
                ),
                ft.Container(height=10),
                self.tabs,
            ],
            expand=True,
        )

    def _create_body_tab(self) -> ft.Container:
        """创建 Body tab 的内容（支持普通文本和HTML预览）"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    # Body 文本
                    self._create_scrollable(self.body_text),
                    # HTML 预览
                    self.html_preview,
                ],
                expand=True,
            ),
            expand=True,
        )

    def _create_scrollable(self, text_control: ft.Text) -> ft.ListView:
        """创建可滚动的文本容器"""
        return ft.ListView(
            controls=[text_control],
            expand=True,
            spacing=5,
        )

    def _detect_response_type(self, headers: dict) -> str:
        """检测响应类型"""
        content_type = headers.get("Content-Type", headers.get("content-type", "")).lower()
        if "html" in content_type:
            return "html"
        elif "json" in content_type:
            return "json"
        elif "xml" in content_type:
            return "xml"
        elif "text" in content_type:
            return "text"
        else:
            return "unknown"

    def _format_html(self, html_content: str) -> str:
        """简单格式化 HTML（添加换行和缩进）"""
        import re
        
        # 移除多余的空白
        formatted = re.sub(r'>\s+<', '><', html_content.strip())
        
        # 简单的缩进处理
        indent = 0
        lines = []
        
        # 分割标签
        tags = re.findall(r'<[^>]+>|[^<]+', formatted)
        
        for tag in tags:
            if tag.startswith('</'):
                indent = max(0, indent - 1)
                lines.append('  ' * indent + tag)
            elif tag.startswith('<') and not tag.startswith('<?') and not tag.startswith('<!--'):
                lines.append('  ' * indent + tag)
                if not tag.endswith('/>') and not tag.startswith('<!'):
                    indent += 1
            else:
                text = tag.strip()
                if text:
                    lines.append('  ' * indent + text)
        
        return '\n'.join(lines)

    def update_response(self, response):
        """
        更新响应数据

        Args:
            response: HttpResponse 对象
        """
        from models import HttpResponse

        if response.error:
            self.status_text.value = f"❌ {response.error}"
            self.status_text.color = ft.Colors.RED
            self.time_text.value = f"耗时: {response.elapsed}ms"
            self.response_type_text.value = ""
            self.body_text.value = response.error
            self.headers_text.value = ""
            self.cookies_text.value = ""
            self.html_preview.visible = False
            self.body_text.visible = True
        else:
            # 状态码颜色
            if response.is_success:
                status_icon = "✅"
                self.status_text.color = ft.Colors.GREEN
            elif response.status_code >= 400:
                status_icon = "❌"
                self.status_text.color = ft.Colors.RED
            else:
                status_icon = "⚠️"
                self.status_text.color = ft.Colors.ORANGE

            self.status_text.value = f"{status_icon} {response.status_code} {response.reason}"
            self.time_text.value = f"耗时: {response.elapsed}ms"

            # 检测响应类型
            response_type = self._detect_response_type(response.headers)
            
            # 格式化响应体
            if response_type == "html":
                # HTML 类型：提供格式化的源码
                formatted_html = self._format_html(response.body)
                self.body_text.value = formatted_html
                self.html_preview.value = formatted_html
                self.html_preview.visible = True
                self.body_text.visible = False
                self.response_type_text.value = f"📄 类型: HTML"
            elif response_type == "json":
                # JSON 类型：自动美化
                self.body_text.value = response.formatted_body
                self.html_preview.visible = False
                self.body_text.visible = True
                self.response_type_text.value = f"📄 类型: JSON"
            else:
                # 其他类型
                self.body_text.value = response.formatted_body
                self.html_preview.visible = False
                self.body_text.visible = True
                type_map = {
                    "xml": "XML",
                    "text": "Text",
                    "unknown": "Unknown"
                }
                self.response_type_text.value = f"📄 类型: {type_map.get(response_type, 'Unknown')}"

            # 格式化响应头
            headers_str = "\n".join(f"{k}: {v}" for k, v in response.headers.items())
            self.headers_text.value = headers_str

            # 格式化 Cookies
            cookies_str = "\n".join(response.headers.get("Set-Cookie", "").split("; "))
            self.cookies_text.value = cookies_str if cookies_str else "无 Cookies"

        self.update()

    def clear(self):
        """清空响应展示"""
        self.status_text.value = "等待发送请求"
        self.status_text.color = None
        self.time_text.value = ""
        self.response_type_text.value = ""
        self.body_text.value = ""
        self.headers_text.value = ""
        self.cookies_text.value = ""
        self.html_preview.visible = False
        self.body_text.visible = True
        self.update()
