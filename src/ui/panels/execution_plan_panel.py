"""执行计划面板 - 显示和管理执行计划"""

import flet as ft
import threading
from typing import Optional, Callable
from services.execution_engine import ExecutionEngine
from managers.request_list_manager import RequestListManager
from ui.dialogs import PlanEditorDialog, StepEditorDialog


class ExecutionPlanPanel(ft.Column):
    """执行计划面板"""
    
    def __init__(self, on_show_monitor: Optional[Callable] = None, page: Optional[ft.Page] = None, 
                 on_show_history: Optional[Callable] = None, on_show_scheduled_tasks: Optional[Callable] = None,
                 on_step_status: Optional[Callable] = None, on_navigate_to_monitor: Optional[Callable] = None):
        super().__init__()
        
        self.spacing = 15
        self.padding = 20
        self.on_show_monitor = on_show_monitor
        self.parent_page = page  # 使用 parent_page 避免与 ft.Control.page 冲突
        self.on_show_history = on_show_history
        self.on_show_scheduled_tasks = on_show_scheduled_tasks
        self.on_step_status_callback = on_step_status  # 步骤状态回调
        self.on_navigate_to_monitor = on_navigate_to_monitor  # 跳转到监控页面的回调
        
        # 管理器
        self.execution_engine = ExecutionEngine()
        self.request_list_manager = RequestListManager()
        
        # 当前执行的计划
        self.current_executing_plan = None
        
        # 构建UI
        self._build_ui()
    
    def _build_ui(self):
        """构建面板UI"""
        # 标题栏
        title_section = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text("执行计划", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
                            ft.Text("管理和自动化执行您的 API 请求流程", size=13, color=ft.Colors.GREY_600),
                        ],
                        spacing=4,
                    ),
                    ft.Container(expand=True),
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.SCHEDULE,
                                tooltip="定时任务",
                                on_click=self._on_view_scheduled_tasks,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.PURPLE_50,
                                    color=ft.Colors.PURPLE_700,
                                ),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.HISTORY,
                                tooltip="查看历史",
                                on_click=self._on_view_history,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.BLUE_50,
                                    color=ft.Colors.BLUE_700,
                                ),
                            ),
                            ft.FilledButton(
                                "新建计划",
                                icon=ft.Icons.ADD,
                                on_click=self._on_create_plan,
                                style=ft.ButtonStyle(
                                    padding=ft.padding.symmetric(horizontal=20, vertical=12),
                                ),
                            ),
                        ],
                        spacing=8,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.only(left=20, right=20, top=20, bottom=20),
        )
        
        # 空状态提示
        self.empty_state = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Icon(ft.Icons.PLAY_CIRCLE_OUTLINE, size=100, color=ft.Colors.GREY_300),
                        padding=30,
                    ),
                    ft.Text("暂无执行计划", size=20, color=ft.Colors.GREY_700, weight=ft.FontWeight.W_600),
                    ft.Text("创建执行计划来自动化您的 API 测试流程", size=14, color=ft.Colors.GREY_500),
                    ft.Container(height=10),
                    ft.FilledButton(
                        "创建第一个计划",
                        icon=ft.Icons.ADD_CIRCLE,
                        on_click=self._on_create_plan,
                        style=ft.ButtonStyle(
                            padding=ft.padding.symmetric(horizontal=24, vertical=14),
                        ),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            padding=80,
            alignment=ft.Alignment(0, 0),
        )
        
        # 计划列表容器
        self.plan_list_container = ft.ListView(
            controls=[],
            spacing=12,
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            expand=True,
        )
        
        self.controls = [title_section, self.empty_state, self.plan_list_container]
    
    def _on_view_history(self, e):
        """查看执行历史"""
        if self.on_show_history:
            self.on_show_history()
    
    def _on_view_scheduled_tasks(self, e):
        """查看定时任务"""
        if self.on_show_scheduled_tasks:
            self.on_show_scheduled_tasks()
    
    def _on_create_plan(self, e):
        """创建计划"""
        if not self.parent_page:
            return
        
        def on_save(name: str, description: str, execution_mode):
            try:
                from managers.execution_plan_manager import ExecutionPlanManager
                manager = ExecutionPlanManager()
                plan = manager.create_plan(name=name, description=description, execution_mode=execution_mode)
                dialog.hide()
                
                plans = manager.get_all_plans()
                self.load_plans(plans)
                
                snack_bar = ft.SnackBar(content=ft.Text(f"计划 '{name}' 创建成功"), duration=2000)
                self.parent_page.overlay.append(snack_bar)
                snack_bar.open = True
                self.parent_page.update()
            except Exception as ex:
                print(f"创建失败: {ex}")
        
        dialog = PlanEditorDialog(on_save=on_save)
        dialog.show(self.parent_page)
    
    def load_plans(self, plans: list):
        """加载计划列表"""
        if not plans:
            self.empty_state.visible = True
            # ListView 始终可见，只是内容为空
            self.plan_list_container.controls.clear()
        else:
            self.empty_state.visible = False
            self.plan_list_container.controls.clear()
            
            for plan in plans:
                card = self._create_plan_card(plan)
                self.plan_list_container.controls.append(card)
        
        try:
            self.update()
        except RuntimeError:
            pass
    
    def _create_plan_card(self, plan) -> ft.Container:
        """创建计划卡片"""
        mode_icon = ft.Icons.PLAY_ARROW if plan.execution_mode.value == "sequential" else ft.Icons.DEVICES
        mode_text = "串行" if plan.execution_mode.value == "sequential" else "并行"
        mode_color = ft.Colors.BLUE if plan.execution_mode.value == "sequential" else ft.Colors.GREEN
        step_count = len(plan.steps)
        
        # 检查是否有定时任务
        has_schedule = plan.schedule and plan.schedule.enabled
        schedule_badge = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.SCHEDULE, size=12, color=ft.Colors.WHITE),
                    ft.Text("定时", size=10, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600),
                ],
                spacing=3,
            ),
            padding=ft.padding.symmetric(horizontal=6, vertical=2),
            bgcolor=ft.Colors.PURPLE,
            border_radius=10,
            visible=has_schedule,
        )
        
        # 执行状态徽章
        status_badge = None
        if plan.last_execution_status:
            if plan.last_execution_status == 'running':
                status_icon = ft.Icons.PLAY_ARROW
                status_color = ft.Colors.BLUE
                status_text = "执行中"
            elif plan.last_execution_status == 'completed':
                status_icon = ft.Icons.CHECK_CIRCLE
                status_color = ft.Colors.GREEN
                status_text = "已完成"
            elif plan.last_execution_status == 'failed':
                status_icon = ft.Icons.ERROR
                status_color = ft.Colors.RED
                status_text = "失败"
            else:
                status_icon = ft.Icons.PENDING
                status_color = ft.Colors.GREY
                status_text = "未执行"
            
            status_badge = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(status_icon, size=12, color=ft.Colors.WHITE),
                        ft.Text(status_text, size=10, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600),
                    ],
                    spacing=3,
                ),
                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                bgcolor=status_color,
                border_radius=10,
            )
        
        # 最后执行时间
        last_exec_text = ""
        if plan.last_execution_time:
            from datetime import datetime
            now = datetime.now()
            diff = now - plan.last_execution_time
            if diff.days > 0:
                last_exec_text = f"最后执行: {diff.days}天前"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                last_exec_text = f"最后执行: {hours}小时前"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                last_exec_text = f"最后执行: {minutes}分钟前"
            else:
                last_exec_text = "最后执行: 刚刚"
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    # 第一行：标题和操作按钮
                    ft.Row(
                        controls=[
                            # 左侧：图标和信息
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        content=ft.Icon(mode_icon, color=mode_color, size=22),
                                        width=45,
                                        height=45,
                                        bgcolor=ft.Colors.with_opacity(0.1, mode_color),
                                        border_radius=10,
                                        alignment=ft.Alignment(0, 0),
                                    ),
                                    ft.Column(
                                        controls=[
                                            ft.Row(
                                                controls=[
                                                    ft.Text(plan.name, size=15, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_900),
                                                    schedule_badge if schedule_badge else ft.Container(width=0),
                                                    status_badge if status_badge else ft.Container(width=0),
                                                ],
                                                spacing=6,
                                            ),
                                            ft.Row(
                                                controls=[
                                                    ft.Container(
                                                        content=ft.Text(mode_text, size=11, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500),
                                                        padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                                        bgcolor=mode_color,
                                                        border_radius=8,
                                                    ),
                                                    ft.Text(f"{step_count}个步骤", size=11, color=ft.Colors.GREY_600),
                                                ],
                                                spacing=6,
                                            ),
                                        ],
                                        spacing=4,
                                        expand=True,
                                    ),
                                ],
                                spacing=12,
                                expand=True,
                            ),
                            
                            # 右侧：操作按钮
                            ft.Row(
                                controls=[
                                    ft.IconButton(
                                        icon=ft.Icons.PLAY_ARROW,
                                        icon_size=18,
                                        icon_color=ft.Colors.GREEN_700,
                                        tooltip="执行计划",
                                        on_click=lambda e, p=plan: self._on_execute_plan(p),
                                        style=ft.ButtonStyle(
                                            bgcolor=ft.Colors.GREEN_50,
                                            padding=6,
                                        ),
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.LIST_ALT,
                                        icon_size=18,
                                        icon_color=ft.Colors.BLUE_700,
                                        tooltip="管理步骤",
                                        on_click=lambda e, p=plan: self._on_view_plan_details(p),
                                        style=ft.ButtonStyle(
                                            bgcolor=ft.Colors.BLUE_50,
                                            padding=6,
                                        ),
                                    ),
                                    ft.PopupMenuButton(
                                        items=[
                                            ft.PopupMenuItem(
                                                content=ft.Text("定时配置"),
                                                icon=ft.Icons.SCHEDULE,
                                                on_click=lambda e, p=plan: self._on_configure_schedule(p),
                                            ),
                                            ft.PopupMenuItem(
                                                content=ft.Text("编辑"),
                                                icon=ft.Icons.EDIT,
                                                on_click=lambda e, p=plan: self._on_edit_plan(p),
                                            ),
                                            ft.PopupMenuItem(
                                                content=ft.Text("删除"),
                                                icon=ft.Icons.DELETE,
                                                on_click=lambda e, p=plan: self._on_delete_plan(p),
                                            ),
                                        ],
                                        icon=ft.Icons.MORE_VERT,
                                        icon_color=ft.Colors.GREY_700,
                                        tooltip="更多操作",
                                        style=ft.ButtonStyle(
                                            bgcolor=ft.Colors.GREY_100,
                                            padding=6,
                                        ),
                                    ),
                                ],
                                spacing=6,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    
                    # 第二行：最后执行时间（如果有）
                    ft.Text(
                        last_exec_text,
                        size=11,
                        color=ft.Colors.GREY_500,
                        visible=bool(last_exec_text),
                    ) if last_exec_text else ft.Container(height=0),
                ],
                spacing=8,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
            ink=True,  # 启用点击效果
            on_click=lambda e, p=plan: self._on_plan_card_click(p),
        )
    
    def _on_plan_card_click(self, plan):
        """处理计划卡片点击事件"""
        print(f"点击计划: {plan.name}")
        # 跳转到监控页面
        if self.on_navigate_to_monitor:
            self.on_navigate_to_monitor(plan)
    
    def _on_execute_plan(self, plan):
        """执行计划"""
        if not plan.steps:
            snack_bar = ft.SnackBar(content=ft.Text("该计划没有步骤"), duration=2000)
            self.parent_page.overlay.append(snack_bar)
            snack_bar.open = True
            self.parent_page.update()
            return
        
        # 更新计划状态为 running
        from datetime import datetime
        plan.last_execution_status = 'running'
        plan.last_execution_time = datetime.now()
        
        # 刷新列表显示
        from managers.execution_plan_manager import ExecutionPlanManager
        manager = ExecutionPlanManager()
        plans = manager.get_all_plans()
        self.load_plans(plans)
        
        self.current_executing_plan = plan
        
        # 立即切换到监控面板并初始化
        if self.on_show_monitor:
            # 传递特殊消息表示开始执行
            self.on_show_monitor(0.0, f"正在启动: {plan.name}")
        
        def on_progress(progress: float, message: str):
            if self.on_show_monitor:
                self.on_show_monitor(progress, message)
        
        def on_step_status(step_index: int, step_name: str, status: str, error: str = None, result: dict = None):
            """步骤状态更新回调"""
            if self.on_step_status_callback:
                try:
                    self.on_step_status_callback(step_index, step_name, status, error, result)
                except Exception as ex:
                    print(f"步骤状态回调失败: {ex}")
        
        self.execution_engine.set_progress_callback(on_progress)
        self.execution_engine.set_step_status_callback(on_step_status)
        
        thread = threading.Thread(target=self._execute_plan_thread, args=(plan,), daemon=True)
        thread.start()
    
    def _execute_plan_thread(self, plan):
        """在线程中执行"""
        try:
            if plan.execution_mode.value == "parallel":
                log = self.execution_engine.execute_plan_parallel(plan)
            else:
                log = self.execution_engine.execute_plan_sequential(plan)
            
            # 更新计划状态
            from datetime import datetime
            plan.last_execution_status = 'completed' if log.failed_steps == 0 else 'failed'
            plan.last_execution_time = datetime.now()
            
            if self.on_show_monitor:
                self.on_show_monitor(1.0, f"执行完成: 成功{log.completed_steps}, 失败{log.failed_steps}")
            
            # 保存执行日志
            from managers.execution_plan_manager import ExecutionPlanManager
            manager = ExecutionPlanManager()
            manager.save_execution_log(log)
            
            # 刷新列表显示
            plans = manager.get_all_plans()
            self.load_plans(plans)
            
        except Exception as e:
            print(f"执行失败: {e}")
            # 更新计划状态为失败
            from datetime import datetime
            plan.last_execution_status = 'failed'
            plan.last_execution_time = datetime.now()
            
            # 刷新列表显示
            from managers.execution_plan_manager import ExecutionPlanManager
            manager = ExecutionPlanManager()
            plans = manager.get_all_plans()
            self.load_plans(plans)
    
    def _on_edit_plan(self, plan):
        """编辑计划"""
        if not self.parent_page:
            return
        
        def on_save(name: str, description: str, execution_mode):
            try:
                from managers.execution_plan_manager import ExecutionPlanManager
                manager = ExecutionPlanManager()
                manager.update_plan(plan_id=plan.id, name=name, description=description, execution_mode=execution_mode)
                dialog.hide()
                
                plans = manager.get_all_plans()
                self.load_plans(plans)
                
                snack_bar = ft.SnackBar(content=ft.Text(f"计划 '{name}' 已更新"), duration=2000)
                self.parent_page.overlay.append(snack_bar)
                snack_bar.open = True
                self.parent_page.update()
            except Exception as ex:
                print(f"更新失败: {ex}")
        
        dialog = PlanEditorDialog(on_save=on_save, plan=plan)
        dialog.show(self.parent_page)
    
    def _on_delete_plan(self, plan):
        """删除计划"""
        if not self.parent_page:
            return
        
        def confirm_delete(e):
            try:
                from managers.execution_plan_manager import ExecutionPlanManager
                manager = ExecutionPlanManager()
                success = manager.delete_plan(plan.id)
                confirm_dialog.open = False
                
                if success:
                    plans = manager.get_all_plans()
                    self.load_plans(plans)
                    
                    snack_bar = ft.SnackBar(content=ft.Text(f"计划 '{plan.name}' 已删除"), duration=2000)
                    self.parent_page.overlay.append(snack_bar)
                    snack_bar.open = True
                
                self.parent_page.update()
            except Exception as ex:
                print(f"删除失败: {ex}")
        
        def cancel_delete(e):
            confirm_dialog.open = False
            self.parent_page.update()
        
        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("确认删除", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Text(f"确定要删除计划 '{plan.name}' 吗？\n此操作不可恢复。"),
            actions=[
                ft.TextButton("取消", on_click=cancel_delete),
                ft.TextButton("删除", on_click=confirm_delete,
                            style=ft.ButtonStyle(bgcolor=ft.Colors.RED, color=ft.Colors.WHITE)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.parent_page.overlay.append(confirm_dialog)
        confirm_dialog.open = True
        self.parent_page.update()
    
    def _on_configure_schedule(self, plan):
        """配置定时执行"""
        if not self.parent_page:
            return
        
        from ui.dialogs import ScheduleConfigDialog
        from managers.scheduler_manager import SchedulerManager
        
        # 获取现有的调度配置
        existing_schedule = plan.schedule
        
        def on_save(schedule_config):
            try:
                # 更新计划中的调度配置
                from managers.execution_plan_manager import ExecutionPlanManager
                plan_manager = ExecutionPlanManager()
                plan_manager.update_plan(plan_id=plan.id, schedule=schedule_config)
                
                # 更新调度管理器
                scheduler = SchedulerManager()
                if schedule_config.enabled:
                    success = scheduler.add_schedule(plan.id, schedule_config)
                else:
                    success = scheduler.remove_schedule(plan.id)
                
                dialog.hide()
                
                if success:
                    status_text = "已启用" if schedule_config.enabled else "已禁用"
                    snack_bar = ft.SnackBar(
                        content=ft.Text(f"定时任务{status_text}"),
                        duration=2000
                    )
                    self.parent_page.overlay.append(snack_bar)
                    snack_bar.open = True
                    self.parent_page.update()
                
                # 刷新列表
                plans = plan_manager.get_all_plans()
                self.load_plans(plans)
                
            except Exception as ex:
                print(f"配置失败: {ex}")
                import traceback
                traceback.print_exc()
        
        dialog = ScheduleConfigDialog(on_save=on_save, schedule=existing_schedule, page=self.parent_page)
        dialog.show(self.parent_page)
    
    def _on_view_plan_details(self, plan):
        """查看计划详情（管理步骤）"""
        if not self.parent_page:
            return
        
        from ui.dialogs import PlanDetailDialog
        from managers.execution_plan_manager import ExecutionPlanManager
        
        # 刷新计划数据以获取最新步骤
        manager = ExecutionPlanManager()
        updated_plan = manager.get_plan(plan.id)
        
        def on_close():
            detail_dialog.hide()
            # 刷新列表
            plans = manager.get_all_plans()
            self.load_plans(plans)
        
        def on_add_step():
            self._show_add_step_dialog(updated_plan, detail_dialog)
        
        def on_edit_step(step):
            self._show_edit_step_dialog(updated_plan, step, detail_dialog)
        
        def on_delete_step(step):
            self._delete_step(updated_plan, step, detail_dialog)
        
        def on_move_step(step, direction):
            self._move_step(updated_plan, step, direction, detail_dialog)
        
        detail_dialog = PlanDetailDialog(
            plan=updated_plan,
            on_close=on_close,
            on_add_step=on_add_step,
            on_edit_step=on_edit_step,
            on_delete_step=on_delete_step,
            on_move_step=on_move_step,
        )
        detail_dialog.show(self.parent_page)
    
    def _show_add_step_dialog(self, plan, detail_dialog):
        """显示添加步骤对话框"""
        from ui.dialogs import StepEditorDialog
        from managers.execution_plan_manager import ExecutionPlanManager
        
        # 获取所有可用的请求
        requests = self.request_list_manager.get_all_requests()
        
        def on_save(request_id: str, name: str, timeout: int, retry_count: int, custom_method: str = None, params_mapping: str = None):
            try:
                manager = ExecutionPlanManager()
                manager.add_step(
                    plan_id=plan.id,
                    request_id=request_id,
                    name=name or f"步骤 {len(plan.steps) + 1}",
                    timeout=timeout,
                    retry_count=retry_count,
                    custom_method=custom_method,
                    params_mapping=params_mapping,
                )
                step_dialog.hide()
                detail_dialog.hide()
                
                # 重新打开详情对话框以刷新
                self._on_view_plan_details(plan)
                
                snack_bar = ft.SnackBar(content=ft.Text("步骤添加成功"), duration=2000)
                self.parent_page.overlay.append(snack_bar)
                snack_bar.open = True
                self.parent_page.update()
            except Exception as ex:
                print(f"添加步骤失败: {ex}")
        
        step_dialog = StepEditorDialog(
            on_save=on_save, 
            available_requests=requests,
            current_plan_steps=plan.steps,  # 传递当前计划的所有步骤
            current_step_index=-1,  # 新建模式，显示所有步骤
        )
        step_dialog.show(self.parent_page)
    
    def _show_edit_step_dialog(self, plan, step, detail_dialog):
        """显示编辑步骤对话框"""
        from ui.dialogs import StepEditorDialog
        from managers.execution_plan_manager import ExecutionPlanManager
        
        requests = self.request_list_manager.get_all_requests()
        
        def on_save(request_id: str, name: str, timeout: int, retry_count: int, custom_method: str = None, params_mapping: str = None):
            try:
                manager = ExecutionPlanManager()
                manager.update_step(
                    step_id=step.id,
                    request_id=request_id,
                    name=name,
                    timeout=timeout,
                    retry_count=retry_count,
                    custom_method=custom_method,
                    params_mapping=params_mapping,
                )
                step_dialog.hide()
                detail_dialog.hide()
                
                # 重新打开详情对话框以刷新
                self._on_view_plan_details(plan)
                
                snack_bar = ft.SnackBar(content=ft.Text("步骤更新成功"), duration=2000)
                self.parent_page.overlay.append(snack_bar)
                snack_bar.open = True
                self.parent_page.update()
            except Exception as ex:
                print(f"更新步骤失败: {ex}")
        
        # 找到当前步骤的索引
        current_step_index = -1
        for idx, s in enumerate(plan.steps):
            if s.id == step.id:
                current_step_index = idx
                break
        
        step_dialog = StepEditorDialog(
            on_save=on_save,
            step=step,
            available_requests=requests,
            current_plan_steps=plan.steps,  # 传递当前计划的所有步骤
            current_step_index=current_step_index,  # 传递当前步骤索引
        )
        step_dialog.show(self.parent_page)
    
    def _delete_step(self, plan, step, detail_dialog):
        """删除步骤"""
        from managers.execution_plan_manager import ExecutionPlanManager
        
        def confirm(e):
            try:
                manager = ExecutionPlanManager()
                manager.delete_step(step.id)
                confirm_dialog.open = False
                detail_dialog.hide()
                
                # 重新打开详情对话框
                self._on_view_plan_details(plan)
                
                snack_bar = ft.SnackBar(content=ft.Text("步骤已删除"), duration=2000)
                self.parent_page.overlay.append(snack_bar)
                snack_bar.open = True
                self.parent_page.update()
            except Exception as ex:
                print(f"删除步骤失败: {ex}")
        
        def cancel(e):
            confirm_dialog.open = False
            self.parent_page.update()
        
        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("确认删除", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Text(f"确定要删除步骤 '{step.name}' 吗？"),
            actions=[
                ft.TextButton("取消", on_click=cancel),
                ft.TextButton("删除", on_click=confirm,
                            style=ft.ButtonStyle(bgcolor=ft.Colors.RED, color=ft.Colors.WHITE)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.parent_page.overlay.append(confirm_dialog)
        confirm_dialog.open = True
        self.parent_page.update()
    
    def _move_step(self, plan, step, direction, detail_dialog):
        """移动步骤"""
        from managers.execution_plan_manager import ExecutionPlanManager
        
        try:
            manager = ExecutionPlanManager()
            success = manager.move_step(step.id, direction)
            
            if success:
                detail_dialog.hide()
                # 重新打开详情对话框
                self._on_view_plan_details(plan)
            else:
                snack_bar = ft.SnackBar(
                    content=ft.Text("无法移动：已经是第一个或最后一个步骤"),
                    duration=2000
                )
                self.parent_page.overlay.append(snack_bar)
                snack_bar.open = True
                self.parent_page.update()
        except Exception as ex:
            print(f"移动步骤失败: {ex}")
