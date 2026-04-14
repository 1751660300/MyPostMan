"""HTTP 请求服务模块 - 处理实际的 HTTP 请求"""

import time
import requests
import sys
import os
import warnings
from typing import Optional
from urllib3.exceptions import InsecureRequestWarning

# 抑制 InsecureRequestWarning 警告（当用户选择不验证 SSL 证书时）
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from models import HttpRequest, HttpResponse, HttpMethod


class HttpService:
    """HTTP 请求服务类"""

    def __init__(self):
        self.session = requests.Session()
        # 设置默认超时
        self.session.timeout = 30

    def send_request(self, request: HttpRequest, verify_ssl: bool = True) -> HttpResponse:
        """
        发送 HTTP 请求

        Args:
            request: 请求数据模型对象
            verify_ssl: 是否验证 SSL 证书

        Returns:
            HttpResponse: 响应数据模型对象
        """
        start_time = time.time()

        try:
            # 准备请求头
            headers = request.get_headers_dict()

            # 根据 body_type 设置 Content-Type
            if request.body_type == "json" and request.body:
                headers["Content-Type"] = "application/json"
            elif request.body_type == "form-data":
                # requests 会自动处理 multipart/form-data
                headers.pop("Content-Type", None)
            elif request.body_type == "x-www-form-urlencoded":
                headers["Content-Type"] = "application/x-www-form-urlencoded"

            # 发送请求
            response = self.session.request(
                method=request.method.value,
                url=request.url,
                headers=headers if headers else None,
                params=request.params if request.params else None,
                data=self._prepare_data(request),
                json=self._prepare_json(request),
                timeout=self.session.timeout,
                allow_redirects=True,
                verify=verify_ssl,
            )

            elapsed = (time.time() - start_time) * 1000  # 转换为毫秒

            return HttpResponse(
                status_code=response.status_code,
                reason=response.reason,
                headers=dict(response.headers),
                body=response.text,
                elapsed=round(elapsed, 2),
            )

        except requests.exceptions.Timeout:
            elapsed = (time.time() - start_time) * 1000
            return HttpResponse(
                error="请求超时",
                elapsed=round(elapsed, 2),
            )
        except requests.exceptions.ConnectionError as e:
            elapsed = (time.time() - start_time) * 1000
            return HttpResponse(
                error=f"连接错误: {str(e)}",
                elapsed=round(elapsed, 2),
            )
        except requests.exceptions.RequestException as e:
            elapsed = (time.time() - start_time) * 1000
            return HttpResponse(
                error=f"请求失败: {str(e)}",
                elapsed=round(elapsed, 2),
            )
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            return HttpResponse(
                error=f"未知错误: {str(e)}",
                elapsed=round(elapsed, 2),
            )

    def _prepare_data(self, request: HttpRequest) -> Optional[dict | str]:
        """准备 data 参数（用于 form-data 和 x-www-form-urlencoded）"""
        if request.body_type in ("form-data", "x-www-form-urlencoded") and request.body:
            try:
                import json
                return json.loads(request.body)
            except (json.JSONDecodeError, ValueError):
                return request.body
        return None

    def _prepare_json(self, request: HttpRequest) -> Optional[dict]:
        """准备 json 参数（用于 JSON 请求体）"""
        if request.body_type == "json" and request.body:
            try:
                import json
                return json.loads(request.body)
            except (json.JSONDecodeError, ValueError):
                return None
        return None

    def close(self):
        """关闭 session"""
        self.session.close()
