"""数据模型模块 - 定义请求和响应的数据结构"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class HttpMethod(Enum):
    """HTTP 请求方法枚举"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass
class HttpRequest:
    """HTTP 请求数据模型"""
    url: str = ""
    method: HttpMethod = HttpMethod.GET
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, str] = field(default_factory=dict)
    body: Optional[str] = None
    body_type: str = "none"  # none, json, form-data, x-www-form-urlencoded, text

    def get_headers_dict(self) -> dict[str, str]:
        """获取过滤后的请求头（过滤空值）"""
        return {k: v for k, v in self.headers.items() if k.strip()}


@dataclass
class HttpResponse:
    """HTTP 响应数据模型"""
    status_code: int = 0
    reason: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    body: str = ""
    elapsed: float = 0.0  # 响应时间（毫秒）
    error: Optional[str] = None

    @property
    def is_success(self) -> bool:
        """判断请求是否成功"""
        return self.error is None and 200 <= self.status_code < 300

    @property
    def formatted_body(self) -> str:
        """格式化响应体（尝试 JSON 格式化）"""
        import json
        try:
            parsed = json.loads(self.body)
            return json.dumps(parsed, indent=2, ensure_ascii=False)
        except (json.JSONDecodeError, ValueError):
            return self.body


@dataclass
class HistoryItem:
    """历史记录项"""
    id: str
    url: str
    method: HttpMethod
    status_code: int
    elapsed: float
    timestamp: float
    request: HttpRequest
    response: HttpResponse


@dataclass
class Environment:
    """环境配置数据模型"""
    id: str
    name: str
    variables: dict[str, str] = field(default_factory=dict)
    is_active: bool = False


@dataclass
class GlobalVariables:
    """全局变量数据模型"""
    variables: dict[str, str] = field(default_factory=dict)


@dataclass
class RecordingHistory:
    """录制历史记录数据模型"""
    id: str = ""  # UUID
    url: str = ""  # 目标 URL
    auth_type: str = "custom"  # 认证类型
    variable_name: str = ""  # 变量名前缀
    value: str = ""  # 值描述
    save_location: str = "global"  # 保存位置：environment 或 global
    created_at: str = ""  # 创建时间
    fields_count: int = 0  # 字段数量
    has_auto_capture: bool = False  # 是否有自动捕获
    script_file: str = ""  # 脚本文件路径
    actions_count: int = 0  # 操作数量
    script_content: str = ""  # 脚本内容（用于编辑）
    field_configs: list = None  # 字段配置列表
