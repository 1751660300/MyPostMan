"""请求列表面板 - 显示保存的API请求列表"""

import flet as ft
from ui.panels.collapsible_list_panel import CollapsibleListPanel


class RequestListPanel(CollapsibleListPanel):
    """
    请求列表面板
    
    继承自 CollapsibleListPanel，专门用于显示保存的API请求列表
    支持添加、导入等额外操作按钮
    """
    
    def __init__(
        self,
        list_view: ft.ListView = None,
        pagination_row: ft.Row = None,
        on_add: callable = None,
        on_import: callable = None,
        on_clear: callable = None,
        on_toggle: callable = None,
    ):
        # 创建额外按钮
        extra_buttons = []
        
        if on_add:
            extra_buttons.append(
                ft.IconButton(
                    icon=ft.Icons.ADD,
                    icon_size=18,
                    tooltip="添加当前请求到列表",
                    on_click=on_add,
                )
            )
        
        if on_import:
            extra_buttons.append(
                ft.IconButton(
                    icon=ft.Icons.CONTENT_PASTE,
                    icon_size=18,
                    tooltip="从剪贴板导入",
                    on_click=on_import,
                )
            )
        
        super().__init__(
            title="请求列表",
            title_color=ft.Colors.BLUE_800,
            list_view=list_view,
            pagination_row=pagination_row,
            extra_buttons=extra_buttons,
            clear_button_icon=ft.Icons.DELETE_SWEEP,
            clear_button_tooltip="清空列表",
            on_clear=on_clear,
            on_toggle=on_toggle,
            content_height=370,
            list_height=300,
        )
