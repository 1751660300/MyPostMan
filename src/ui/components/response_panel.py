"""响应展示面板组件"""

import flet as ft
import json


class ResponsePanel(ft.Container):
    """响应展示面板组件"""

    def __init__(self):
        super().__init__()
        self.expand = True
        self.padding = 15

        # 状态信息
        self.status_text = ft.Text("", size=15, weight=ft.FontWeight.BOLD)
        self.time_text = ft.Text("", size=13, color=ft.Colors.GREY_700)

        # 响应类型信息
        self.response_type_text = ft.Text("", size=12, color=ft.Colors.BLUE)

        # Tab 切换内容
        self.body_text = ft.Text("", size=13, font_family="Consolas")
        self.headers_text = ft.Text("", size=13, font_family="Consolas")
        self.cookies_text = ft.Text("", size=13, font_family="Consolas")

        # HTML 预览
        self.html_preview = ft.TextField(
            multiline=True,
            read_only=True,
            text_size=12,
            text_style=ft.TextStyle(font_family="Consolas", size=12),
            expand=True,
            visible=False,
        )

        # 使用 TabBar + TabBarView
        self.tabs = ft.Tabs(
            length=3,
            selected_index=0,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        tab_alignment=ft.TabAlignment.START,
                        tabs=[
                            ft.Tab(label=ft.Text("Body")),
                            ft.Tab(label=ft.Text("Headers")),
                            ft.Tab(label=ft.Text("Cookies")),
                        ],
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            self._create_body_tab(),
                            self._create_scrollable(self.headers_text),
                            self._create_scrollable(self.cookies_text),
                        ],
                    ),
                ],
            ),
        )

        self.content = ft.Column(
            controls=[
                # 状态行
                ft.Row(
                    controls=[
                        self.status_text,
                        ft.Container(width=10),
                        self.time_text,
                        ft.Container(expand=True),
                        self.response_type_text,
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.Divider(height=1),
                # Tab 内容
                self.tabs,
            ],
            expand=True,
            spacing=10,
        )

    def _create_body_tab(self) -> ft.Container:
        """创建 Body Tab 内容"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.TextButton(
                                    "格式化 JSON",
                                    icon=ft.Icons.FORMAT_PAINT,
                                    on_click=self._format_response_json,
                                ),
                                ft.TextButton(
                                    "复制响应",
                                    icon=ft.Icons.CONTENT_COPY,
                                    on_click=self._copy_response,
                                ),
                            ],
                        ),
                        padding=ft.padding.only(bottom=5),
                    ),
                    self._create_scrollable(self.body_text),
                ],
                expand=True,
            ),
            expand=True,
        )

    def _create_scrollable(self, text_control: ft.Text) -> ft.Container:
        """创建可滚动容器"""
        return ft.Container(
            content=ft.ListView(
                controls=[text_control],
                expand=True,
                spacing=10,
                padding=10,
            ),
            expand=True,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
        )

    def _format_response_json(self, e):
        """格式化响应 JSON"""
        try:
            body = self.body_text.value
            if body:
                parsed = json.loads(body)
                self.body_text.value = json.dumps(parsed, indent=2, ensure_ascii=False)
                self.body_text.update()
        except (json.JSONDecodeError, ValueError):
            pass  # 不是 JSON，忽略

    def _copy_response(self, e):
        """复制响应内容"""
        if self.body_text.value:
            try:
                if hasattr(self, 'page') and self.page:
                    self.page.clipboard.set(self.body_text.value)
            except RuntimeError:
                pass

    def _detect_response_type(self, headers: dict) -> str:
        """检测响应类型"""
        content_type = headers.get("Content-Type", headers.get("content-type", "")).lower()
        if "html" in content_type:
            return "html"
        elif "json" in content_type:
            return "json"
        elif "xml" in content_type:
            return "xml"
        elif "text" in content_type:
            return "text"
        else:
            return "unknown"

    def _format_html(self, html_content: str) -> str:
        """简单格式化 HTML（添加换行和缩进）"""
        import re
        
        # 移除多余的空白
        formatted = re.sub(r'>\s+<', '><', html_content.strip())
        
        # 简单的缩进处理
        indent = 0
        lines = []
        
        # 分割标签
        tags = re.findall(r'<[^>]+>|[^<]+', formatted)
        
        for tag in tags:
            if tag.startswith('</'):
                indent = max(0, indent - 1)
                lines.append('  ' * indent + tag)
            elif tag.startswith('<') and not tag.startswith('<?') and not tag.startswith('<!--'):
                lines.append('  ' * indent + tag)
                if not tag.endswith('/>') and not tag.startswith('<!'):
                    indent += 1
            else:
                text = tag.strip()
                if text:
                    lines.append('  ' * indent + text)
        
        return '\n'.join(lines)

    def update_response(self, response):
        """
        更新响应数据（兼容旧接口）
        
        Args:
            response: HttpResponse 对象
        """
        if response.error:
            self.status_text.value = f"❌ {response.error}"
            self.status_text.color = ft.Colors.RED
            self.time_text.value = f"耗时: {response.elapsed}ms"
            self.response_type_text.value = ""
            self.body_text.value = response.error
            self.headers_text.value = ""
            self.cookies_text.value = ""
            self.html_preview.visible = False
            self.body_text.visible = True
        else:
            # 状态码颜色
            if response.is_success:
                status_icon = "✅"
                self.status_text.color = ft.Colors.GREEN
            elif response.status_code >= 400:
                status_icon = "❌"
                self.status_text.color = ft.Colors.RED
            else:
                status_icon = "⚠️"
                self.status_text.color = ft.Colors.ORANGE

            self.status_text.value = f"{status_icon} {response.status_code} {response.reason}"
            self.time_text.value = f"耗时: {response.elapsed}ms"

            # 检测响应类型
            response_type = self._detect_response_type(response.headers)
            
            # 格式化响应体
            if response_type == "html":
                # HTML 类型：提供格式化的源码
                formatted_html = self._format_html(response.body)
                self.body_text.value = formatted_html
                self.html_preview.value = formatted_html
                self.html_preview.visible = True
                self.body_text.visible = False
                self.response_type_text.value = f"📄 类型: HTML"
            elif response_type == "json":
                # JSON 类型：自动美化
                self.body_text.value = response.formatted_body
                self.html_preview.visible = False
                self.body_text.visible = True
                self.response_type_text.value = f"📄 类型: JSON"
            else:
                # 其他类型
                self.body_text.value = response.formatted_body
                self.html_preview.visible = False
                self.body_text.visible = True
                type_map = {
                    "xml": "XML",
                    "text": "Text",
                    "unknown": "Unknown"
                }
                self.response_type_text.value = f"📄 类型: {type_map.get(response_type, 'Unknown')}"

            # 格式化响应头
            headers_str = "\n".join(f"{k}: {v}" for k, v in response.headers.items())
            self.headers_text.value = headers_str

            # 格式化 Cookies
            cookies_str = "\n".join(response.headers.get("Set-Cookie", "").split("; "))
            self.cookies_text.value = cookies_str if cookies_str else "无 Cookies"

        try:
            if self.page:
                self.update()
        except RuntimeError:
            pass

    def set_response(self, status_code: int, elapsed: float, body: str, 
                     headers: dict = None, cookies: dict = None, 
                     content_type: str = None, error: str = None):
        """
        设置响应数据

        Args:
            status_code: HTTP 状态码
            elapsed: 响应时间（毫秒）
            body: 响应体
            headers: 响应头
            cookies: Cookies
            content_type: 内容类型
            error: 错误信息
        """
        # 更新状态文本
        if error:
            self.status_text.value = f"错误"
            self.status_text.color = ft.Colors.RED
        elif 200 <= status_code < 300:
            self.status_text.value = f"{status_code} OK"
            self.status_text.color = ft.Colors.GREEN
        elif 400 <= status_code < 500:
            self.status_text.value = f"{status_code} Client Error"
            self.status_text.color = ft.Colors.ORANGE
        else:
            self.status_text.value = f"{status_code}"
            self.status_text.color = ft.Colors.RED

        # 更新时间
        self.time_text.value = f"{elapsed:.0f}ms"

        # 更新内容类型
        if content_type:
            self.response_type_text.value = content_type.split(';')[0]
        else:
            self.response_type_text.value = ""

        # 设置 Body
        if error:
            self.body_text.value = f"错误: {error}"
        elif body:
            # 尝试格式化 JSON
            try:
                parsed = json.loads(body)
                self.body_text.value = json.dumps(parsed, indent=2, ensure_ascii=False)
            except (json.JSONDecodeError, ValueError):
                self.body_text.value = body
        else:
            self.body_text.value = "(无响应体)"

        # 设置 Headers
        if headers:
            headers_text = "\n".join(f"{k}: {v}" for k, v in headers.items())
            self.headers_text.value = headers_text
        else:
            self.headers_text.value = "(无响应头)"

        # 设置 Cookies
        if cookies:
            cookies_text = "\n".join(f"{k}: {v}" for k, v in cookies.items())
            self.cookies_text.value = cookies_text
        else:
            self.cookies_text.value = "(无 Cookies)"

        # 检查是否为 HTML
        if content_type and 'html' in content_type.lower():
            self.html_preview.value = body
            self.html_preview.visible = True
        else:
            self.html_preview.visible = False

        # 更新 UI
        try:
            if self.page:
                self.update()
        except RuntimeError:
            pass

    def clear(self):
        """清空响应数据"""
        self.status_text.value = "等待发送请求"
        self.status_text.color = ft.Colors.BLACK
        self.time_text.value = ""
        self.response_type_text.value = ""
        self.body_text.value = ""
        self.headers_text.value = ""
        self.cookies_text.value = ""
        self.html_preview.value = ""
        self.html_preview.visible = False

        try:
            if self.page:
                self.update()
        except RuntimeError:
            pass
