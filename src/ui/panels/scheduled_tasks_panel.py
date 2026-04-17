"""定时任务管理面板 - 查看和管理所有定时任务"""

import flet as ft
from typing import Optional, Callable
from datetime import datetime


class ScheduledTasksPanel(ft.Column):
    """
    定时任务管理面板
    
    显示所有已配置的定时任务，支持启用/禁用/删除
    """
    
    def __init__(self, on_back: Optional[Callable] = None):
        """
        初始化面板
        
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
                        ft.Icons.SCHEDULE,
                        size=80,
                        color=ft.Colors.GREY_400,
                    ),
                    ft.Text(
                        "暂无定时任务",
                        size=18,
                        color=ft.Colors.GREY_600,
                        weight=ft.FontWeight.W_500,
                    ),
                    ft.Text(
                        "在计划卡片上点击\"定时配置\"按钮添加定时任务",
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
        
        # 任务列表容器
        self.tasks_container = ft.ListView(
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
                                "定时任务管理",
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
                    
                    # 任务列表容器
                    self.tasks_container,
                ],
                spacing=15,
            ),
            padding=ft.padding.only(left=20, right=20, top=20, bottom=20),
            expand=True,
        )
        
        # 添加主容器到面板
        self.controls = [self.main_container]
    
    def load_tasks(self, scheduled_plans: list):
        """
        加载定时任务列表
        
        Args:
            scheduled_plans: 已调度的计划列表，每个元素包含 'plan' 和 'next_run_time'
        """
        if not scheduled_plans:
            # 显示空状态
            self.empty_state.visible = True
            self.tasks_container.visible = False
        else:
            # 隐藏空状态，显示任务列表
            self.empty_state.visible = False
            self.tasks_container.visible = True
            
            # 清空现有列表
            self.tasks_container.controls.clear()
            
            # 添加任务卡片
            for item in scheduled_plans:
                plan = item['plan']
                next_run_time = item.get('next_run_time')
                card = self._create_task_card(plan, next_run_time)
                self.tasks_container.controls.append(card)
        
        try:
            self.update()
        except RuntimeError:
            pass
    
    def _create_task_card(self, plan, next_run_time) -> ft.Container:
        """
        创建任务卡片
        
        Args:
            plan: 执行计划对象
            next_run_time: 下次执行时间
            
        Returns:
            ft.Container: 任务卡片容器
        """
        # 调度类型图标
        schedule_type_icons = {
            'cron': ft.Icons.CALENDAR_MONTH,
            'interval': ft.Icons.REPEAT,
            'once': ft.Icons.EVENT,
        }
        
        schedule_type_texts = {
            'cron': 'Cron',
            'interval': '间隔',
            'once': '一次性',
        }
        
        schedule_type = plan.schedule.schedule_type.value if plan.schedule else 'unknown'
        icon = schedule_type_icons.get(schedule_type, ft.Icons.HELP)
        type_text = schedule_type_texts.get(schedule_type, '未知')
        
        # 格式化下次执行时间
        if next_run_time:
            next_run_str = next_run_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            next_run_str = "未设置"
        
        # 状态文本和颜色
        is_enabled = plan.schedule and plan.schedule.enabled
        status_text = "已启用" if is_enabled else "已禁用"
        status_color = ft.Colors.GREEN if is_enabled else ft.Colors.GREY
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    # 头部：计划名称和状态
                    ft.Row(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(icon, color=ft.Colors.PURPLE, size=24),
                                    ft.Column(
                                        controls=[
                                            ft.Text(
                                                plan.name,
                                                size=16,
                                                weight=ft.FontWeight.BOLD,
                                            ),
                                            ft.Text(
                                                f"类型: {type_text} • 下次执行: {next_run_str}",
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
                                    status_text,
                                    size=12,
                                    color=ft.Colors.WHITE,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                bgcolor=status_color,
                                border_radius=12,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    
                    ft.Divider(height=5),
                    
                    # 底部：操作按钮
                    ft.Row(
                        controls=[
                            ft.Text(
                                f"步骤数: {len(plan.steps)}",
                                size=12,
                                color=ft.Colors.GREY_700,
                            ),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.Icons.PLAY_ARROW if not is_enabled else ft.Icons.PAUSE,
                                icon_color=ft.Colors.BLUE,
                                tooltip="启用" if not is_enabled else "暂停",
                                on_click=lambda e, p=plan: self._on_toggle_schedule(p, not is_enabled),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                icon_color=ft.Colors.RED,
                                tooltip="删除定时任务",
                                on_click=lambda e, p=plan: self._on_delete_schedule(p),
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
    
    def _on_toggle_schedule(self, plan, enable: bool):
        """切换定时任务状态"""
        try:
            from managers.scheduler_manager import SchedulerManager
            from managers.execution_plan_manager import ExecutionPlanManager
            
            scheduler = SchedulerManager()
            plan_manager = ExecutionPlanManager()
            
            if enable:
                # 启用：添加到调度器
                success = scheduler.add_schedule(plan.id, plan.schedule)
                status_text = "已启用"
            else:
                # 禁用：从调度器移除
                success = scheduler.remove_schedule(plan.id)
                status_text = "已禁用"
            
            if success:
                # 更新数据库中的配置
                plan.schedule.enabled = enable
                plan_manager.update_plan(plan_id=plan.id, schedule=plan.schedule)
                
                # 刷新列表
                scheduled_plans = scheduler.get_scheduled_plans()
                self.load_tasks(scheduled_plans)
                
                print(f"定时任务{status_text}: {plan.name}")
            
        except Exception as e:
            print(f"操作失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_delete_schedule(self, plan):
        """删除定时任务"""
        try:
            from managers.scheduler_manager import SchedulerManager
            from managers.execution_plan_manager import ExecutionPlanManager
            
            scheduler = SchedulerManager()
            plan_manager = ExecutionPlanManager()
            
            # 从调度器移除
            success = scheduler.remove_schedule(plan.id)
            
            if success:
                # 清除数据库中的调度配置
                plan.schedule = None
                plan_manager.update_plan(plan_id=plan.id, schedule=None)
                
                # 刷新列表
                scheduled_plans = scheduler.get_scheduled_plans()
                self.load_tasks(scheduled_plans)
                
                print(f"已删除定时任务: {plan.name}")
            
        except Exception as e:
            print(f"删除失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_back(self, e):
        """处理返回按钮点击"""
        if self.on_back:
            self.on_back()
