"""执行计划编辑对话框 - 创建和编辑执行计划"""

import flet as ft
from typing import Optional, Callable
from models.execution_plan import ExecutionPlan, ExecutionMode


class PlanEditorDialog:
    """执行计划编辑对话框"""
    
    def __init__(self, on_save: Callable, plan: Optional[ExecutionPlan] = None):
        """
        初始化对话框
        
        Args:
            on_save: 保存回调函数，参数为 (name, description, execution_mode)
            plan: 要编辑的计划（None表示新建）
        """
        self.on_save = on_save
        self.plan = plan
        self.is_editing = plan is not None
        
        # 构建对话框
        self.dialog = self._build_dialog()
    
    def _build_dialog(self) -> ft.AlertDialog:
        """构建对话框UI"""
        # 名称输入
        self.name_field = ft.TextField(
            label="计划名称 *",
            hint_text="例如：API自动化测试流程",
            value=self.plan.name if self.is_editing else "",
            autofocus=True,
            prefix_icon=ft.Icons.LABEL,
            border_radius=8,
            width=460,  # 与内容区域宽度一致（500 - 20*2）
        )
        
        # 描述输入
        self.description_field = ft.TextField(
            label="描述（可选）",
            hint_text="简要说明此计划的用途...",
            value=self.plan.description if self.is_editing else "",
            multiline=True,
            min_lines=2,
            max_lines=4,
            prefix_icon=ft.Icons.DESCRIPTION,
            border_radius=8,
            width=460,  # 与内容区域宽度一致
        )
        
        # 执行模式标题
        mode_title = ft.Row(
            controls=[
                ft.Icon(ft.Icons.SETTINGS, color=ft.Colors.BLUE, size=20),
                ft.Text("执行模式", size=16, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_800),
            ],
            spacing=8,
        )
        
        # 执行模式选择
        self.mode_segmented = ft.SegmentedButton(
            selected=[self.plan.execution_mode.value if self.is_editing else "sequential"],
            segments=[
                ft.Segment(
                    value="sequential",
                    label=ft.Text("串行", weight=ft.FontWeight.W_500),
                    icon=ft.Icons.PLAY_ARROW,
                    tooltip="按顺序依次执行每个步骤",
                ),
                ft.Segment(
                    value="parallel",
                    label=ft.Text("并行", weight=ft.FontWeight.W_500),
                    icon=ft.Icons.DEVICES,
                    tooltip="同时执行所有步骤",
                ),
            ],
            on_change=self._on_mode_change,
        )
        
        # 执行模式说明卡片
        self.mode_description_card = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.INFO_OUTLINE,
                        color=ft.Colors.BLUE_700,
                        size=18,
                    ),
                    ft.Text(
                        "串行模式：按顺序执行，每步可使用上一步的结果",
                        size=13,
                        color=ft.Colors.GREY_700,
                    ),
                ],
                spacing=10,
            ),
            padding=12,
            bgcolor=ft.Colors.BLUE_50,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.BLUE_200),
        )
        
        # 取消按钮
        cancel_btn = ft.TextButton(
            "取消",
            on_click=self._on_cancel,
            style=ft.ButtonStyle(
                color=ft.Colors.GREY_700,
            ),
        )
        
        # 保存按钮
        save_btn = ft.FilledButton(
            "保存" if self.is_editing else "创建计划",
            on_click=self._on_save,
            icon=ft.Icons.CHECK,
            style=ft.ButtonStyle(
                padding=ft.padding.symmetric(horizontal=20, vertical=12),
            ),
        )
        
        # 构建对话框
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.ADD_TASK if not self.is_editing else ft.Icons.EDIT_NOTE,
                        color=ft.Colors.BLUE,
                        size=28,
                    ),
                    ft.Text(
                        "新建执行计划" if not self.is_editing else "编辑执行计划",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREY_900,
                    ),
                ],
                spacing=12,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        self.name_field,
                        ft.Container(height=12),
                        self.description_field,
                        ft.Container(height=20),
                        mode_title,
                        ft.Container(height=8),
                        self.mode_segmented,
                        ft.Container(height=10),
                        self.mode_description_card,
                    ],
                    tight=True,
                    spacing=0,
                ),
                width=500,
                padding=ft.padding.all(20),
            ),
            actions=[
                cancel_btn,
                ft.Container(width=10),
                save_btn,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=16),
        )
        
        return dialog
    
    def _on_mode_change(self, e):
        """处理执行模式变更"""
        mode = e.control.selected[0] if e.control.selected else "sequential"
        
        # 更新说明卡片
        if mode == "sequential":
            self.mode_description_card.content = ft.Row(
                controls=[
                    ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.BLUE_700, size=18),
                    ft.Text(
                        "串行模式：按顺序执行，每步可使用上一步的结果",
                        size=13,
                        color=ft.Colors.GREY_700,
                    ),
                ],
                spacing=10,
            )
            self.mode_description_card.bgcolor = ft.Colors.BLUE_50
            self.mode_description_card.border = ft.border.all(1, ft.Colors.BLUE_200)
        else:
            self.mode_description_card.content = ft.Row(
                controls=[
                    ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.GREEN_700, size=18),
                    ft.Text(
                        "并行模式：同时执行所有步骤，适合独立请求",
                        size=13,
                        color=ft.Colors.GREY_700,
                    ),
                ],
                spacing=10,
            )
            self.mode_description_card.bgcolor = ft.Colors.GREEN_50
            self.mode_description_card.border = ft.border.all(1, ft.Colors.GREEN_200)
        
        try:
            self.dialog.update()
        except RuntimeError:
            pass
    
    def _on_save(self, e):
        """处理保存"""
        name = self.name_field.value.strip()
        if not name:
            self.name_field.error_text = "请输入计划名称"
            try:
                self.dialog.update()
            except RuntimeError:
                pass
            return
        
        description = self.description_field.value.strip()
        mode_value = self.mode_segmented.selected[0] if self.mode_segmented.selected else "sequential"
        execution_mode = ExecutionMode(mode_value)
        
        # 调用保存回调
        self.on_save(name, description, execution_mode)
    
    def _on_cancel(self, e):
        """处理取消"""
        if hasattr(self.dialog, 'open'):
            self.dialog.open = False
        try:
            self.dialog.page.update()
        except (RuntimeError, AttributeError):
            pass
    
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
