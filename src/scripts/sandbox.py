"""Python脚本沙箱 - 安全执行用户自定义脚本"""

import json
import re
from typing import Any, Optional
from datetime import datetime


class ScriptSandbox:
    """
    Python脚本沙箱
    
    提供安全的脚本执行环境，限制可访问的模块和函数
    """
    
    # 允许导入的模块白名单
    ALLOWED_MODULES = {
        'json',
        're',
        'math',
        'datetime',
        'time',
        'base64',
        'hashlib',
        'urllib.parse',
        'collections',
        'itertools',
    }
    
    # 内置函数白名单
    ALLOWED_BUILTINS = {
        'abs', 'all', 'any', 'bool', 'bytes', 'chr', 'dict', 'dir',
        'divmod', 'enumerate', 'filter', 'float', 'format', 'frozenset',
        'hasattr', 'hash', 'hex', 'id', 'int', 'isinstance', 'issubclass',
        'iter', 'len', 'list', 'map', 'max', 'min', 'next', 'object',
        'oct', 'ord', 'pow', 'print', 'range', 'repr', 'reversed',
        'round', 'set', 'slice', 'sorted', 'str', 'sum', 'tuple', 'type',
        'zip', 'None', 'True', 'False',
    }
    
    def __init__(self, timeout: int = 10):
        """
        初始化沙箱
        
        Args:
            timeout: 脚本执行超时时间（秒）
        """
        self.timeout = timeout
    
    def execute(self, script: str, context: dict) -> dict:
        """
        执行用户脚本
        
        Args:
            script: Python脚本代码
            context: 执行上下文，包含 response, variables, prev_result 等
            
        Returns:
            dict: 执行结果 {
                'success': bool,
                'result': Any,
                'variables': dict,  # 脚本中设置的变量
                'error': str | None
            }
        """
        if not script or not script.strip():
            return {
                'success': True,
                'result': None,
                'variables': {},
                'error': None,
            }
        
        try:
            # 准备安全的命名空间
            safe_globals = self._build_safe_globals(context)
            
            # 用于捕获脚本输出的字典
            output = {'result': None, 'variables': {}}
            
            # 添加输出捕获对象
            safe_globals['_output'] = output
            
            # 执行脚本
            exec(script, safe_globals)
            
            # 提取脚本中设置的变量（排除内置和下划线开头的）
            variables = {
                k: v for k, v in safe_globals.items()
                if not k.startswith('_') and k not in self.ALLOWED_BUILTINS
                and k not in context.keys()
            }
            
            return {
                'success': True,
                'result': output.get('result'),
                'variables': variables,
                'error': None,
            }
            
        except TimeoutError:
            return {
                'success': False,
                'result': None,
                'variables': {},
                'error': f'脚本执行超时（{self.timeout}秒）',
            }
        except Exception as e:
            return {
                'success': False,
                'result': None,
                'variables': {},
                'error': f'{type(e).__name__}: {str(e)}',
            }
    
    def _build_safe_globals(self, context: dict) -> dict:
        """
        构建安全的 globals 字典
        
        Args:
            context: 执行上下文
            
        Returns:
            dict: 安全的 globals 字典
        """
        # 创建受限的 builtins
        safe_builtins = {
            name: getattr(__builtins__, name) if hasattr(__builtins__, name) else None
            for name in self.ALLOWED_BUILTINS
        }
        
        # 构建 globals
        safe_globals = {
            '__builtins__': safe_builtins,
            '__name__': '__sandbox__',
        }
        
        # 添加允许的模块
        for module_name in self.ALLOWED_MODULES:
            try:
                module = __import__(module_name)
                # 处理子模块（如 urllib.parse）
                if '.' in module_name:
                    parts = module_name.split('.')
                    for part in parts[1:]:
                        module = getattr(module, part)
                safe_globals[module_name.replace('.', '_')] = module
            except ImportError:
                pass
        
        # 添加工具函数
        safe_globals.update(self._get_utility_functions())
        
        # 添加上下文对象
        safe_globals.update(context)
        
        return safe_globals
    
    def _get_utility_functions(self) -> dict:
        """获取工具函数"""
        
        def json_parse(text: str) -> Any:
            """解析JSON字符串"""
            try:
                return json.loads(text)
            except Exception as e:
                raise ValueError(f"JSON解析失败: {e}")
        
        def json_stringify(obj: Any, indent: int = 2) -> str:
            """将对象转换为JSON字符串"""
            try:
                return json.dumps(obj, ensure_ascii=False, indent=indent)
            except Exception as e:
                raise ValueError(f"JSON序列化失败: {e}")
        
        def regex_match(pattern: str, text: str) -> Optional[str]:
            """正则表达式匹配"""
            match = re.search(pattern, text)
            return match.group(0) if match else None
        
        def regex_extract(pattern: str, text: str, group: int = 1) -> Optional[str]:
            """正则表达式提取"""
            match = re.search(pattern, text)
            return match.group(group) if match else None
        
        def base64_encode(text: str) -> str:
            """Base64编码"""
            import base64
            return base64.b64encode(text.encode('utf-8')).decode('utf-8')
        
        def base64_decode(text: str) -> str:
            """Base64解码"""
            import base64
            return base64.b64decode(text.encode('utf-8')).decode('utf-8')
        
        return {
            'json_parse': json_parse,
            'json_stringify': json_stringify,
            'regex_match': regex_match,
            'regex_extract': regex_extract,
            'base64_encode': base64_encode,
            'base64_decode': base64_decode,
        }
    
    def validate_script(self, script: str) -> tuple[bool, str]:
        """
        验证脚本安全性
        
        Args:
            script: 要验证的脚本
            
        Returns:
            tuple[bool, str]: (是否安全, 错误信息)
        """
        if not script or not script.strip():
            return True, ""
        
        # 检查危险关键字
        dangerous_patterns = [
            r'\bimport\s+os\b',
            r'\bimport\s+sys\b',
            r'\bimport\s+subprocess\b',
            r'\bimport\s+shutil\b',
            r'\bos\.',
            r'\bsys\.',
            r'\beval\s*\(',
            r'\bexec\s*\(',
            r'\b__import__\s*\(',
            r'\bopen\s*\(',
            r'\bfile\s*\(',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, script):
                return False, f"检测到不安全的代码: {pattern}"
        
        return True, ""
