"""步骤管理对话框 - 添加和编辑执行步骤"""

import flet as ft
from typing import Optional, Callable, List
from models.execution_plan import ExecutionStep

try:
    import flet_code_editor as fce
    HAS_CODE_EDITOR = True
except ImportError:
    HAS_CODE_EDITOR = False
    print("警告: flet-code-editor 未安装，将使用普通文本框")


class StepEditorDialog:
    """步骤编辑对话框"""
    
    def __init__(self, on_save: Callable, available_requests: List, step: Optional[ExecutionStep] = None, 
                 current_plan_steps: List = None, current_step_index: int = -1):
        """
        初始化对话框
        
        Args:
            on_save: 保存回调函数，参数为 (request_id, name, order_index, timeout, retry_count, custom_method, params_mapping)
            available_requests: 可用的请求列表 [RequestItem, ...]
            step: 要编辑的步骤（None表示新建）
            current_plan_steps: 当前计划的所有步骤列表（用于过滤可选的前置步骤）
            current_step_index: 当前步骤的索引（-1表示新建）
        """
        self.on_save = on_save
        self.available_requests = available_requests
        self.step = step
        self.is_editing = step is not None
        self.current_plan_steps = current_plan_steps or []
        self.current_step_index = current_step_index
        
        # 构建对话框
        self.dialog = self._build_dialog()
    
    def _create_params_mapping_table(self) -> ft.Container:
        """创建参数映射表格"""
        # 表头
        header_row = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text("参数名", size=12, weight=ft.FontWeight.BOLD, width=120),
                    ft.Text("来源类型", size=12, weight=ft.FontWeight.BOLD, width=200),
                    ft.Text("变量名", size=12, weight=ft.FontWeight.BOLD, expand=True),
                    ft.Container(width=40),  # 删除按钮占位
                ],
                spacing=8,
            ),
            padding=ft.padding.symmetric(vertical=8, horizontal=8),
            bgcolor=ft.Colors.GREY_200,
            border_radius=ft.border_radius.only(top_left=6, top_right=6),
        )
        
        # 表格内容区域
        self.params_rows_container = ft.Column(
            controls=[],
            spacing=4,
            scroll=ft.ScrollMode.AUTO,
        )
        
        # 添加按钮
        add_btn = ft.TextButton(
            "添加映射",
            icon=ft.Icons.ADD,
            on_click=self._add_param_row,
            style=ft.ButtonStyle(
                color=ft.Colors.GREEN_700,
            ),
        )
        
        # 解析现有的 params_mapping
        if self.is_editing and self.step.params_mapping:
            try:
                import json
                mappings = json.loads(self.step.params_mapping)
                for param_name, var_ref in mappings.items():
                    self._add_param_row_data(param_name, var_ref)
            except:
                pass
        
        # 如果没有数据，添加一个空行
        if len(self.params_rows_container.controls) == 0:
            self._add_param_row(None)
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    header_row,
                    ft.Container(
                        content=self.params_rows_container,
                        height=280,  # 进一步增加高度以显示更多行
                    ),
                    add_btn,
                ],
                spacing=8,
            ),
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            padding=0,
        )
    
    def _add_param_row(self, e):
        """添加参数映射行"""
        self._add_param_row_data("", "")
        # 只在 dialog 存在时才更新
        if hasattr(self, 'dialog') and self.dialog:
            try:
                self.dialog.update()
            except RuntimeError:
                pass
    
    def _add_param_row_data(self, param_name: str, var_ref: str):
        """添加参数映射行数据"""
        # 解析变量引用
        source_type = "step"
        var_value = var_ref
        
        if var_ref.startswith("{{") and var_ref.endswith("}}"):
            inner = var_ref[2:-2].strip()
            if inner.startswith("step_"):
                source_type = "step"
                var_value = inner
            elif inner.startswith("global."):
                source_type = "global"
                var_value = inner[7:]  # 移除 "global." 前缀
            elif inner.startswith("env."):
                source_type = "env"
                var_value = inner[4:]  # 移除 "env." 前缀
        
        # 参数名输入
        param_field = ft.TextField(
            hint_text="参数名",
            value=param_name,
            width=120,
            text_size=12,
            dense=False,  # 不使用紧凑模式
            height=48,  # 增加高度以匹配 Dropdown
            content_padding=ft.padding.symmetric(horizontal=10, vertical=12),
        )
        
        # 构建来源选项（显示具体的步骤名称、全局变量、环境变量）
        source_options = [ft.dropdown.Option("step", "-- 选择前置步骤 --")]
        
        # 添加步骤选项（只显示当前步骤之前的步骤）
        if self.current_plan_steps:
            for idx, plan_step in enumerate(self.current_plan_steps):
                # 如果是编辑模式，排除当前步骤及其之后的步骤
                # 如果是新建模式，显示所有现有步骤
                if self.is_editing and idx >= self.current_step_index:
                    continue  # 跳过当前步骤及之后的步骤
                
                # 查找对应的请求信息
                req_name = plan_step.name
                for req in self.available_requests:
                    if req.id == plan_step.request_id:
                        req_name = req.name or req.url
                        break
                
                step_id = f"step_{plan_step.request_id}"
                source_options.append(ft.dropdown.Option(step_id, f"步骤{idx+1}: {req_name}"))
        elif self.available_requests:
            # 如果没有计划步骤列表，但有可用请求（新建时）
            for req in self.available_requests:
                step_id = f"step_{req.id}"
                step_name = req.name or req.url
                source_options.append(ft.dropdown.Option(step_id, f"步骤: {step_name}"))
        
        # 添加全局变量选项（只显示类型，不显示具体变量）
        source_options.append(ft.dropdown.Option("global", "全局变量"))
        
        # 添加环境变量选项（只显示类型，不显示具体变量）
        source_options.append(ft.dropdown.Option("env", "环境变量"))
        
        # 来源类型下拉框
        source_dropdown = ft.Dropdown(
            options=source_options,
            value=source_type,  # 使用解析后的类型
            width=200,
            text_size=12,
            dense=False,  # 不使用紧凑模式
            height=45,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=10),
        )
        
        # 变量/字段输入（只填写变量名，不包含前缀）
        if source_type == "step":
            hint = "例如: data.user.id"
            initial_value = var_value
        elif source_type == "global":
            hint = "全局变量名"
            initial_value = var_value
        elif source_type == "env":
            hint = "环境变量名"
            initial_value = var_value
        else:
            hint = "变量名或字段路径"
            initial_value = var_value
        
        var_field = ft.TextField(
            hint_text=hint,
            value=initial_value,
            expand=True,
            text_size=12,
            dense=False,  # 不使用紧凑模式
            height=48,  # 增加高度以匹配 Dropdown
            content_padding=ft.padding.symmetric(horizontal=10, vertical=12),
        )
        
        # 删除按钮
        delete_btn = ft.IconButton(
            ft.Icons.DELETE_OUTLINE,
            icon_size=20,
            tooltip="删除此行",
            width=48,  # 与 TextField 高度一致
            height=48,  # 与 TextField 高度一致
        )
        
        # 创建行容器
        row_container = ft.Container(
            content=ft.Row(
                controls=[
                    param_field,
                    source_dropdown,
                    var_field,
                    delete_btn,
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,  # 垂直居中对齐
            ),
            padding=ft.padding.symmetric(vertical=6, horizontal=8),  # 调整内边距，总高度约 60px
            bgcolor=ft.Colors.WHITE,
            border_radius=4,
        )
        
        # 删除功能
        def delete_row(e):
            if row_container in self.params_rows_container.controls:
                self.params_rows_container.controls.remove(row_container)
                # 只在 dialog 存在时才更新
                if hasattr(self, 'dialog') and self.dialog:
                    try:
                        self.dialog.update()
                    except RuntimeError:
                        pass
        
        delete_btn.on_click = delete_row
        
        # 添加到容器
        self.params_rows_container.controls.append(row_container)
    
    def _get_params_mapping_json(self) -> str:
        """获取参数映射的 JSON 字符串"""
        import json
        mappings = {}
        
        for row_container in self.params_rows_container.controls:
            row = row_container.content
            param_field = row.controls[0]  # 参数名
            source_dropdown = row.controls[1]  # 来源类型（step/global/env）
            var_field = row.controls[2]  # 变量名
            
            param_name = param_field.value.strip()
            source_type = source_dropdown.value
            var_name = var_field.value.strip()
            
            if param_name and source_type and var_name:
                # 根据来源类型构建变量引用
                if source_type == "global":
                    var_ref = f"{{{{global.{var_name}}}}}"
                elif source_type == "env":
                    var_ref = f"{{{{env.{var_name}}}}}"
                else:  # step
                    # 步骤类型，var_name 应该是完整的 step_xxx 格式
                    if not var_name.startswith("{{"):
                        var_ref = f"{{{{{var_name}}}}}"
                    else:
                        var_ref = var_name
                
                mappings[param_name] = var_ref
        
        return json.dumps(mappings, ensure_ascii=False) if mappings else None
    
    def _build_dialog(self) -> ft.AlertDialog:
        """构建对话框UI"""
        # 1. 请求选择下拉框
        request_options = [
            ft.dropdown.Option(key=req.id, text=req.name or req.url)
            for req in self.available_requests
        ]
        
        self.request_dropdown = ft.Dropdown(
            label="选择请求 *",
            hint_text="从请求列表中选择一个",
            options=request_options,
            value=self.step.request_id if self.is_editing else None,
            border_radius=8,
            width=500,
        )
        
        # 2. 步骤名称
        self.name_field = ft.TextField(
            label="步骤名称",
            hint_text="可选，默认为请求名称",
            value=self.step.name if self.is_editing else "",
            border_radius=8,
            width=500,
        )
        
        # 3. 参数映射配置
        params_title = ft.Row(
            controls=[
                ft.Icon(ft.Icons.LINK, color=ft.Colors.GREEN, size=18),
                ft.Text("参数映射", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
            ],
            spacing=6,
        )
        
        params_hint = ft.Container(
            content=ft.Text(
                "将上一步的结果、全局变量或环境变量映射到当前请求的参数",
                size=11,
                color=ft.Colors.GREY_600,
            ),
            padding=8,
            bgcolor=ft.Colors.GREEN_50,
            border_radius=6,
        )
        
        # 参数映射表格
        self.params_mapping_container = self._create_params_mapping_table()
        
        # 4. 自定义方法
        method_title = ft.Row(
            controls=[
                ft.Icon(ft.Icons.CODE, color=ft.Colors.PURPLE, size=18),
                ft.Text("自定义方法", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
            ],
            spacing=6,
        )
        
        method_hint = ft.Container(
            content=ft.Column([
                ft.Text("编写Python方法处理响应数据，必须返回dict", size=11, color=ft.Colors.GREY_700),
                ft.Text("示例:", size=11, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_600),
                ft.Text("def process(response):\n    return {'user_id': response['data']['id']}", 
                       size=10, color=ft.Colors.GREY_600, font_family="Consolas"),
            ], spacing=3),
            padding=8,
            bgcolor=ft.Colors.PURPLE_50,
            border_radius=6,
        )
        
        # 使用 flet_code_editor 或降级为 TextField
        if HAS_CODE_EDITOR:
            self.custom_method_field = fce.CodeEditor(
                language=fce.CodeLanguage.PYTHON,
                code_theme=fce.CodeTheme.ATOM_ONE_LIGHT,
                value=self.step.custom_method if self.is_editing and self.step.custom_method else "",
                width=500,
                height=300,
            )
            # 包装在 Container 中以添加白色背景和边框
            self.custom_method_container = ft.Container(
                content=self.custom_method_field,
                bgcolor=ft.Colors.WHITE,
                border=ft.border.all(1.5, ft.Colors.PURPLE_300),
                border_radius=8,
                padding=0,
            )
        else:
            # 降级方案：使用增强的 TextField
            self.custom_method_field = ft.TextField(
                label="自定义方法代码",
                hint_text="def process(response):\n    return response",
                value=self.step.custom_method if self.is_editing and self.step.custom_method else "",
                border_radius=8,
                width=500,
                min_lines=6,
                max_lines=12,
                multiline=True,
                text_size=12,
                text_style=ft.TextStyle(font_family="Consolas", size=12),
                filled=True,
                bgcolor=ft.Colors.WHITE,
                border_color=ft.Colors.PURPLE_200,
                focused_border_color=ft.Colors.PURPLE_400,
                cursor_color=ft.Colors.PURPLE_700,
            )
            self.custom_method_container = self.custom_method_field
        
        # 5. 高级设置
        advanced_title = ft.Row(
            controls=[
                ft.Icon(ft.Icons.TUNE, color=ft.Colors.BLUE, size=18),
                ft.Text("高级设置", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
            ],
            spacing=6,
        )
        
        # 超时时间和重试次数（并排显示）
        self.timeout_field = ft.TextField(
            label="超时时间（秒）",
            value=str(self.step.timeout) if self.is_editing else "30",
            keyboard_type=ft.KeyboardType.NUMBER,
            text_size=14,
            width=180,
            dense=True,
        )
        
        self.retry_field = ft.TextField(
            label="重试次数",
            value=str(self.step.retry_count) if self.is_editing else "3",
            keyboard_type=ft.KeyboardType.NUMBER,
            text_size=14,
            width=180,
            dense=True,
        )
        
        settings_card = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("超时时间", size=12, color=ft.Colors.GREY_600),
                                self.timeout_field,
                            ],
                            spacing=6,
                        ),
                        expand=1,
                    ),
                    ft.Container(width=15),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("重试次数", size=12, color=ft.Colors.GREY_600),
                                self.retry_field,
                            ],
                            spacing=6,
                        ),
                        expand=1,
                    ),
                ],
            ),
            padding=15,
            bgcolor=ft.Colors.GREY_50,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_200),
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
            "保存" if self.is_editing else "添加步骤",
            on_click=self._on_save,
            icon=ft.Icons.ADD,
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
                        ft.Icons.ADD_CIRCLE_OUTLINE if not self.is_editing else ft.Icons.EDIT,
                        color=ft.Colors.BLUE,
                        size=26,
                    ),
                    ft.Text(
                        "添加执行步骤" if not self.is_editing else "编辑步骤",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREY_900,
                    ),
                ],
                spacing=10,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        self.request_dropdown,
                        ft.Container(height=12),
                        self.name_field,
                        ft.Container(height=18),
                        params_title,
                        ft.Container(height=6),
                        params_hint,
                        ft.Container(height=8),
                        self.params_mapping_container,
                        ft.Container(height=18),
                        method_title,
                        ft.Container(height=6),
                        method_hint,
                        ft.Container(height=8),
                        self.custom_method_container,
                        ft.Container(height=18),
                        advanced_title,
                        ft.Container(height=8),
                        settings_card,
                    ],
                    tight=True,
                    spacing=0,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=580,
                height=550,
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
    
    def _on_save(self, e):
        """处理保存"""
        request_id = self.request_dropdown.value
        if not request_id:
            self.request_dropdown.error_text = "请选择一个请求"
            try:
                self.dialog.update()
            except RuntimeError:
                pass
            return
        
        name = self.name_field.value.strip()
        
        try:
            timeout = int(self.timeout_field.value or "30")
            retry_count = int(self.retry_field.value or "3")
        except ValueError:
            self.timeout_field.error_text = "请输入有效的数字"
            try:
                self.dialog.update()
            except RuntimeError:
                pass
            return
        
        # 获取自定义方法和参数映射
        if HAS_CODE_EDITOR:
            custom_method = self.custom_method_field.value.strip() if self.custom_method_field.value and self.custom_method_field.value.strip() else None
        else:
            custom_method = self.custom_method_field.value.strip() if self.custom_method_field.value.strip() else None
        
        # 从表格获取参数映射
        params_mapping = self._get_params_mapping_json()
        
        # 调用保存回调
        self.on_save(request_id, name, timeout, retry_count, custom_method, params_mapping)
    
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
