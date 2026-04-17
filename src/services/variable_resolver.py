"""变量解析器 - 解析执行计划中的变量引用"""

import re
from typing import Any, Optional


class VariableResolver:
    """
    变量解析器
    
    支持以下变量语法：
    - ${prev_step.response.data.user_id} - 引用上一步的响应数据
    - ${global.base_url} - 引用全局变量
    - ${env.api_key} - 引用环境变量
    - ${current.variables.token} - 引用当前步骤的变量
    """
    
    def __init__(self):
        self.context = {}
    
    def set_context(self, context: dict):
        """
        设置上下文
        
        Args:
            context: 上下文字典，包含 prev_step, global, env, current 等
        """
        self.context = context
    
    def resolve(self, text: str) -> str:
        """
        解析文本中的所有变量引用
        
        Args:
            text: 包含变量引用的文本
            
        Returns:
            str: 解析后的文本
        """
        if not text or '${' not in text:
            return text
        
        # 正则表达式匹配 ${...} 模式
        pattern = r'\$\{([^}]+)\}'
        
        def replace_var(match):
            var_path = match.group(1).strip()
            value = self._get_value_by_path(var_path)
            
            if value is None:
                # 未找到变量，返回原始占位符
                return match.group(0)
            
            # 转换为字符串
            if isinstance(value, (dict, list)):
                import json
                return json.dumps(value, ensure_ascii=False)
            return str(value)
        
        try:
            result = re.sub(pattern, replace_var, text)
            return result
        except Exception as e:
            print(f"变量解析错误: {e}")
            return text
    
    def resolve_value(self, text: str) -> Any:
        """
        解析单个变量引用，返回实际值
        
        Args:
            text: 变量引用，如 "${prev_step.response.data.id}"
            
        Returns:
            Any: 解析后的值，如果解析失败则返回原始文本
        """
        if not text or not text.startswith('${') or not text.endswith('}'):
            return text
        
        var_path = text[2:-1].strip()  # 移除 ${ 和 }
        value = self._get_value_by_path(var_path)
        
        return value if value is not None else text
    
    def _get_value_by_path(self, path: str) -> Any:
        """
        根据路径获取值
        
        Args:
            path: 变量路径，如 "prev_step.response.data.user_id"
            
        Returns:
            Any: 找到的值，如果未找到则返回 None
        """
        # 分割路径
        parts = path.split('.')
        
        if not parts:
            return None
        
        # 获取根对象
        root_key = parts[0]
        if root_key not in self.context:
            return None
        
        current = self.context[root_key]
        
        # 逐级访问
        for part in parts[1:]:
            if current is None:
                return None
            
            if isinstance(current, dict):
                if part not in current:
                    return None
                current = current[part]
            elif hasattr(current, part):
                current = getattr(current, part)
            else:
                return None
        
        return current
    
    def extract_variables(self, text: str) -> list[str]:
        """
        提取文本中的所有变量引用
        
        Args:
            text: 包含变量引用的文本
            
        Returns:
            list[str]: 变量路径列表
        """
        if not text or '${' not in text:
            return []
        
        pattern = r'\$\{([^}]+)\}'
        matches = re.findall(pattern, text)
        
        return [m.strip() for m in matches]
    
    def has_unresolved_variables(self, text: str) -> bool:
        """
        检查文本是否包含未解析的变量
        
        Args:
            text: 要检查的文本
            
        Returns:
            bool: 是否包含未解析的变量
        """
        variables = self.extract_variables(text)
        
        for var_path in variables:
            value = self._get_value_by_path(var_path)
            if value is None:
                return True
        
        return False
