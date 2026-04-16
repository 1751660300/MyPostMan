"""历史列表面板 - 显示API请求历史记录"""

import flet as ft
from ui.panels.collapsible_list_panel import CollapsibleListPanel


class HistoryListPanel(CollapsibleListPanel):
    """
    历史列表面板
    
    继承自 CollapsibleListPanel，专门用于显示API请求历史记录
    """
    
    def __init__(
        self,
        list_view: ft.ListView = None,
        pagination_row: ft.Row = None,
        on_clear: callable = None,
        on_toggle: callable = None,
    ):
        super().__init__(
            title="历史记录",
            title_color=ft.Colors.GREY_800,
            list_view=list_view,
            pagination_row=pagination_row,
            extra_buttons=[],  # 历史列表没有额外按钮
            clear_button_icon=ft.Icons.DELETE_SWEEP,
            clear_button_tooltip="清空历史",
            on_clear=on_clear,
            on_toggle=on_toggle,
            content_height=370,
            list_height=300,
        )
