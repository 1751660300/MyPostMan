"""执行上下文管理器 - 管理执行过程中的变量和状态"""

from typing import Any, Optional
from datetime import datetime


class ExecutionContext:
    """
    执行上下文
    
    管理执行计划运行时的变量、状态和数据传递
    """
    
    def __init__(self):
        # 全局变量
        self.global_vars = {}
        
        # 环境变量
        self.env_vars = {}
        
        # 步骤变量（每个步骤的局部变量）
        self.step_variables = {}
        
        # 上一步的执行结果
        self.prev_step_result = None
        
        # 当前步骤信息
        self.current_step = None
        
        # 所有步骤的执行结果
        self.step_results = {}
        
        # 执行开始时间
        self.started_at = None
        
        # 自定义变量（用户可以在脚本中设置）
        self.custom_vars = {}
    
    def set_global_vars(self, vars_dict: dict):
        """设置全局变量"""
        self.global_vars.update(vars_dict)
    
    def set_env_vars(self, vars_dict: dict):
        """设置环境变量"""
        self.env_vars.update(vars_dict)
    
    def start_execution(self):
        """标记执行开始"""
        self.started_at = datetime.now()
    
    def set_current_step(self, step_id: str, step_name: str):
        """
        设置当前步骤
        
        Args:
            step_id: 步骤ID
            step_name: 步骤名称
        """
        self.current_step = {
            'id': step_id,
            'name': step_name,
            'variables': {},
        }
    
    def save_step_result(self, step_id: str, result: dict):
        """
        保存步骤执行结果
        
        Args:
            step_id: 步骤ID
            result: 执行结果
        """
        self.step_results[step_id] = result
        
        # 更新上一步结果
        self.prev_step_result = result
        
        # 如果当前步骤有变量，保存到步骤变量中
        if self.current_step and self.current_step.get('id') == step_id:
            self.step_variables[step_id] = self.current_step.get('variables', {})
    
    def set_variable(self, key: str, value: Any):
        """
        设置变量（在当前步骤上下文中）
        
        Args:
            key: 变量名
            value: 变量值
        """
        if self.current_step:
            self.current_step.setdefault('variables', {})[key] = value
            self.custom_vars[key] = value
    
    def get_context_dict(self) -> dict:
        """
        获取完整的上下文字典（用于变量解析器）
        
        Returns:
            dict: 上下文字典
        """
        return {
            'global': self.global_vars,
            'env': self.env_vars,
            'prev_step': self.prev_step_result or {},
            'current': {
                'step': self.current_step or {},
                'variables': self.custom_vars,
            },
            'step_results': self.step_results,
            'custom': self.custom_vars,
        }
    
    def get_variable(self, key: str, default: Any = None) -> Any:
        """
        获取变量值
        
        查找顺序：
        1. 当前步骤变量
        2. 自定义变量
        3. 全局变量
        4. 环境变量
        
        Args:
            key: 变量名
            default: 默认值
            
        Returns:
            Any: 变量值
        """
        # 当前步骤变量
        if self.current_step:
            step_vars = self.current_step.get('variables', {})
            if key in step_vars:
                return step_vars[key]
        
        # 自定义变量
        if key in self.custom_vars:
            return self.custom_vars[key]
        
        # 全局变量
        if key in self.global_vars:
            return self.global_vars[key]
        
        # 环境变量
        if key in self.env_vars:
            return self.env_vars[key]
        
        return default
    
    def clear(self):
        """清空上下文（准备下一次执行）"""
        self.global_vars.clear()
        self.env_vars.clear()
        self.step_variables.clear()
        self.prev_step_result = None
        self.current_step = None
        self.step_results.clear()
        self.started_at = None
        self.custom_vars.clear()
    
    def get_execution_duration(self) -> Optional[float]:
        """
        获取执行时长（秒）
        
        Returns:
            Optional[float]: 执行时长，如果未开始则返回None
        """
        if not self.started_at:
            return None
        
        return (datetime.now() - self.started_at).total_seconds()
