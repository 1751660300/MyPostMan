"""主界面模块 - 构建完整的 API 测试界面"""

import flet as ft
import threading
import sys
import os
import uuid

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models import HttpRequest, HttpMethod
from services import HttpService
from managers import HistoryManager, EnvironmentManager, GlobalVariableManager, RequestListManager
from .components import DynamicKeyValueList, ResponsePanel, BodyEditor, RequestRunner


class RequestTab:
    """单个请求Tab的数据和组件"""
    
    def __init__(self, tab_id: str, name: str = "新请求"):
        self.tab_id = tab_id
        self.name = name
        self.is_modified = False  # 是否有未保存的修改
        
        # 请求组件
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
        
        self.url_input = ft.TextField(
            expand=True,
            hint_text="api/endpoint",
            prefix="",
            text_size=14,
            label_style=ft.TextStyle(size=13, weight=ft.FontWeight.BOLD),
        )
        
        # 默认请求头
        default_headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "MyPostMan/1.0",
        }
        self.headers_list = DynamicKeyValueList(default_data=default_headers)
        self.params_list = DynamicKeyValueList()
        self.body_editor = BodyEditor()
        self.request_runner = RequestRunner()
        self.response_panel = ResponsePanel()
        
        # 加载指示器
        self.loading_indicator = ft.ProgressRing(
            visible=False,
            width=30,
            height=30,
        )
        
        # 发送按钮
        self.send_btn = ft.Button(
            "发送",
            icon=ft.Icons.SEND,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE,
                color=ft.Colors.WHITE,
                padding=ft.padding.symmetric(vertical=12, horizontal=20),
                text_style=ft.TextStyle(size=15, weight=ft.FontWeight.BOLD),
            ),
        )
    
    def get_request_data(self) -> dict:
        """获取当前请求的所有数据"""
        return {
            'method': self.method_dropdown.value,
            'url': self.url_input.value,
            'headers': self.headers_list.get_data(),
            'params': self.params_list.get_data(),
            'body': self.body_editor.get_body(),
            'body_type': self.body_editor.get_body_type(),
        }
    
    def set_request_data(self, data: dict):
        """设置请求数据"""
        self.method_dropdown.value = data.get('method', 'GET')
        self.url_input.value = data.get('url', '')
        self.headers_list.set_data(data.get('headers', {}))
        self.params_list.set_data(data.get('params', {}))
        self.body_editor.set_body(data.get('body', ''))
        self.body_editor.set_body_type(data.get('body_type', 'none'))
        self.is_modified = False


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
        
        # 多Tab管理
        self.request_tabs = []  # 所有RequestTab列表
        self.current_tab_index = -1  # 当前激活的Tab索引
        self.tab_bar_row = ft.Row(controls=[], spacing=5, scroll=ft.ScrollMode.AUTO)  # Tab栏UI组件

        # 历史记录分页状态
        self.history_page = 1
        self.history_page_size = 10
        # 搜索过滤状态
        self.history_search_keyword = ""
        self.request_list_search_keyword = ""
        
        # 请求列表分页状态
        self.request_list_page = 1
        self.request_list_page_size = 10

        self.history_pagination = ft.Row(
            controls=[],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        )
        
        self.request_list_pagination = ft.Row(
            controls=[],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        )

        # 设置页面属性
        self.page.title = "MyPostMan - API 测试工具"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.window_width = 1400
        self.page.window_height = 900
        self.page.window_min_width = 1000
        self.page.window_min_height = 700

        self._build_ui()

        # 加载历史记录
        self._update_history_list()

        # 默认创建一个新Tab
        self._create_new_tab()
    
    def _create_new_tab(self, request_data: dict = None):
        """创建新的请求Tab"""
        tab_id = str(uuid.uuid4())[:8]
        name = f"请求 {len(self.request_tabs) + 1}"
        
        new_tab = RequestTab(tab_id, name)
        
        if request_data:
            new_tab.set_request_data(request_data)
            new_tab.name = request_data.get('name', new_tab.name)
        
        self.request_tabs.append(new_tab)
        self.current_tab_index = len(self.request_tabs) - 1
        
        # 更新Tab栏
        self._update_tab_bar()
    
    def _save_tab(self, tab_index: int):
        """保存指定Tab的请求数据到请求列表"""
        if tab_index < 0 or tab_index >= len(self.request_tabs):
            return

        tab = self.request_tabs[tab_index]
        
        # 获取当前请求数据
        request_data = tab.get_request_data()
        
        # 构建完整URL
        full_url = self._build_full_url(request_data['url'])
        
        # 添加到请求列表（如果已存在则更新）
        if hasattr(tab, 'request_list_id') and tab.request_list_id:
            # 更新现有请求
            self.request_list_manager.update_request(
                request_id=tab.request_list_id,
                url=full_url,
                method=request_data['method'],
                name=tab.name,  # 添加名称更新
                params=request_data['params'],
                headers=request_data['headers'],
                body=request_data['body'],
                body_type=request_data['body_type'],
            )
        else:
            # 添加新请求
            request = self.request_list_manager.add_request(
                url=full_url,
                method=request_data['method'],
                params=request_data['params'],
                headers=request_data['headers'],
                body=request_data['body'],
                body_type=request_data['body_type'],
            )
            tab.request_list_id = request.id if request else None
        
        # 标记为已保存
        tab.is_modified = False
        
        # 更新Tab栏显示
        self._update_tab_bar()
        
        # 更新请求列表视图
        self._update_request_list_view()
        
        # 显示提示
        snack_bar = ft.SnackBar(content=ft.Text(f"已保存: {tab.name}"), duration=2000)
        self.page.overlay.append(snack_bar)
        snack_bar.open = True
        self.page.update()

    def _close_tab(self, tab_index: int):
        """关闭指定Tab"""
        if tab_index < 0 or tab_index >= len(self.request_tabs):
            return

        # 如果只剩一个Tab，不允许关闭
        if len(self.request_tabs) == 1:
            snack_bar = ft.SnackBar(content=ft.Text("至少保留一个请求Tab"), duration=2000)
            self.page.overlay.append(snack_bar)
            snack_bar.open = True
            self.page.update()
            return

        # 检查是否有未保存的修改
        tab = self.request_tabs[tab_index]
        if tab.is_modified:
            # 先保存再关闭
            self._save_tab(tab_index)

        # 删除Tab
        self.request_tabs.pop(tab_index)

        # 调整当前Tab索引
        if self.current_tab_index >= tab_index:
            self.current_tab_index = max(0, self.current_tab_index - 1)

        # 更新Tab栏
        self._update_tab_bar()
    
    def _switch_tab(self, tab_index: int):
        """切换到指定Tab"""
        if tab_index < 0 or tab_index >= len(self.request_tabs):
            return
        
        self.current_tab_index = tab_index
        self._update_tab_bar()
    
    def _update_tab_bar(self):
        """更新Tab栏显示"""
        # 清空Tab栏
        self.tab_bar_row.controls.clear()

        # 添加所有Tab
        for i, tab in enumerate(self.request_tabs):
            is_active = (i == self.current_tab_index)

            # 创建Tab按钮
            # 保存按钮：只在有未保存的修改时显示
            save_btn = ft.IconButton(
                icon=ft.Icons.SAVE,
                icon_size=16,
                icon_color=ft.Colors.GREEN_700,
                on_click=lambda e, idx=i: self._save_tab(idx),
                width=24,
                height=24,
                padding=2,
                tooltip="保存此请求",
                visible=tab.is_modified,  # 只在有修改时显示
            )
            
            # 重命名按钮
            rename_btn = ft.IconButton(
                icon=ft.Icons.EDIT,
                icon_size=16,
                icon_color=ft.Colors.BLUE_700,
                on_click=lambda e, idx=i: self._show_rename_dialog(idx),
                width=24,
                height=24,
                padding=2,
                tooltip="重命名此Tab",
            )

            # 关闭按钮：始终显示
            close_btn = ft.IconButton(
                icon=ft.Icons.CLOSE,
                icon_size=16,
                icon_color=ft.Colors.RED_700 if tab.is_modified else ft.Colors.GREY_600,
                on_click=lambda e, idx=i: self._close_tab(idx),
                width=24,
                height=24,
                padding=2,
                tooltip="关闭此Tab",
            )
            
            tab_btn = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(
                            f"{'● ' if tab.is_modified else ''}{tab.name}",     
                            size=12,
                            color=ft.Colors.BLUE if is_active else ft.Colors.GREY_700,
                            weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL,
                        ),
                        ft.Container(expand=True),  # 占位符，让按钮靠右        
                        save_btn,   # 保存按钮（条件显示）
                        rename_btn, # 重命名按钮（始终显示）
                        close_btn,  # 关闭按钮（始终显示）
                    ],
                    spacing=4,
                    alignment=ft.MainAxisAlignment.START
                ),
                padding=ft.padding.symmetric(horizontal=12, vertical=6),        
                bgcolor=ft.Colors.BLUE_50 if is_active else ft.Colors.GREY_100, 
                border_radius=6,
                border=ft.border.all(2, ft.Colors.BLUE if is_active else ft.Colors.TRANSPARENT),
                on_click=lambda e, idx=i: self._switch_tab(idx),
            )

            self.tab_bar_row.controls.append(tab_btn)

        # 添加新建Tab按钮
        new_tab_btn = ft.IconButton(
            icon=ft.Icons.ADD,
            icon_size=20,
            tooltip="新建请求Tab",
            on_click=lambda e: self._create_new_tab(),
        )
        self.tab_bar_row.controls.append(new_tab_btn)

        # 更新UI
        try:
            if self.tab_bar_row.page:
                self.tab_bar_row.update()
        except RuntimeError:
            pass

        # 更新当前Tab的内容
        self._load_current_tab()
    
    def _load_current_tab(self):
        """加载当前Tab的内容到界面"""
        if self.current_tab_index < 0 or self.current_tab_index >= len(self.request_tabs):
            return

        current_tab = self.request_tabs[self.current_tab_index]

        # 更新URL输入框
        self.url_input.value = current_tab.url_input.value
        
        # 更新方法下拉框
        self.method_dropdown.value = current_tab.method_dropdown.value
        
        # 更新Params
        self.params_list.set_data(current_tab.params_list.get_data())
        
        # 更新Headers
        self.headers_list.set_data(current_tab.headers_list.get_data())
        
        # 更新Body
        self.body_editor.set_body(current_tab.body_editor.get_body())
        self.body_editor.set_body_type(current_tab.body_editor.get_body_type())
        
        # 更新Runner和响应面板(这些组件状态不需要特殊处理)
        
        # 统一更新UI - 只在控件已添加到页面后才调用update()
        try:
            if self.url_input.page:
                self.url_input.update()
            if self.method_dropdown.page:
                self.method_dropdown.update()
            if self.params_list.page:
                self.params_list.update()
            if self.headers_list.page:
                self.headers_list.update()
            if self.body_editor.page:
                self.body_editor.update()
        except RuntimeError:
            # 控件还未添加到页面，忽略错误
            pass
    
    def _sync_ui_to_current_tab(self):
        """将界面组件的数据同步到当前Tab对象"""
        if self.current_tab_index < 0 or self.current_tab_index >= len(self.request_tabs):
            return
        
        current_tab = self.request_tabs[self.current_tab_index]
        
        # 同步URL和方法
        current_tab.url_input.value = self.url_input.value
        current_tab.method_dropdown.value = self.method_dropdown.value
        
        # 同步Params和Headers
        current_tab.params_list.set_data(self.params_list.get_data())
        current_tab.headers_list.set_data(self.headers_list.get_data())
        
        # 同步Body
        current_tab.body_editor.set_body(self.body_editor.get_body())
        current_tab.body_editor.set_body_type(self.body_editor.get_body_type())
        
        # 标记为已修改
        current_tab.is_modified = True
    
    def _on_tab_url_change(self, e):
        """当前Tab的URL变化时标记为已修改并同步数据"""
        if self.current_tab_index >= 0 and self.current_tab_index < len(self.request_tabs):
            # 同步数据到Tab对象
            self._sync_ui_to_current_tab()
            self._update_tab_bar()
            
            # 调用URL自动解析逻辑
            self._on_url_change(e)

    def _on_tab_method_change(self, e):
        """当前Tab的方法变化时标记为已修改并同步数据"""
        if self.current_tab_index >= 0 and self.current_tab_index < len(self.request_tabs):
            # 同步数据到Tab对象
            self._sync_ui_to_current_tab()
            self._update_tab_bar()
    
    def _show_rename_dialog(self, tab_index: int):
        """显示重命名对话框"""
        if tab_index < 0 or tab_index >= len(self.request_tabs):
            return
        
        tab = self.request_tabs[tab_index]
        
        # 创建文本输入框
        name_input = ft.TextField(
            value=tab.name,
            label="Tab 名称",
            text_size=14,
            autofocus=True,
        )
        
        def on_confirm(e):
            """确认重命名"""
            new_name = name_input.value.strip()
            if new_name:
                tab.name = new_name
                tab.is_modified = True  # 标记为已修改
                self._update_tab_bar()
                self.page.pop_dialog()
        
        def on_cancel(e):
            """取消重命名"""
            self.page.pop_dialog()
        
        def on_key_press(e):
            """回车键确认"""
            if e.key == "ENTER":
                on_confirm(e)
            elif e.key == "ESCAPE":
                on_cancel(e)
        
        name_input.on_submit = on_confirm
        name_input.on_key_press = on_key_press
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("重命名 Tab"),
            content=ft.Column(
                controls=[
                    name_input,
                ],
                tight=True,
            ),
            actions=[
                ft.TextButton(
                    "取消",
                    on_click=on_cancel,
                ),
                ft.TextButton(
                    "确定",
                    on_click=on_confirm,
                    style=ft.ButtonStyle(
                        color=ft.Colors.BLUE,
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = dialog
        self.page.show_dialog(dialog)
        
        # 自动聚焦到输入框（TextField已设置autofocus=True，无需手动调用）
    
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

    def _on_url_change(self, e):
        """URL输入框内容变化时自动解析参数"""
        url = self.url_input.value.strip()
        if not url:
            return
        
        # 解析URL中的查询参数
        params = self._parse_url_params(url)
        
        # 如果有参数且当前params列表为空，自动填充
        if params and not self.params_list.get_data():
            self.params_list.set_data(params)
            try:
                self.params_list.update()
            except:
                pass
            
            # 清理URL中的查询参数，只保留路径部分
            clean_url = self._clean_url_params(url)
            if clean_url != url:
                self.url_input.value = clean_url
                try:
                    self.url_input.update()
                except:
                    pass

    def _parse_url_params(self, url: str) -> dict[str, str]:
        """从URL中解析查询参数"""
        from urllib.parse import urlparse, parse_qs
        
        try:
            # 如果URL不包含协议，添加临时协议用于解析
            if not url.startswith(('http://', 'https://')):
                url = 'http://temp' + url
            
            parsed = urlparse(url)
            
            # 解析查询参数
            if parsed.query:
                query_params = parse_qs(parsed.query)
                # parse_qs返回的是列表，转换为单个值
                return {k: v[0] if len(v) == 1 else v for k, v in query_params.items()}
            
            return {}
        except Exception:
            return {}
    
    def _clean_url_params(self, url: str) -> str:
        """清理URL中的查询参数，只保留路径部分"""
        from urllib.parse import urlparse
        
        try:
            # 如果URL不包含协议，添加临时协议用于解析
            if not url.startswith(('http://', 'https://')):
                url = 'http://temp' + url
                parsed = urlparse(url)
                # 重建不带查询参数的URL
                clean_path = f"{parsed.path}"
                # 如果原始URL以/开头，返回相对路径
                if clean_path.startswith('/'):
                    return clean_path[1:] if clean_path != '/' else ''
                return clean_path
            else:
                parsed = urlparse(url)
                return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        except Exception:
            return url
    
    def _update_request_list_view(self):
        """更新请求 URL 列表视图（支持分页和搜索）"""
        self.request_list_view.controls.clear()
        
        # 使用分页查询
        requests, total = self.request_list_manager.get_paged(
            page=self.request_list_page,
            page_size=self.request_list_page_size,
            keyword=self.request_list_search_keyword
        )
        
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
        
        # 更新分页控件
        self._update_request_list_pagination(total)
        
        # 更新视图
        try:
            if hasattr(self.request_list_view, 'page') and self.request_list_view.page:
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
                self.request_list_page = 1  # 重置到第一页
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
        
        self.request_list_page = 1  # 重置到第一页
        self._update_request_list_view()
        snack_bar = ft.SnackBar(content=ft.Text("已添加到请求列表"), duration=2000)
        self.page.overlay.append(snack_bar)
        snack_bar.open = True
        self.page.update()
    
    def _on_clear_request_list(self, e):
        """清空请求列表"""
        self.request_list_manager.clear_all()
        self.request_list_page = 1  # 重置页码
        self.request_list_search_keyword = ""  # 清空搜索
        self._update_request_list_view()
        snack_bar = ft.SnackBar(content=ft.Text("请求列表已清空"), duration=2000)
        self.page.overlay.append(snack_bar)
        snack_bar.open = True
        self.page.update()
    
    def _on_remove_request(self, request_id: str):
        """删除请求列表项"""
        self.request_list_manager.remove_request(request_id)
        # 如果当前页没有数据了，回到上一页
        requests, total = self.request_list_manager.get_paged(
            page=self.request_list_page,
            page_size=self.request_list_page_size,
            keyword=self.request_list_search_keyword
        )
        if len(requests) == 0 and self.request_list_page > 1:
            self.request_list_page -= 1
        self._update_request_list_view()
    
    def _on_request_list_click(self, e):
        """点击请求列表项，创建新的Tab页或跳转到已存在的Tab"""
        req = e.control.data
        if req:
            # 检查是否已经有相同 request_list_id 的 Tab 打开
            existing_tab_index = None
            for i, tab in enumerate(self.request_tabs):
                if hasattr(tab, 'request_list_id') and tab.request_list_id == req.id:
                    existing_tab_index = i
                    break
            
            if existing_tab_index is not None:
                # 如果已存在，跳转到该 Tab
                self._switch_tab(existing_tab_index)
                snack_bar = ft.SnackBar(content=ft.Text(f"已跳转到: {req.name or req.url}"), duration=1500)
            else:
                # 如果不存在，创建新的Tab
                # 从完整 URL 中提取路径部分
                path_url = self._extract_path_from_url(req.url)

                # 构建请求数据
                request_data = {
                    'name': req.name or req.url,
                    'method': req.method,
                    'url': path_url,
                    'params': req.params if hasattr(req, 'params') else {},
                    'headers': req.headers if hasattr(req, 'headers') else {},
                    'body': req.body if hasattr(req, 'body') else '',
                    'body_type': req.body_type if hasattr(req, 'body_type') else 'none',
                }

                # 创建新的Tab
                self._create_new_tab(request_data)

                # 保存request_list_id以便后续更新
                if hasattr(req, 'id'):
                    self.request_tabs[self.current_tab_index].request_list_id = req.id

                snack_bar = ft.SnackBar(content=ft.Text(f"已打开新Tab: {req.name or req.url}"), duration=1500)
            
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
        # 历史记录列表 - 设置最大高度
        self.history_list = ft.ListView(
            expand=False,
            spacing=8,
            padding=8,
            height=300,  # 最大高度300px
            auto_scroll=False,
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

        # 请求列表 - 设置最大高度
        self.request_list_view = ft.ListView(
            expand=False,
            spacing=6,
            padding=8,
            height=300,  # 最大高度300px
            auto_scroll=False,
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
                            ft.Container(height=5),
                            # 分页控件
                            self.history_pagination,
                            ft.Container(height=5),
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
                    height=400,  # 固定高度容器（包含列表300px + 分页控件约50px + 按钮约50px）
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
                            ft.Container(height=5),
                            # 分页控件
                            self.request_list_pagination,
                            ft.Container(height=5),
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
                    height=400,  # 固定高度容器（包含列表300px + 分页控件约50px + 按钮约50px）
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
        """构建主内容区域 - 显示请求编辑界面"""
        # [步骤2-完成] 构建Tab栏
        # Tab栏已在类初始化时创建(self.tab_bar_row)
        
        # [步骤2-完成] 构建请求编辑区域 - 这些是全局显示组件
        # 方法下拉框
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
            on_select=self._on_tab_method_change,
        )

        # URL输入框
        self.url_input = ft.TextField(
            expand=True,
            hint_text="输入请求URL地址",
            text_size=14,
            label_style=ft.TextStyle(size=13, weight=ft.FontWeight.BOLD),
            on_change=self._on_tab_url_change,
        )

        # 发送按钮
        self.send_btn = ft.Button(
            "发送",
            icon=ft.Icons.SEND,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE,
                color=ft.Colors.WHITE,
                padding=ft.padding.symmetric(vertical=12, horizontal=20),
                text_style=ft.TextStyle(size=15, weight=ft.FontWeight.BOLD),
            ),
            on_click=self._on_send_request,
        )

        # Headers和Params列表
        default_headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "MyPostMan/1.0",
        }
        self.headers_list = DynamicKeyValueList(default_data=default_headers)
        self.params_list = DynamicKeyValueList()
        
        # Body编辑器
        self.body_editor = BodyEditor()
        
        # 请求运行器
        self.request_runner = RequestRunner()
        
        # 响应面板
        self.response_panel = ResponsePanel()

        # 加载指示器
        self.loading_indicator = ft.ProgressRing(
            visible=False,
            width=30,
            height=30,
        )

        # [步骤2-完成] 组装主内容区域
        return ft.Container(
            content=ft.Column(
                controls=[
                    # Tab栏
                    self.tab_bar_row,
                    ft.Divider(height=1),
                    
                    # URL输入区域
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                self.method_dropdown,
                                self.url_input,
                                self.send_btn,
                                self.loading_indicator,
                            ],
                            spacing=10,
                        ),
                        padding=10,
                    ),
                    
                    # 请求配置区域(可滚动)
                    ft.Container(
                        content=self._build_request_tabs(),
                        expand=True,
                    ),
                    
                    # 响应面板区域
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                self.response_panel,
                            ],
                            spacing=10,
                        ),
                        expand=True,
                    ),
                ],
                expand=True,
            ),
            expand=True,
        )

    def _build_request_tabs(self) -> ft.Tabs:
        """构建请求配置Tab控件(Params/Headers/Body/Runner)"""
        # 使用 TabBar + TabBarView 的标准结构
        return ft.Tabs(
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
    
    def _on_request_tab_change(self, e):
        """请求配置Tab切换时同步数据"""
        # 同步当前界面数据到Tab对象
        self._sync_ui_to_current_tab()

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

        # 检查 SSL 配置，如果不验证则弹框提示
        if not self.request_runner.is_ssl_verify():
            self._show_ssl_warning_dialog(url)
            return

        # 直接发送请求（SSL 验证开启）
        self._do_send_request(url)
    
    def _show_ssl_warning_dialog(self, url: str):
        """显示 SSL 警告对话框"""
        def on_confirm(e):
            """确认继续发送请求"""
            self.page.pop_dialog()
            self._do_send_request(url)
        
        def on_cancel(e):
            """取消发送请求"""
            self.page.pop_dialog()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("⚠️ SSL 证书验证已关闭"),
            content=ft.Text(
                '当前 Runner 配置中 SSL 认证设置为"不认证"。\n\n'
                "这意味着请求将不会验证服务器的 SSL 证书，可能存在安全风险。\n\n"
                "建议：\n"
                "• 生产环境：请开启 SSL 认证\n"
                "• 测试环境/自签名证书：可以继续使用\n\n"
                "是否继续发送请求？",
                size=14,
            ),
            actions=[
                ft.TextButton(
                    "取消",
                    on_click=on_cancel,
                ),
                ft.TextButton(
                    "继续发送",
                    on_click=on_confirm,
                    style=ft.ButtonStyle(
                        color=ft.Colors.ORANGE,
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = dialog
        self.page.show_dialog(dialog)
    
    def _do_send_request(self, url: str):
        """执行发送请求的逻辑"""
        # 显示加载状态
        self.is_loading = True
        self.loading_indicator.visible = True
        self.send_btn.disabled = True
        try:
            self.loading_indicator.update()
            self.send_btn.update()
        except RuntimeError:
            pass

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
        """更新历史记录列表显示（支持分页）"""
        self.history_list.controls.clear()

        # 使用分页查询
        history, total = self.history_manager.get_paged(
            page=self.history_page,
            page_size=self.history_page_size
        )

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

        # 更新分页控件
        self._update_history_pagination(total)

        try:
            if self.history_list.page:
                self.history_list.update()
        except RuntimeError:
            pass

    def _update_history_pagination(self, total: int):
        """更新历史记录分页控件"""
        self.history_pagination.controls.clear()

        # 计算总页数（至少为1）
        if total == 0:
            total_pages = 1
        else:
            total_pages = (total + self.history_page_size - 1) // self.history_page_size

        # 上一页按钮
        if self.history_page > 1:
            self.history_pagination.controls.append(
                ft.IconButton(
                    icon=ft.Icons.CHEVRON_LEFT,
                    icon_size=18,
                    tooltip="上一页",
                    on_click=lambda e: self._history_prev_page(),
                )
            )
        elif total > 0:
            # 禁用状态的上一页按钮
            self.history_pagination.controls.append(
                ft.IconButton(
                    icon=ft.Icons.CHEVRON_LEFT,
                    icon_size=18,
                    tooltip="上一页",
                    opacity=0.3,
                    disabled=True,
                )
            )

        # 页码信息
        self.history_pagination.controls.append(
            ft.Text(
                f"第 {self.history_page}/{total_pages} 页 (共 {total} 条)",
                size=11,
                color=ft.Colors.GREY_600,
            )
        )

        # 下一页按钮
        if self.history_page < total_pages and total > 0:
            self.history_pagination.controls.append(
                ft.IconButton(
                    icon=ft.Icons.CHEVRON_RIGHT,
                    icon_size=18,
                    tooltip="下一页",
                    on_click=lambda e: self._history_next_page(),
                )
            )
        elif total > 0:
            # 禁用状态的下一页按钮
            self.history_pagination.controls.append(
                ft.IconButton(
                    icon=ft.Icons.CHEVRON_RIGHT,
                    icon_size=18,
                    tooltip="下一页",
                    opacity=0.3,
                    disabled=True,
                )
            )

        try:
            if hasattr(self.history_pagination, 'page') and self.history_pagination.page:
                self.history_pagination.update()
        except RuntimeError:
            pass

    def _history_prev_page(self):
        """上一页"""
        if self.history_page > 1:
            self.history_page -= 1
            self._update_history_list()

    def _history_next_page(self):
        """下一页"""
        self.history_page += 1
        self._update_history_list()

    def _on_history_click(self, e):
        """点击历史记录项，创建新的Tab页"""
        history = e.control.data
        if history:
            # 从完整 URL 中提取路径部分
            path_url = self._extract_path_from_url(history.url)

            # 构建请求数据（使用 HistoryItem 的 request 对象）
            request_data = {
                'name': f"历史 - {history.url}",
                'method': history.method,
                'url': path_url,
                'params': history.request.params if history.request.params else {},
                'headers': history.request.headers if history.request.headers else {},
                'body': history.request.body if history.request.body else '',
                'body_type': history.request.body_type if history.request.body_type else 'none',
            }

            # 创建新的Tab
            self._create_new_tab(request_data)

            snack_bar = ft.SnackBar(content=ft.Text(f"已打开新Tab: {history.url}"), duration=1500)
            self.page.overlay.append(snack_bar)
            snack_bar.open = True
            self.page.update()

    def _on_clear_history(self, e):
        """清空历史记录"""
        self.history_manager.clear()
        self.history_page = 1  # 重置页码
        self.history_search_keyword = ""  # 清空搜索
        self._update_history_list()
        snack_bar = ft.SnackBar(content=ft.Text("历史记录已清空"), duration=2000)
        self.page.overlay.append(snack_bar)
        snack_bar.open = True
        self.page.update()

    def _on_history_search_change(self, e):
        """历史记录搜索变化"""
        self.history_search_keyword = self.history_search_input.value.strip() if hasattr(self, 'history_search_input') and self.history_search_input.value else ""
        self.history_page = 1  # 重置到第一页
        self._update_history_list()

    def _on_request_list_search_change(self, e):
        """请求列表搜索变化"""
        self.request_list_search_keyword = self.request_list_search_input.value.strip() if hasattr(self, 'request_list_search_input') and self.request_list_search_input.value else ""
        self.request_list_page = 1  # 重置到第一页
        self._update_request_list_view()
    
    def _update_request_list_pagination(self, total: int):
        """更新请求列表分页控件"""
        self.request_list_pagination.controls.clear()

        # 计算总页数（至少为1）
        if total == 0:
            total_pages = 1
        else:
            total_pages = (total + self.request_list_page_size - 1) // self.request_list_page_size

        # 上一页按钮
        if self.request_list_page > 1:
            self.request_list_pagination.controls.append(
                ft.IconButton(
                    icon=ft.Icons.CHEVRON_LEFT,
                    icon_size=18,
                    tooltip="上一页",
                    on_click=lambda e: self._request_list_prev_page(),
                )
            )
        elif total > 0:
            # 禁用状态的上一页按钮
            self.request_list_pagination.controls.append(
                ft.IconButton(
                    icon=ft.Icons.CHEVRON_LEFT,
                    icon_size=18,
                    tooltip="上一页",
                    opacity=0.3,
                    disabled=True,
                )
            )

        # 页码信息
        self.request_list_pagination.controls.append(
            ft.Text(
                f"第 {self.request_list_page}/{total_pages} 页 (共 {total} 条)",
                size=11,
                color=ft.Colors.GREY_600,
            )
        )

        # 下一页按钮
        if self.request_list_page < total_pages and total > 0:
            self.request_list_pagination.controls.append(
                ft.IconButton(
                    icon=ft.Icons.CHEVRON_RIGHT,
                    icon_size=18,
                    tooltip="下一页",
                    on_click=lambda e: self._request_list_next_page(),
                )
            )
        elif total > 0:
            # 禁用状态的下一页按钮
            self.request_list_pagination.controls.append(
                ft.IconButton(
                    icon=ft.Icons.CHEVRON_RIGHT,
                    icon_size=18,
                    tooltip="下一页",
                    opacity=0.3,
                    disabled=True,
                )
            )

        try:
            if hasattr(self.request_list_pagination, 'page') and self.request_list_pagination.page:
                self.request_list_pagination.update()
        except RuntimeError:
            pass

    def _request_list_prev_page(self):
        """请求列表上一页"""
        if self.request_list_page > 1:
            self.request_list_page -= 1
            self._update_request_list_view()

    def _request_list_next_page(self):
        """请求列表下一页"""
        self.request_list_page += 1
        self._update_request_list_view()

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
