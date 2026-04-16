"""可折叠的分页列表面板 - 提供通用的列表展示功能"""

import flet as ft
from typing import Callable, Optional


class CollapsibleListPanel(ft.Column):
    """
    可折叠的分页列表面板基类
    
    提供以下功能：
    - 可展开/折叠的内容区域
    - 分页控件
    - 统一的标题栏布局
    - 自定义操作按钮支持
    """
    
    def __init__(
        self,
        title: str,
        title_color: str = ft.Colors.GREY_800,
        list_view: ft.ListView = None,
        pagination_row: ft.Row = None,
        extra_buttons: list = None,
        clear_button_icon: ft.Icons = ft.Icons.DELETE_SWEEP,
        clear_button_tooltip: str = "清空",
        on_clear: Optional[Callable] = None,
        on_toggle: Optional[Callable] = None,
        content_height: int = 370,
        list_height: int = 300,
    ):
        super().__init__()
        
        # 保存配置
        self.title = title
        self.title_color = title_color
        self.content_height = content_height
        self.list_height = list_height
        
        # 创建或使用的组件
        self.list_view = list_view or ft.ListView(
            expand=False,
            spacing=8,
            padding=8,
            height=list_height,
            auto_scroll=False,
        )
        
        self.pagination_row = pagination_row or ft.Row(
            controls=[],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        )
        
        # 清空按钮
        self.clear_btn = ft.IconButton(
            icon=clear_button_icon,
            icon_size=18,
            tooltip=clear_button_tooltip,
            on_click=on_clear,
        )
        
        # 展开/折叠按钮
        self.toggle_btn = ft.IconButton(
            icon=ft.Icons.EXPAND_MORE,
            icon_size=20,
            on_click=self._handle_toggle,
        )
        self._on_toggle_callback = on_toggle
        
        # 额外按钮（在清空按钮之前）
        self.extra_buttons = extra_buttons or []
        
        # 内容容器（可折叠部分）
        self.content_container = ft.Container(
            content=ft.Column(
                controls=[
                    self.list_view,
                    ft.Container(height=5),
                    self.pagination_row,
                ],
                spacing=0,
            ),
            height=content_height,
            visible=True,
        )
        
        # 构建UI
        self.spacing = 0
        self.controls = [
            # 标题栏
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=title_color),
                        ft.Row(
                            controls=self._build_header_buttons(),
                            spacing=0,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
            ),
            # 内容区域
            self.content_container,
        ]
    
    def _build_header_buttons(self) -> list:
        """构建标题栏按钮列表（可被子类重写）"""
        buttons = []
        
        # 添加额外按钮
        buttons.extend(self.extra_buttons)
        
        # 添加清空按钮
        buttons.append(self.clear_btn)
        
        # 添加展开/折叠按钮
        buttons.append(self.toggle_btn)
        
        return buttons
    
    def _handle_toggle(self, e):
        """处理展开/折叠点击"""
        # 切换可见性
        is_visible = self.content_container.visible
        self.content_container.visible = not is_visible
        
        # 更新图标
        self.toggle_btn.icon = ft.Icons.EXPAND_LESS if not is_visible else ft.Icons.EXPAND_MORE
        
        # 调用回调
        if self._on_toggle_callback:
            self._on_toggle_callback(e)
        
        # 更新UI
        try:
            if hasattr(self, 'page') and self.page:
                self.update()
        except RuntimeError:
            pass
    
    def set_expanded(self, expanded: bool):
        """设置展开/折叠状态"""
        self.content_container.visible = expanded
        self.toggle_btn.icon = ft.Icons.EXPAND_LESS if expanded else ft.Icons.EXPAND_MORE
        try:
            if hasattr(self, 'page') and self.page:
                self.update()
        except RuntimeError:
            pass
    
    def is_expanded(self) -> bool:
        """检查是否展开"""
        return self.content_container.visible
    
    def update_pagination(self, controls: list):
        """更新分页控件"""
        self.pagination_row.controls.clear()
        self.pagination_row.controls.extend(controls)
        try:
            if hasattr(self.pagination_row, 'page') and self.pagination_row.page:
                self.pagination_row.update()
        except RuntimeError:
            pass
    
    def update_list(self):
        """更新列表视图"""
        try:
            if hasattr(self.list_view, 'page') and self.list_view.page:
                self.list_view.update()
        except RuntimeError:
            pass
