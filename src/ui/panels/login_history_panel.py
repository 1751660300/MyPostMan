"""
登录录制历史面板 - 显示和管理已录制的认证信息（数据库版本）
"""
import flet as ft
from typing import Callable, Optional
from services.recording_history_service import RecordingHistoryService
from models.models import RecordingHistory


class LoginHistoryPanel(ft.Container):
    """登录录制历史面板
    
    显示所有已录制的认证信息，支持查看、删除、编辑脚本和重新使用
    """
    
    def __init__(self):
        super().__init__()
        self.service = RecordingHistoryService()
        self.history_data: list[RecordingHistory] = []
        self.page_size = 20
        self.current_page = 0
        self._page = None  # 初始化 _page
        
        self._build_ui()
        # 不在 __init__ 中加载数据，等待 show() 调用
    
    def show(self, page):
        """显示面板"""
        self._page = page
        # 每次显示时重新加载数据
        self._load_history()
    
    def _build_ui(self):
        """构建UI"""
        # 标题栏
        title_row = ft.Row([
            ft.Text("📋 登录录制历史", size=20, weight=ft.FontWeight.BOLD),
        ], alignment=ft.MainAxisAlignment.START)
        
        # 历史记录列表
        self.history_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=10,
        )
        
        # 分页控制
        self.page_text = ft.Text("第 1 页", size=13)  # 保存引用
        self.pagination = ft.Row([
            ft.IconButton(
                icon=ft.Icons.FIRST_PAGE,
                tooltip="第一页",
                on_click=self._on_first_page,
            ),
            ft.IconButton(
                icon=ft.Icons.CHEVRON_LEFT,
                tooltip="上一页",
                on_click=self._on_prev_page,
            ),
            self.page_text,  # 使用保存的引用
            ft.IconButton(
                icon=ft.Icons.CHEVRON_RIGHT,
                tooltip="下一页",
                on_click=self._on_next_page,
            ),
            ft.IconButton(
                icon=ft.Icons.LAST_PAGE,
                tooltip="最后一页",
                on_click=self._on_last_page,
            ),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=5)
        
        # 空状态提示
        self.empty_hint = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.VIDEOCAM_OFF, size=64, color=ft.Colors.GREY_400),
                ft.Text("暂无录制记录", size=16, color=ft.Colors.GREY_600),
                ft.Text("使用登录录制功能捕获认证信息", size=13, color=ft.Colors.GREY_500),
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10),
            padding=40,
            visible=False,
        )
        
        # 主内容
        self.content = ft.Column([
            title_row,
            ft.Divider(),
            ft.Container(
                content=self.history_list,
                expand=True,
            ),
            self.pagination,
            self.empty_hint,
        ], expand=True)
        
        self.padding = 20
        self.expand = True
    
    def _load_history(self):
        """加载历史记录"""
        try:
            offset = self.current_page * self.page_size
            self.history_data = self.service.get_all_records(limit=self.page_size, offset=offset)
            total_count = self.service.get_total_count()
            total_pages = (total_count + self.page_size - 1) // self.page_size
            
            print(f"✅ 加载了 {len(self.history_data)} 条录制记录（第 {self.current_page + 1}/{total_pages} 页）")
            self._render_history()
            self._update_pagination(total_pages)
        except Exception as e:
            print(f"❌ 加载历史记录失败: {e}")
            import traceback
            traceback.print_exc()
            self._show_empty()
    
    def _render_history(self):
        """渲染历史记录列表"""
        self.history_list.controls.clear()
        
        if not self.history_data:
            self._show_empty()
            return
        
        self.empty_hint.visible = False
        self.pagination.visible = True
        
        for record in self.history_data:
            card = self._create_history_card(record)
            self.history_list.controls.append(card)
        
        if self._page:
            try:
                self._page.update()
            except RuntimeError:
                pass
    
    def _create_history_card(self, record: RecordingHistory) -> ft.Container:
        """创建历史记录卡片"""
        # 图标和颜色
        icon = ft.Icons.KEY
        icon_color = ft.Colors.BLUE
        type_text = "自定义"
        
        # 保存位置文本
        if record.save_location == 'environment':
            location_text = "环境变量"
            location_color = ft.Colors.GREEN
        else:
            location_text = "全局变量"
            location_color = ft.Colors.PURPLE
        
        # 是否有脚本
        has_script = bool(record.script_file or record.script_content)
        print(f"🔍 检查记录 {record.id}:")
        print(f"   - script_file: {record.script_file}")
        print(f"   - script_content 长度: {len(record.script_content) if record.script_content else 0}")
        print(f"   - has_script: {has_script}")
        
        if has_script:
            # 使用 Container 包裹 Text 作为徽章
            script_badge = ft.Container(
                content=ft.Text("有脚本", size=9, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.GREEN_400,
                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                border_radius=4,
            )
            edit_tooltip = "编辑脚本"
            edit_enabled = True
        else:
            script_badge = None
            edit_tooltip = "此记录没有关联的脚本"
            edit_enabled = False
        
        # 构建头部左侧内容
        left_controls = [
            ft.Icon(icon, size=20, color=icon_color),
            ft.Text(record.variable_name if record.variable_name else type_text, weight=ft.FontWeight.W_500, size=14),
        ]
        if script_badge:
            left_controls.append(script_badge)
        
        card = ft.Container(
            content=ft.Column([
                # 头部：类型和操作按钮
                ft.Row([
                    ft.Row(left_controls, spacing=5),
                    ft.Row([
                        ft.Text(record.created_at, size=11, color=ft.Colors.GREY_500),
                        ft.IconButton(
                            icon=ft.Icons.EDIT_NOTE,
                            icon_size=18,
                            icon_color=ft.Colors.ORANGE_400,
                            tooltip="重命名",
                            on_click=lambda e, r=record: self._on_rename_record(r),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.PLAY_ARROW,
                            icon_size=18,
                            icon_color=ft.Colors.GREEN_600 if edit_enabled else ft.Colors.GREY_400,
                            tooltip="执行自动化脚本" if edit_enabled else "没有关联的脚本",
                            disabled=not edit_enabled,
                            on_click=lambda e, r=record: self._on_execute_script(r) if edit_enabled else None,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.EDIT,
                            icon_size=18,
                            icon_color=ft.Colors.BLUE_400 if edit_enabled else ft.Colors.GREY_400,
                            tooltip=edit_tooltip,
                            disabled=not edit_enabled,
                            on_click=lambda e, r=record: self._on_edit_script(r) if edit_enabled else None,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_size=18,
                            icon_color=ft.Colors.RED_400,
                            tooltip="删除此记录",
                            on_click=lambda e, r=record: self._on_delete_record(r),
                        ),
                    ], spacing=5),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Divider(height=5),
                
                # URL
                ft.Row([
                    ft.Icon(ft.Icons.LINK, size=14, color=ft.Colors.GREY_600),
                    ft.Text(record.url, size=12, color=ft.Colors.GREY_700, selectable=True),
                ], spacing=5),
                
                # 变量名
                ft.Row([
                    ft.Icon(ft.Icons.LABEL, size=14, color=ft.Colors.GREY_600),
                    ft.Text(f"变量名: {record.variable_name}", size=12, weight=ft.FontWeight.W_500),
                ], spacing=5),
                
                # 字段数量
                ft.Row([
                    ft.Icon(ft.Icons.DATA_USAGE, size=14, color=ft.Colors.GREY_600),
                    ft.Text(f"字段数: {record.fields_count}", size=12),
                ], spacing=5),
                
                # 保存位置
                ft.Row([
                    ft.Icon(ft.Icons.STORAGE, size=14, color=ft.Colors.GREY_600),
                    ft.Text(f"保存到: {location_text}", size=12, color=location_color),
                ], spacing=5),
                
                # 值预览
                ft.Container(
                    content=ft.Text(record.value, size=11, color=ft.Colors.GREY_600, selectable=True),
                    padding=8,
                    bgcolor=ft.Colors.GREY_100,
                    border_radius=4,
                ),
            ], spacing=8),
            padding=12,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=5,
                color=ft.Colors.BLACK12,
            ),
        )
        
        return card
    
    def _on_rename_record(self, record: RecordingHistory):
        """重命名记录"""
        if not self._page:
            return
        
        # 创建输入框
        name_field = ft.TextField(
            label="记录名称",
            value=record.variable_name,
            hint_text="请输入新的名称",
            width=400,
        )
        
        def on_confirm(e):
            """确认重命名"""
            new_name = name_field.value.strip()
            
            if not new_name:
                snack_bar = ft.SnackBar(
                    content=ft.Text("❌ 名称不能为空"),
                    duration=2000,
                    bgcolor=ft.Colors.RED,
                )
                self._page.overlay.append(snack_bar)
                snack_bar.open = True
                self._page.update()
                return
            
            # 更新数据库
            from models.database import DatabaseManager, RecordingHistoryModel
            session = self.service.db_manager.get_session()
            try:
                db_record = session.query(RecordingHistoryModel)\
                    .filter(RecordingHistoryModel.id == record.id)\
                    .first()
                
                if db_record:
                    db_record.variable_name = new_name
                    session.commit()
                    
                    dialog.open = False
                    self._page.update()
                    
                    # 重新加载列表
                    self._load_history()
                    
                    snack_bar = ft.SnackBar(
                        content=ft.Text(f"✅ 已重命名为: {new_name}"),
                        duration=2000,
                        bgcolor=ft.Colors.GREEN,
                    )
                    self._page.overlay.append(snack_bar)
                    snack_bar.open = True
                    self._page.update()
                else:
                    dialog.open = False
                    self._page.update()
                    
                    snack_bar = ft.SnackBar(
                        content=ft.Text("❌ 记录不存在"),
                        duration=2000,
                        bgcolor=ft.Colors.RED,
                    )
                    self._page.overlay.append(snack_bar)
                    snack_bar.open = True
                    self._page.update()
            except Exception as ex:
                session.rollback()
                dialog.open = False
                self._page.update()
                
                snack_bar = ft.SnackBar(
                    content=ft.Text(f"❌ 重命名失败: {ex}"),
                    duration=2000,
                    bgcolor=ft.Colors.RED,
                )
                self._page.overlay.append(snack_bar)
                snack_bar.open = True
                self._page.update()
            finally:
                session.close()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("✏️ 重命名记录"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("修改此录制记录的名称", size=13, color=ft.Colors.GREY_600),
                    ft.Divider(),
                    name_field,
                ], tight=True, spacing=10),
                width=450,
                padding=10,
            ),
            actions=[
                ft.TextButton("取消", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.Button("💾 保存", on_click=on_confirm),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()
    
    def _on_edit_script(self, record: RecordingHistory):
        """编辑脚本"""
        if not self._page:
            return
        
        # 调试信息
        print(f"🔍 检查脚本关联:")
        print(f"   - script_file: {record.script_file}")
        print(f"   - script_content 长度: {len(record.script_content) if record.script_content else 0}")
        
        if not record.script_content and not record.script_file:
            snack_bar = ft.SnackBar(
                content=ft.Text("⚠️ 此记录没有关联的脚本\n\n可能是旧数据或录制时未生成脚本"),
                duration=3000,
                bgcolor=ft.Colors.ORANGE,
            )
            self._page.overlay.append(snack_bar)
            snack_bar.open = True
            self._page.update()
            return
        
        # 读取脚本内容
        script_content = record.script_content
        if not script_content and record.script_file:
            print(f"📄 从文件读取脚本: {record.script_file}")
            try:
                with open(record.script_file, 'r', encoding='utf-8') as f:
                    script_content = f.read()
                print(f"✅ 成功读取脚本，长度: {len(script_content)}")
            except FileNotFoundError:
                snack_bar = ft.SnackBar(
                    content=ft.Text(f"❌ 脚本文件不存在\n{record.script_file}"),
                    duration=3000,
                    bgcolor=ft.Colors.RED,
                )
                self._page.overlay.append(snack_bar)
                snack_bar.open = True
                self._page.update()
                return
            except Exception as e:
                snack_bar = ft.SnackBar(
                    content=ft.Text(f"❌ 读取脚本失败: {e}"),
                    duration=3000,
                    bgcolor=ft.Colors.RED,
                )
                self._page.overlay.append(snack_bar)
                snack_bar.open = True
                self._page.update()
                return
        
        # 创建脚本编辑器对话框
        script_field = ft.TextField(
            value=script_content,
            multiline=True,
            min_lines=20,
            max_lines=25,
            text_size=13,
            text_style=ft.TextStyle(font_family="Consolas", size=13),
            bgcolor=ft.Colors.GREY_900,
            color=ft.Colors.GREEN_300,
            cursor_color=ft.Colors.GREEN_300,
            selection_color=ft.Colors.with_opacity(0.3, ft.Colors.GREEN),
            width=800,
            height=500,
            border_radius=8,
            border_color=ft.Colors.GREY_700,
            focused_border_color=ft.Colors.BLUE_400,
            focused_border_width=2,
        )
        
        def on_save(e):
            """保存脚本"""
            new_content = script_field.value
            
            # 更新数据库
            success = self.service.update_script_content(record.id, new_content)
            
            # 如果有关联的文件，也更新文件
            if success and record.script_file:
                try:
                    with open(record.script_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                except Exception as ex:
                    print(f"⚠️ 保存脚本文件失败: {ex}")
            
            dialog.open = False
            self._page.update()
            
            snack_bar = ft.SnackBar(
                content=ft.Text("✅ 脚本已保存"),
                duration=2000,
                bgcolor=ft.Colors.GREEN,
            )
            self._page.overlay.append(snack_bar)
            snack_bar.open = True
            self._page.update()
        
        # 标题区域
        title_section = ft.Row([
            ft.Icon(ft.Icons.CODE, color=ft.Colors.BLUE, size=24),
            ft.Column([
                ft.Text(
                    f"编辑脚本 - {record.variable_name}",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_900,
                ),
                ft.Text(
                    "Playwright Python 自动化脚本",
                    size=12,
                    color=ft.Colors.GREY_600,
                ),
            ], spacing=2),
        ], spacing=12)
        
        # 提示信息卡片
        hint_card = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.BLUE_700, size=16),
                ft.Text(
                    "💡 提示：支持语法高亮、自动缩进。使用 Tab 键缩进，Shift+Tab 取消缩进",
                    size=12,
                    color=ft.Colors.GREY_700,
                ),
            ], spacing=8),
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            bgcolor=ft.Colors.BLUE_50,
            border_radius=6,
            border=ft.border.all(1, ft.Colors.BLUE_200),
        )
        
        # 取消按钮
        cancel_btn = ft.TextButton(
            "取消",
            on_click=lambda e: setattr(dialog, 'open', False),
            style=ft.ButtonStyle(
                color=ft.Colors.GREY_700,
            ),
        )
        
        # 保存按钮
        save_btn = ft.Button(
            "保存",
            icon=ft.Icons.SAVE,
            on_click=on_save,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_600,
                color=ft.Colors.WHITE,
                padding=ft.padding.symmetric(horizontal=20, vertical=10),
            ),
        )
        
        dialog = ft.AlertDialog(
            modal=True,
            title=title_section,
            content=ft.Container(
                content=ft.Column([
                    hint_card,
                    ft.Container(height=8),
                    script_field,
                ], tight=False, spacing=8, scroll=ft.ScrollMode.AUTO),
                width=850,
                height=600,
                padding=12,
            ),
            actions=[
                cancel_btn,
                save_btn,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()
    
    def _on_execute_script(self, record: RecordingHistory):
        """执行自动化脚本"""
        if not self._page:
            return
        
        # 检查是否有脚本
        if not record.script_content and not record.script_file:
            snack_bar = ft.SnackBar(
                content=ft.Text("⚠️ 此记录没有关联的脚本\n\n无法执行，请先编辑或重新录制"),
                duration=3000,
                bgcolor=ft.Colors.ORANGE,
            )
            self._page.overlay.append(snack_bar)
            snack_bar.open = True
            self._page.update()
            return
        
        # 读取脚本内容
        script_content = record.script_content
        if not script_content and record.script_file:
            try:
                with open(record.script_file, 'r', encoding='utf-8') as f:
                    script_content = f.read()
            except Exception as e:
                snack_bar = ft.SnackBar(
                    content=ft.Text(f"❌ 读取脚本失败: {e}"),
                    duration=3000,
                    bgcolor=ft.Colors.RED,
                )
                self._page.overlay.append(snack_bar)
                snack_bar.open = True
                self._page.update()
                return
        
        # 确认执行对话框
        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.PLAY_ARROW, color=ft.Colors.GREEN, size=24),
                ft.Column([
                    ft.Text(
                        "执行自动化脚本",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREY_900,
                    ),
                    ft.Text(
                        f"{record.variable_name}",
                        size=12,
                        color=ft.Colors.GREY_600,
                    ),
                ], spacing=2),
            ], spacing=12),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        "即将执行以下操作：",
                        size=13,
                        weight=ft.FontWeight.W_500,
                        color=ft.Colors.GREY_800,
                    ),
                    ft.Container(height=8),
                    ft.Row([
                        ft.Icon(ft.Icons.LINK, size=16, color=ft.Colors.GREY_600),
                        ft.Text(record.url, size=12, color=ft.Colors.GREY_700),
                    ], spacing=5),
                    ft.Container(height=5),
                    ft.Row([
                        ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=ft.Colors.BLUE_600),
                        ft.Text(
                            "• 将打开浏览器并自动执行脚本\n"
                            "• 请确保 Playwright 已安装\n"
                            "• 执行过程中请勿关闭浏览器窗口",
                            size=12,
                            color=ft.Colors.GREY_700,
                        ),
                    ], spacing=5),
                ], spacing=8),
                padding=12,
                width=500,
            ),
            actions=[
                ft.TextButton(
                    "取消",
                    on_click=lambda e: setattr(confirm_dialog, 'open', False),
                ),
                ft.Button(
                    "执行",
                    icon=ft.Icons.PLAY_ARROW,
                    on_click=lambda e: self._execute_script_action(record, script_content, confirm_dialog),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.GREEN_600,
                        color=ft.Colors.WHITE,
                        padding=ft.padding.symmetric(horizontal=20, vertical=10),
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self._page.overlay.append(confirm_dialog)
        confirm_dialog.open = True
        self._page.update()
    
    def _execute_script_action(self, record: RecordingHistory, script_content: str, dialog):
        """执行脚本的具体操作"""
        import subprocess
        import tempfile
        import os
        
        # 关闭确认对话框
        dialog.open = False
        self._page.update()
        
        # 显示执行中提示
        progress_snack = ft.SnackBar(
            content=ft.Row([
                ft.ProgressRing(width=20, height=20, stroke_width=2),
                ft.Text("正在执行脚本并捕获网络请求...", size=13),
            ], spacing=10),
            duration=10000,
            bgcolor=ft.Colors.BLUE_600,
        )
        self._page.overlay.append(progress_snack)
        progress_snack.open = True
        self._page.update()
        
        # 创建临时目录和文件（使用项目目录）
        try:
            import sys
            import os
            
            # 获取项目根目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            temp_dir = os.path.join(project_root, "temp_execution")
            
            # 创建临时目录（如果不存在）
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            
            har_file = os.path.join(temp_dir, "execution.har")
            
            # 修改脚本，添加 HAR 记录功能
            modified_script = self._inject_har_recording(script_content, har_file)
            
            # 写入修改后的脚本
            temp_script_path = os.path.join(temp_dir, "script.py")
            with open(temp_script_path, 'w', encoding='utf-8') as f:
                f.write(modified_script)
            
            print(f"📄 临时脚本文件: {temp_script_path}")
            print(f"📊 HAR 文件路径: {har_file}")
            
            # 在后台线程执行脚本
            import threading
            
            def run_script():
                try:
                    # 使用当前项目的 Python 解释器执行脚本
                    import sys
                    python_executable = sys.executable
                    
                    print(f"🐍 使用 Python: {python_executable}")
                    print(f"📄 执行脚本: {temp_script_path}")
                    
                    result = subprocess.run(
                        [python_executable, temp_script_path],
                        capture_output=True,
                        text=True,
                        timeout=300,  # 5分钟超时
                        encoding='utf-8'
                    )
                    
                    # 检查是否生成了 HAR 文件
                    har_data = None
                    if os.path.exists(har_file):
                        print(f"✅ HAR 文件已生成: {har_file}")
                        try:
                            with open(har_file, 'r', encoding='utf-8') as f:
                                har_data = f.read()
                            print(f"📊 HAR 文件大小: {len(har_data)} bytes")
                        except Exception as e:
                            print(f"⚠️ 读取 HAR 文件失败: {e}")
                    else:
                        print(f"⚠️ HAR 文件未生成: {har_file}")
                    
                    # 删除临时文件（在项目目录下）
                    try:
                        import shutil
                        if os.path.exists(temp_dir):
                            shutil.rmtree(temp_dir)
                            print(f"🗑️ 已清理临时目录: {temp_dir}")
                    except Exception as e:
                        print(f"⚠️ 清理临时目录失败: {e}")
                    
                    # 在主线程更新 UI
                    def update_ui():
                        progress_snack.open = False
                        self._page.update()
                        
                        if result.returncode == 0:
                            # 成功
                            if har_data:
                                # 分析 HAR 文件并提取字段
                                self._analyze_har_and_extract_fields(record, har_data)
                            else:
                                snack_bar = ft.SnackBar(
                                    content=ft.Text("✅ 脚本执行成功，但未捕获到网络请求"),
                                    duration=3000,
                                    bgcolor=ft.Colors.ORANGE,
                                )
                                self._page.overlay.append(snack_bar)
                                snack_bar.open = True
                                self._page.update()
                                print("✅ 脚本执行成功，但无 HAR 数据")
                        else:
                            # 失败
                            error_msg = result.stderr[:500] if result.stderr else "未知错误"
                            snack_bar = ft.SnackBar(
                                content=ft.Text(f"❌ 脚本执行失败:\n{error_msg}"),
                                duration=5000,
                                bgcolor=ft.Colors.RED,
                            )
                            self._page.overlay.append(snack_bar)
                            snack_bar.open = True
                            self._page.update()
                            print(f"❌ 脚本执行失败: {error_msg}")
                    
                    self._page.run_thread(lambda: None)  # 确保在主线程
                    update_ui()
                    
                except subprocess.TimeoutExpired:
                    # 超时
                    try:
                        import shutil
                        if os.path.exists(temp_dir):
                            shutil.rmtree(temp_dir)
                            print(f"🗑️ 已清理临时目录: {temp_dir}")
                    except:
                        pass
                    
                    def update_ui():
                        progress_snack.open = False
                        self._page.update()
                        
                        snack_bar = ft.SnackBar(
                            content=ft.Text("⏱️ 脚本执行超时（5分钟）"),
                            duration=3000,
                            bgcolor=ft.Colors.ORANGE,
                        )
                        self._page.overlay.append(snack_bar)
                        snack_bar.open = True
                        self._page.update()
                    
                    self._page.run_thread(lambda: None)
                    update_ui()
                    
                except Exception as e:
                    # 其他错误
                    try:
                        import shutil
                        if os.path.exists(temp_dir):
                            shutil.rmtree(temp_dir)
                            print(f"🗑️ 已清理临时目录: {temp_dir}")
                    except:
                        pass
                    
                    def update_ui():
                        progress_snack.open = False
                        self._page.update()
                        
                        snack_bar = ft.SnackBar(
                            content=ft.Text(f"❌ 执行出错: {str(e)}"),
                            duration=3000,
                            bgcolor=ft.Colors.RED,
                        )
                        self._page.overlay.append(snack_bar)
                        snack_bar.open = True
                        self._page.update()
                    
                    self._page.run_thread(lambda: None)
                    update_ui()
            
            # 启动后台线程
            thread = threading.Thread(target=run_script, daemon=True)
            thread.start()
            
        except Exception as e:
            progress_snack.open = False
            self._page.update()
            
            snack_bar = ft.SnackBar(
                content=ft.Text(f"❌ 创建临时文件失败: {e}"),
                duration=3000,
                bgcolor=ft.Colors.RED,
            )
            self._page.overlay.append(snack_bar)
            snack_bar.open = True
            self._page.update()
    
    def _inject_har_recording(self, script_content: str, har_file: str) -> str:
        """修改脚本，注入 HAR 记录功能"""
        import re
        
        # 检查是否已经有 context 定义
        has_context = 'context = browser.new_context' in script_content or 'context=' in script_content
        
        if not has_context:
            # 如果没有 context，需要添加
            lines = script_content.split('\n')
            new_lines = []
            
            for i, line in enumerate(lines):
                new_lines.append(line)
                
                # 在 browser.new_page() 之前插入 context 创建
                if 'browser.new_page()' in line and 'context' not in script_content:
                    indent = len(line) - len(line.lstrip())
                    spaces = ' ' * indent
                    # 插入 context 创建代码（带 HAR 记录）
                    new_lines.insert(-1, f'{spaces}# 创建 context 并启用 HAR 记录')
                    new_lines.insert(-1, f'{spaces}context = browser.new_context(record_har_path=r"{har_file}")')
                    new_lines.insert(-1, f'{spaces}page = context.new_page()')
                    # 删除原来的 page = browser.new_page()
                    new_lines.pop(-4)
        else:
            # 如果已有 context，修改为带 HAR 记录
            # 使用字符串替换而不是正则表达式，避免路径转义问题
            import re as regex_module
            
            # 查找 context = browser.new_context(...) 并添加 record_har_path
            pattern = r'(context\s*=\s*browser\.new_context\()([^)]*)(\))'
            
            def replace_func(match):
                prefix = match.group(1)  # context = browser.new_context(
                params = match.group(2)  # 现有参数
                suffix = match.group(3)  # )
                
                # 如果已经有参数，添加逗号
                if params.strip():
                    return f'{prefix}{params}, record_har_path=r"{har_file}"{suffix}'
                else:
                    return f'{prefix}record_har_path=r"{har_file}"{suffix}'
            
            script_content = regex_module.sub(pattern, replace_func, script_content)
        
        return script_content
    
    def _analyze_har_and_extract_fields(self, record: RecordingHistory, har_data: str):
        """分析 HAR 文件并提取字段"""
        try:
            from services.har_analyzer import HarAnalyzer
            import json
            import tempfile
            import os
            
            # 将 HAR 数据写入临时文件
            temp_har = tempfile.NamedTemporaryFile(mode='w', suffix='.har', delete=False, encoding='utf-8')
            temp_har.write(har_data)
            temp_har.close()
            
            try:
                # 创建 HAR 分析器
                analyzer = HarAnalyzer(temp_har.name)
                
                # 获取摘要信息
                summary = analyzer.get_summary()
                print(f"📊 HAR 摘要: {summary['total_requests']} 个请求")
                
                # 获取用户配置的字段
                field_configs = record.field_configs if record.field_configs else []
                print(f"🔍 用户配置了 {len(field_configs)} 个字段")
                
                if field_configs:
                    # 根据用户配置提取字段
                    extracted_data = {}
                    for config in field_configs:
                        var_name = config.get('name', '')
                        path = config.get('path', '')
                        source = config.get('source', 'response')
                        extract_type = config.get('extract_type', 'json')
                        
                        if not var_name or not path:
                            continue
                        
                        # 提取字段值
                        result = analyzer.extract_field({
                            'name': var_name,
                            'path': path,
                            'source': source,
                            'extract_type': extract_type,
                        })
                        
                        if result:
                            extracted_data[var_name] = result
                            print(f"✅ 提取成功: {var_name} = {result['value'][:50]}...")
                        else:
                            print(f"⚠️ 提取失败: {var_name}")
                    
                    print(f"📊 成功提取 {len(extracted_data)}/{len(field_configs)} 个字段")
                    
                    # 显示提取结果对话框
                    self._show_execution_results(record, analyzer, summary, extracted_data, field_configs)
                else:
                    # 没有配置字段，只显示摘要
                    print("⚠️ 没有配置要提取的字段")
                    self._show_execution_results(record, analyzer, summary, {}, [])
                
            finally:
                # 删除临时 HAR 文件
                try:
                    os.unlink(temp_har.name)
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ 分析 HAR 文件失败: {e}")
            import traceback
            traceback.print_exc()
            
            snack_bar = ft.SnackBar(
                content=ft.Text(f"❌ 分析 HAR 文件失败: {str(e)}"),
                duration=3000,
                bgcolor=ft.Colors.RED,
            )
            self._page.overlay.append(snack_bar)
            snack_bar.open = True
            self._page.update()
    
    def _show_execution_results(self, record: RecordingHistory, analyzer, summary, extracted_data: dict, field_configs: list):
        """显示执行结果和提取的字段"""
        if not self._page:
            return
        
        # 构建结果显示
        items = []
        
        # 标题
        items.append(ft.Text(
            f"✅ 脚本执行成功！",
            weight=ft.FontWeight.BOLD,
            size=16,
            color=ft.Colors.GREEN_700,
        ))
        items.append(ft.Divider(height=10))
        
        # HAR 摘要
        items.append(ft.Text(
            f"📊 捕获到 {summary['total_requests']} 个网络请求",
            size=13,
            color=ft.Colors.GREY_700,
        ))
        items.append(ft.Container(height=5))
        
        if extracted_data:
            # 显示提取的字段
            items.append(ft.Text(
                f"🔍 成功提取 {len(extracted_data)}/{len(field_configs)} 个字段：",
                weight=ft.FontWeight.W_500,
                size=14,
                color=ft.Colors.BLUE_700,
            ))
            items.append(ft.Container(height=8))
            
            for var_name, field_data in extracted_data.items():
                value = field_data.get('value', '')
                source = field_data.get('source', '')
                path = field_data.get('path', '')
                extract_type = field_data.get('extract_type', 'json')
                
                # 根据来源选择图标和颜色
                if source == 'response':
                    icon = ft.Icons.DATA_OBJECT
                    icon_color = ft.Colors.BLUE
                    source_text = "响应体"
                elif source == 'header':
                    icon = ft.Icons.LABEL
                    icon_color = ft.Colors.PURPLE
                    source_text = "响应头"
                else:
                    icon = ft.Icons.COOKIE
                    icon_color = ft.Colors.ORANGE
                    source_text = "Cookie"
                
                # 提取方式标签
                extract_type_text = "正则" if extract_type == 'regex' else "JSON"
                extract_type_color = ft.Colors.GREEN if extract_type == 'regex' else ft.Colors.BLUE
                
                # 值预览
                value_preview = value[:80] + "..." if len(value) > 80 else value
                
                # 创建卡片
                card = ft.Container(
                    content=ft.Column([
                        # 第一行：变量名 + 标签
                        ft.Row([
                            ft.Icon(icon, size=18, color=icon_color),
                            ft.Text(
                                var_name,
                                weight=ft.FontWeight.BOLD,
                                size=13,
                                color=ft.Colors.GREY_900,
                            ),
                            ft.Container(
                                content=ft.Text(source_text, size=10, color=ft.Colors.WHITE),
                                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                bgcolor=icon_color,
                                border_radius=4,
                            ),
                            ft.Container(
                                content=ft.Text(extract_type_text, size=10, color=ft.Colors.WHITE),
                                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                bgcolor=extract_type_color,
                                border_radius=4,
                            ),
                        ], spacing=6, wrap=True),
                        
                        # 第二行：值
                        ft.Container(
                            content=ft.Text(
                                value_preview,
                                size=11,
                                color=ft.Colors.GREY_800,
                                selectable=True,
                            ),
                            padding=8,
                            bgcolor=ft.Colors.GREY_100,
                            border_radius=4,
                            margin=ft.margin.only(top=4, bottom=4),
                        ),
                        
                        # 第三行：路径
                        ft.Row([
                            ft.Icon(ft.Icons.CODE, size=12, color=ft.Colors.GREY_500),
                            ft.Text(path, size=10, color=ft.Colors.GREY_600, selectable=True),
                        ], spacing=4),
                    ], spacing=6),
                    padding=10,
                    bgcolor=ft.Colors.WHITE,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=8,
                    margin=ft.margin.only(bottom=8),
                )
                
                items.append(card)
        else:
            # 没有提取到字段
            items.append(ft.Text(
                "⚠️ 未提取到字段值",
                size=13,
                color=ft.Colors.ORANGE_700,
            ))
            items.append(ft.Container(height=5))
            items.append(ft.Text(
                "可能的原因：\n"
                "• 字段配置的路径或正则表达式不匹配\n"
                "• 网络请求的响应格式发生变化\n"
                "• 请检查录制时的字段配置是否正确",
                size=11,
                color=ft.Colors.GREY_600,
            ))
        
        # 检查是否有未提取到的字段
        extracted_names = set(extracted_data.keys())
        missing_fields = [config for config in field_configs if config.get('name') not in extracted_names]
        
        if missing_fields:
            # 有未提取到的字段，显示手动输入框
            items.append(ft.Divider(height=10))
            items.append(ft.Text(
                f"⚠️ 以下 {len(missing_fields)} 个字段未提取到，请手动输入：",
                weight=ft.FontWeight.W_500,
                size=13,
                color=ft.Colors.ORANGE_700,
            ))
            items.append(ft.Container(height=5))
            
            # 为每个未提取的字段创建输入框
            manual_input_fields = {}
            
            for config in missing_fields:
                field_name = config.get('name', '')
                extract_type = config.get('extract_type', 'json')
                path = config.get('path', '')
                source = config.get('source', 'response')
                
                # 根据来源选择图标和提示
                if source == 'response':
                    icon = ft.Icons.DATA_OBJECT
                    icon_color = ft.Colors.BLUE
                    source_text = "响应体"
                elif source == 'header':
                    icon = ft.Icons.LABEL
                    icon_color = ft.Colors.PURPLE
                    source_text = "响应头"
                else:
                    icon = ft.Icons.COOKIE
                    icon_color = ft.Colors.ORANGE
                    source_text = "Cookie"
                
                extract_type_text = "正则" if extract_type == 'regex' else "JSON"
                
                # 创建字段输入卡片
                field_card = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(icon, size=16, color=icon_color),
                            ft.Text(
                                field_name,
                                weight=ft.FontWeight.BOLD,
                                size=13,
                            ),
                            ft.Container(
                                content=ft.Text("未提取", size=9, color=ft.Colors.WHITE),
                                padding=ft.padding.symmetric(horizontal=4, vertical=1),
                                bgcolor=ft.Colors.ORANGE,
                                border_radius=3,
                            ),
                            ft.Container(
                                content=ft.Text(extract_type_text, size=9, color=ft.Colors.WHITE),
                                padding=ft.padding.symmetric(horizontal=4, vertical=1),
                                bgcolor=ft.Colors.GREEN if extract_type == 'regex' else ft.Colors.BLUE,
                                border_radius=3,
                            ),
                        ], spacing=5),
                        ft.TextField(
                            hint_text=f"请输入 {field_name} 的值",
                            width=500,
                            multiline=True,
                            min_lines=2,
                            max_lines=4,
                            text_size=12,
                            key=f"manual_input_{field_name}",
                        ),
                    ], spacing=6),
                    padding=10,
                    bgcolor=ft.Colors.ORANGE_50,
                    border_radius=6,
                    border=ft.border.all(1, ft.Colors.ORANGE_200),
                    margin=ft.margin.only(bottom=8),
                )
                
                items.append(field_card)
                
                # 保存输入框引用
                manual_input_fields[field_name] = field_card.content.controls[-1]
        
        items.append(ft.Divider(height=10))
        
        # 保存选项
        save_to_env_checkbox = ft.Checkbox(
            label="保存到当前环境（否则保存到全局变量）",
            value=True,
        )
        
        prefix_field = ft.TextField(
            label="变量名前缀（可选）",
            hint_text="例如: api，将保存为 api_token, api_user_id 等",
            width=400,
            text_size=13,
        )
        
        # 保存按钮回调函数
        def on_save(e):
            """保存提取的字段"""
            # 合并自动提取和手动输入的数据
            all_data = dict(extracted_data)  # 复制已提取的数据
            
            # 添加手动输入的字段
            if 'manual_input_fields' in locals() and manual_input_fields:
                for field_name, text_field in manual_input_fields.items():
                    manual_value = text_field.value
                    if manual_value and manual_value.strip():
                        all_data[field_name] = {
                            'value': manual_value.strip(),
                            'source': 'manual',
                            'path': '手动输入',
                            'extract_type': 'manual',
                        }
            
            if not all_data:
                snack_bar = ft.SnackBar(
                    content=ft.Text("❌ 没有可保存的字段"),
                    duration=2000,
                    bgcolor=ft.Colors.RED,
                )
                self._page.overlay.append(snack_bar)
                snack_bar.open = True
                self._page.update()
                return
            
            try:
                from managers.environment_manager import EnvironmentManager
                from managers.global_variable_manager import GlobalVariableManager
                
                prefix = prefix_field.value.strip()
                save_to_env = save_to_env_checkbox.value
                
                saved_count = 0
                errors = []
                
                if save_to_env:
                    # 保存到环境变量
                    env_manager = EnvironmentManager()
                    current_env = env_manager.get_active_environment()
                    
                    if not current_env:
                        snack_bar = ft.SnackBar(
                            content=ft.Text("❌ 没有选中的环境，请先选择一个环境"),
                            duration=2000,
                            bgcolor=ft.Colors.RED,
                        )
                        self._page.overlay.append(snack_bar)
                        snack_bar.open = True
                        self._page.update()
                        return
                    
                    # 获取当前环境变量
                    current_variables = dict(current_env.variables) if current_env.variables else {}
                    
                    # 添加所有字段（自动+手动）
                    for var_name, field_data in all_data.items():
                        final_name = f"{prefix}_{var_name}" if prefix else var_name
                        value = field_data.get('value', '')
                        current_variables[final_name] = value
                    
                    # 更新环境变量
                    success = env_manager.update_environment(
                        current_env.id,
                        variables=current_variables
                    )
                    
                    if success:
                        saved_count = len(all_data)
                    else:
                        errors = list(all_data.keys())
                else:
                    # 保存到全局变量
                    global_var_manager = GlobalVariableManager()
                    
                    for var_name, field_data in all_data.items():
                        final_name = f"{prefix}_{var_name}" if prefix else var_name
                        value = field_data.get('value', '')
                        
                        success = global_var_manager.set_variable(final_name, value)
                        if success:
                            saved_count += 1
                        else:
                            errors.append(final_name)
                
                # 关闭对话框
                result_dialog.open = False
                self._page.update()
                
                # 显示保存结果
                if errors:
                    snack_msg = f"✅ 成功保存 {saved_count} 个字段，{len(errors)} 个失败"
                    snack_color = ft.Colors.ORANGE
                else:
                    snack_msg = f"✅ 成功保存 {saved_count} 个字段到{'环境' if save_to_env else '全局变量'}"
                    snack_color = ft.Colors.GREEN
                
                snack_bar = ft.SnackBar(
                    content=ft.Text(snack_msg),
                    duration=3000,
                    bgcolor=snack_color,
                )
                self._page.overlay.append(snack_bar)
                snack_bar.open = True
                self._page.update()
                
            except Exception as ex:
                print(f"保存失败: {ex}")
                import traceback
                traceback.print_exc()
                
                snack_bar = ft.SnackBar(
                    content=ft.Text(f"❌ 保存失败: {ex}"),
                    duration=3000,
                    bgcolor=ft.Colors.RED,
                )
                self._page.overlay.append(snack_bar)
                snack_bar.open = True
                self._page.update()
        
        # 保存选项卡片
        save_options_card = ft.Container(
            content=ft.Column([
                ft.Text(
                    "💾 保存提取的字段",
                    weight=ft.FontWeight.W_500,
                    size=14,
                    color=ft.Colors.GREY_800,
                ),
                ft.Container(height=8),
                save_to_env_checkbox,
                ft.Container(height=8),
                prefix_field,
                ft.Container(height=10),
                ft.Row([
                    ft.Button(
                        "关闭",
                        icon=ft.Icons.CLOSE,
                        on_click=lambda e: setattr(result_dialog, 'open', False),
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.GREY_200,
                            color=ft.Colors.GREY_800,
                        ),
                    ),
                    ft.Button(
                        "保存所有字段",
                        icon=ft.Icons.SAVE,
                        on_click=on_save,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.PURPLE_600,
                            color=ft.Colors.WHITE,
                        ),
                    ),
                ], alignment=ft.MainAxisAlignment.END, spacing=10),
            ], spacing=8),
            padding=15,
            bgcolor=ft.Colors.GREY_50,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_200),
        )
        
        items.append(save_options_card)
        
        # 创建对话框
        result_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=24),
                ft.Text("执行结果", size=18, weight=ft.FontWeight.BOLD),
            ], spacing=10),
            content=ft.Container(
                content=ft.Column(
                    controls=items,
                    scroll=ft.ScrollMode.AUTO,
                    spacing=8,
                ),
                width=650,
                height=600,
                padding=15,
            ),
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self._page.overlay.append(result_dialog)
        result_dialog.open = True
        self._page.update()

    def _on_delete_record(self, record: RecordingHistory):
        """删除记录"""
        if not self._page:
            return
        
        def confirm_delete(e):
            success = self.service.delete_record(record.id)
            
            dialog.open = False
            self._page.update()
            
            if success:
                # 重新加载列表
                self._load_history()
                
                snack_bar = ft.SnackBar(
                    content=ft.Text("✅ 已删除"),
                    duration=2000,
                    bgcolor=ft.Colors.GREEN,
                )
                self._page.overlay.append(snack_bar)
                snack_bar.open = True
                self._page.update()
            else:
                snack_bar = ft.SnackBar(
                    content=ft.Text("❌ 删除失败"),
                    duration=2000,
                    bgcolor=ft.Colors.RED,
                )
                self._page.overlay.append(snack_bar)
                snack_bar.open = True
                self._page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("确认删除"),
            content=ft.Text(f"确定要删除这条录制记录吗？\n\nURL: {record.url}\n时间: {record.created_at}"),
            actions=[
                ft.TextButton("取消", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.TextButton("删除", style=ft.ButtonStyle(color=ft.Colors.RED), on_click=confirm_delete),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()
    
    def _show_empty(self):
        """显示空状态"""
        self.history_list.controls.clear()
        self.empty_hint.visible = True
        self.pagination.visible = False
        if self._page:
            try:
                self._page.update()
            except RuntimeError:
                pass
    
    def _update_pagination(self, total_pages: int):
        """更新分页控件"""
        if self._page and hasattr(self, 'page_text'):
            self.page_text.value = f"第 {self.current_page + 1}/{total_pages} 页"
            try:
                self._page.update()
            except RuntimeError:
                pass
    
    def _on_first_page(self, e):
        """第一页"""
        if self.current_page > 0:
            self.current_page = 0
            self._load_history()
    
    def _on_prev_page(self, e):
        """上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self._load_history()
    
    def _on_next_page(self, e):
        """下一页"""
        total_count = self.service.get_total_count()
        total_pages = (total_count + self.page_size - 1) // self.page_size
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self._load_history()
    
    def _on_last_page(self, e):
        """最后一页"""
        total_count = self.service.get_total_count()
        total_pages = (total_count + self.page_size - 1) // self.page_size
        if total_pages > 0:
            self.current_page = total_pages - 1
            self._load_history()
