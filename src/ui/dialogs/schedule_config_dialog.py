"""调度配置对话框 - 设置执行计划的定时任务"""

import flet as ft
from datetime import datetime
from typing import Optional, Callable
from models.execution_plan import ScheduleConfig, ScheduleType


class ScheduleConfigDialog:
    """调度配置对话框"""
    
    def __init__(self, on_save: Callable, schedule: Optional[ScheduleConfig] = None, page=None):
        """
        初始化对话框
        
        Args:
            on_save: 保存回调函数，参数为 ScheduleConfig
            schedule: 现有的调度配置（None表示新建）
            page: Flet页面对象，用于显示日期时间选择器
        """
        self.on_save = on_save
        self.schedule = schedule
        self.is_editing = schedule is not None
        self.page = page  # 保存page引用
        
        # 创建日期和时间选择器
        try:
            self.date_picker = ft.DatePicker(
                on_change=self._on_date_changed,
            )
        except AttributeError:
            print("警告: 当前Flet版本不支持DatePicker")
            self.date_picker = None
        
        try:
            self.time_picker = ft.TimePicker(
                on_change=self._on_time_changed,
            )
        except AttributeError:
            print("警告: 当前Flet版本不支持TimePicker")
            self.time_picker = None
        
        # 构建对话框
        self.dialog = self._build_dialog()
    
    def _build_dialog(self) -> ft.AlertDialog:
        """构建对话框UI"""
        # 标题
        title_section = ft.Row(
            controls=[
                ft.Icon(ft.Icons.ALARM, color=ft.Colors.BLUE, size=28),
                ft.Text(
                    "定时执行配置",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_900,
                ),
            ],
            spacing=12,
        )
        
        # 启用开关卡片
        self.enabled_switch = ft.Switch(
            value=self.schedule.enabled if self.is_editing else False,
            label="",
        )
        
        enabled_card = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text("启用定时执行", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_800),
                            ft.Text("开启后，计划将按照设定的时间自动执行", size=12, color=ft.Colors.GREY_600),
                        ],
                        spacing=3,
                        expand=True,
                    ),
                    self.enabled_switch,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.all(15),
            bgcolor=ft.Colors.BLUE_50,
            border_radius=10,
            border=ft.border.all(1, ft.Colors.BLUE_200),
        )
        
        # 调度类型选择
        schedule_type_value = self.schedule.schedule_type.value if self.is_editing else "cron"
        
        type_title = ft.Row(
            controls=[
                ft.Icon(ft.Icons.SCHEDULE, color=ft.Colors.GREY_700, size=18),
                ft.Text("调度类型", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_800),
            ],
            spacing=6,
        )
        
        self.type_dropdown = ft.Dropdown(
            label="选择调度方式",
            hint_text="请选择一种调度方式",
            options=[
                ft.dropdown.Option(key="cron", text="Cron表达式 - 灵活的时间规则"),
                ft.dropdown.Option(key="interval", text="间隔执行 - 固定时间间隔"),
                ft.dropdown.Option(key="once", text="一次性执行 - 指定时间执行一次"),
            ],
            value=schedule_type_value,
            on_select=self._on_type_change,
            border_radius=8,
            width=460,
        )
        
        # Cron表达式输入
        self.cron_help_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.BLUE_700, size=16),
                            ft.Text("Cron 表达式说明", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.BLUE_900),
                        ],
                        spacing=6,
                    ),
                    ft.Text("格式: 分 时 日 月 周", size=11, color=ft.Colors.GREY_700),
                    ft.Text("示例: 0 9 * * * = 每天9点执行", size=11, color=ft.Colors.GREY_600),
                    ft.Text("示例: */30 * * * * = 每30分钟执行", size=11, color=ft.Colors.GREY_600),
                ],
                spacing=4,
            ),
            padding=10,
            bgcolor=ft.Colors.BLUE_50,
            border_radius=8,
            visible=(schedule_type_value == "cron"),
        )
        
        self.cron_field = ft.TextField(
            label="Cron表达式",
            hint_text="例如: 0 9 * * *",
            value=self.schedule.cron_expression if self.is_editing and self.schedule.cron_expression else "",
            visible=(schedule_type_value == "cron"),
            border_radius=8,
            width=460,
        )
        
        # 间隔秒数输入
        self.interval_help_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.GREEN_700, size=16),
                            ft.Text("间隔时间说明", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.GREEN_900),
                        ],
                        spacing=6,
                    ),
                    ft.Text("常用间隔:", size=11, color=ft.Colors.GREY_700),
                    ft.Text("• 60秒 = 1分钟", size=11, color=ft.Colors.GREY_600),
                    ft.Text("• 3600秒 = 1小时", size=11, color=ft.Colors.GREY_600),
                    ft.Text("• 86400秒 = 1天", size=11, color=ft.Colors.GREY_600),
                ],
                spacing=4,
            ),
            padding=10,
            bgcolor=ft.Colors.GREEN_50,
            border_radius=8,
            visible=(schedule_type_value == "interval"),
        )
        
        self.interval_field = ft.TextField(
            label="间隔时间（秒）",
            hint_text="例如: 3600 (每小时)",
            value=str(self.schedule.interval_seconds) if self.is_editing and self.schedule.interval_seconds else "3600",
            keyboard_type=ft.KeyboardType.NUMBER,
            visible=(schedule_type_value == "interval"),
            border_radius=8,
            width=460,
        )
        
        # 开始时间选择
        self.once_help_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.ORANGE_700, size=16),
                            ft.Text("时间格式说明", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.ORANGE_900),
                        ],
                        spacing=6,
                    ),
                    ft.Text("请选择执行的日期和时间", size=11, color=ft.Colors.GREY_700),
                ],
                spacing=4,
            ),
            padding=10,
            bgcolor=ft.Colors.ORANGE_50,
            border_radius=8,
            visible=(schedule_type_value == "once"),
        )
        
        # 日期时间显示字段（只读）
        initial_datetime_str = ""
        if self.is_editing and self.schedule.start_time:
            initial_datetime_str = self.schedule.start_time.strftime("%Y-%m-%d %H:%M:%S")
        
        self.datetime_display = ft.TextField(
            label="执行时间",
            hint_text="请点击右侧按钮选择日期和时间",
            value=initial_datetime_str,
            read_only=True,
            border_radius=8,
            expand=True,  # 自动扩展填充可用空间
        )
        
        # 日期时间选择按钮行
        self.datetime_picker_row = ft.Container(
            content=ft.Row(
                controls=[
                    self.datetime_display,
                    ft.Container(width=8),
                    ft.IconButton(
                        icon=ft.Icons.CALENDAR_TODAY,
                        icon_size=20,
                        tooltip="选择日期",
                        on_click=self._on_pick_date,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.BLUE_50,
                            color=ft.Colors.BLUE,
                            padding=8,
                        ),
                    ),
                    ft.Container(width=5),
                    ft.IconButton(
                        icon=ft.Icons.ACCESS_TIME,
                        icon_size=20,
                        tooltip="选择时间",
                        on_click=self._on_pick_time,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.GREEN_50,
                            color=ft.Colors.GREEN,
                            padding=8,
                        ),
                    ),
                ],
                spacing=0,
            ),
            width=460,  # 固定总宽度
            visible=(schedule_type_value == "once"),
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
            "保存配置",
            on_click=self._on_save,
            icon=ft.Icons.CHECK,
            style=ft.ButtonStyle(
                padding=ft.padding.symmetric(horizontal=20, vertical=12),
            ),
        )
        
        # 构建对话框
        dialog = ft.AlertDialog(
            modal=True,
            title=title_section,
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        enabled_card,
                        ft.Container(height=18),
                        type_title,
                        ft.Container(height=8),
                        self.type_dropdown,
                        ft.Container(height=12),
                        self.cron_help_card,
                        ft.Container(height=8),
                        self.cron_field,
                        self.interval_help_card,
                        ft.Container(height=8),
                        self.interval_field,
                        self.once_help_card,
                        ft.Container(height=8),
                        self.datetime_picker_row,
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
    
    def _on_type_change(self, e):
        """处理类型变更"""
        schedule_type = e.control.value
        
        # 更新字段可见性
        self.cron_field.visible = (schedule_type == "cron")
        self.interval_field.visible = (schedule_type == "interval")
        self.datetime_picker_row.visible = (schedule_type == "once")
        
        # 更新帮助卡片可见性
        self.cron_help_card.visible = (schedule_type == "cron")
        self.interval_help_card.visible = (schedule_type == "interval")
        self.once_help_card.visible = (schedule_type == "once")
        
        try:
            self.dialog.update()
        except RuntimeError:
            pass
    
    def _on_pick_date(self, e):
        """选择日期"""
        if self.page:
            try:
                # 确保日期选择器在页面中
                if self.date_picker not in self.page.overlay:
                    self.page.overlay.append(self.date_picker)
                
                # 打开日期选择器
                self.date_picker.open = True
                self.page.update()
                print("日期选择器已打开")
            except Exception as ex:
                print(f"打开日期选择器失败: {ex}")
                import traceback
                traceback.print_exc()
    
    def _on_date_changed(self, e):
        """日期选择完成"""
        print(f"日期选择器回调触发, value: {e.control.value}, type: {type(e.control.value)}")
        
        if e.control.value:
            selected_date = e.control.value
            
            # DatePicker 返回的是 datetime 对象（UTC时间）
            # 我们需要提取用户选择的日期部分，而不是转换时区
            if hasattr(selected_date, 'year') and hasattr(selected_date, 'month') and hasattr(selected_date, 'day'):
                # 直接提取年、月、日，忽略时间和时区
                year = selected_date.year
                month = selected_date.month
                day = selected_date.day
                date_str = f"{year:04d}-{month:02d}-{day:02d}"
            else:
                #  fallback: 使用 strftime
                date_str = selected_date.strftime('%Y-%m-%d')
            
            print(f"提取的日期: {date_str}")
            
            # 获取当前时间或默认时间
            current_time = "00:00:00"
            if self.datetime_display.value and len(self.datetime_display.value) > 10:
                current_time = self.datetime_display.value[11:]
            
            # 组合日期和时间
            datetime_str = f"{date_str} {current_time}"
            print(f"更新日期时间为: {datetime_str}")
            
            self.datetime_display.value = datetime_str
            self.datetime_display.error_text = None
            
            # 关闭日期选择器
            e.control.open = False
            
            try:
                if self.page:
                    self.page.update()
                
                import time
                time.sleep(0.1)
                
                self.dialog.update()
                print("对话框已更新")
            except (RuntimeError, AttributeError) as ex:
                print(f"更新日期失败: {ex}")
                import traceback
                traceback.print_exc()
        else:
            print("日期选择器返回值为空")
    
    def _on_pick_time(self, e):
        """选择时间"""
        if not self.time_picker:
            print("错误: TimePicker 不可用")
            return
        
        if self.page:
            try:
                # 确保时间选择器在页面中
                if self.time_picker not in self.page.overlay:
                    self.page.overlay.append(self.time_picker)
                
                # 打开时间选择器
                self.time_picker.open = True
                self.page.update()
                print("时间选择器已打开")
            except Exception as ex:
                print(f"打开时间选择器失败: {ex}")
                import traceback
                traceback.print_exc()
    
    def _on_time_changed(self, e):
        """时间选择完成"""
        if e.control.value:
            selected_time = e.control.value
            # 获取当前日期或默认日期
            from datetime import datetime
            current_date = datetime.now().strftime('%Y-%m-%d')
            if self.datetime_display.value and len(self.datetime_display.value) >= 10:
                current_date = self.datetime_display.value[:10]
            
            # 组合日期和时间
            time_str = selected_time.strftime('%H:%M:%S')
            datetime_str = f"{current_date} {time_str}"
            self.datetime_display.value = datetime_str
            self.datetime_display.error_text = None  # 清除错误提示
            
            # 关闭时间选择器
            e.control.open = False
            
            try:
                # 先更新页面（关闭选择器）
                if self.page:
                    self.page.update()
                # 再更新对话框
                self.dialog.update()
            except (RuntimeError, AttributeError) as ex:
                print(f"更新时间失败: {ex}")
    
    def _on_save(self, e):
        """处理保存"""
        enabled = self.enabled_switch.value
        schedule_type = ScheduleType(self.type_dropdown.value)
        
        # 根据类型获取配置
        cron_expression = None
        interval_seconds = None
        start_time = None
        
        if schedule_type == ScheduleType.CRON:
            cron_expression = self.cron_field.value.strip()
            if not cron_expression:
                self.cron_field.error_text = "请输入Cron表达式"
                try:
                    self.dialog.update()
                except RuntimeError:
                    pass
                return
                
        elif schedule_type == ScheduleType.INTERVAL:
            try:
                interval_seconds = int(self.interval_field.value or "3600")
            except ValueError:
                self.interval_field.error_text = "请输入有效的数字"
                try:
                    self.dialog.update()
                except RuntimeError:
                    pass
                return
                
        elif schedule_type == ScheduleType.ONCE:
            time_str = self.datetime_display.value.strip()
            if time_str:
                try:
                    start_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    self.datetime_display.error_text = "时间格式错误，请使用日期时间选择器"
                    try:
                        self.dialog.update()
                    except RuntimeError:
                        pass
                    return
        
        # 创建调度配置
        schedule_config = ScheduleConfig(
            enabled=enabled,
            schedule_type=schedule_type,
            cron_expression=cron_expression,
            interval_seconds=interval_seconds,
            start_time=start_time,
        )
        
        # 调用保存回调
        self.on_save(schedule_config)
    
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
        # 将日期时间选择器添加到页面
        if self.date_picker not in page.overlay:
            page.overlay.append(self.date_picker)
        if self.time_picker not in page.overlay:
            page.overlay.append(self.time_picker)
        
        # 显示对话框
        page.overlay.append(self.dialog)
        self.dialog.open = True
        page.update()
    
    def hide(self):
        """隐藏对话框"""
        if hasattr(self.dialog, 'open'):
            self.dialog.open = False
        
        # 关闭日期时间选择器
        if hasattr(self.date_picker, 'open'):
            self.date_picker.open = False
        if hasattr(self.time_picker, 'open'):
            self.time_picker.open = False
        
        try:
            if self.page:
                self.page.update()
        except (RuntimeError, AttributeError):
            pass
