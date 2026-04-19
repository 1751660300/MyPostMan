"""
登录录制对话框 - 使用 Playwright Codegen 自动捕获用户操作
"""
import flet as ft
from typing import Callable
import webbrowser


class LoginRecorderDialog:
    """登录录制对话框
    
    使用 Playwright 自动捕获登录过程中的 Token/Cookie
    """
    
    def __init__(self, on_save: Callable, env_manager=None):
        self.on_save = on_save
        self.env_manager = env_manager
        
        # 录制状态
        self.is_recording = False
        self.captured_data = {}
        self.should_stop = False  # 停止标志
        self.capture_fields = []  # 用户配置的捕获字段列表
        self.user_actions = []  # 用户操作记录列表
        self.codegen_process = None  # Codegen 进程引用
        self.generated_script_file = None  # Codegen 生成的脚本文件路径
        self.generated_script_content = None  # Codegen 生成的脚本内容
        
        self.dialog = self._build_dialog()
    
    def _build_dialog(self) -> ft.AlertDialog:
        """构建对话框"""
        # URL 输入
        self.url_field = ft.TextField(
            label="目标页面URL",
            hint_text="https://example.com/page",
            width=500,
        )
        
        # 字段配置区域
        fields_config_section = ft.Column([
            ft.Text("📋 要捕获的字段配置", weight=ft.FontWeight.BOLD, size=14),
            ft.Text("添加需要从响应中提取的字段（支持 JSON 路径）", size=12, color=ft.Colors.GREY_600),
        ], spacing=5)
        
        # 字段列表容器
        self.fields_list = ft.Column([], spacing=8)
        
        # 添加字段按钮
        add_field_btn = ft.TextButton(
            "添加字段",
            icon=ft.Icons.ADD,
            on_click=self._on_add_field,
        )
        
        fields_config_section.controls.extend([
            self.fields_list,
            add_field_btn,
        ])
        
        # 录制状态显示
        self.status_text = ft.Text(
            "准备就绪 - 请配置要捕获的字段",
            size=14,
            color=ft.Colors.GREY_600,
        )
        
        # 捕获的数据显示区域（使用可滚动的 Container）
        self.captured_info = ft.Container(
            content=ft.Column([
                ft.Text("📋 捕获的数据将在此显示", size=12, color=ft.Colors.GREY),
            ]),
            padding=10,
            bgcolor=ft.Colors.GREY_200,
            border_radius=8,
            visible=False,
            height=300,  # 限制最大高度
        )
        
        # 按钮行
        btn_row = ft.Row([
            ft.Button(
                "开始录制",
                icon=ft.Icons.FIBER_MANUAL_RECORD,
                on_click=self._on_start_recording,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.RED_500,
                    color=ft.Colors.WHITE,
                ),
            ),
            ft.TextButton(
                "取消",
                on_click=self._on_cancel,
            ),
        ])
        
        return ft.AlertDialog(
            modal=True,
            title=ft.Text("🎬 数据录制器"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        "自动捕获页面交互过程中的数据\n"
                        "请在打开的浏览器中完成操作，系统会自动提取配置的字段",
                        size=13,
                        color=ft.Colors.GREY_700,
                    ),
                    ft.Divider(),
                    self.url_field,
                    ft.Divider(height=10),
                    fields_config_section,
                    ft.Divider(height=10),
                    self.status_text,
                    ft.Divider(height=10),
                    self.captured_info,
                ], tight=True, spacing=10, scroll=ft.ScrollMode.AUTO),  # 添加滚动
                width=600,  # 增加宽度
                height=600,  # 增加高度
                padding=10,
            ),
            actions=[btn_row],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    
    def _on_add_field(self, e):
        """添加字段配置项"""
        field_index = len(self.capture_fields)
        
        # 创建字段配置行
        field_row = ft.Row([
            ft.TextField(
                label="变量名",
                hint_text="例如: user_id",
                width=120,
                text_size=12,
                key=f"field_name_{field_index}",
            ),
            ft.Dropdown(
                label="提取方式",
                options=[
                    ft.dropdown.Option("json", "JSON路径"),
                    ft.dropdown.Option("regex", "正则表达式"),
                ],
                value="json",
                width=110,
                text_size=12,
                key=f"field_extract_type_{field_index}",
            ),
            ft.TextField(
                label="路径/正则",
                hint_text="data.token 或 (?<=token\":\")[^\"]+",
                width=200,
                text_size=12,
                key=f"field_path_{field_index}",
            ),
            ft.Dropdown(
                label="来源",
                options=[
                    ft.dropdown.Option("response", "响应体"),
                    ft.dropdown.Option("header", "响应头"),
                    ft.dropdown.Option("cookie", "Cookie"),
                ],
                value="response",
                width=100,
                text_size=12,
                key=f"field_source_{field_index}",
            ),
            ft.IconButton(
                icon=ft.Icons.DELETE,
                icon_color=ft.Colors.RED_400,
                tooltip="删除此字段",
                on_click=lambda e, idx=field_index: self._on_remove_field(idx),
            ),
        ], spacing=8)
        
        # 添加到列表
        self.fields_list.controls.append(field_row)
        
        # 保存字段配置
        self.capture_fields.append({
            'index': field_index,
            'row': field_row,
        })
        
        self.page.update()
    
    def _on_remove_field(self, index: int):
        """删除字段配置项"""
        # 找到对应的配置
        for i, field in enumerate(self.capture_fields):
            if field['index'] == index:
                # 从 UI 中移除
                self.fields_list.controls.remove(field['row'])
                # 从列表中移除
                self.capture_fields.pop(i)
                break
        
        self.page.update()
    
    def _get_field_configs(self) -> list:
        """从 UI 中获取用户配置的字段列表"""
        configs = []
        
        for field in self.capture_fields:
            row = field['row']
            # 获取各个输入框的值
            name_field = row.controls[0]  # 变量名
            extract_type_dropdown = row.controls[1]  # 提取方式
            path_field = row.controls[2]  # 路径/正则
            source_dropdown = row.controls[3]  # 来源
            
            name = name_field.value.strip()
            extract_type = extract_type_dropdown.value
            path = path_field.value.strip()
            source = source_dropdown.value
            
            if name and path:
                configs.append({
                    'name': name,
                    'path': path,
                    'source': source,
                    'extract_type': extract_type,  # json 或 regex
                })
        
        return configs
    
    def _extract_json_value(self, data: dict, json_path: str):
        """从 JSON 数据中提取指定路径的值
        
        支持点号分隔的路径，例如: data.user.id
        """
        try:
            keys = json_path.split('.')
            current = data
            
            for key in keys:
                if isinstance(current, dict):
                    current = current.get(key)
                else:
                    return None
                
                if current is None:
                    return None
            
            return current
        except:
            return None
    
    def _check_browser_installed(self) -> bool:
        """检查 Chromium 浏览器是否已安装"""
        import os
        import glob
        
        # Playwright 浏览器默认安装路径
        local_app_data = os.environ.get('LOCALAPPDATA', '')
        if not local_app_data:
            return False
        
        # Chromium 安装路径
        chromium_path = os.path.join(
            local_app_data,
            'ms-playwright',
            'chromium-*',  # 版本号可能不同
            'chrome-win64',
            'chrome.exe'
        )
        
        # 使用 glob 查找
        matches = glob.glob(chromium_path)
        
        return len(matches) > 0
    
    def _show_browser_install_dialog(self, url: str):
        """显示浏览器安装对话框"""
        def on_install(e):
            """开始安装浏览器"""
            install_btn.disabled = True
            install_btn.text = "正在下载..."
            cancel_btn.visible = False
            status_text.value = "⏳ 正在下载 Chromium 浏览器（约 300MB）...\n这可能需要几分钟，请耐心等待"
            self.page.update()
            
            # 在后台线程执行安装
            import threading
            import subprocess
            
            def install_browser():
                try:
                    # 执行 playwright install chromium
                    result = subprocess.run(
                        ['playwright', 'install', 'chromium'],
                        capture_output=True,
                        text=True,
                        timeout=600  # 10分钟超时
                    )
                    
                    if result.returncode == 0:
                        # 安装成功
                        self.page.run_thread(lambda: self._on_install_success(url))
                    else:
                        # 安装失败
                        error_msg = result.stderr if result.stderr else "未知错误"
                        self.page.run_thread(lambda: self._on_install_failed(error_msg))
                        
                except subprocess.TimeoutExpired:
                    self.page.run_thread(lambda: self._on_install_failed("下载超时，请检查网络连接"))
                except Exception as ex:
                    self.page.run_thread(lambda: self._on_install_failed(str(ex)))
            
            thread = threading.Thread(target=install_browser, daemon=True)
            thread.start()
        
        def on_cancel(e):
            """取消安装"""
            self.dialog.open = False
            self.page.update()
        
        status_text = ft.Text(
            "检测到 Chromium 浏览器未安装\n\n"
            "自动录制功能需要 Chromium 浏览器支持。\n"
            '点击“开始下载”将自动下载安装（约 300MB）。\n\n'
            "或者您可以选择手动模式，无需安装浏览器。",
            size=13,
            color=ft.Colors.GREY_700,
        )
        
        install_btn = ft.Button(
            "开始下载",
            icon=ft.Icons.DOWNLOAD,
            on_click=on_install,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_600,
                color=ft.Colors.WHITE,
            ),
        )
        
        manual_btn = ft.Button(
            "使用手动模式",
            icon=ft.Icons.HANDYMAN,
            on_click=lambda e: self._show_manual_mode(url),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_600,
                color=ft.Colors.WHITE,
            ),
        )
        
        cancel_btn = ft.TextButton(
            "取消",
            on_click=on_cancel,
        )
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("🌐 需要安装浏览器"),
            content=ft.Container(
                content=ft.Column([
                    status_text,
                ], tight=True, spacing=10),
                width=500,
                padding=10,
            ),
            actions=[
                install_btn,
                manual_btn,
                cancel_btn,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _on_install_success(self, url: str):
        """浏览器安装成功"""
        # 关闭安装对话框
        self.page.overlay.clear()
        
        # 显示成功提示
        snack_bar = ft.SnackBar(
            content=ft.Text("✅ 浏览器安装成功！正在启动录制..."),
            duration=2000,
            bgcolor=ft.Colors.GREEN,
        )
        self.page.overlay.append(snack_bar)
        snack_bar.open = True
        self.page.update()
        
        # 重新开始录制
        self._start_playwright_recording(url)
    
    def _on_install_failed(self, error_msg: str):
        """浏览器安装失败"""
        # 恢复按钮状态
        btn_row = self.dialog.actions[0]
        btn_row.controls[0].disabled = False
        
        # 显示错误对话框
        error_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("❌ 安装失败"),
            content=ft.Text(
                f"浏览器安装失败：\n\n{error_msg}\n\n"
                f"建议：\n"
                f"1. 检查网络连接\n"
                f"2. 使用手动模式\n"
                f"3. 手动运行命令：playwright install chromium",
                size=13,
            ),
            actions=[
                ft.TextButton(
                    "使用手动模式",
                    on_click=lambda e: [
                        setattr(error_dialog, 'open', False),
                        self._show_manual_mode(self.url_field.value.strip()),
                    ],
                ),
                ft.TextButton(
                    "关闭",
                    on_click=lambda e: setattr(error_dialog, 'open', False),
                ),
            ],
        )
        
        self.page.overlay.append(error_dialog)
        error_dialog.open = True
        self.page.update()
    
    def _on_start_recording(self, e):
        """开始录制"""
        url = self.url_field.value.strip()
        if not url:
            self._update_status("❌ 请输入URL", ft.Colors.RED)
            return
        
        # 检查是否配置了字段
        if not self.capture_fields:
            self._update_status("⚠️ 请至少添加一个要捕获的字段", ft.Colors.ORANGE)
            return
        
        if not url.startswith('http'):
            url = 'https://' + url
        
        try:
            # 尝试使用 Playwright
            self._start_playwright_recording(url)
        except ImportError:
            # 降级方案：手动模式
            self._show_manual_mode(url)
    
    def _start_playwright_recording(self, url: str):
        """使用 Playwright CLI codegen 录制（推荐方式）"""
        try:
            from playwright.sync_api import sync_playwright
            
            # 检查浏览器是否已安装
            if not self._check_browser_installed():
                self._show_browser_install_dialog(url)
                return
            
            self.is_recording = True
            self.should_stop = False
            self._update_status("🔴 正在启动 Codegen 录制模式...", ft.Colors.ORANGE)
            
            # 生成临时脚本文件路径（使用项目目录）
            import tempfile
            import os
            from datetime import datetime
            
            # 获取项目根目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            temp_dir = os.path.join(project_root, "recorded_scripts")
            
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            
            timestamp = int(datetime.now().timestamp())
            temp_script = os.path.join(temp_dir, f"playwright_codegen_{timestamp}.py")
            
            # 在后台线程运行 codegen
            import threading
            thread = threading.Thread(
                target=self._run_codegen_cli,
                args=(url, temp_script),
                daemon=True
            )
            thread.start()
            
            # 更新UI状态 - 禁用开始按钮
            btn_row = self.dialog.actions[0]
            btn_row.controls[0].disabled = True   # 禁用开始按钮
            self.page.update()
            
        except ImportError:
            self._show_manual_mode(url)
    
    def _run_codegen_cli(self, url: str, output_script: str):
        """运行 Playwright CLI codegen 命令
        
        注意：Codegen CLI 不支持生成 HAR 文件
        HAR 文件需要在运行生成的脚本时才会创建
        """
        import subprocess
        import os
        
        try:
            self.page.run_thread(lambda: self._update_status(
                f"✅ Codegen 已启动！\n请在打开的浏览器中操作，关闭浏览器后自动生成脚本",
                ft.Colors.GREEN
            ))
            
            # 生成 HAR 文件路径（与脚本同目录）
            har_file = output_script.replace('.py', '.har')
            
            # 构建 codegen 命令（包含 HAR 记录）
            cmd = [
                'playwright', 'codegen',
                '--target=python',
                f'--save-har={har_file}',  # 添加 HAR 文件支持
                '-o', output_script,
                url
            ]
            
            print(f"🚀 执行命令: {' '.join(cmd)}")
            print(f"📄 HAR 文件将保存到: {har_file}")
            
            # 执行 codegen 命令（会阻塞直到浏览器关闭）
            self.codegen_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待进程完成或超时
            try:
                self.codegen_process.wait(timeout=600)  # 10分钟超时
                result = self.codegen_process
            except subprocess.TimeoutExpired:
                self.codegen_process.kill()
                raise
            
            # codegen 结束后，读取生成的脚本
            if os.path.exists(output_script):
                with open(output_script, 'r', encoding='utf-8') as f:
                    generated_code = f.read()
                
                print(f"✅ Codegen 脚本已生成: {output_script}")
                print(f"📝 脚本长度: {len(generated_code)} 字符")
                
                # output_script 已经在项目目录中，直接使用
                final_script = output_script
                
                print(f"💾 脚本已保存到: {final_script}")
                
                # 保存脚本文件路径和内容，供后续使用
                self.generated_script_file = final_script
                self.generated_script_content = generated_code
                
                # 分析 HAR 文件提取字段数据
                if os.path.exists(har_file):
                    print(f"🔍 发现 HAR 文件: {har_file}")
                    try:
                        from services.har_analyzer import HarAnalyzer
                        
                        analyzer = HarAnalyzer(har_file)
                        field_configs = self._get_field_configs()
                        
                        if field_configs:
                            captured_data = analyzer.extract_all_fields(field_configs)
                            print(f"📊 从 HAR 文件中提取了 {len(captured_data)} 个字段")
                        else:
                            captured_data = {}
                            print("⚠️ 没有配置要提取的字段")
                        
                        # 打印摘要
                        summary = analyzer.get_summary()
                        print(f"📈 HAR 摘要: {summary['total_requests']} 个请求")
                        
                    except Exception as e:
                        print(f"⚠️ HAR 分析失败: {e}")
                        import traceback
                        traceback.print_exc()
                        captured_data = {}
                else:
                    print(f"⚠️ HAR 文件不存在: {har_file}")
                    captured_data = {}
                
                # 记录操作
                self.user_actions.append({
                    'type': 'navigate',
                    'url': url,
                    'timestamp': self._get_current_time(),
                })
                
                # 更新UI
                def on_codegen_complete():
                    # 保存捕获的数据
                    self.captured_data = captured_data
                    
                    # 显示结果
                    if captured_data:
                        self._show_captured_data(captured_data)
                        self._update_status(
                            f"✅ 录制完成！捕获 {len(captured_data)} 个字段\n脚本: {final_script}",
                            ft.Colors.GREEN
                        )
                    else:
                        self._show_captured_data({})
                        self._update_status(
                            f"✅ 录制完成！脚本已保存\n请查看: {final_script}\n⚠️ 未捕获到配置的字段",
                            ft.Colors.ORANGE
                        )
                    
                    self.is_recording = False
                    self._reset_buttons()
                    
                    # 显示提示
                    snack_bar = ft.SnackBar(
                        content=ft.Text(
                            f"✅ 录制完成！\n"
                            f"脚本: {final_script}\n"
                            f"字段: {len(captured_data)} 个"
                        ),
                        duration=5000,
                        bgcolor=ft.Colors.GREEN if captured_data else ft.Colors.ORANGE,
                    )
                    self.page.overlay.append(snack_bar)
                    snack_bar.open = True
                    self.page.update()
                
                self.page.run_thread(on_codegen_complete)
            else:
                def on_codegen_failed():
                    self._update_status("❌ 脚本生成失败", ft.Colors.RED)
                    self.is_recording = False
                    self._reset_buttons()
                
                self.page.run_thread(on_codegen_failed)
        
        except subprocess.TimeoutExpired:
            def on_timeout():
                self._update_status("⏱️ 录制超时（10分钟）", ft.Colors.ORANGE)
                self.is_recording = False
                self._reset_buttons()
            
            self.page.run_thread(on_timeout)
        
        except Exception as e:
            print(f"❌ Codegen 执行失败: {e}")
            import traceback
            traceback.print_exc()
            
            def on_error():
                self._update_status(f"❌ 录制失败: {str(e)}", ft.Colors.RED)
                self.is_recording = False
                self._reset_buttons()
            
            self.page.run_thread(on_error)
    
    def _show_manual_mode(self, url: str):
        """显示手动模式（当 Playwright 不可用时）"""
        self._update_status(
            "💡 Playwright 未安装，切换到手动模式\n"
            "请使用 pip install playwright 安装以获得自动录制功能",
            ft.Colors.ORANGE
        )
        
        # 打开浏览器
        webbrowser.open(url)
        
        # 显示手动输入界面
        self.captured_info.visible = True
        self.captured_info.content = ft.Column([
            ft.Text("✋ 手动输入认证信息", weight=ft.FontWeight.BOLD, size=13),
            ft.TextField(
                label="Token 或 Cookie",
                multiline=True,
                min_lines=3,
                max_lines=5,
            ),
            ft.Text("提示：从浏览器开发者工具 → Network 标签中复制", size=11, color=ft.Colors.GREY),
        ])
        
        self.page.update()
    
    def _on_cancel(self, e):
        """取消对话框"""
        self.is_recording = False
        self.should_stop = True
        
        # 如果是 Codegen 模式，终止进程及其所有子进程
        if self.codegen_process and self.codegen_process.poll() is None:
            print("🛑 取消录制，终止 Codegen 进程...")
            try:
                import platform
                
                if platform.system() == 'Windows':
                    # Windows: 使用 taskkill 强制终止进程树
                    import subprocess as sp_module
                    pid = self.codegen_process.pid
                    sp_module.run(['taskkill', '/F', '/T', '/PID', str(pid)], 
                          capture_output=True, timeout=5)
                    print(f"✅ 已终止进程树 (PID: {pid})")
                else:
                    # Linux/Mac
                    self.codegen_process.terminate()
                    try:
                        self.codegen_process.wait(timeout=5)
                    except Exception:
                        self.codegen_process.kill()
                        self.codegen_process.wait(timeout=2)
            except Exception as ex:
                print(f"⚠️ 终止进程失败: {ex}")
            finally:
                self.codegen_process = None
        
        self.dialog.open = False
        if hasattr(self, 'page'):
            self.page.update()
    
    def _on_save_captured_data(self, e):
        """保存捕获的所有字段数据"""
        prefix = self.variable_name_field.value.strip()
        
        save_to_env = self.save_to_env_checkbox.value
        saved_count = 0
        errors = []
        
        try:
            # 如果有自动捕获的数据，保存它们
            if self.captured_data:
                for var_name, field_data in self.captured_data.items():
                    # 如果提供了前缀，添加前缀
                    final_name = f"{prefix}_{var_name}" if prefix else var_name
                    value = field_data['value']
                    
                    try:
                        if save_to_env and self.env_manager:
                            # 保存到当前环境
                            active_env = self.env_manager.get_active_environment()
                            if active_env:
                                # 获取当前环境变量
                                current_variables = dict(active_env.variables) if active_env.variables else {}
                                # 添加新字段
                                current_variables[final_name] = value
                                # 更新环境
                                success = self.env_manager.update_environment(
                                    active_env.id,
                                    variables=current_variables
                                )
                                if success:
                                    saved_count += 1
                                else:
                                    errors.append(f"{final_name}: 更新失败")
                            else:
                                errors.append(f"未选择环境")
                        else:
                            # 保存到全局变量
                            from managers.global_variable_manager import GlobalVariableManager
                            global_mgr = GlobalVariableManager()
                            global_mgr.set_variable(final_name, value)
                            saved_count += 1
                    except Exception as ex:
                        errors.append(f"{final_name}: {str(ex)}")
            else:
                # 没有自动捕获的数据，使用手动输入的值
                field_configs = self._get_field_configs()
                
                if field_configs and hasattr(self, 'manual_value_fields'):
                    # 有多个字段配置，遍历每个字段
                    for config in field_configs:
                        field_name = config['name']
                        
                        # 获取对应字段的输入值
                        if field_name in self.manual_value_fields:
                            manual_value = self.manual_value_fields[field_name].value
                            
                            if not manual_value or not manual_value.strip():
                                errors.append(f"{field_name}: 值为空")
                                continue
                            
                            final_name = field_name  # 直接使用配置的字段名
                            
                            try:
                                if save_to_env and self.env_manager:
                                    active_env = self.env_manager.get_active_environment()
                                    if active_env:
                                        # 获取当前环境变量
                                        current_variables = dict(active_env.variables) if active_env.variables else {}
                                        # 添加新字段
                                        current_variables[final_name] = manual_value.strip()
                                        # 更新环境
                                        success = self.env_manager.update_environment(
                                            active_env.id,
                                            variables=current_variables
                                        )
                                        if success:
                                            saved_count += 1
                                        else:
                                            errors.append(f"{final_name}: 更新失败")
                                    else:
                                        errors.append(f"未选择环境")
                                else:
                                    from managers.global_variable_manager import GlobalVariableManager
                                    global_mgr = GlobalVariableManager()
                                    global_mgr.set_variable(final_name, manual_value.strip())
                                    saved_count += 1
                            except Exception as ex:
                                errors.append(f"{final_name}: {str(ex)}")
                        else:
                            errors.append(f"{field_name}: 找不到输入框")
                elif hasattr(self, 'manual_value_field'):
                    # 单个字段，使用旧逻辑
                    manual_value = self.manual_value_field.value
                    if not manual_value or not manual_value.strip():
                        snack_bar = ft.SnackBar(
                            content=ft.Text("❌ 请输入要保存的值"),
                            duration=2000,
                            bgcolor=ft.Colors.RED,
                        )
                        self.page.overlay.append(snack_bar)
                        snack_bar.open = True
                        self.page.update()
                        return
                    
                    # 获取用户配置的字段名称
                    field_configs = self._get_field_configs()
                    
                    # 如果用户配置了字段，使用第一个字段的名称；否则使用前缀或默认值
                    if field_configs:
                        final_name = field_configs[0]['name']  # 使用用户配置的第一个字段名
                    elif prefix:
                        final_name = f"{prefix}_value"
                    else:
                        final_name = "manual_value"
                    
                    try:
                        if save_to_env and self.env_manager:
                            active_env = self.env_manager.get_active_environment()
                            if active_env:
                                # 获取当前环境变量
                                current_variables = dict(active_env.variables) if active_env.variables else {}
                                # 添加新字段
                                current_variables[final_name] = manual_value.strip()
                                # 更新环境
                                success = self.env_manager.update_environment(
                                    active_env.id,
                                    variables=current_variables
                                )
                                if success:
                                    saved_count += 1
                                else:
                                    errors.append(f"{final_name}: 更新失败")
                            else:
                                errors.append(f"未选择环境")
                        else:
                            from managers.global_variable_manager import GlobalVariableManager
                            global_mgr = GlobalVariableManager()
                            global_mgr.set_variable(final_name, manual_value.strip())
                            saved_count += 1
                    except Exception as ex:
                        errors.append(f"{final_name}: {str(ex)}")
                else:
                    snack_bar = ft.SnackBar(
                        content=ft.Text("❌ 没有可保存的数据"),
                        duration=2000,
                        bgcolor=ft.Colors.RED,
                    )
                    self.page.overlay.append(snack_bar)
                    snack_bar.open = True
                    self.page.update()
                    return
            
            # 添加到历史记录 - 只要停止录制就生成记录
            # 获取字段配置
            field_configs = self._get_field_configs()
            
            record = {
                'url': self.url_field.value.strip(),
                'auth_type': 'custom',
                'variable_name': prefix if prefix else (list(self.captured_data.keys())[0] if self.captured_data else 'manual'),
                'value': f'{saved_count} fields',
                'save_location': 'environment' if save_to_env else 'global',
                'created_at': self._get_current_time(),
                'fields_count': saved_count,
                'has_auto_capture': len(self.captured_data) > 0,
                'field_configs': field_configs,  # 添加字段配置
            }
            
            # 优先使用 Codegen 生成的脚本
            if hasattr(self, 'generated_script_file') and self.generated_script_file:
                record['script_file'] = self.generated_script_file
                record['actions_count'] = len(self.user_actions) if self.user_actions else 1
                print(f"✅ 使用 Codegen 生成的脚本: {self.generated_script_file}")
            # 其次使用手动录制的脚本
            elif self.user_actions and len(self.user_actions) > 1:  # 至少有 navigate 之外的操作
                script_content = self._generate_python_script()
                script_filename = f"replay_{self._get_current_time().replace(' ', '_').replace(':', '-')}.py"
                
                try:
                    with open(script_filename, 'w', encoding='utf-8') as f:
                        f.write(script_content)
                    print(f"✅ Python 脚本已保存到: {script_filename}")
                    record['script_file'] = script_filename
                    record['actions_count'] = len(self.user_actions)
                except Exception as e:
                    print(f"⚠️ 保存脚本失败: {e}")
            
            self._add_to_history(record)
            
            # 显示成功提示
            if errors:
                snack_msg = f"✅ 成功保存 {saved_count} 个字段，{len(errors)} 个失败"
                snack_color = ft.Colors.ORANGE
            else:
                snack_msg = f"✅ 成功保存 {saved_count} 个字段"
                snack_color = ft.Colors.GREEN
            
            snack_bar = ft.SnackBar(
                content=ft.Text(snack_msg),
                duration=3000,
                bgcolor=snack_color,
            )
            self.page.overlay.append(snack_bar)
            snack_bar.open = True
            self.page.update()
            
            # 关闭对话框
            self.dialog.open = False
            self.page.update()
            
        except Exception as ex:
            print(f"❌ 保存失败: {ex}")
            import traceback
            traceback.print_exc()
            
            snack_bar = ft.SnackBar(
                content=ft.Text(f"❌ 保存失败: {str(ex)}"),
                duration=5000,
                bgcolor=ft.Colors.RED,
            )
            self.page.overlay.append(snack_bar)
            snack_bar.open = True
            self.page.update()
    
    def _show_captured_data(self, data: dict):
        """显示捕获的数据 - 录制完成页面"""
        # 构建详细的数据列表
        items = []
        
        if data:
            # 有捕获的数据
            items.append(ft.Text(
                f"✅ 录制完成！共捕获 {len(data)} 个字段",
                weight=ft.FontWeight.BOLD,
                size=14,
                color=ft.Colors.GREEN_700,
            ))
            items.append(ft.Divider(height=10))
            
            for idx, (var_name, field_data) in enumerate(data.items(), 1):
                value = field_data['value']
                source = field_data['source']
                path = field_data['path']
                url = field_data.get('url', 'N/A')
                extract_type = field_data.get('extract_type', 'json')  # 获取提取方式
                
                # 根据来源选择图标和颜色
                if source == 'response':
                    icon = ft.Icons.DATA_OBJECT
                    icon_color = ft.Colors.BLUE
                    source_text = "响应体"
                    bg_color = ft.Colors.BLUE_50
                elif source == 'header':
                    icon = ft.Icons.LABEL
                    icon_color = ft.Colors.PURPLE
                    source_text = "响应头"
                    bg_color = ft.Colors.PURPLE_50
                else:  # cookie
                    icon = ft.Icons.COOKIE
                    icon_color = ft.Colors.ORANGE
                    source_text = "Cookie"
                    bg_color = ft.Colors.ORANGE_50
                
                # 提取方式标签
                extract_type_text = "正则" if extract_type == 'regex' else "JSON"
                extract_type_color = ft.Colors.GREEN if extract_type == 'regex' else ft.Colors.BLUE
                
                # 值预览（更智能的截断）
                if len(value) > 80:
                    value_preview = value[:80] + "..."
                else:
                    value_preview = value
                
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
                        ], spacing=6, alignment=ft.MainAxisAlignment.START, wrap=True),
                        
                        # 第二行：值（可复制）
                        ft.Container(
                            content=ft.Row([
                                ft.Text(
                                    value_preview,
                                    size=11,
                                    color=ft.Colors.GREY_800,
                                    selectable=True,
                                    expand=True,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.CONTENT_COPY,
                                    icon_size=16,
                                    tooltip="复制值",
                                    on_click=lambda e, v=value: self._copy_to_clipboard(v),
                                ),
                            ], spacing=5),
                            padding=8,
                            bgcolor=ft.Colors.WHITE,
                            border_radius=4,
                            margin=ft.margin.only(top=4, bottom=4),
                        ),
                        
                        # 第三行：路径/正则表达式
                        ft.Row([
                            ft.Icon(ft.Icons.CODE, size=12, color=ft.Colors.GREY_500),
                            ft.Text(
                                f"{path}",
                                size=10,
                                color=ft.Colors.GREY_600,
                                selectable=True,
                            ),
                        ], spacing=4),
                        
                        # 第四行：URL（如果太长则截断）
                        ft.Row([
                            ft.Icon(ft.Icons.LINK, size=12, color=ft.Colors.GREY_500),
                            ft.Text(
                                url[:70] + "..." if len(url) > 70 else url,
                                size=10,
                                color=ft.Colors.GREY_500,
                                selectable=True,
                            ),
                        ], spacing=4),
                    ], spacing=6),
                    padding=10,
                    bgcolor=bg_color,
                    border_radius=8,
                    margin=ft.margin.only(bottom=10),
                )
                
                items.append(card)
                
        else:
            # 没有捕获到数据，显示手动输入提示
            items.append(ft.Text(
                "⚠️ 未自动捕获到字段",
                weight=ft.FontWeight.BOLD,
                size=14,
                color=ft.Colors.ORANGE_700,
            ))
            items.append(ft.Divider(height=10))
            items.append(ft.Text(
                "您可以手动填写要保存的变量名和值：",
                size=13,
                color=ft.Colors.GREY_700,
            ))
            items.append(ft.Divider(height=10))
        
        # 添加操作提示和保存表单
        self.variable_name_field = ft.TextField(
            label="批量保存前缀（可选）",
            hint_text="例如: api，将保存为 api_user_id, api_token 等",
            width=500,
            text_size=13,
        )
        
        # 如果没有自动捕获的数据，添加手动输入区域
        if not data:
            # 获取用户配置的字段
            field_configs = self._get_field_configs()
            
            if field_configs:
                # 有字段配置，为每个字段创建输入框
                items.append(ft.Text(
                    "✏️ 请为每个配置的字段输入值：",
                    weight=ft.FontWeight.W_500,
                    size=13,
                    color=ft.Colors.GREY_800,
                ))
                items.append(ft.Container(height=5))
                
                # 为每个字段创建输入框
                self.manual_value_fields = {}  # 保存所有字段的输入框引用
                for config in field_configs:
                    field_name = config['name']
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
                                    content=ft.Text(source_text, size=9, color=ft.Colors.WHITE),
                                    padding=ft.padding.symmetric(horizontal=4, vertical=1),
                                    bgcolor=icon_color,
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
                        bgcolor=ft.Colors.GREY_50,
                        border_radius=6,
                        border=ft.border.all(1, ft.Colors.GREY_200),
                        margin=ft.margin.only(bottom=8),
                    )
                    
                    items.append(field_card)
                    
                    # 保存输入框引用（通过最后一个 TextField）
                    self.manual_value_fields[field_name] = field_card.content.controls[-1]
                
                items.append(ft.Divider(height=10))
            else:
                # 没有字段配置，使用单个输入框
                self.manual_value_field = ft.TextField(
                    label="手动输入值",
                    hint_text="请输入要保存的值",
                    width=500,
                    multiline=True,
                    min_lines=3,
                    max_lines=5,
                    text_size=13,
                )
                items.append(self.manual_value_field)
                items.append(ft.Text(
                    "💡 提示：您也可以从浏览器开发者工具中复制数据粘贴到这里",
                    size=11,
                    color=ft.Colors.GREY_600,
                ))
                items.append(ft.Divider(height=10))
        else:
            # 有自动捕获的数据，检查是否有未捕获的字段配置
            field_configs = self._get_field_configs()
            captured_names = set(data.keys())
            
            # 找出配置了但未捕获到的字段
            missing_fields = [config for config in field_configs if config['name'] not in captured_names]
            
            if missing_fields:
                # 有未捕获的字段，显示手动输入框
                items.append(ft.Divider(height=10))
                items.append(ft.Text(
                    f"⚠️ 以下 {len(missing_fields)} 个字段未自动捕获到，请手动输入：",
                    weight=ft.FontWeight.W_500,
                    size=13,
                    color=ft.Colors.ORANGE_700,
                ))
                items.append(ft.Container(height=5))
                
                # 为每个未捕获的字段创建输入框
                if not hasattr(self, 'manual_value_fields'):
                    self.manual_value_fields = {}
                
                for config in missing_fields:
                    field_name = config['name']
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
                                    content=ft.Text("未捕获", size=9, color=ft.Colors.WHITE),
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
                    self.manual_value_fields[field_name] = field_card.content.controls[-1]
        
        self.save_to_env_checkbox = ft.Checkbox(
            label="保存到当前环境（否则保存到全局变量）",
            value=True,
        )
        
        save_btn = ft.Button(
            "保存所有字段",
            icon=ft.Icons.SAVE,
            on_click=self._on_save_captured_data,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.PURPLE_600,
                color=ft.Colors.WHITE,
            ),
            width=500,
        )
        
        items.extend([
            ft.Divider(height=10),
            self.variable_name_field,
            self.save_to_env_checkbox,
            save_btn,
        ])
        
        # 使用 ListView 使内容可滚动
        self.captured_info.content = ft.ListView(
            controls=items,
            expand=True,
            spacing=8,
            padding=5,
            auto_scroll=False,  # 不自动滚动
        )
        self.captured_info.visible = True
        
        # 更新对话框以应用新的高度
        if hasattr(self, 'page'):
            self.page.update()
    
    def _copy_to_clipboard(self, text: str):
        """复制文本到剪贴板"""
        try:
            import pyperclip
            pyperclip.copy(text)
            
            # 显示提示
            snack_bar = ft.SnackBar(
                content=ft.Text("✅ 已复制到剪贴板"),
                duration=1500,
                bgcolor=ft.Colors.GREEN,
            )
            self.page.overlay.append(snack_bar)
            snack_bar.open = True
            self.page.update()
        except ImportError:
            # 如果没有安装 pyperclip，使用 Flet 的剪贴板 API
            try:
                self.page.set_clipboard(text)
                snack_bar = ft.SnackBar(
                    content=ft.Text("✅ 已复制到剪贴板"),
                    duration=1500,
                    bgcolor=ft.Colors.GREEN,
                )
                self.page.overlay.append(snack_bar)
                snack_bar.open = True
                self.page.update()
            except Exception as e:
                print(f"⚠️ 复制失败: {e}")
    
    def _update_status(self, message: str, color: str):
        """更新状态文本"""
        self.status_text.value = message
        self.status_text.color = color
        if hasattr(self, 'page'):
            self.page.update()
    
    def _reset_buttons(self):
        """重置按钮状态"""
        if hasattr(self, 'dialog'):
            # actions[0] 是 btn_row，buttons 在 controls 中
            btn_row = self.dialog.actions[0]
            btn_row.controls[0].disabled = False  # 启用开始按钮
            if hasattr(self, 'page'):
                self.page.update()
    
    def _add_to_history(self, record: dict):
        """添加到历史记录（数据库）"""
        try:
            from services.recording_history_service import RecordingHistoryService
            
            # 读取脚本内容
            script_content = ""
            if record.get('script_file'):
                try:
                    with open(record['script_file'], 'r', encoding='utf-8') as f:
                        script_content = f.read()
                except Exception as e:
                    print(f"⚠️ 读取脚本文件失败: {e}")
            
            # 添加脚本内容到记录
            record['script_content'] = script_content
            
            # 保存到数据库
            service = RecordingHistoryService()
            record_id = service.add_record(record)
            
            if record_id:
                print(f"✅ 录制记录已保存到数据库")
            else:
                print(f"❌ 保存录制记录失败")
        except Exception as e:
            print(f"❌ 保存历史记录失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _generate_python_script(self) -> str:
        """生成可执行的 Python 脚本（带 HAR 文件支持）"""
        # 生成 HAR 文件名
        har_filename = f"recording_{self._get_current_time().replace(' ', '_').replace(':', '-')}.har"
        
        script_lines = [
            '"""',
            '自动录制的 Playwright 脚本',
            f'生成时间: {self._get_current_time()}',
            f'目标 URL: {self.url_field.value.strip()}',
            f'HAR 文件: {har_filename}（记录所有网络请求）',
            '"""',
            'from playwright.sync_api import sync_playwright',
            'import time',
            'import json',
            '',
            'def run():',
            '    with sync_playwright() as p:',
            '        browser = p.chromium.launch(headless=False)',
            f'        # 启用 HAR 记录',
            f'        context = browser.new_context(record_har_path="{har_filename}")',
            '        page = context.new_page()',
            '',
        ]
        
        # 添加用户操作步骤
        for action in self.user_actions:
            if action['type'] == 'navigate':
                script_lines.append(f'        # 导航到页面')
                script_lines.append(f'        page.goto("{action["url"]}")')
                script_lines.append(f'        page.wait_for_load_state("networkidle")')
                script_lines.append('')
            
            elif action['type'] == 'click':
                selector = action.get('selector', '')
                if selector:
                    script_lines.append(f'        # 点击元素')
                    script_lines.append(f'        page.click("{selector}")')
                    script_lines.append(f'        time.sleep(0.5)  # 等待')
                    script_lines.append('')
            
            elif action['type'] == 'input':
                selector = action.get('selector', '')
                value = action.get('value', '')
                if selector:
                    script_lines.append(f'        # 输入文本')
                    script_lines.append(f'        page.fill("{selector}", "{value}")')
                    script_lines.append(f'        time.sleep(0.3)  # 等待')
                    script_lines.append('')
        
        script_lines.extend([
            '        print("✅ 脚本执行完成")',
            f'        print(f"📄 HAR 文件已保存: {har_filename}")',
            '        print("💡 提示: 可以使用以下工具分析 HAR 文件:")',
            '        print("   - Chrome DevTools: chrome://net-export/")',
            '        print("   - HAR Viewer: https://toolbox.googleapps.com/apps/har_analyzer/")',
            '        print("   - Fiddler, Charles 等抓包工具")',
            '        time.sleep(2)',
            '        browser.close()',
            '',
            'if __name__ == "__main__":',
            '    run()',
        ])
        
        return '\n'.join(script_lines)
    
    def show(self, page):
        """显示对话框"""
        self.page = page
        page.overlay.append(self.dialog)
        self.dialog.open = True
        page.update()
