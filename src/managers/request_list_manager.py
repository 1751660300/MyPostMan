"""请求 URL 列表管理模块 - 管理常用的请求 URL"""

import json
import os
import yaml
import uuid
from typing import Optional
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import sys

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from models.database import DatabaseManager, RequestListModel


class RequestItem:
    """请求项数据模型"""
    def __init__(self, id: str, url: str, method: str = "GET", name: str = "",
                 params: dict = None, headers: dict = None, body: str = "",
                 body_type: str = "none", created_at: str = None):
        self.id = id
        self.url = url
        self.method = method
        self.name = name
        self.params = params or {}
        self.headers = headers or {}
        self.body = body or ""
        self.body_type = body_type or "none"
        self.created_at = created_at or datetime.now().isoformat()


class RequestListManager:
    """请求 URL 列表管理器（基于数据库）"""

    def __init__(self, db_path: str = None):
        # 数据库路径默认为与模块同目录下的 mypostman.db
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), "mypostman.db")
        self.db = DatabaseManager(db_path)
        # 迁移旧数据（如果存在）
        self._migrate_from_json()

    def _migrate_from_json(self):
        """从旧的 JSON 文件迁移数据到数据库"""
        try:
            session = self.db.get_session()
            # 检查数据库中是否已有数据
            count = session.query(RequestListModel).count()
            session.close()
            
            if count > 0:
                # 已有数据，不需要迁移
                return

            storage_file = os.path.join(os.path.dirname(__file__), "request_list.json")
            if not os.path.exists(storage_file):
                return

            with open(storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            session = self.db.get_session()
            try:
                for item in data:
                    request_model = RequestListModel(
                        id=item.get('id', str(uuid.uuid4())),
                        url=item.get('url', ''),
                        method=item.get('method', 'GET'),
                        name=item.get('name', ''),
                        params=json.dumps(item.get('params', {}), ensure_ascii=False),
                        headers=json.dumps(item.get('headers', {}), ensure_ascii=False),
                        created_at=datetime.fromisoformat(item.get('created_at', datetime.now().isoformat()))
                    )
                    session.add(request_model)
                session.commit()
                
                # 迁移成功后，备份并重命名旧文件
                backup_file = storage_file + ".backup"
                if not os.path.exists(backup_file):
                    os.rename(storage_file, backup_file)
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        except Exception as e:
            # 迁移失败不影响正常使用
            print(f"迁移旧数据失败（可忽略）: {e}")

    def _model_to_item(self, model: RequestListModel) -> RequestItem:
        """将数据库模型转换为 RequestItem"""
        return RequestItem(
            id=model.id,
            url=model.url,
            method=model.method,
            name=model.name,
            params=json.loads(model.params) if model.params else {},
            headers=json.loads(model.headers) if model.headers else {},
            body=model.body if hasattr(model, 'body') else "",
            body_type=model.body_type if hasattr(model, 'body_type') else "none",
            created_at=model.created_at.isoformat() if model.created_at else datetime.now().isoformat()
        )

    def add_request(self, url: str, method: str = "GET", name: str = "",
                   params: dict = None, headers: dict = None, body: str = None,
                   body_type: str = "none") -> RequestItem:
        """
        添加请求项

        Args:
            url: 请求 URL
            method: 请求方法
            name: 请求名称（可选）
            params: 请求参数
            headers: 请求头
            body: 请求体
            body_type: 请求体类型

        Returns:
            RequestItem: 新创建的请求项
        """
        # 如果没有提供名称，使用 URL 的最后部分
        if not name:
            name = url.split('/')[-1] or url

        request_id = str(uuid.uuid4())
        created_at = datetime.now()

        session = self.db.get_session()
        try:
            request_model = RequestListModel(
                id=request_id,
                url=url,
                method=method,
                name=name,
                params=json.dumps(params or {}, ensure_ascii=False),
                headers=json.dumps(headers or {}, ensure_ascii=False),
                body=body or "",
                body_type=body_type or "none",
                created_at=created_at
            )
            session.add(request_model)
            session.commit()

            return self._model_to_item(request_model)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def update_request(self, request_id: str, url: str = None, method: str = None,
                      name: str = None, params: dict = None, headers: dict = None,
                      body: str = None, body_type: str = None) -> Optional[RequestItem]:
        """
        更新请求项

        Args:
            request_id: 请求项 ID
            url: 请求 URL
            method: 请求方法
            name: 请求名称
            params: 请求参数
            headers: 请求头
            body: 请求体
            body_type: 请求体类型

        Returns:
            Optional[RequestItem]: 更新后的请求项，如果不存在则返回 None
        """
        session = self.db.get_session()
        try:
            request = session.query(RequestListModel).filter_by(id=request_id).first()
            if not request:
                return None

            if url is not None:
                request.url = url
            if method is not None:
                request.method = method
            if name is not None:
                request.name = name
            if params is not None:
                request.params = json.dumps(params, ensure_ascii=False)
            if headers is not None:
                request.headers = json.dumps(headers, ensure_ascii=False)
            if body is not None:
                request.body = body
            if body_type is not None:
                request.body_type = body_type

            session.commit()
            return self._model_to_item(request)
        except Exception as e:
            session.rollback()
            return None
        finally:
            session.close()

    def remove_request(self, request_id: str) -> bool:
        """
        删除请求项

        Args:
            request_id: 请求项 ID

        Returns:
            bool: 是否删除成功
        """
        session = self.db.get_session()
        try:
            request = session.query(RequestListModel).filter_by(id=request_id).first()
            if request:
                session.delete(request)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            return False
        finally:
            session.close()

    def get_request(self, request_id: str) -> Optional[RequestItem]:
        """
        获取请求项

        Args:
            request_id: 请求项 ID

        Returns:
            Optional[RequestItem]: 请求项，如果不存在则返回 None
        """
        session = self.db.get_session()
        try:
            model = session.query(RequestListModel).filter_by(id=request_id).first()
            if model:
                return self._model_to_item(model)
            return None
        finally:
            session.close()

    def get_all_requests(self) -> list[RequestItem]:
        """
        获取所有请求项

        Returns:
            list[RequestItem]: 请求项列表
        """
        session = self.db.get_session()
        try:
            models = session.query(RequestListModel).order_by(RequestListModel.created_at).all()
            return [self._model_to_item(m) for m in models]
        finally:
            session.close()

    def get_paged(self, page: int = 1, page_size: int = 20, keyword: str = "") -> tuple[list[RequestItem], int]:
        """
        分页查询请求列表（按创建时间排序）

        Args:
            page: 页码（从1开始）
            page_size: 每页数量
            keyword: 搜索关键词（可选，匹配 name 或 url）

        Returns:
            tuple: (请求列表, 总记录数)
        """
        session = self.db.get_session()
        try:
            # 构建查询
            query = session.query(RequestListModel)
            
            # 如果有搜索关键词，添加过滤条件
            if keyword:
                keyword_pattern = f"%{keyword}%"
                query = query.filter(
                    (RequestListModel.name.like(keyword_pattern)) |
                    (RequestListModel.url.like(keyword_pattern))
                )
            
            # 获取总记录数
            total = query.count()
            
            # 计算偏移量
            offset = (page - 1) * page_size
            
            # 分页查询，按创建时间排序
            models = query.order_by(
                RequestListModel.created_at
            ).limit(page_size).offset(offset).all()
            
            return [self._model_to_item(m) for m in models], total
        finally:
            session.close()

    def clear_all(self):
        """清空所有请求项"""
        session = self.db.get_session()
        try:
            session.query(RequestListModel).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
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
