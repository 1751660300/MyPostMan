"""设置面板组件 - 提供系统设置功能"""

import flet as ft
from typing import Callable, Optional
from managers.settings_manager import SettingsManager


class SettingsPanel(ft.Container):
    """
    设置面板
    
    提供系统设置功能，包括 SSL 认证等配置
    """
    
    def __init__(self, on_back: Optional[Callable] = None):
        """
        初始化设置面板
        
        Args:
            on_back: 返回回调函数
        """
        super().__init__()
        
        self.on_back = on_back
        self.expand = True
        self.visible = False
        
        # 设置管理器
        self.settings_manager = SettingsManager()
        
        # SSL 验证开关状态
        self.ssl_verify_enabled = self.settings_manager.get_ssl_verify_enabled()
        
        # 构建 UI
        self._build_ui()
    
    def _build_ui(self):
        """构建设置面板 UI"""
        # 返回按钮
        back_btn = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            icon_size=24,
            tooltip="返回",
            on_click=self._on_back_click,
        )
        
        # SSL 认证开关
        self.ssl_switch = ft.Switch(
            value=self.ssl_verify_enabled,
            on_change=self._on_ssl_switch_change,
        )
        
        self.ssl_status_text = ft.Text(
            "已开启（推荐）" if self.ssl_verify_enabled else "已关闭（存在风险）",
            size=14,
            color=ft.Colors.GREEN if self.ssl_verify_enabled else ft.Colors.ORANGE,
        )
        
        # SSL 设置卡片
        ssl_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.SHIELD, color=ft.Colors.BLUE, size=24),
                            ft.Text("SSL 证书验证", size=16, weight=ft.FontWeight.BOLD),
                        ],
                        spacing=12,
                    ),
                    ft.Divider(height=15),
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        "启用 SSL 证书验证以确保请求安全性",
                                        size=13,
                                        color=ft.Colors.GREY_700,
                                    ),
                                    ft.Text(
                                        "• 生产环境：建议开启\n"
                                        "• 测试环境/自签名证书：可以关闭",
                                        size=12,
                                        color=ft.Colors.GREY_600,
                                    ),
                                ],
                                spacing=8,
                                expand=True,
                            ),
                            ft.Row(
                                controls=[
                                    self.ssl_switch,
                                    self.ssl_status_text,
                                ],
                                spacing=12,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
                spacing=8,
            ),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.GREY_300),
            margin=ft.margin.only(bottom=15),
        )
        
        # 主内容
        self.content = ft.Container(
            content=ft.Column(
                controls=[
                    # 标题栏
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                back_btn,
                                ft.Text("系统设置", size=22, weight=ft.FontWeight.BOLD),
                            ],
                            spacing=12,
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        padding=ft.padding.only(left=20, right=20, top=20, bottom=15),
                    ),
                    ft.Divider(height=1),
                    # 设置内容
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Container(height=20),
                                ft.Text("安全设置", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
                                ft.Container(height=10),
                                ssl_card,
                            ],
                            spacing=0,
                            scroll=ft.ScrollMode.AUTO,
                        ),
                        padding=ft.padding.symmetric(horizontal=20, vertical=10),
                        expand=True,
                    ),
                ],
                spacing=0,
            ),
            expand=True,
            bgcolor=ft.Colors.GREY_100,
        )
    
    def _on_back_click(self, e):
        """返回按钮点击事件"""
        if self.on_back:
            self.on_back()
    
    def _on_ssl_switch_change(self, e):
        """SSL 开关切换事件"""
        is_enabled = self.ssl_switch.value
        
        if not is_enabled:
            # 关闭 SSL 验证，显示风险提示
            self._show_ssl_warning_dialog()
        else:
            # 开启 SSL 验证，直接保存
            self.ssl_verify_enabled = True
            self.ssl_status_text.value = "已开启（推荐）"
            self.ssl_status_text.color = ft.Colors.GREEN
            # 保存到数据库
            self.settings_manager.set_ssl_verify_enabled(True)
            try:
                self.update()
            except RuntimeError:
                pass
    
    def _show_ssl_warning_dialog(self):
        """显示 SSL 风险提示对话框"""
        def on_confirm(e):
            """确认关闭 SSL 验证"""
            self.page.pop_dialog()
            self.ssl_verify_enabled = False
            self.ssl_status_text.value = "已关闭（存在风险）"
            self.ssl_status_text.color = ft.Colors.ORANGE
            # 保存到数据库
            self.settings_manager.set_ssl_verify_enabled(False)
            try:
                self.update()
            except RuntimeError:
                pass
        
        def on_cancel(e):
            """取消关闭，恢复开关状态"""
            self.page.pop_dialog()
            self.ssl_switch.value = True  # 恢复为开启状态
            try:
                self.ssl_switch.update()
            except RuntimeError:
                pass
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("⚠️ 安全风险提示"),
            content=ft.Text(
                "关闭 SSL 证书验证后，请求将不会验证服务器的 SSL 证书，可能存在安全风险。\n\n"
                "建议：\n"
                "• 生产环境：请保持开启状态\n"
                "• 测试环境/自签名证书：可以临时关闭\n\n"
                "是否确认关闭 SSL 证书验证？",
                size=14,
            ),
            actions=[
                ft.TextButton(
                    "取消",
                    on_click=on_cancel,
                ),
                ft.TextButton(
                    "确认关闭",
                    on_click=on_confirm,
                    style=ft.ButtonStyle(
                        color=ft.Colors.ORANGE,
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = dialog
        self.page.show_dialog(dialog)
    
    def is_ssl_verify_enabled(self) -> bool:
        """获取 SSL 验证状态"""
        return self.ssl_verify_enabled
