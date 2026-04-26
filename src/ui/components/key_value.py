"""键值对输入组件"""

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
