"""主界面模块 - 构建完整的 API 测试界面"""

import flet as ft
import threading

from models import HttpRequest, HttpMethod
from services import HttpService
from history_manager import HistoryManager
from environment_manager import EnvironmentManager
from global_variable_manager import GlobalVariableManager
from request_list_manager import RequestListManager
from ui_components import DynamicKeyValueList, ResponsePanel, BodyEditor, RequestRunner


class ApiTestPage:
    """API 测试主界面"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.http_service = HttpService()
        self.history_manager = HistoryManager()
        self.env_manager = EnvironmentManager()
        self.global_var_manager = GlobalVariableManager()
        self.request_list_manager = RequestListManager()
        self.is_loading = False

        # 设置页面属性
        self.page.title = "MyPostMan - API 测试工具"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.window_width = 1400
        self.page.window_height = 900
        self.page.window_min_width = 1000
        self.page.window_min_height = 700

        self._build_ui()
    
    def _on_toggle_history(self, e):
        """切换历史记录区域的展开/折叠"""
        # 获取当前可见状态
        content_container = self.history_section.controls[1]
        is_visible = content_container.visible

        # 切换可见性
        content_container.visible = not is_visible

        # 更新图标（展开/折叠按钮在 Row 的 controls[0] 位置）
        toggle_btn = self.history_section.controls[0].content.controls[1].controls[0]
        toggle_btn.icon = ft.Icons.EXPAND_LESS if not is_visible else ft.Icons.EXPAND_MORE

        self.history_section.update()
    
    def _on_toggle_request_list(self, e):
        """切换请求列表区域的展开/折叠"""
        # 获取当前可见状态
        content_container = self.request_list_section.controls[1]
        is_visible = content_container.visible

        # 切换可见性
        content_container.visible = not is_visible

        # 更新图标（展开/折叠按钮在 Row 的 controls[2] 位置）
        toggle_btn = self.request_list_section.controls[0].content.controls[1].controls[2]
        toggle_btn.icon = ft.Icons.EXPAND_LESS if not is_visible else ft.Icons.EXPAND_MORE

        self.request_list_section.update()
    
    def _update_request_list_view(self):
        """更新请求 URL 列表视图"""
        self.request_list_view.controls.clear()
        
        requests = self.request_list_manager.get_all_requests()
        for req in requests:
            # 创建列表项
            tile = ft.ListTile(
                leading=ft.Container(
                    content=ft.Text(
                        req.method[:3],
                        size=10,
                        color=ft.Colors.WHITE,
                        weight=ft.FontWeight.BOLD,
                    ),
                    bgcolor=ft.Colors.BLUE,
                    padding=5,
                    border_radius=4,
                ),
                title=ft.Text(
                    req.name or req.url,
                    size=12,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                subtitle=ft.Text(
                    req.url,
                    size=10,
                    color=ft.Colors.GREY_600,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                trailing=ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_size=18,
                    tooltip="删除此项",
                    on_click=lambda e, req_id=req.id: self._on_remove_request(req_id),
                ),
                data=req,
                on_click=self._on_request_list_click,
            )
            self.request_list_view.controls.append(tile)
        
        # 更新视图
        try:
            if self.request_list_view.page:
                self.request_list_view.update()
        except RuntimeError:
            pass

    async def _on_import_from_clipboard(self, e):
        """从剪贴板导入 URL"""
        try:
            # 获取剪贴板内容（异步调用）
            clipboard_text = await self.page.clipboard.get()

            if not clipboard_text:
                snack_bar = ft.SnackBar(content=ft.Text("剪贴板为空"), duration=2000)
                self.page.overlay.append(snack_bar)
                snack_bar.open = True
                self.page.update()
                return

            # 导入到请求列表
            imported = self.request_list_manager.import_from_clipboard(clipboard_text)

            if imported:
                self._update_request_list_view()
                snack_bar = ft.SnackBar(
                    content=ft.Text(f"成功导入 {len(imported)} 个 URL"),
                    duration=2000
                )
                self.page.overlay.append(snack_bar)
                snack_bar.open = True
                self.page.update()
            else:
                snack_bar = ft.SnackBar(content=ft.Text("未找到有效的 URL"), duration=2000)
                self.page.overlay.append(snack_bar)
                snack_bar.open = True
                self.page.update()
        except Exception as ex:
            snack_bar = ft.SnackBar(content=ft.Text(f"导入失败: {str(ex)}"), duration=2000)
            self.page.overlay.append(snack_bar)
            snack_bar.open = True
            self.page.update()
    
    def _on_add_to_request_list(self, e):
        """添加当前 URL 到请求列表"""
        url = self.url_input.value.strip()
        if not url:
            snack_bar = ft.SnackBar(content=ft.Text("请先输入 URL"), duration=2000)
            self.page.overlay.append(snack_bar)
            snack_bar.open = True
            self.page.update()
            return
        
        # 构建完整 URL
        full_url = self._build_full_url(url)
        
        # 获取当前参数
        params = self.params_list.get_data()
        headers = self.headers_list.get_data()
        method = self.method_dropdown.value
        
        # 添加到请求列表
        self.request_list_manager.add_request(
            url=full_url,
            method=method,
            params=params,
            headers=headers
        )
        
        self._update_request_list_view()
        snack_bar = ft.SnackBar(content=ft.Text("已添加到请求列表"), duration=2000)
        self.page.overlay.append(snack_bar)
        snack_bar.open = True
        self.page.update()
    
    def _on_clear_request_list(self, e):
        """清空请求列表"""
        self.request_list_manager.clear_all()
        self._update_request_list_view()
        snack_bar = ft.SnackBar(content=ft.Text("请求列表已清空"), duration=2000)
        self.page.overlay.append(snack_bar)
        snack_bar.open = True
        self.page.update()
    
    def _on_remove_request(self, request_id: str):
        """删除请求列表项"""
        self.request_list_manager.remove_request(request_id)
        self._update_request_list_view()
    
    def _on_request_list_click(self, e):
        """点击请求列表项"""
        req = e.control.data
        if req:
            # 从完整 URL 中提取路径部分
            path_url = self._extract_path_from_url(req.url)
            
            # 设置 URL
            self.url_input.value = path_url
            
            # 设置请求方法
            self.method_dropdown.value = req.method
            
            # 设置参数
            if req.params:
                self.params_list.set_data(req.params)
            
            # 设置请求头
            if req.headers:
                self.headers_list.set_data(req.headers)
            
            # 更新 UI
            self.page.update()
            
            snack_bar = ft.SnackBar(content=ft.Text(f"已加载: {req.name or req.url}"), duration=1500)
            self.page.overlay.append(snack_bar)
            snack_bar.open = True
            self.page.update()

    def _build_ui(self):
        """构建整个界面"""
        # 主布局：左侧历史 + 右侧主内容
        main_row = ft.Row(
            controls=[
                self._build_sidebar(),
                ft.VerticalDivider(width=1),
                self._build_main_content(),
            ],
            expand=True,
        )

        self.page.add(main_row)

    def _build_sidebar(self) -> ft.Container:
        """构建侧边栏（历史记录 + 环境管理 + 请求列表）"""
        self.history_list = ft.ListView(
            expand=True,
            spacing=8,
            padding=8,
        )
        
        # 清空历史按钮（必须在 history_section 之前定义）
        self.clear_history_btn = ft.Button(
            "清空历史",
            icon=ft.Icons.DELETE_SWEEP,
            on_click=self._on_clear_history,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREY_200,
                color=ft.Colors.GREY_800,
            ),
        )

        # 请求列表
        self.request_list_view = ft.ListView(
            expand=True,
            spacing=6,
            padding=8,
        )
        self._update_request_list_view()
        
        # 历史记录区域（可展开）
        self.history_section = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text("历史记录", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
                            ft.Row(
                                controls=[
                                    ft.IconButton(
                                        icon=ft.Icons.EXPAND_MORE,
                                        icon_size=20,
                                        on_click=self._on_toggle_history,
                                    ),
                                ],
                                spacing=0,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                ),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            self.history_list,
                            ft.Container(height=10),
                            ft.Row(
                                controls=[
                                    ft.TextButton(
                                        "清空历史",
                                        icon=ft.Icons.DELETE_SWEEP,
                                        on_click=self._on_clear_history,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.END,
                            ),
                        ],
                        spacing=0,
                    ),
                    expand=True,
                    visible=True,
                ),
            ],
            spacing=0,
        )
        
        # 请求列表区域（可展开）
        self.request_list_section = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text("请求列表", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
                            ft.Row(
                                controls=[
                                    ft.IconButton(
                                        icon=ft.Icons.ADD,
                                        icon_size=18,
                                        tooltip="添加当前请求到列表",
                                        on_click=self._on_add_to_request_list,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.CONTENT_PASTE,
                                        icon_size=18,
                                        tooltip="从剪贴板导入",
                                        on_click=self._on_import_from_clipboard,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.EXPAND_MORE,
                                        icon_size=20,
                                        on_click=self._on_toggle_request_list,
                                    ),
                                ],
                                spacing=0,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                ),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            self.request_list_view,
                            ft.Container(height=10),
                            ft.Row(
                                controls=[
                                    ft.TextButton(
                                        "清空列表",
                                        icon=ft.Icons.DELETE_SWEEP,
                                        on_click=self._on_clear_request_list,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.END,
                            ),
                        ],
                        spacing=0,
                    ),
                    expand=True,
                    visible=True,
                ),
            ],
            spacing=0,
        )

        # 环境选择下拉框
        self.env_dropdown = ft.Dropdown(
            label="环境",
            width=220,
            on_text_change=self._on_env_change,
            text_size=14,
        )
        self._update_env_dropdown()

        # 环境管理按钮
        self.manage_env_btn = ft.Button(
            "管理环境",
            icon=ft.Icons.SETTINGS,
            on_click=self._on_manage_environments,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_50,
                color=ft.Colors.BLUE,
            ),
        )

        # 全局变量管理按钮
        self.manage_global_var_btn = ft.Button(
            "全局变量",
            icon=ft.Icons.ADD,
            on_click=self._on_manage_global_variables,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_50,
                color=ft.Colors.GREEN,
            ),
        )

        # 当前环境信息显示
        self.env_info_text = ft.Text(
            "未选择环境",
            size=12,
            color=ft.Colors.GREY_700,
            weight=ft.FontWeight.W_500,
        )
        self._update_env_info()

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("环境管理", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
                                self.env_dropdown,
                                ft.Row(
                                    controls=[
                                        self.manage_env_btn,
                                        self.manage_global_var_btn,
                                    ],
                                    spacing=8,
                                ),
                                self.env_info_text,
                            ],
                            spacing=10,
                        ),
                        padding=12,
                        bgcolor=ft.Colors.BLUE_50,
                        border_radius=8,
                    ),
                    ft.Divider(height=15),
                    # 请求列表区域
                    self.request_list_section,
                    ft.Divider(height=15),
                    # 历史记录区域
                    self.history_section,
                ],
                spacing=8,
            ),
            width=300,
            bgcolor=ft.Colors.GREY_100,
            padding=15,
        )

    def _build_main_content(self) -> ft.Container:
        """构建主内容区（请求表单 + 响应展示）"""
        # 请求方法下拉框
        self.method_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("GET"),
                ft.dropdown.Option("POST"),
                ft.dropdown.Option("PUT"),
                ft.dropdown.Option("DELETE"),
                ft.dropdown.Option("PATCH"),
                ft.dropdown.Option("HEAD"),
                ft.dropdown.Option("OPTIONS"),
            ],
            value="GET",
            width=140,
            label="方法",
            text_size=14,
            label_style=ft.TextStyle(size=13, weight=ft.FontWeight.BOLD),
        )

        # URL 输入框
        self.url_input = ft.TextField(
            # label="请求 URL",
            expand=True,
            hint_text="api/endpoint",
            prefix="",
            text_size=14,
            label_style=ft.TextStyle(size=13, weight=ft.FontWeight.BOLD),
        )
        
        # 初始化 URL 前缀
        self._update_url_prefix()

        # 发送按钮
        self.send_btn = ft.Button(
            "发送",
            icon=ft.Icons.SEND,
            on_click=self._on_send_request,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE,
                color=ft.Colors.WHITE,
                padding=ft.padding.symmetric(vertical=12, horizontal=20),
                text_style=ft.TextStyle(size=15, weight=ft.FontWeight.BOLD),
            ),
        )
        
        # Headers 和 Params 列表
        self.headers_list = DynamicKeyValueList()
        self.params_list = DynamicKeyValueList()
        
        # Body 编辑器
        self.body_editor = BodyEditor()
        
        # 请求运行器（请求次数和并发数）
        self.request_runner = RequestRunner()

        # 请求配置 Tabs（使用 TabBar + TabBarView）
        self.request_tabs = ft.Tabs(
            length=4,
            selected_index=0,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        tab_alignment=ft.TabAlignment.START,
                        tabs=[
                            ft.Tab(label=ft.Text("Params")),
                            ft.Tab(label=ft.Text("Headers")),
                            ft.Tab(label=ft.Text("Body")),
                            ft.Tab(label=ft.Text("Runner")),
                        ],
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            self.params_list,
                            self.headers_list,
                            self.body_editor,
                            self.request_runner,
                        ],
                    ),
                ],
            ),
        )

        # 响应面板
        self.response_panel = ResponsePanel()

        # 加载指示器
        self.loading_indicator = ft.ProgressRing(
            visible=False,
            width=30,
            height=30,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    # 顶部：URL 输入行
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                self.method_dropdown,
                                self.url_input,
                                self.loading_indicator,
                                self.send_btn,
                            ],
                            spacing=8,
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        padding=12,
                        bgcolor=ft.Colors.GREY_50,
                        border_radius=8,
                    ),
                    ft.Container(height=8),
                    # 中间：请求配置 Tabs
                    ft.Container(
                        content=self.request_tabs,
                        expand=True,
                    ),
                    ft.Container(height=8),
                    # 底部：响应展示
                    ft.Container(
                        content=self.response_panel,
                        expand=True,
                    ),
                ],
                expand=True,
                spacing=0,
            ),
            expand=True,
            padding=15,
        )

    def _on_send_request(self, e):
        """发送请求按钮点击事件"""
        if self.is_loading:
            return

        url = self.url_input.value.strip()
        if not url:
            snack_bar = ft.SnackBar(content=ft.Text("请输入请求 URL"), duration=2000)
            self.page.overlay.append(snack_bar)
            snack_bar.open = True
            self.page.update()
            return

        # 显示加载状态
        self.is_loading = True
        self.loading_indicator.visible = True
        self.send_btn.disabled = True
        self.loading_indicator.update()
        self.send_btn.update()
        
        # 重置进度
        self.request_runner.reset_progress()

        # 在新线程中发送请求，支持多次请求和并发
        thread = threading.Thread(
            target=self._send_requests_thread,
            args=(url,)
        )
        thread.start()

    def _send_requests_thread(self, url: str):
        """在线程中发送请求（支持多次和并发）"""
        request_count = self.request_runner.get_request_count()
        concurrency_count = self.request_runner.get_concurrency_count()
        
        # 如果只请求一次，使用原有逻辑
        if request_count == 1:
            self._send_single_request(url)
            return
        
        # 多次请求，支持并发
        import concurrent.futures
        
        success_count = 0
        fail_count = 0
        total = request_count
        
        try:
            # 使用线程池实现并发
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency_count) as executor:
                # 提交所有任务
                future_to_index = {
                    executor.submit(self._send_single_request_internal, url, i): i
                    for i in range(request_count)
                }
                
                # 处理完成的任务
                for i, future in enumerate(concurrent.futures.as_completed(future_to_index)):
                    index = future_to_index[future] + 1
                    try:
                        success = future.result()
                        if success:
                            success_count += 1
                        else:
                            fail_count += 1
                        
                        # 更新进度
                        progress = i / total
                        self.page.run_thread(
                            self.request_runner.set_progress,
                            progress,
                            f"进度: {i}/{total} (成功: {success_count}, 失败: {fail_count})"
                        )
                    except Exception as e:
                        fail_count += 1
                        self.page.run_thread(
                            self.request_runner.set_progress,
                            (i + 1) / total,
                            f"进度: {i+1}/{total} (成功: {success_count}, 失败: {fail_count})"
                        )
            
            # 完成
            self.page.run_thread(
                self.request_runner.set_progress,
                1.0,
                f"完成! 总计: {total}, 成功: {success_count}, 失败: {fail_count}"
            )
            
            # 恢复按钮状态
            self.page.run_thread(self._reset_ui_after_requests)
            
        except Exception as e:
            self.page.run_thread(self._handle_request_error, f"批量请求失败: {str(e)}")

    def _send_single_request(self, url: str):
        """发送单次请求（原有逻辑）"""
        try:
            # 获取 base_url 并拼接完整 URL
            full_url = self._build_full_url(url)
            
            # 解析变量
            resolved_url = self._resolve_variables(full_url)
            resolved_headers = {k: self._resolve_variables(v) for k, v in self.headers_list.get_data().items()}
            resolved_params = {k: self._resolve_variables(v) for k, v in self.params_list.get_data().items()}
            resolved_body = self._resolve_variables(self.body_editor.get_body()) if self.body_editor.get_body_type() != "none" else None
            body_type = self.body_editor.get_body_type()

            # 构建请求对象
            method = HttpMethod(self.method_dropdown.value)

            request = HttpRequest(
                url=resolved_url,
                method=method,
                headers=resolved_headers,
                params=resolved_params,
                body=resolved_body,
                body_type=body_type,
            )

            # 发送请求（使用 Runner 中的 SSL 设置）
            verify_ssl = self.request_runner.is_ssl_verify()
            response = self.http_service.send_request(request, verify_ssl=verify_ssl)

            # 添加到历史记录
            self.history_manager.add_entry(request, response)

            # 更新 UI（需要在主线程中执行）
            self.page.run_thread(self._update_ui_after_request, response)

        except Exception as e:
            self.page.run_thread(self._handle_request_error, str(e))

    def _send_single_request_internal(self, url: str, index: int) -> bool:
        """发送单次请求（内部方法，返回是否成功）"""
        try:
            # 获取 base_url 并拼接完整 URL
            full_url = self._build_full_url(url)
            
            # 解析变量
            resolved_url = self._resolve_variables(full_url)
            resolved_headers = {k: self._resolve_variables(v) for k, v in self.headers_list.get_data().items()}
            resolved_params = {k: self._resolve_variables(v) for k, v in self.params_list.get_data().items()}
            resolved_body = self._resolve_variables(self.body_editor.get_body()) if self.body_editor.get_body_type() != "none" else None
            body_type = self.body_editor.get_body_type()

            # 构建请求对象
            method = HttpMethod(self.method_dropdown.value)

            request = HttpRequest(
                url=resolved_url,
                method=method,
                headers=resolved_headers,
                params=resolved_params,
                body=resolved_body,
                body_type=body_type,
            )

            # 发送请求（使用 Runner 中的 SSL 设置）
            verify_ssl = self.request_runner.is_ssl_verify()
            response = self.http_service.send_request(request, verify_ssl=verify_ssl)

            # 添加到历史记录
            self.history_manager.add_entry(request, response)

            # 如果是第一次，更新 UI
            if index == 0:
                self.page.run_thread(self._update_ui_after_request, response)

            return response.is_success

        except Exception:
            return False

    def _reset_ui_after_requests(self):
        """请求完成后重置 UI 状态"""
        self.is_loading = False
        self.loading_indicator.visible = False
        self.send_btn.disabled = False
        self.loading_indicator.update()
        self.send_btn.update()

    def _build_full_url(self, url: str) -> str:
        """
        构建完整的 URL（拼接 base_url 和用户输入的路径）
        
        Args:
            url: 用户输入的 URL 路径
            
        Returns:
            str: 完整的 URL
        """
        if not url:
            return ""
        
        # 如果用户输入的是完整 URL（以 http:// 或 https:// 开头），直接返回
        if url.startswith('http://') or url.startswith('https://'):
            return url
        
        # 获取活动环境的 base_url
        active_env = self.env_manager.get_active_environment()
        if active_env and 'base_url' in active_env.variables:
            base_url = active_env.variables['base_url']
            
            # 确保 base_url 不以斜杠结尾，用户输入以斜杠开头
            base_url = base_url.rstrip('/')
            if not url.startswith('/'):
                url = '/' + url
            
            return base_url + url
        else:
            # 没有环境或没有 base_url，返回原始输入
            return url

    def _resolve_variables(self, text: str) -> str:
        """
        解析文本中的变量（{{variable_name}}格式）

        变量解析优先级：
        1. 环境变量（如果选择了环境）
        2. 全局变量

        支持环境变量中引用全局变量，如：{{global_var_name}}

        Args:
            text: 包含变量的文本

        Returns:
            str: 解析后的文本
        """
        import re

        if not text:
            return text

        # 获取所有变量
        all_vars = {}

        # 首先添加全局变量（优先级较低）
        all_vars.update(self.global_var_manager.get_all_variables())

        # 然后添加环境变量（优先级较高，会覆盖全局变量）
        env_vars = self.env_manager.get_active_variables()
        all_vars.update(env_vars)

        # 解析 {{variable}} 格式的变量
        def replace_var(match):
            var_name = match.group(1)
            return all_vars.get(var_name, match.group(0))  # 如果变量不存在，保留原文

        # 替换所有匹配的变量（支持多轮解析，处理环境变量中引用全局变量的情况）
        resolved_text = text
        # 最多解析 10 轮，防止无限循环
        for _ in range(10):
            new_text = re.sub(r'\{\{(\w+)\}\}', replace_var, resolved_text)
            # 如果没有更多变量可替换，退出循环
            if new_text == resolved_text:
                break
            resolved_text = new_text

        return resolved_text

    def _update_ui_after_request(self, response):
        """请求完成后更新 UI"""
        # 更新响应面板
        self.response_panel.update_response(response)

        # 更新历史记录列表
        self._update_history_list()

        # 恢复按钮状态
        self.is_loading = False
        self.loading_indicator.visible = False
        self.send_btn.disabled = False
        self.loading_indicator.update()
        self.send_btn.update()

    def _handle_request_error(self, error_msg: str):
        """处理请求错误"""
        self.response_panel.update_response(
            type('HttpResponse', (), {'error': error_msg, 'elapsed': 0})()
        )

        # 恢复按钮状态
        self.is_loading = False
        self.loading_indicator.visible = False
        self.send_btn.disabled = False
        self.loading_indicator.update()
        self.send_btn.update()

    def _update_history_list(self):
        """更新历史记录列表显示"""
        self.history_list.controls.clear()

        history = self.history_manager.get_recent(50)
        for entry in history:
            # 状态码颜色
            if entry.response.is_success:
                color = ft.Colors.GREEN
            elif entry.status_code >= 400:
                color = ft.Colors.RED
            else:
                color = ft.Colors.ORANGE

            tile = ft.ListTile(
                leading=ft.Container(
                    content=ft.Text(
                        entry.method.value[:3],
                        size=10,
                        color=ft.Colors.WHITE,
                        weight=ft.FontWeight.BOLD,
                    ),
                    bgcolor=ft.Colors.BLUE,
                    padding=5,
                    border_radius=4,
                ),
                title=ft.Text(
                    entry.url,
                    size=12,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                subtitle=ft.Text(
                    f"{entry.status_code} · {entry.elapsed}ms",
                    size=10,
                    color=color,
                ),
                data=entry,
                on_click=self._on_history_click,
            )
            self.history_list.controls.append(tile)

        self.history_list.update()

    def _on_history_click(self, e):
        """点击历史记录项"""
        entry = e.control.data
        if entry:
            # 恢复请求数据
            self.method_dropdown.value = entry.method.value
            
            # 从完整 URL 中提取路径部分（移除 base_url 前缀）
            full_url = entry.request.url
            path_url = self._extract_path_from_url(full_url)
            
            self.url_input.value = path_url
            self.headers_list.set_data(entry.request.headers)
            self.params_list.set_data(entry.request.params)
            self.body_editor.set_body(entry.request.body or "")
            self.body_editor.set_body_type(entry.request.body_type)

            # 更新响应
            self.response_panel.update_response(entry.response)

            # 更新所有控件
            self.page.update()

    def _on_clear_history(self, e):
        """清空历史记录"""
        self.history_manager.clear()
        self.history_list.controls.clear()
        self.history_list.update()
        snack_bar = ft.SnackBar(content=ft.Text("历史记录已清空"), duration=2000)
        self.page.overlay.append(snack_bar)
        snack_bar.open = True
        self.page.update()

    def _update_env_dropdown(self):
        """更新环境下拉框选项"""
        self.env_dropdown.options = [
            ft.dropdown.Option(env.id, env.name)
            for env in self.env_manager.get_all_environments()
        ]
        active_env = self.env_manager.get_active_environment()
        if active_env:
            self.env_dropdown.value = active_env.id

    def _update_env_info(self):
        """更新环境信息显示"""
        active_env = self.env_manager.get_active_environment()
        if active_env:
            var_count = len(active_env.variables)
            self.env_info_text.value = f"当前: {active_env.name} ({var_count}个变量)"
        else:
            self.env_info_text.value = "未选择环境"

    def _on_env_change(self, e):
        """环境切换事件"""
        env_id = self.env_dropdown.value
        if env_id:
            self.env_manager.set_active(env_id)
            self._update_env_info()
            # 更新 URL 前缀
            self._update_url_prefix()
            snack_bar = ft.SnackBar(content=ft.Text(f"已切换到环境: {self.env_manager.get_active_environment().name}"), duration=2000)
            self.page.overlay.append(snack_bar)
            snack_bar.open = True
            self.page.update()
    
    def _extract_path_from_url(self, full_url: str) -> str:
        """
        从完整 URL 中提取路径部分（移除 base_url 前缀）
        
        Args:
            full_url: 完整的 URL
            
        Returns:
            str: 路径部分（用于显示在输入框中）
        """
        if not full_url:
            return ""
        
        # 获取活动环境的 base_url
        active_env = self.env_manager.get_active_environment()
        if active_env and 'base_url' in active_env.variables:
            base_url = active_env.variables['base_url'].rstrip('/')
            
            # 如果完整 URL 以 base_url 开头，移除 base_url 前缀
            if full_url.startswith(base_url):
                path = full_url[len(base_url):]
                # 移除开头的斜杠
                if path.startswith('/'):
                    path = path[1:]
                return path
        
        # 如果是完整 URL（以 http:// 或 https:// 开头），尝试提取路径
        if full_url.startswith('http://') or full_url.startswith('https://'):
            # 移除协议前缀
            if full_url.startswith('http://'):
                rest = full_url[7:]
            else:
                rest = full_url[8:]
            
            # 找到第一个斜杠，后面的是路径
            slash_pos = rest.find('/')
            if slash_pos > 0:
                return rest[slash_pos + 1:]
        
        # 返回原始输入
        return full_url

    def _update_url_prefix(self):
        """根据环境的 base_url 更新 URL 前缀"""
        active_env = self.env_manager.get_active_environment()

        if active_env and 'base_url' in active_env.variables:
            base_url = active_env.variables['base_url']
            # 解析 base_url，提取协议和域名部分
            # 例如: http://localhost:8080/api -> http://localhost:8080
            if base_url.startswith('http://'):
                base_url = base_url[7:]
            elif base_url.startswith('https://'):
                base_url = base_url[8:]

            # 找到第一个斜杠，前面的是协议+域名
            slash_pos = base_url.find('/')
            if slash_pos > 0:
                domain = base_url[:slash_pos]
                self.url_input.prefix = domain + '/'
            else:
                self.url_input.prefix = base_url + '/'
        else:
            # 没有环境或没有 base_url，使用默认前缀
            self.url_input.prefix = ""

        # 更新 URL 值（移除已有的前缀部分）
        current_url = self.url_input.value or ""
        if current_url.startswith('http://') or current_url.startswith('https://'):
            # 移除完整的 URL 前缀
            if current_url.startswith('http://'):
                current_url = current_url[7:]
            else:
                current_url = current_url[8:]

            # 找到域名部分并移除
            slash_pos = current_url.find('/')
            if slash_pos > 0:
                current_url = current_url[slash_pos + 1:]

            self.url_input.value = current_url

        # 只有在控件已添加到页面时才调用 update
        try:
            if self.url_input.page:
                self.url_input.update()
        except RuntimeError:
            # 控件还未添加到页面，忽略此错误
            pass

    def _on_manage_environments(self, e):
        """打开环境管理对话框"""
        self._show_environment_dialog()

    def _show_environment_dialog(self):
        """显示环境管理对话框"""
        # 环境列表
        env_list_view = ft.ListView(expand=True, spacing=8)

        def refresh_env_list():
            env_list_view.controls.clear()
            for env in self.env_manager.get_all_environments():
                is_active = env.is_active
                # 使用卡片样式展示环境信息
                card = ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(
                                ft.Icons.CHECK_CIRCLE if is_active else ft.Icons.RADIO_BUTTON_UNCHECKED,
                                color=ft.Colors.GREEN if is_active else ft.Colors.GREY_400,
                                size=24,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(env.name, size=16, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"{len(env.variables)} 个变量", size=12, color=ft.Colors.GREY_600),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Button(
                                        "编辑",
                                        icon=ft.Icons.EDIT,
                                        on_click=lambda ev, env_id=env.id: self._show_edit_environment_dialog(env_id),
                                    ),
                                    ft.Button(
                                        "删除",
                                        icon=ft.Icons.DELETE,
                                        on_click=lambda ev, env_id=env.id: self._delete_environment(env_id),
                                        style=ft.ButtonStyle(
                                            bgcolor=ft.Colors.RED_50,
                                            color=ft.Colors.RED,
                                        ),
                                    ),
                                ],
                                spacing=8,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=15,
                    bgcolor=ft.Colors.GREEN_50 if is_active else ft.Colors.GREY_50,
                    border_radius=8,
                    border=ft.border.all(2, ft.Colors.GREEN if is_active else ft.Colors.GREY_300),
                    on_click=lambda ev, env_id=env.id: self._activate_environment(env_id),
                )
                env_list_view.controls.append(card)

        refresh_env_list()

        # 添加环境按钮
        add_env_btn = ft.Button(
            "添加环境",
            icon=ft.Icons.ADD_CIRCLE,
            on_click=lambda e: self._show_add_environment_dialog(refresh_env_list),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE,
                color=ft.Colors.WHITE,
                padding=12,
            ),
        )

        # 对话框内容
        dialog_content = ft.Container(
            content=ft.Column(
                controls=[
                    env_list_view,
                    ft.Divider(height=20),
                    add_env_btn,
                ],
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
            width=700,
            height=500,
        )

        # 对话框
        env_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("环境管理", size=20, weight=ft.FontWeight.BOLD),
            content=dialog_content,
            actions=[
                ft.TextButton("关闭", on_click=lambda e: self._close_dialog()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # 显示对话框
        self.page.dialog = env_dialog
        self.page.show_dialog(env_dialog)

    def _show_add_environment_dialog(self, refresh_callback):
        """显示添加环境对话框"""
        name_input = ft.TextField(
            label="环境名称",
            hint_text="例如：开发环境、测试环境",
            width=400,
        )

        variables_area = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

        # 表头
        header_row = ft.Row(
            controls=[
                ft.Text("变量名", size=14, weight=ft.FontWeight.BOLD, width=180),
                ft.Text("变量值", size=14, weight=ft.FontWeight.BOLD, expand=True),
                ft.Container(width=40),  # 占位，对齐删除按钮
            ],
            spacing=10,
        )
        
        # 提示信息
        hint_text = ft.Text(
            "提示：必须包含 base_url 变量。可使用 {{变量名}} 引用全局变量",
            size=12,
            color=ft.Colors.BLUE_700,
            italic=True,
        )

        # 添加默认变量行
        def add_variable_row(key="", value=""):
            key_field = ft.TextField(
                label="",
                hint_text="变量名",
                value=key,
                width=180,
                text_size=14,
            )
            value_field = ft.TextField(
                label="",
                hint_text="变量值",
                value=value,
                expand=True,
                text_size=14,
            )
            remove_btn = ft.IconButton(
                ft.Icons.DELETE_OUTLINE,
                icon_size=20,
                tooltip="删除此变量",
            )

            row_container = ft.Row(
                controls=[key_field, value_field, remove_btn],
                spacing=10,
                alignment=ft.MainAxisAlignment.START,
            )

            def remove_row(e):
                if row_container in variables_area.controls:
                    variables_area.controls.remove(row_container)
                    variables_area.update()

            remove_btn.on_click = remove_row

            variables_area.controls.append(row_container)
            return row_container, key_field, value_field

        # 初始添加3行
        rows = []
        for _ in range(3):
            row, key_field, value_field = add_variable_row()
            rows.append((row, key_field, value_field))

        add_var_btn = ft.TextButton(
            "添加变量",
            icon=ft.Icons.ADD,
            on_click=lambda e: rows.append(add_variable_row()),
        )

        def save_env(e):
            name = name_input.value.strip()
            if not name:
                snack_bar = ft.SnackBar(content=ft.Text("请输入环境名称"), duration=2000)
                self.page.overlay.append(snack_bar)
                snack_bar.open = True
                self.page.update()
                return

            # 收集变量
            variables = {}
            for _, key_field, value_field in rows:
                key = key_field.value.strip()
                value = value_field.value.strip()
                if key:
                    variables[key] = value

            # 验证 base_url 是否存在
            if 'base_url' not in variables:
                snack_bar = ft.SnackBar(content=ft.Text("环境变量中必须包含 base_url 字段"), duration=2000)
                self.page.overlay.append(snack_bar)
                snack_bar.open = True
                self.page.update()
                return

            try:
                # 创建环境
                new_env = self.env_manager.add_environment(name, variables)
                self.env_manager.set_active(new_env.id)

                # 刷新列表
                refresh_callback()
                self._update_env_dropdown()
                self._update_env_info()
                self._update_url_prefix()  # 更新 URL 前缀

                # 关闭对话框
                self._close_dialog()

                snack_bar = ft.SnackBar(content=ft.Text(f"环境 '{name}' 已创建"), duration=2000)
                self.page.overlay.append(snack_bar)
                snack_bar.open = True
                self.page.update()
            except ValueError as ve:
                snack_bar = ft.SnackBar(content=ft.Text(str(ve)), duration=2000)
                self.page.overlay.append(snack_bar)
                snack_bar.open = True
                self.page.update()
            except Exception as ex:
                snack_bar = ft.SnackBar(content=ft.Text(f"创建环境失败: {str(ex)}"), duration=2000)
                self.page.overlay.append(snack_bar)
                snack_bar.open = True
                self.page.update()

        # 对话框
        add_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("添加环境", size=20, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        name_input,
                        ft.Container(height=15),
                        ft.Text("环境变量", size=16, weight=ft.FontWeight.BOLD),
                        hint_text,
                        header_row,
                        variables_area,
                        add_var_btn,
                    ],
                    spacing=8,
                ),
                width=650,
                height=500,
            ),
            actions=[
                ft.TextButton("取消", on_click=lambda e: self._close_dialog()),
                ft.Button(
                    "保存",
                    icon=ft.Icons.SAVE,
                    on_click=save_env,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE,
                        color=ft.Colors.WHITE,
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = add_dialog
        self.page.show_dialog(add_dialog)

    def _show_edit_environment_dialog(self, env_id):
        """显示编辑环境对话框"""
        env = self.env_manager.get_environment(env_id)
        if not env:
            return

        name_input = ft.TextField(
            label="环境名称",
            value=env.name,
            width=400,
        )
        
        variables_area = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
        
        # 表头
        header_row = ft.Row(
            controls=[
                ft.Text("变量名", size=14, weight=ft.FontWeight.BOLD, width=180),
                ft.Text("变量值", size=14, weight=ft.FontWeight.BOLD, expand=True),
                ft.Container(width=40),
            ],
            spacing=10,
        )
        
        # 提示信息
        hint_text = ft.Text(
            "提示：必须包含 base_url 变量。可使用 {{变量名}} 引用全局变量",
            size=12,
            color=ft.Colors.BLUE_700,
            italic=True,
        )

        rows = []

        def add_variable_row(key="", value=""):
            key_field = ft.TextField(
                label="",
                hint_text="变量名",
                value=key,
                width=180,
                text_size=14,
            )
            value_field = ft.TextField(
                label="",
                hint_text="变量值",
                value=value,
                expand=True,
                text_size=14,
            )
            remove_btn = ft.IconButton(
                ft.Icons.DELETE_OUTLINE,
                icon_size=20,
                tooltip="删除此变量",
            )

            row_container = ft.Row(
                controls=[key_field, value_field, remove_btn],
                spacing=10,
                alignment=ft.MainAxisAlignment.START,
            )

            def remove_row(e):
                if row_container in variables_area.controls:
                    variables_area.controls.remove(row_container)
                    variables_area.update()

            remove_btn.on_click = remove_row

            variables_area.controls.append(row_container)
            return row_container, key_field, value_field

        # 添加现有变量
        for key, value in env.variables.items():
            row, key_field, value_field = add_variable_row(key, value)
            rows.append((row, key_field, value_field))

        # 添加空行
        if len(rows) < 3:
            for _ in range(3 - len(rows)):
                row, key_field, value_field = add_variable_row()
                rows.append((row, key_field, value_field))

        add_var_btn = ft.TextButton("添加变量", icon=ft.Icons.ADD, on_click=lambda e: rows.append(add_variable_row()))

        def save_env(e):
            name = name_input.value.strip()
            if not name:
                snack_bar = ft.SnackBar(content=ft.Text("请输入环境名称"), duration=2000)
                self.page.overlay.append(snack_bar)
                snack_bar.open = True
                self.page.update()
                return

            # 收集变量
            variables = {}
            for _, key_field, value_field in rows:
                key = key_field.value.strip()
                value = value_field.value.strip()
                if key:
                    variables[key] = value

            # 验证 base_url 是否存在
            if 'base_url' not in variables:
                snack_bar = ft.SnackBar(content=ft.Text("环境变量中必须包含 base_url 字段"), duration=2000)
                self.page.overlay.append(snack_bar)
                snack_bar.open = True
                self.page.update()
                return

            try:
                # 更新环境
                self.env_manager.update_environment(env_id, name, variables)

                # 刷新列表
                self._update_env_dropdown()
                self._update_env_info()
                self._update_url_prefix()  # 更新 URL 前缀

                # 关闭对话框
                self._close_dialog()

                snack_bar = ft.SnackBar(content=ft.Text(f"环境 '{name}' 已更新"), duration=2000)
                self.page.overlay.append(snack_bar)
                snack_bar.open = True
                self.page.update()
            except ValueError as ve:
                snack_bar = ft.SnackBar(content=ft.Text(str(ve)), duration=2000)
                self.page.overlay.append(snack_bar)
                snack_bar.open = True
                self.page.update()
            except Exception as ex:
                snack_bar = ft.SnackBar(content=ft.Text(f"更新环境失败: {str(ex)}"), duration=2000)
                self.page.overlay.append(snack_bar)
                snack_bar.open = True
                self.page.update()

        def delete_env(e):
            if self.env_manager.delete_environment(env_id):
                self._update_env_dropdown()
                self._update_env_info()
                self._close_dialog()
                snack_bar = ft.SnackBar(content=ft.Text("环境已删除"), duration=2000)
                self.page.overlay.append(snack_bar)
                snack_bar.open = True
                self.page.update()
            else:
                snack_bar = ft.SnackBar(content=ft.Text("无法删除最后一个环境"), duration=2000)
                self.page.overlay.append(snack_bar)
                snack_bar.open = True
                self.page.update()

        # 对话框
        edit_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("编辑环境", size=20, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        name_input,
                        ft.Container(height=15),
                        ft.Text("环境变量", size=16, weight=ft.FontWeight.BOLD),
                        hint_text,
                        header_row,
                        variables_area,
                        add_var_btn,
                    ],
                    spacing=8,
                ),
                width=650,
                height=500,
            ),
            actions=[
                ft.TextButton(
                    "删除环境",
                    icon=ft.Icons.DELETE,
                    on_click=delete_env,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.RED_50,
                        color=ft.Colors.RED,
                    ),
                ),
                ft.TextButton("取消", on_click=lambda e: self._close_dialog()),
                ft.Button(
                    "保存",
                    icon=ft.Icons.SAVE,
                    on_click=save_env,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE,
                        color=ft.Colors.WHITE,
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = edit_dialog
        self.page.show_dialog(edit_dialog)

    def _activate_environment(self, env_id):
        """激活环境"""
        self.env_manager.set_active(env_id)
        self._update_env_dropdown()
        self._update_env_info()
        self._update_url_prefix()  # 更新 URL 前缀
        self._close_dialog()
        env = self.env_manager.get_environment(env_id)
        snack_bar = ft.SnackBar(content=ft.Text(f"已激活环境: {env.name}"), duration=2000)
        self.page.overlay.append(snack_bar)
        snack_bar.open = True
        self.page.update()

    def _delete_environment(self, env_id):
        """删除环境"""
        env = self.env_manager.get_environment(env_id)
        if env:
            if self.env_manager.delete_environment(env_id):
                self._update_env_dropdown()
                self._update_env_info()
                snack_bar = ft.SnackBar(content=ft.Text(f"环境 '{env.name}' 已删除"), duration=2000)
                self.page.overlay.append(snack_bar)
                snack_bar.open = True
                self.page.update()
            else:
                snack_bar = ft.SnackBar(content=ft.Text("无法删除最后一个环境"), duration=2000)
                self.page.overlay.append(snack_bar)
                snack_bar.open = True
                self.page.update()

    def _on_manage_global_variables(self, e):
        """打开全局变量管理对话框"""
        self._show_global_variable_dialog()

    def _show_global_variable_dialog(self):
        """显示全局变量管理对话框"""
        variables_area = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
        
        # 表头
        header_row = ft.Row(
            controls=[
                ft.Text("变量名", size=14, weight=ft.FontWeight.BOLD, width=180),
                ft.Text("变量值", size=14, weight=ft.FontWeight.BOLD, expand=True),
                ft.Container(width=40),
            ],
            spacing=10,
        )
        
        rows = []

        def add_variable_row(key="", value=""):
            key_field = ft.TextField(
                label="",
                hint_text="变量名",
                value=key,
                width=180,
                text_size=14,
            )
            value_field = ft.TextField(
                label="",
                hint_text="变量值",
                value=value,
                expand=True,
                text_size=14,
            )
            remove_btn = ft.IconButton(
                ft.Icons.DELETE_OUTLINE,
                icon_size=20,
                tooltip="删除此变量",
            )

            row_container = ft.Row(
                controls=[key_field, value_field, remove_btn],
                spacing=10,
                alignment=ft.MainAxisAlignment.START,
            )

            def remove_row(e):
                if row_container in variables_area.controls:
                    variables_area.controls.remove(row_container)
                    variables_area.update()

            remove_btn.on_click = remove_row

            variables_area.controls.append(row_container)
            return row_container, key_field, value_field

        # 添加现有全局变量
        for key, value in self.global_var_manager.get_all_variables().items():
            row, key_field, value_field = add_variable_row(key, value)
            rows.append((row, key_field, value_field))

        # 添加空行
        if len(rows) < 3:
            for _ in range(3 - len(rows)):
                row, key_field, value_field = add_variable_row()
                rows.append((row, key_field, value_field))

        add_var_btn = ft.TextButton("添加变量", icon=ft.Icons.ADD, on_click=lambda e: rows.append(add_variable_row()))

        def save_global_vars(e):
            # 收集变量
            variables = {}
            for _, key_field, value_field in rows:
                key = key_field.value.strip()
                value = value_field.value.strip()
                if key:
                    variables[key] = value

            # 保存全局变量
            self.global_var_manager.set_variables(variables)

            # 关闭对话框
            self._close_dialog()

            snack_bar = ft.SnackBar(content=ft.Text("全局变量已保存"), duration=2000)
            self.page.overlay.append(snack_bar)
            snack_bar.open = True
            self.page.update()

        # 对话框
        global_var_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("全局变量管理", size=20, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("全局变量在所有环境中都可用", size=13, color=ft.Colors.GREY_700),
                        ft.Container(height=10),
                        header_row,
                        variables_area,
                        add_var_btn,
                    ],
                    spacing=8,
                ),
                width=650,
                height=500,
            ),
            actions=[
                ft.TextButton(
                    "清空所有",
                    icon=ft.Icons.DELETE_SWEEP,
                    on_click=lambda e: self._clear_all_global_vars(),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.RED_50,
                        color=ft.Colors.RED,
                    ),
                ),
                ft.TextButton("取消", on_click=lambda e: self._close_dialog()),
                ft.Button(
                    "保存",
                    icon=ft.Icons.SAVE,
                    on_click=save_global_vars,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE,
                        color=ft.Colors.WHITE,
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = global_var_dialog
        self.page.show_dialog(global_var_dialog)

    def _clear_all_global_vars(self):
        """清空所有全局变量"""
        self.global_var_manager.clear_all()
        self._close_dialog()
        snack_bar = ft.SnackBar(content=ft.Text("全局变量已清空"), duration=2000)
        self.page.overlay.append(snack_bar)
        snack_bar.open = True
        self.page.update()

    def _close_dialog(self):
        """关闭对话框"""
        self.page.pop_dialog()
