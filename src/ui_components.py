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

    def __init__(self):
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
            "+ 添加参数",
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
        
        # 初始添加3行（不调用 update）
        for _ in range(3):
            row = KeyValueRow(on_delete=self._remove_row)
            self.data_area.controls.append(row)

    def _add_row(self):
        """添加一行键值输入"""
        row = KeyValueRow(on_delete=self._remove_row)
        self.data_area.controls.append(row)
        if self.data_area.page:
            self.data_area.update()

    def _remove_row(self, row: KeyValueRow):
        """删除指定行"""
        if row in self.data_area.controls:
            self.data_area.controls.remove(row)
            # 确保至少有3行
            while len(self.data_area.controls) < 3:
                self._add_row()
            if self.data_area.page:
                self.data_area.update()

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
        if self.data_area.page:
            self.data_area.update()


class BodyEditor(ft.Container):
    """Body 编辑器组件（类似 Postman）"""

    def __init__(self):
        super().__init__()
        self.expand = True
        
        # Body 类型选择
        self.body_type_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("none", "none"),
                ft.dropdown.Option("json", "raw (JSON)"),
                ft.dropdown.Option("text", "raw (Text)"),
                ft.dropdown.Option("x-www-form-urlencoded", "x-www-form-urlencoded"),
            ],
            value="none",
            width=220,
            label="Body 类型",
            on_text_change=self._on_body_type_change,
            text_size=13,
            label_style=ft.TextStyle(size=12, weight=ft.FontWeight.BOLD),
        )
        
        # Body 输入
        self.body_input = ft.TextField(
            multiline=True,
            min_lines=8,
            max_lines=20,
            hint_text='{\n  "key": "value"\n}',
            expand=True,
            text_size=13,
            text_style=ft.TextStyle(font_family="Consolas"),
        )
        
        # 格式化按钮
        self.format_btn = ft.IconButton(
            icon=ft.Icons.FORMAT_ALIGN_LEFT,
            tooltip="格式化 JSON",
            on_click=self._format_json,
        )
        
        self.content = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        self.body_type_dropdown,
                        self.format_btn,
                    ],
                    spacing=10,
                ),
                ft.Container(height=10),
                self.body_input,
            ],
            expand=True,
        )

    def _on_body_type_change(self, e):
        """Body 类型切换时更新提示文本"""
        body_type = self.body_type_dropdown.value
        if body_type == "json":
            self.body_input.hint_text = '{\n  "key": "value"\n}'
        elif body_type == "text":
            self.body_input.hint_text = "纯文本内容"
        elif body_type == "x-www-form-urlencoded":
            self.body_input.hint_text = 'key1=value1&key2=value2 或 JSON 格式'
        else:
            self.body_input.hint_text = ""
        self.body_input.update()

    def _format_json(self, e):
        """格式化 JSON"""
        import json
        try:
            body = self.body_input.value
            if body:
                parsed = json.loads(body)
                self.body_input.value = json.dumps(parsed, indent=2, ensure_ascii=False)
                self.body_input.update()
        except json.JSONDecodeError as ex:
            pass  # 忽略格式错误

    def get_body(self) -> str:
        return self.body_input.value

    def get_body_type(self) -> str:
        return self.body_type_dropdown.value

    def set_body(self, body: str):
        self.body_input.value = body
        self.body_input.update()

    def set_body_type(self, body_type: str):
        self.body_type_dropdown.value = body_type
        self.body_type_dropdown.update()


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
        if self.progress_bar.page:
            self.progress_bar.update()
            self.progress_text.update()

    def reset_progress(self):
        """重置进度"""
        self.progress_bar.value = 0
        self.progress_bar.visible = False
        self.progress_text.value = ""
        if self.progress_bar.page:
            self.progress_bar.update()
            self.progress_text.update()


class ResponsePanel(ft.Container):
    """响应展示面板组件"""

    def __init__(self):
        super().__init__()
        self.expand = True
        self.padding = 15

        # 状态信息
        self.status_text = ft.Text("等待发送请求", size=15, weight=ft.FontWeight.BOLD)
        self.time_text = ft.Text("", size=13, color=ft.Colors.GREY_700)

        # Tab 切换内容
        self.body_text = ft.Text("", size=13, font_family="Consolas")
        self.headers_text = ft.Text("", size=13, font_family="Consolas")
        self.cookies_text = ft.Text("", size=13, font_family="Consolas")

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
                            self._create_scrollable(self.body_text),
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

    def _create_scrollable(self, text_control: ft.Text) -> ft.ListView:
        """创建可滚动的文本容器"""
        return ft.ListView(
            controls=[text_control],
            expand=True,
            spacing=5,
        )

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
            self.body_text.value = response.error
            self.headers_text.value = ""
            self.cookies_text.value = ""
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

            # 格式化响应体
            self.body_text.value = response.formatted_body

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
        self.body_text.value = ""
        self.headers_text.value = ""
        self.cookies_text.value = ""
        self.update()
