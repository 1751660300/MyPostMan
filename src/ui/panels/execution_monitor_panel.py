"""执行监控面板 - 实时显示执行进度和结果"""

import flet as ft
from typing import Optional, Callable
from services.execution_engine import ExecutionEngine


class ExecutionMonitorPanel(ft.Column):
    """
    执行监控面板
    
    显示执行计划的实时进度、步骤状态和结果
    """
    
    def __init__(self, on_back: Optional[Callable] = None, on_stop: Optional[Callable] = None):
        """
        初始化执行监控面板
        
        Args:
            on_back: 返回按钮回调函数
            on_stop: 停止执行回调函数
        """
        super().__init__()
        
        self.spacing = 15
        self.padding = 20
        self.on_back = on_back
        self.on_stop_callback = on_stop
        
        # 存储步骤执行结果
        self.step_results = {}
        
        # 构建UI
        self._build_ui()
    
    def _build_ui(self):
        """构建面板UI"""
        # 标题栏
        title_row = ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    tooltip="返回",
                    on_click=self._on_back,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.GREY_100,
                    ),
                ),
                ft.Text(
                    "执行监控",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_900,
                ),
                ft.Container(expand=True),
                ft.FilledButton(
                    "停止",
                    icon=ft.Icons.STOP,
                    on_click=self._on_stop,
                    visible=False,  # 初始隐藏
                    style=ft.ButtonStyle(
                        padding=ft.padding.symmetric(horizontal=16, vertical=10),
                    ),
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
        )
        
        # 进度卡片
        self.progress_text = ft.Text(
            "准备执行...",
            size=13,
            color=ft.Colors.GREY_700,
            weight=ft.FontWeight.W_500,
        )
        
        self.progress_card = ft.Container(
            content=ft.Column(
                controls=[
                    # 进度条
                    ft.ProgressBar(
                        value=0,
                        color=ft.Colors.BLUE,
                        bgcolor=ft.Colors.BLUE_100,
                        height=12,
                        border_radius=6,
                    ),
                    ft.Container(height=8),
                    # 进度文本
                    self.progress_text,
                ],
                spacing=0,
            ),
            padding=ft.padding.all(16),
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
        )
        
        # 步骤列表容器
        self.steps_container = ft.ListView(
            controls=[],
            spacing=10,
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            expand=True,
        )
        
        # 空状态提示
        self.empty_state = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.PLAY_CIRCLE_OUTLINE,
                            size=100,
                            color=ft.Colors.GREY_300,
                        ),
                        padding=30,
                    ),
                    ft.Text(
                        "暂无执行任务",
                        size=20,
                        color=ft.Colors.GREY_700,
                        weight=ft.FontWeight.W_600,
                    ),
                    ft.Text(
                        "从执行计划页面开始一个新的执行",
                        size=14,
                        color=ft.Colors.GREY_500,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            padding=80,
            alignment=ft.Alignment(0, 0),
        )
        
        # 添加所有控件，增加外层容器控制边距
        self.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        title_row,
                        ft.Container(height=15),
                        self.progress_card,
                        ft.Container(height=15),
                        self.empty_state,
                        self.steps_container,
                    ],
                    spacing=0,
                ),
                padding=ft.padding.only(left=20, right=20, top=20),
            ),
        ]
    
    def start_execution(self, plan_name: str, total_steps: int):
        """
        开始执行
        
        Args:
            plan_name: 计划名称
            total_steps: 总步骤数
        """
        # 清空步骤列表
        self.steps_container.controls.clear()
        
        # 隐藏空状态，显示步骤列表
        self.empty_state.visible = False
        self.steps_container.visible = True
        
        # 重置进度
        progress_bar = self.progress_card.content.controls[0]
        progress_bar.value = 0
        self.progress_text.value = f"开始执行: {plan_name} (共{total_steps}个步骤)"
        
        # 初始化所有步骤为等待状态
        for i in range(1, total_steps + 1):
            step_card = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Icon(ft.Icons.PENDING, color=ft.Colors.GREY_400, size=20),
                                    width=36,
                                    height=36,
                                    bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREY_400),
                                    border_radius=8,
                                    alignment=ft.Alignment(0, 0),
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            f"步骤 {i}: 待执行",
                                            size=14,
                                            weight=ft.FontWeight.W_600,
                                            color=ft.Colors.GREY_700,
                                        ),
                                        ft.Text(
                                            "等待执行...",
                                            size=12,
                                            color=ft.Colors.GREY_500,
                                        ),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                            ],
                            spacing=10,
                            expand=True,
                        ),
                        ft.Container(
                            content=ft.Text(
                                "等待中",
                                size=11,
                                color=ft.Colors.WHITE,
                                weight=ft.FontWeight.W_600,
                            ),
                            padding=ft.padding.symmetric(horizontal=10, vertical=4),
                            bgcolor=ft.Colors.GREY_400,
                            border_radius=12,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                padding=ft.padding.symmetric(horizontal=14, vertical=10),
                bgcolor=ft.Colors.GREY_50,
                border_radius=10,
                border=ft.border.all(1.5, ft.Colors.GREY_300),
            )
            self.steps_container.controls.append(step_card)
        
        try:
            self.update()
        except RuntimeError:
            pass
    
    def update_progress(self, progress: float, message: str):
        """
        更新进度
        
        Args:
            progress: 进度值 (0.0 - 1.0)
            message: 进度消息
        """
        # 获取进度条控件（第一个子控件）
        progress_bar = self.progress_card.content.controls[0]
        progress_bar.value = progress
        
        # 更新进度文本
        self.progress_text.value = message
        
        try:
            self.update()
        except RuntimeError:
            pass
    
    def add_step_status(self, step_index: int, step_name: str, status: str, error: str = None, result: dict = None):
        """
        添加或更新步骤状态
        
        Args:
            step_index: 步骤索引（从1开始）
            step_name: 步骤名称
            status: 状态 (running | completed | failed)
            error: 错误信息（可选）
            result: 执行结果数据（可选）
        """
        # 保存步骤结果
        if result:
            self.step_results[step_index] = result
        
        # 根据状态设置图标和颜色
        if status == 'running':
            icon = ft.Icons.PLAY_ARROW
            color = ft.Colors.BLUE
            bg_color = ft.Colors.BLUE_50
            status_text = "执行中..."
        elif status == 'completed':
            icon = ft.Icons.CHECK_CIRCLE
            color = ft.Colors.GREEN
            bg_color = ft.Colors.GREEN_50
            status_text = "成功"
        elif status == 'failed':
            icon = ft.Icons.ERROR
            color = ft.Colors.RED
            bg_color = ft.Colors.RED_50
            status_text = "失败"
        else:
            icon = ft.Icons.PENDING
            color = ft.Colors.GREY
            bg_color = ft.Colors.GREY_50
            status_text = "等待中"
        
        # 检查是否已经存在该步骤的卡片
        card_index = step_index - 1  # 列表索引从0开始
        
        if card_index < len(self.steps_container.controls):
            # 更新现有卡片
            old_card = self.steps_container.controls[card_index]
            
            # 创建新卡片
            new_card = ft.Container(
                content=ft.Row(
                    controls=[
                        # 左侧：图标和状态徽章
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Icon(icon, color=color, size=20),
                                    width=36,
                                    height=36,
                                    bgcolor=ft.Colors.with_opacity(0.2, color),
                                    border_radius=8,
                                    alignment=ft.Alignment(0, 0),
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            f"步骤 {step_index}: {step_name}",
                                            size=14,
                                            weight=ft.FontWeight.W_600,
                                            color=ft.Colors.GREY_900,
                                        ),
                                        ft.Text(
                                            error if error else status_text,
                                            size=12,
                                            color=ft.Colors.GREY_600,
                                        ),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                            ],
                            spacing=10,
                            expand=True,
                        ),
                        
                        # 右侧：状态标签
                        ft.Container(
                            content=ft.Text(
                                status_text,
                                size=11,
                                color=ft.Colors.WHITE,
                                weight=ft.FontWeight.W_600,
                            ),
                            padding=ft.padding.symmetric(horizontal=10, vertical=4),
                            bgcolor=color,
                            border_radius=12,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                padding=ft.padding.symmetric(horizontal=14, vertical=10),
                bgcolor=bg_color,
                border_radius=10,
                border=ft.border.all(1.5, color),
                ink=True,
                on_click=lambda e, idx=step_index, name=step_name, st=status, err=error: self._on_step_click(idx, name, st, err),
            )
            
            # 替换旧卡片
            self.steps_container.controls[card_index] = new_card
        else:
            # 如果不存在，则添加新卡片
            step_card = ft.Container(
                content=ft.Row(
                    controls=[
                        # 左侧：图标和状态徽章
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Icon(icon, color=color, size=20),
                                    width=36,
                                    height=36,
                                    bgcolor=ft.Colors.with_opacity(0.2, color),
                                    border_radius=8,
                                    alignment=ft.Alignment(0, 0),
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            f"步骤 {step_index}: {step_name}",
                                            size=14,
                                            weight=ft.FontWeight.W_600,
                                            color=ft.Colors.GREY_900,
                                        ),
                                        ft.Text(
                                            error if error else status_text,
                                            size=12,
                                            color=ft.Colors.GREY_600,
                                        ),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                            ],
                            spacing=10,
                            expand=True,
                        ),
                        
                        # 右侧：状态标签
                        ft.Container(
                            content=ft.Text(
                                status_text,
                                size=11,
                                color=ft.Colors.WHITE,
                                weight=ft.FontWeight.W_600,
                            ),
                            padding=ft.padding.symmetric(horizontal=10, vertical=4),
                            bgcolor=color,
                            border_radius=12,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                padding=ft.padding.symmetric(horizontal=14, vertical=10),
                bgcolor=bg_color,
                border_radius=10,
                border=ft.border.all(1.5, color),
                ink=True,
                on_click=lambda e, idx=step_index, name=step_name, st=status, err=error: self._on_step_click(idx, name, st, err),
            )
            
            self.steps_container.controls.append(step_card)
        
        try:
            self.update()
        except RuntimeError:
            pass
    
    def _on_step_click(self, step_index: int, step_name: str, status: str, error: str = None):
        """处理步骤点击事件"""
        print(f"点击步骤 {step_index}: {step_name} - 状态: {status}")
        
        # 获取步骤结果
        result = self.step_results.get(step_index, {})
        
        if not result and status != 'running':
            # 如果没有结果且不是执行中，显示简单提示
            snack_bar = ft.SnackBar(
                content=ft.Text(f"步骤 {step_index} 暂无详细数据"),
                duration=2000
            )
            try:
                self.page.overlay.append(snack_bar)
                snack_bar.open = True
                self.page.update()
            except:
                pass
            return
        
        # 创建详情对话框
        dialog = self._create_step_detail_dialog(step_index, step_name, status, error, result)
        
        try:
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()
        except Exception as e:
            print(f"显示对话框失败: {e}")
    
    def _create_step_detail_dialog(self, step_index: int, step_name: str, status: str, error: str, result: dict) -> ft.AlertDialog:
        """创建步骤详情对话框"""
        import json
        
        # 标题
        title_row = ft.Row(
            controls=[
                ft.Icon(
                    ft.Icons.CHECK_CIRCLE if status == 'completed' else ft.Icons.ERROR if status == 'failed' else ft.Icons.PLAY_ARROW,
                    color=ft.Colors.GREEN if status == 'completed' else ft.Colors.RED if status == 'failed' else ft.Colors.BLUE,
                    size=24
                ),
                ft.Text(
                    f"步骤 {step_index}: {step_name}",
                    size=18,
                    weight=ft.FontWeight.BOLD
                ),
            ],
            spacing=10,
        )
        
        # 构建内容
        content_controls = []
        
        # 1. 请求信息
        if 'request' in result:
            request = result['request']
            request_section = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("📤 请求信息", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.BLUE_700),
                        ft.Divider(height=5),
                        ft.Text(f"方法: {request.get('method', 'N/A')}", size=12, color=ft.Colors.GREY_800),
                        ft.Text(f"URL: {request.get('url', 'N/A')}", size=12, color=ft.Colors.GREY_800, selectable=True),
                    ] + (
                        [ft.Text(f"Headers: {json.dumps(request.get('headers', {}), indent=2, ensure_ascii=False)}", 
                                size=11, color=ft.Colors.GREY_700, selectable=True)]
                        if request.get('headers') else []
                    ) + (
                        [ft.Text(f"Params: {json.dumps(request.get('params', {}), indent=2, ensure_ascii=False)}", 
                                size=11, color=ft.Colors.GREY_700, selectable=True)]
                        if request.get('params') else []
                    ),
                    spacing=6,
                ),
                padding=10,
                bgcolor=ft.Colors.BLUE_50,
                border_radius=8,
            )
            content_controls.append(request_section)
            content_controls.append(ft.Container(height=10))
        
        # 2. 响应信息
        if 'status_code' in result or 'data' in result:
            response_items = []
            
            if 'status_code' in result and result['status_code'] is not None:
                status_color = ft.Colors.GREEN if result['status_code'] < 400 else ft.Colors.RED
                response_items.append(
                    ft.Row([
                        ft.Text("状态码:", size=12, weight=ft.FontWeight.W_600),
                        ft.Container(
                            content=ft.Text(str(result['status_code']), size=12, color=ft.Colors.WHITE),
                            padding=ft.padding.symmetric(horizontal=8, vertical=3),
                            bgcolor=status_color,
                            border_radius=5,
                        ),
                    ], spacing=8)
                )
            
            if 'execution_time' in result:
                response_items.append(
                    ft.Text(f"耗时: {result['execution_time']:.2f}ms", size=12, color=ft.Colors.GREY_700)
                )
            
            if 'data' in result:
                data_str = result['data']
                # 尝试格式化 JSON
                try:
                    if isinstance(data_str, str):
                        parsed = json.loads(data_str)
                        data_str = json.dumps(parsed, indent=2, ensure_ascii=False)
                except:
                    pass
                
                response_items.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text("响应数据:", size=12, weight=ft.FontWeight.W_600),
                            ft.Container(
                                content=ft.Text(data_str, size=11, color=ft.Colors.GREY_800, selectable=True),
                                padding=8,
                                bgcolor=ft.Colors.WHITE,
                                border_radius=5,
                            ),
                        ], spacing=5),
                        width=500,
                    )
                )
            
            response_section = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("📥 响应信息", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.GREEN_700),
                        ft.Divider(height=5),
                    ] + response_items,
                    spacing=6,
                ),
                padding=10,
                bgcolor=ft.Colors.GREEN_50,
                border_radius=8,
            )
            content_controls.append(response_section)
            content_controls.append(ft.Container(height=10))
        
        # 3. 脚本输出
        if 'script_output' in result:
            script_section = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("⚙️ 脚本执行结果", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.PURPLE_700),
                        ft.Divider(height=5),
                        ft.Container(
                            content=ft.Text(
                                str(result['script_output']),
                                size=11,
                                color=ft.Colors.GREY_800,
                                selectable=True
                            ),
                            padding=8,
                            bgcolor=ft.Colors.WHITE,
                            border_radius=5,
                        ),
                    ],
                    spacing=6,
                ),
                padding=10,
                bgcolor=ft.Colors.PURPLE_50,
                border_radius=8,
            )
            content_controls.append(script_section)
            content_controls.append(ft.Container(height=10))
        
        # 4. 错误信息
        if error or (result.get('error') and result.get('success') == False):
            error_msg = error or result.get('error', '未知错误')
            error_section = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("❌ 错误信息", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.RED_700),
                        ft.Divider(height=5),
                        ft.Text(error_msg, size=12, color=ft.Colors.RED_900, selectable=True),
                    ],
                    spacing=6,
                ),
                padding=10,
                bgcolor=ft.Colors.RED_50,
                border_radius=8,
            )
            content_controls.append(error_section)
        
        # 如果没有内容，显示提示
        if not content_controls:
            content_controls.append(
                ft.Text("暂无详细信息", size=14, color=ft.Colors.GREY_600)
            )
        
        # 关闭按钮
        close_btn = ft.FilledButton(
            "关闭",
            icon=ft.Icons.CLOSE,
            on_click=lambda e: self._close_detail_dialog(e, dialog),
        )
        
        # 创建对话框
        dialog = ft.AlertDialog(
            modal=True,
            title=title_row,
            content=ft.Container(
                content=ft.Column(
                    controls=content_controls,
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=600,
                height=500,
            ),
            actions=[close_btn],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        return dialog
    
    def _close_detail_dialog(self, e, dialog):
        """关闭详情对话框"""
        dialog.open = False
        try:
            self.page.update()
        except:
            pass
    
    def complete_execution(self, success_count: int, failed_count: int, duration: float):
        """
        执行完成
        
        Args:
            success_count: 成功步骤数
            failed_count: 失败步骤数
            duration: 执行时长（秒）
        """
        progress_bar = self.progress_card.content.controls[0]
        progress_bar.value = 1.0
        self.progress_text.value = (
            f"执行完成! 成功: {success_count}, 失败: {failed_count}, "
            f"耗时: {duration:.2f}秒"
        )
        
        try:
            self.update()
        except RuntimeError:
            pass
    
    def _on_stop(self, e):
        """处理停止按钮点击"""
        print("停止执行")
        # 调用停止回调
        if self.on_stop_callback:
            self.on_stop_callback()
        
        # 更新UI
        self.progress_text.value = "正在停止..."
        try:
            self.update()
        except RuntimeError:
            pass
    
    def _on_back(self, e):
        """处理返回按钮点击"""
        if self.on_back:
            self.on_back()
