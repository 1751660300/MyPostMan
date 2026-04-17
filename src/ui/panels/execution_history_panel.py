"""执行历史面板 - 查看执行计划的历史记录"""

import flet as ft
from typing import Optional, Callable
from datetime import datetime


class ExecutionHistoryPanel(ft.Column):
    """
    执行历史面板
    
    显示执行计划的历史记录列表
    """
    
    def __init__(self, on_back: Optional[Callable] = None):
        """
        初始化执行历史面板
        
        Args:
            on_back: 返回按钮回调函数
        """
        super().__init__()
        
        self.spacing = 15
        self.padding = 20
        self.on_back = on_back
        
        # 构建UI
        self._build_ui()
    
    def _build_ui(self):
        """构建面板UI"""
        # 空状态提示
        self.empty_state = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.HISTORY,
                        size=80,
                        color=ft.Colors.GREY_400,
                    ),
                    ft.Text(
                        "暂无执行历史",
                        size=18,
                        color=ft.Colors.GREY_600,
                        weight=ft.FontWeight.W_500,
                    ),
                    ft.Text(
                        "执行计划后将在此处显示历史记录",
                        size=14,
                        color=ft.Colors.GREY_500,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15,
            ),
            padding=60,
            alignment=ft.Alignment(0, 0),
        )
        
        # 历史记录列表容器
        self.history_list_container = ft.ListView(
            controls=[],
            expand=True,
            spacing=10,
            padding=10,
            visible=False,
        )
        
        # 外层容器，添加边距
        self.main_container = ft.Container(
            content=ft.Column(
                controls=[
                    # 标题栏
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.ARROW_BACK,
                                tooltip="返回",
                                on_click=self._on_back,
                            ),
                            ft.Text(
                                "执行历史",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.BLUE_800,
                            ),
                            ft.Container(expand=True),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    
                    ft.Divider(),
                    
                    # 空状态提示
                    self.empty_state,
                    
                    # 历史记录列表容器
                    self.history_list_container,
                ],
                spacing=15,
            ),
            padding=ft.padding.only(left=20, right=20, top=20, bottom=20),
            expand=True,
        )
        
        # 添加主容器到面板
        self.controls = [self.main_container]
    
    def load_history(self, logs: list):
        """
        加载执行历史记录
        
        Args:
            logs: 执行日志列表
        """
        if not logs:
            # 显示空状态
            self.empty_state.visible = True
            self.history_list_container.visible = False
        else:
            # 隐藏空状态，显示历史列表
            self.empty_state.visible = False
            self.history_list_container.visible = True
            
            # 清空现有列表
            self.history_list_container.controls.clear()
            
            # 按时间倒序排列
            sorted_logs = sorted(logs, key=lambda l: l.started_at, reverse=True)
            
            # 添加历史记录卡片
            for log in sorted_logs:
                card = self._create_history_card(log)
                self.history_list_container.controls.append(card)
        
        try:
            self.update()
        except RuntimeError:
            pass
    
    def _create_history_card(self, log) -> ft.Container:
        """
        创建历史记录卡片
        
        Args:
            log: 执行日志对象
            
        Returns:
            ft.Container: 历史记录卡片容器
        """
        # 状态图标和颜色
        status_config = {
            'completed': {'icon': ft.Icons.CHECK_CIRCLE, 'color': ft.Colors.GREEN, 'text': '已完成'},
            'failed': {'icon': ft.Icons.ERROR, 'color': ft.Colors.RED, 'text': '失败'},
            'stopped': {'icon': ft.Icons.STOP, 'color': ft.Colors.ORANGE, 'text': '已停止'},
            'running': {'icon': ft.Icons.PLAY_ARROW, 'color': ft.Colors.BLUE, 'text': '执行中'},
        }
        
        config = status_config.get(log.status.value, {'icon': ft.Icons.HELP, 'color': ft.Colors.GREY, 'text': '未知'})
        
        # 计算耗时
        duration_text = "N/A"
        if log.completed_at and log.started_at:
            duration = (log.completed_at - log.started_at).total_seconds()
            duration_text = f"{duration:.2f}秒"
        
        # 格式化时间
        started_time = log.started_at.strftime("%Y-%m-%d %H:%M:%S")
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    # 头部：计划名称和状态
                    ft.Row(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(config['icon'], color=config['color'], size=24),
                                    ft.Column(
                                        controls=[
                                            ft.Text(
                                                log.plan_name,
                                                size=16,
                                                weight=ft.FontWeight.BOLD,
                                            ),
                                            ft.Text(
                                                f"开始时间: {started_time}",
                                                size=12,
                                                color=ft.Colors.GREY_600,
                                            ),
                                        ],
                                        spacing=3,
                                    ),
                                ],
                                spacing=10,
                                expand=True,
                            ),
                            ft.Container(
                                content=ft.Text(
                                    config['text'],
                                    size=12,
                                    color=ft.Colors.WHITE,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                bgcolor=config['color'],
                                border_radius=12,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    
                    ft.Divider(height=5),
                    
                    # 底部：统计信息
                    ft.Row(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.LIST_ALT, size=16, color=ft.Colors.GREY_600),
                                    ft.Text(f"总步骤: {log.total_steps}", size=12, color=ft.Colors.GREY_700),
                                ],
                                spacing=5,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.CHECK, size=16, color=ft.Colors.GREEN),
                                    ft.Text(f"成功: {log.completed_steps}", size=12, color=ft.Colors.GREEN),
                                ],
                                spacing=5,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.CLOSE, size=16, color=ft.Colors.RED),
                                    ft.Text(f"失败: {log.failed_steps}", size=12, color=ft.Colors.RED),
                                ],
                                spacing=5,
                            ),
                            ft.Container(expand=True),
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.TIMER, size=16, color=ft.Colors.GREY_600),
                                    ft.Text(f"耗时: {duration_text}", size=12, color=ft.Colors.GREY_700),
                                ],
                                spacing=5,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                ],
                spacing=8,
            ),
            padding=15,
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_300),
        )
    
    def _on_back(self, e):
        """处理返回按钮点击"""
        if self.on_back:
            self.on_back()
