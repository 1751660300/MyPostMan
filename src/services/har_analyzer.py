"""HAR 文件分析器 - 从 HAR 文件中提取字段数据"""

import json
import re
from typing import Optional


class HarAnalyzer:
    """HAR 文件分析器
    
    解析 HAR 文件，提取响应数据、Header、Cookie 等信息
    """
    
    def __init__(self, har_file: str):
        """初始化分析器
        
        Args:
            har_file: HAR 文件路径
        """
        self.har_file = har_file
        self.har_data = None
        self.entries = []
        
        # 加载 HAR 文件
        self._load_har()
    
    def _load_har(self):
        """加载 HAR 文件"""
        try:
            with open(self.har_file, 'r', encoding='utf-8') as f:
                self.har_data = json.load(f)
            
            # 提取所有请求条目
            if 'log' in self.har_data and 'entries' in self.har_data['log']:
                self.entries = self.har_data['log']['entries']
                print(f"✅ 加载 HAR 文件: {len(self.entries)} 个请求")
            else:
                print(f"⚠️ HAR 文件格式不正确")
                self.entries = []
        except Exception as e:
            print(f"❌ 加载 HAR 文件失败: {e}")
            self.entries = []
    
    def extract_response_body(self, pattern: str, url_pattern: str = None, extract_type: str = 'json') -> Optional[dict]:
        """从响应体中提取数据
        
        Args:
            pattern: JSON 路径或正则表达式
            url_pattern: URL 过滤模式（可选）
            extract_type: 提取方式 ('json' 或 'regex')
            
        Returns:
            包含 value, source, path, url 的字典，未找到返回 None
        """
        for entry in self.entries:
            # URL 过滤
            if url_pattern and url_pattern not in entry['request']['url']:
                continue
            
            # 检查响应
            response = entry.get('response', {})
            content = response.get('content', {})
            
            try:
                text = content.get('text', '')
                if not text:
                    continue
                
                value = None
                
                if extract_type == 'regex':
                    # 使用正则表达式提取
                    value = self._extract_regex_value(text, pattern)
                else:
                    # 使用 JSON 路径提取
                    # 只处理 JSON 响应
                    content_type = ''
                    for header in response.get('headers', []):
                        if header['name'].lower() == 'content-type':
                            content_type = header['value']
                            break
                    
                    if 'application/json' not in content_type:
                        continue
                    
                    data = json.loads(text)
                    value = self._extract_json_value(data, pattern)
                
                if value is not None:
                    return {
                        'value': str(value),
                        'source': 'response',
                        'path': pattern,
                        'url': entry['request']['url'],
                        'extract_type': extract_type,
                    }
            except (json.JSONDecodeError, KeyError, re.error):
                continue
        
        return None
    
    @staticmethod
    def _extract_regex_value(text: str, regex_pattern: str) -> Optional[str]:
        """使用正则表达式从文本中提取值
        
        Args:
            text: 要搜索的文本
            regex_pattern: 正则表达式模式
            
        Returns:
            提取的值或 None
        """
        try:
            match = re.search(regex_pattern, text)
            if match:
                # 如果有捕获组，返回第一个捕获组
                if match.groups():
                    return match.group(1)
                # 否则返回整个匹配
                return match.group(0)
            return None
        except re.error:
            return None
    
    def extract_header(self, header_name: str, url_pattern: str = None) -> Optional[dict]:
        """从响应头中提取字段
        
        Args:
            header_name: Header 名称
            url_pattern: URL 过滤模式（可选）
            
        Returns:
            包含 value, source, path, url 的字典，未找到返回 None
        """
        for entry in self.entries:
            # URL 过滤
            if url_pattern and url_pattern not in entry['request']['url']:
                continue
            
            response = entry.get('response', {})
            
            # 查找 Header
            for header in response.get('headers', []):
                if header['name'].lower() == header_name.lower():
                    return {
                        'value': header['value'],
                        'source': 'header',
                        'path': header_name,
                        'url': entry['request']['url'],
                    }
        
        return None
    
    def extract_cookie(self, cookie_name: str) -> Optional[dict]:
        """从 Cookie 中提取字段
        
        Args:
            cookie_name: Cookie 名称
            
        Returns:
            包含 value, source, path, url 的字典，未找到返回 None
        """
        for entry in self.entries:
            # 检查响应的 Cookie
            response = entry.get('response', {})
            
            for header in response.get('headers', []):
                if header['name'].lower() == 'set-cookie':
                    cookie_value = header['value']
                    
                    # 解析 Set-Cookie header
                    if f'{cookie_name}=' in cookie_value:
                        # 提取 cookie 值
                        parts = cookie_value.split(';')[0]  # 去掉过期时间等
                        if '=' in parts:
                            name, value = parts.split('=', 1)
                            if name.strip() == cookie_name:
                                return {
                                    'value': value.strip(),
                                    'source': 'cookie',
                                    'path': cookie_name,
                                    'url': entry['request']['url'],
                                }
        
        return None
    
    def extract_field(self, field_config: dict) -> Optional[dict]:
        """根据配置提取字段
        
        Args:
            field_config: 字段配置 {'name': '', 'path': '', 'source': '', 'extract_type': ''}
            
        Returns:
            提取的数据或 None
        """
        var_name = field_config['name']
        path = field_config['path']
        source = field_config['source']
        extract_type = field_config.get('extract_type', 'json')  # 默认 json
        
        if source == 'response':
            return self.extract_response_body(path, extract_type=extract_type)
        elif source == 'header':
            return self.extract_header(path)
        elif source == 'cookie':
            return self.extract_cookie(path)
        
        return None
    
    def extract_all_fields(self, field_configs: list) -> dict:
        """批量提取所有配置的字段
        
        Args:
            field_configs: 字段配置列表
            
        Returns:
            {var_name: extracted_data}
        """
        captured_data = {}
        
        for config in field_configs:
            var_name = config['name']
            
            # 如果已经捕获，跳过
            if var_name in captured_data:
                continue
            
            # 提取字段
            result = self.extract_field(config)
            
            if result:
                captured_data[var_name] = result
                print(f"✅ 提取字段: {var_name} = {result['value'][:50]}...")
            else:
                print(f"⚠️ 未找到字段: {var_name}")
        
        return captured_data
    
    @staticmethod
    def _extract_json_value(data: dict, json_path: str):
        """从 JSON 数据中提取指定路径的值
        
        Args:
            data: JSON 数据
            json_path: 点号分隔的路径，如 "data.user.id"
            
        Returns:
            提取的值或 None
        """
        try:
            keys = json_path.split('.')
            current = data
            
            for key in keys:
                if isinstance(current, dict):
                    current = current.get(key)
                elif isinstance(current, list):
                    # 支持数组索引，如 "items.0.id"
                    try:
                        index = int(key)
                        current = current[index]
                    except (ValueError, IndexError):
                        return None
                else:
                    return None
                
                if current is None:
                    return None
            
            return current
        except Exception:
            return None
    
    def get_summary(self) -> dict:
        """获取 HAR 文件摘要信息
        
        Returns:
            摘要信息字典
        """
        total_requests = len(self.entries)
        
        # 统计不同类型的请求
        methods = {}
        status_codes = {}
        
        for entry in self.entries:
            method = entry['request']['method']
            status = entry['response']['status']
            
            methods[method] = methods.get(method, 0) + 1
            status_codes[str(status)] = status_codes.get(str(status), 0) + 1
        
        return {
            'total_requests': total_requests,
            'methods': methods,
            'status_codes': status_codes,
        }
