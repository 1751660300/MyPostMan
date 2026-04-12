"""请求 URL 列表管理模块 - 管理常用的请求 URL"""

import json
import os
import yaml
from typing import Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class RequestItem:
    """请求项数据模型"""
    id: str
    url: str
    method: str = "GET"
    name: str = ""
    params: dict[str, str] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class RequestListManager:
    """请求 URL 列表管理器"""
    
    def __init__(self, storage_file: str = "request_list.json"):
        self.storage_file = os.path.join(os.path.dirname(__file__), storage_file)
        self.requests: list[RequestItem] = []
        self._load_from_file()
    
    def _load_from_file(self):
        """从文件加载请求列表"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.requests = [RequestItem(**item) for item in data]
        except Exception:
            self.requests = []
    
    def _save_to_file(self):
        """保存请求列表到文件"""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(r) for r in self.requests], f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def add_request(self, url: str, method: str = "GET", name: str = "", 
                   params: dict[str, str] = None, headers: dict[str, str] = None) -> RequestItem:
        """
        添加请求项
        
        Args:
            url: 请求 URL
            method: 请求方法
            name: 请求名称（可选）
            params: 请求参数
            headers: 请求头
            
        Returns:
            RequestItem: 新创建的请求项
        """
        import uuid
        
        # 如果没有提供名称，使用 URL 的最后部分
        if not name:
            name = url.split('/')[-1] or url
        
        request_item = RequestItem(
            id=str(uuid.uuid4()),
            url=url,
            method=method,
            name=name,
            params=params or {},
            headers=headers or {}
        )
        
        self.requests.append(request_item)
        self._save_to_file()
        return request_item
    
    def remove_request(self, request_id: str) -> bool:
        """
        删除请求项
        
        Args:
            request_id: 请求项 ID
            
        Returns:
            bool: 是否删除成功
        """
        original_count = len(self.requests)
        self.requests = [r for r in self.requests if r.id != request_id]
        
        if len(self.requests) < original_count:
            self._save_to_file()
            return True
        return False
    
    def get_request(self, request_id: str) -> Optional[RequestItem]:
        """
        获取请求项
        
        Args:
            request_id: 请求项 ID
            
        Returns:
            Optional[RequestItem]: 请求项，如果不存在则返回 None
        """
        for request in self.requests:
            if request.id == request_id:
                return request
        return None
    
    def get_all_requests(self) -> list[RequestItem]:
        """
        获取所有请求项
        
        Returns:
            list[RequestItem]: 请求项列表
        """
        return self.requests.copy()
    
    def clear_all(self):
        """清空所有请求项"""
        self.requests = []
        self._save_to_file()
    
    def import_from_clipboard(self, clipboard_text: str) -> list[RequestItem]:
        """
        从剪贴板文本导入请求项

        支持的格式：
        1. 每行一个 URL（简单格式）
        2. JSON 格式数组
        3. Swagger JSON 定义（包含 paths 字段）
        4. Swagger YAML 定义（包含 paths 字段）
        5. curl 命令格式（从浏览器开发者工具复制）

        Args:
            clipboard_text: 剪贴板文本

        Returns:
            list[RequestItem]: 导入的请求项列表
        """
        imported = []

        # 1. 尝试解析 Swagger JSON
        try:
            data = json.loads(clipboard_text)
            if isinstance(data, dict) and 'paths' in data:
                # Swagger JSON 格式
                return self._parse_swagger(data)
            elif isinstance(data, list):
                # 普通 JSON 数组格式
                for item in data:
                    if isinstance(item, dict) and 'url' in item:
                        request = self.add_request(
                            url=item['url'],
                            method=item.get('method', 'GET'),
                            name=item.get('name', ''),
                            params=item.get('params', {}),
                            headers=item.get('headers', {})
                        )
                        imported.append(request)
                return imported
        except (json.JSONDecodeError, ValueError):
            pass

        # 2. 尝试解析 Swagger YAML
        try:
            data = yaml.safe_load(clipboard_text)
            if isinstance(data, dict) and 'paths' in data:
                # Swagger YAML 格式
                return self._parse_swagger(data)
        except yaml.YAMLError:
            pass

        # 3. 尝试解析 curl 命令格式
        if clipboard_text.strip().startswith('curl'):
            return self._parse_curl_commands(clipboard_text)

        # 4. 按行解析 URL
        lines = clipboard_text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and (line.startswith('http://') or line.startswith('https://') or line.startswith('/')):
                # 尝试从 URL 中提取参数
                url = line
                params = {}

                # 解析查询参数
                if '?' in url:
                    from urllib.parse import urlparse, parse_qs
                    parsed = urlparse(url)
                    query_params = parse_qs(parsed.query)
                    params = {k: v[0] for k, v in query_params.items()}
                    url = f"{parsed.path}"

                request = self.add_request(
                    url=url,
                    method="GET",
                    params=params
                )
                imported.append(request)

        return imported

    def _parse_swagger(self, swagger_data: dict) -> list[RequestItem]:
        """
        解析 Swagger 定义（JSON 或 YAML 格式）
        
        Args:
            swagger_data: Swagger 定义数据
            
        Returns:
            list[RequestItem]: 解析出的请求项列表
        """
        imported = []
        
        # 获取 basePath（如果有）
        base_path = swagger_data.get('basePath', '')
        
        # 获取 servers（OpenAPI 3.0 格式）
        servers = swagger_data.get('servers', [])
        server_url = ''
        if servers:
            server_url = servers[0].get('url', '')
            # 如果 server_url 是相对路径，添加到 base_path
            if not server_url.startswith('http'):
                base_path = server_url + base_path
        
        # 获取 paths
        paths = swagger_data.get('paths', {})
        
        for path, methods in paths.items():
            if isinstance(methods, dict):
                for method, details in methods.items():
                    method = method.upper()
                    if method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
                        full_url = f"{base_path}{path}"
                        
                        # 获取摘要/描述
                        summary = details.get('summary', '') or details.get('description', '') or full_url
                        
                        # 提取参数
                        params = {}
                        headers = {}
                        
                        # OpenAPI 2.0 (Swagger) 格式
                        if 'parameters' in details:
                            for param in details['parameters']:
                                if param.get('in') == 'query' and 'name' in param:
                                    params[param['name']] = str(param.get('default', ''))
                                elif param.get('in') == 'header' and 'name' in param:
                                    headers[param['name']] = str(param.get('default', ''))
                        
                        # OpenAPI 3.0 格式
                        if 'requestBody' in details:
                            request_body = details['requestBody']
                            if 'content' in request_body:
                                content = request_body['content']
                                if 'application/json' in content:
                                    headers['Content-Type'] = 'application/json'
                        
                        # 提取 tags 作为名称的一部分
                        tags = details.get('tags', [])
                        if tags:
                            name = f"[{', '.join(tags)}] {summary}"
                        else:
                            name = summary
                        
                        request = self.add_request(
                            url=full_url,
                            method=method,
                            name=name,
                            params=params,
                            headers=headers
                        )
                        imported.append(request)
        
        return imported

    def _parse_curl_commands(self, curl_text: str) -> list[RequestItem]:
        """
        解析 curl 命令格式
        
        Args:
            curl_text: 包含 curl 命令的文本
            
        Returns:
            list[RequestItem]: 解析出的请求项列表
        """
        import re
        from urllib.parse import urlparse, parse_qs
        
        imported = []
        
        # 分割多个 curl 命令（以 curl 开头为分隔符）
        commands = re.split(r'(?=curl\s)', curl_text.strip())
        
        for cmd in commands:
            cmd = cmd.strip()
            if not cmd.startswith('curl'):
                continue
            
            # 提取 URL
            url_match = re.search(r"curl\s+['\"]?([^'\"]+)['\"]?", cmd)
            if not url_match:
                continue
            
            url = url_match.group(1).strip()
            
            # 提取请求方法
            method = "GET"
            method_match = re.search(r"-X\s+(\w+)", cmd)
            if method_match:
                method = method_match.group(1).upper()
            
            # 提取请求头
            headers = {}
            header_matches = re.findall(r"-H\s+['\"]([^'\"]+)['\"]", cmd)
            for header_str in header_matches:
                if ':' in header_str:
                    key, value = header_str.split(':', 1)
                    headers[key.strip()] = value.strip()
            
            # 提取数据（用于 POST/PUT 等）
            body = None
            data_match = re.search(r"(?:-d|--data)\s+['\"]([^'\"]*)['\"]", cmd)
            if data_match:
                body = data_match.group(1)
                # 如果是 JSON 格式，尝试解析
                if 'application/json' in headers.get('Content-Type', ''):
                    try:
                        json.loads(body)
                        # 如果是有效的 JSON，可以存储或标记
                    except json.JSONDecodeError:
                        pass
            
            # 解析 URL 中的查询参数
            params = {}
            if '?' in url:
                parsed = urlparse(url)
                query_params = parse_qs(parsed.query)
                params = {k: v[0] for k, v in query_params.items()}
                url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            
            # 提取请求名称
            name = url.split('/')[-1] or url
            if 'summary' in headers:
                name = headers['summary']
            
            request = self.add_request(
                url=url,
                method=method,
                name=name,
                params=params,
                headers=headers
            )
            imported.append(request)
        
        return imported
