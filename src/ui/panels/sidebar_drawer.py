"""侧边抽屉菜单组件 - 提供页面导航功能"""

import flet as ft
from typing import Callable, Optional


class SidebarDrawer(ft.Container):
    """
    侧边抽屉菜单
    
    提供可折叠的侧边导航菜单，支持多个页面切换
    """
    
    def __init__(
        self,
        width: int = 60,
        expanded_width: int = 200,
        on_page_change: Optional[Callable] = None,
    ):
        """
        初始化侧边抽屉
        
        Args:
            width: 折叠时的宽度
            expanded_width: 展开时的宽度
            on_page_change: 页面切换回调函数，接收页面名称参数
        """
        super().__init__()
        
        self.width = width
        self.expanded_width = expanded_width
        self.is_expanded = False
        self.on_page_change = on_page_change
        self.current_page = "home"
        
        # 菜单项定义
        self.menu_items = [
            {
                "id": "home",
                "icon": ft.Icons.HOME,
                "title": "首页",
                "tooltip": "API测试",
            },
            {
                "id": "execution_plan",
                "icon": ft.Icons.PLAY_CIRCLE,
                "title": "执行计划",
                "tooltip": "批量执行请求",
            },
            {
                "id": "settings",
                "icon": ft.Icons.SETTINGS,
                "title": "设置",
                "tooltip": "系统设置",
            },
        ]
        
        # 构建UI
        self._build_ui()
    
    def _build_ui(self):
        """构建抽屉UI"""
        # 展开/折叠按钮
        self.toggle_btn = ft.IconButton(
            icon=ft.Icons.MENU,
            icon_size=24,
            icon_color=ft.Colors.WHITE,
            tooltip="展开菜单",
            on_click=self._on_toggle,
            width=40,
            height=40,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.TRANSPARENT,
                color=ft.Colors.WHITE,
            ),
        )
        
        # Logo/标题区域
        self.logo_text = ft.Text(
            "MyPostMan",
            color=ft.Colors.WHITE,
            size=16,
            weight=ft.FontWeight.BOLD,
            visible=False,
        )
        
        # 菜单项容器
        self.menu_container = ft.Column(
            controls=[],
            spacing=4,
        )
        
        # 重建菜单项
        self._rebuild_menu_items()
        
        # 主内容
        self.content = ft.Column(
            controls=[
                # 顶部区域
                ft.Container(
                    content=ft.Row(
                        controls=[
                            self.toggle_btn,
                            ft.Container(width=8),
                            self.logo_text,
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    padding=ft.padding.only(left=10, right=10, top=15, bottom=10),
                ),
                ft.Divider(height=1, color=ft.Colors.GREY_700),
                # 菜单项
                ft.Container(
                    content=self.menu_container,
                    padding=ft.padding.symmetric(horizontal=8, vertical=10),
                    expand=True,
                ),
            ],
            spacing=0,
        )
        
        # 设置容器属性
        self.width = self.width
        self.bgcolor = ft.Colors.GREY_900
    
    def _rebuild_menu_items(self):
        """重建菜单项列表"""
        self.menu_container.controls.clear()
        
        for item in self.menu_items:
            is_active = (item["id"] == self.current_page)
            
            # 根据展开状态决定布局
            if self.is_expanded:
                # 展开模式：图标 + 文字
                menu_content = ft.Row(
                    controls=[
                        ft.Icon(
                            item["icon"],
                            color=ft.Colors.WHITE if is_active else ft.Colors.GREY_400,
                            size=20,
                        ),
                        ft.Text(
                            item["title"],
                            color=ft.Colors.WHITE if is_active else ft.Colors.GREY_300,
                            size=14,
                            weight=ft.FontWeight.W_500 if is_active else ft.FontWeight.NORMAL,
                        ),
                    ],
                    spacing=12,
                    alignment=ft.MainAxisAlignment.START,
                )
                padding = ft.padding.symmetric(vertical=10, horizontal=12)
            else:
                # 折叠模式：只显示图标，居中
                menu_content = ft.Container(
                    content=ft.Icon(
                        item["icon"],
                        color=ft.Colors.WHITE if is_active else ft.Colors.GREY_400,
                        size=22,
                    ),
                    alignment=ft.Alignment(0, 0),
                )
                padding = ft.padding.symmetric(vertical=12, horizontal=0)
            
            menu_item = ft.Container(
                content=menu_content,
                padding=padding,
                bgcolor=ft.Colors.BLUE_600 if is_active else ft.Colors.TRANSPARENT,
                border_radius=8,
                on_click=lambda e, page_id=item["id"]: self._on_menu_click(page_id),
                tooltip=item["tooltip"],
                data=item["id"],
                ink=True,
            )
            
            self.menu_container.controls.append(menu_item)
    
    def _on_toggle(self, e):
        """处理展开/折叠点击"""
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            # 展开
            self.width = self.expanded_width
            self.toggle_btn.tooltip = "折叠菜单"
            self.logo_text.visible = True
        else:
            # 折叠
            self.width = 60
            self.toggle_btn.tooltip = "展开菜单"
            self.logo_text.visible = False
        
        # 重建菜单项以更新布局
        self._rebuild_menu_items()
        
        try:
            self.update()
        except RuntimeError:
            pass
    
    def _on_menu_click(self, page_id: str):
        """处理菜单项点击"""
        if page_id == self.current_page:
            return
        
        # 更新当前页面
        old_page = self.current_page
        self.current_page = page_id
        
        # 重建菜单项以更新激活状态
        self._rebuild_menu_items()
        
        # 调用回调
        if self.on_page_change:
            self.on_page_change(page_id, old_page)
        
        try:
            self.update()
        except RuntimeError:
            pass
    
    def set_active_page(self, page_id: str):
        """
        设置活动页面（编程方式）
        
        Args:
            page_id: 页面ID
        """
        if page_id == self.current_page:
            return
        
        old_page = self.current_page
        self.current_page = page_id
        
        # 重建菜单项
        self._rebuild_menu_items()
        
        # 调用回调
        if self.on_page_change:
            self.on_page_change(page_id, old_page)
        
        try:
            self.update()
        except RuntimeError:
            pass
    
    def get_active_page(self) -> str:
        """获取当前活动页面ID"""
        return self.current_page
