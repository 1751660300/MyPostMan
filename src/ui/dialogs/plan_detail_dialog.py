"""计划详情对话框 - 查看和管理执行计划的步骤"""

import flet as ft
from typing import Optional, Callable, List
from models.execution_plan import ExecutionPlan, ExecutionStep


class PlanDetailDialog:
    """计划详情对话框"""
    
    def __init__(self, plan: ExecutionPlan, on_close: Callable, on_add_step: Callable, 
                 on_edit_step: Callable, on_delete_step: Callable, on_move_step: Callable):
        """
        初始化对话框
        
        Args:
            plan: 执行计划对象
            on_close: 关闭回调
            on_add_step: 添加步骤回调
            on_edit_step: 编辑步骤回调
            on_delete_step: 删除步骤回调
            on_move_step: 移动步骤回调 (step_id, direction) direction: 'up' or 'down'
        """
        self.plan = plan
        self.on_close = on_close
        self.on_add_step = on_add_step
        self.on_edit_step = on_edit_step
        self.on_delete_step = on_delete_step
        self.on_move_step = on_move_step
        
        # 构建对话框
        self.dialog = self._build_dialog()
    
    def _build_dialog(self) -> ft.AlertDialog:
        """构建对话框UI"""
        # 标题信息
        mode_text = "串行" if self.plan.execution_mode.value == "sequential" else "并行"
        mode_icon = ft.Icons.PLAY_ARROW if self.plan.execution_mode.value == "sequential" else ft.Icons.DEVICES
        mode_color = ft.Colors.BLUE if self.plan.execution_mode.value == "sequential" else ft.Colors.GREEN
        
        title_section = ft.Row(
            controls=[
                ft.Icon(mode_icon, color=mode_color, size=28),
                ft.Column(
                    controls=[
                        ft.Text(
                            self.plan.name,
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_900,
                        ),
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Text(mode_text, size=11, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600),
                                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                    bgcolor=mode_color,
                                    border_radius=10,
                                ),
                                ft.Text(f"{len(self.plan.steps)}个步骤", size=12, color=ft.Colors.GREY_600),
                            ],
                            spacing=8,
                        ),
                    ],
                    spacing=4,
                ),
            ],
            spacing=12,
        )
        
        # 步骤列表容器
        self.steps_list = ft.ListView(
            controls=[],
            expand=True,
            spacing=10,
            padding=5,
        )
        
        # 重建步骤列表
        self._rebuild_steps_list()
        
        # 添加步骤按钮
        add_step_btn = ft.FilledButton(
            "添加步骤",
            icon=ft.Icons.ADD_CIRCLE,
            on_click=self._on_add_step,
            style=ft.ButtonStyle(
                padding=ft.padding.symmetric(horizontal=20, vertical=12),
            ),
        )
        
        # 关闭按钮
        close_btn = ft.TextButton(
            "关闭",
            on_click=lambda e: self._close(),
            style=ft.ButtonStyle(
                color=ft.Colors.GREY_700,
            ),
        )
        
        # 构建对话框
        dialog = ft.AlertDialog(
            modal=True,
            title=title_section,
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Container(height=5),
                        self.steps_list,
                        ft.Container(height=10),
                        add_step_btn,
                    ],
                    spacing=0,
                ),
                width=650,
                height=550,
                padding=ft.padding.all(15),
            ),
            actions=[
                close_btn,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=16),
        )
        
        return dialog
    
    def _rebuild_steps_list(self):
        """重建步骤列表"""
        self.steps_list.controls.clear()
        
        if not self.plan.steps:
            # 空状态
            self.steps_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.INBOX, size=56, color=ft.Colors.GREY_300),
                            ft.Text("暂无步骤", size=15, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500),
                            ft.Text("点击“添加步骤”开始配置执行流程", size=12, color=ft.Colors.GREY_500),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    padding=40,
                    alignment=ft.Alignment(0, 0),
                )
            )
        else:
            # 排序步骤
            sorted_steps = sorted(self.plan.steps, key=lambda s: s.order_index)
            
            for idx, step in enumerate(sorted_steps):
                step_card = self._create_step_card(step, idx, len(sorted_steps))
                self.steps_list.controls.append(step_card)
    
    def _create_step_card(self, step: ExecutionStep, index: int, total: int) -> ft.Container:
        """创建步骤卡片"""
        # 上移按钮
        move_up_btn = ft.IconButton(
            icon=ft.Icons.ARROW_UPWARD,
            icon_size=18,
            icon_color=ft.Colors.GREY_700,
            tooltip="上移",
            on_click=lambda e, s=step: self._on_move_step(s, 'up'),
            visible=(index > 0),
        )
        
        # 下移按钮
        move_down_btn = ft.IconButton(
            icon=ft.Icons.ARROW_DOWNWARD,
            icon_size=18,
            icon_color=ft.Colors.GREY_700,
            tooltip="下移",
            on_click=lambda e, s=step: self._on_move_step(s, 'down'),
            visible=(index < total - 1),
        )
        
        # 编辑按钮
        edit_btn = ft.IconButton(
            icon=ft.Icons.EDIT,
            icon_size=18,
            icon_color=ft.Colors.BLUE,
            tooltip="编辑步骤",
            on_click=lambda e, s=step: self._on_edit_step(s),
        )
        
        # 删除按钮
        delete_btn = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_size=18,
            icon_color=ft.Colors.RED,
            tooltip="删除步骤",
            on_click=lambda e, s=step: self._on_delete_step(s),
        )
        
        # 序号徽章
        step_number = ft.Container(
            content=ft.Text(
                str(index + 1),
                size=13,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE,
            ),
            width=28,
            height=28,
            bgcolor=ft.Colors.BLUE,
            border_radius=14,
            alignment=ft.Alignment(0, 0),
        )
        
        # 步骤名称和详情
        step_info = ft.Column(
            controls=[
                ft.Text(
                    step.name,
                    size=14,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.GREY_900,
                ),
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.LINK, size=13, color=ft.Colors.GREY_500),
                        ft.Text(
                            f"{step.request_id[:8]}...",
                            size=11,
                            color=ft.Colors.GREY_600,
                        ),
                        ft.Container(width=10),
                        ft.Icon(ft.Icons.TIMER, size=13, color=ft.Colors.GREY_500),
                        ft.Text(
                            f"{step.timeout}秒",
                            size=11,
                            color=ft.Colors.GREY_600,
                        ),
                        ft.Container(width=10),
                        ft.Icon(ft.Icons.REPLAY, size=13, color=ft.Colors.GREY_500),
                        ft.Text(
                            f"重试{step.retry_count}次",
                            size=11,
                            color=ft.Colors.GREY_600,
                        ),
                    ],
                    spacing=3,
                ),
            ],
            spacing=4,
            expand=True,
        )
        
        return ft.Container(
            content=ft.Row(
                controls=[
                    step_number,
                    step_info,
                    ft.Row(
                        controls=[
                            move_up_btn,
                            move_down_btn,
                            edit_btn,
                            delete_btn,
                        ],
                        spacing=2,
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            border=ft.border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=3,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 1),
            ),
        )
    
    def _on_add_step(self, e):
        """处理添加步骤"""
        self.on_add_step()
    
    def _on_edit_step(self, step: ExecutionStep):
        """处理编辑步骤"""
        self.on_edit_step(step)
    
    def _on_delete_step(self, step: ExecutionStep):
        """处理删除步骤"""
        self.on_delete_step(step)
    
    def _on_move_step(self, step: ExecutionStep, direction: str):
        """处理移动步骤"""
        self.on_move_step(step, direction)
    
    def refresh(self):
        """刷新步骤列表"""
        self._rebuild_steps_list()
        try:
            self.dialog.update()
        except RuntimeError:
            pass
    
    def _close(self):
        """关闭对话框"""
        self.on_close()
    
    def show(self, page: ft.Page):
        """显示对话框"""
        page.overlay.append(self.dialog)
        self.dialog.open = True
        page.update()
    
    def hide(self):
        """隐藏对话框"""
        if hasattr(self.dialog, 'open'):
            self.dialog.open = False
        try:
            self.dialog.page.update()
        except (RuntimeError, AttributeError):
            pass
