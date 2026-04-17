"""执行引擎 - 执行计划的串行和并行执行"""

import uuid
import time
import threading
from datetime import datetime
from typing import Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from models.execution_plan import ExecutionPlan, ExecutionStep, ExecutionLog, ExecutionStatus
from services.services import HttpService
from services.variable_resolver import VariableResolver
from services.execution_context import ExecutionContext
from scripts.sandbox import ScriptSandbox
from managers.request_list_manager import RequestListManager


class ExecutionEngine:
    """
    执行引擎
    
    支持串行和并行执行计划，处理变量传递和脚本执行
    """
    
    def __init__(self):
        self.http_service = HttpService()
        self.variable_resolver = VariableResolver()
        self.script_sandbox = ScriptSandbox(timeout=10)
        self.context = ExecutionContext()
        self.request_list_manager = RequestListManager()
        
        # 进度回调
        self.on_progress: Optional[Callable] = None
        
        # 步骤状态回调
        self.on_step_status: Optional[Callable] = None
        
        # 停止标志
        self._stop_flag = False
        self._current_log: Optional[ExecutionLog] = None
    
    def set_progress_callback(self, callback: Callable):
        """
        设置进度回调
        
        Args:
            callback: 回调函数，接收 (progress: float, message: str)
        """
        self.on_progress = callback
    
    def set_step_status_callback(self, callback: Callable):
        """
        设置步骤状态回调
        
        Args:
            callback: 回调函数，接收 (step_index: int, step_name: str, status: str, error: str)
        """
        self.on_step_status = callback
    
    def stop_execution(self):
        """停止当前执行"""
        self._stop_flag = True
        if self._current_log:
            self._current_log.status = ExecutionStatus.STOPPED
            self._current_log.completed_at = datetime.now()
    
    def is_stopped(self) -> bool:
        """检查是否已停止"""
        return self._stop_flag
    
    def reset_stop_flag(self):
        """重置停止标志（在执行新计划前调用）"""
        self._stop_flag = False
        self._current_log = None
    
    def initialize_context(self, env_name: str = None):
        """
        初始化执行上下文（加载全局变量和环境变量）
        
        Args:
            env_name: 环境名称，如果为None则使用当前选中的环境
        """
        from managers.global_variable_manager import GlobalVariableManager
        from managers.environment_manager import EnvironmentManager
        
        # 加载全局变量
        global_var_manager = GlobalVariableManager()
        global_vars = global_var_manager.get_all_variables()
        self.context.set_global_vars(global_vars)
        
        # 加载环境变量
        if env_name:
            env_manager = EnvironmentManager()
            env = env_manager.get_environment(env_name)
            if env:
                self.context.set_env_vars(env.variables)
    
    def execute_plan_sequential(self, plan: ExecutionPlan) -> ExecutionLog:
        """
        串行执行计划
        
        Args:
            plan: 执行计划
            
        Returns:
            ExecutionLog: 执行日志
        """
        # 重置停止标志
        self.reset_stop_flag()
        
        # 创建执行日志
        log_id = str(uuid.uuid4())[:8]
        log = ExecutionLog(
            id=log_id,
            plan_id=plan.id,
            plan_name=plan.name,
            started_at=datetime.now(),
            status=ExecutionStatus.RUNNING,
            total_steps=len(plan.steps),
        )
        self._current_log = log
        
        # 初始化上下文
        self.context.clear()
        self.initialize_context()  # 加载全局变量和环境变量
        self.context.start_execution()
        
        # 按顺序执行步骤
        steps = sorted(plan.steps, key=lambda s: s.order_index)
        
        for i, step in enumerate(steps):
            # 检查是否停止
            if self.is_stopped():
                log.status = ExecutionStatus.STOPPED
                log.completed_at = datetime.now()
                self._send_progress(1.0, "执行已停止")
                return log
            
            try:
                # 更新当前步骤
                self.context.set_current_step(step.id, step.name)
                
                # 发送进度
                progress = i / len(steps)
                self._send_progress(progress, f"执行步骤 {i+1}/{len(steps)}: {step.name}")
                
                # 通知步骤开始执行
                if self.on_step_status:
                    try:
                        self.on_step_status(i + 1, step.name, 'running', None)
                    except Exception as ex:
                        print(f"步骤状态回调失败: {ex}")
                
                # 执行步骤
                result = self._execute_step(step)
                
                # 保存结果
                self.context.save_step_result(step.id, result)
                
                # 通知步骤完成/失败
                if self.on_step_status:
                    try:
                        status = 'completed' if result.get('success', False) else 'failed'
                        error = result.get('error') if not result.get('success', False) else None
                        # 传递结果数据
                        self.on_step_status(i + 1, step.name, status, error, result)
                    except Exception as ex:
                        print(f"步骤状态回调失败: {ex}")
                
                if not result.get('success', False):
                    log.failed_steps += 1
                    
                    # 如果步骤失败且不允许继续，则停止
                    if not result.get('continue_on_error', True):
                        log.status = ExecutionStatus.FAILED
                        log.error_message = result.get('error', '步骤执行失败')
                        break
                else:
                    log.completed_steps += 1
                
            except Exception as e:
                log.failed_steps += 1
                log.status = ExecutionStatus.FAILED
                log.error_message = f"步骤执行异常: {str(e)}"
                
                # 通知步骤失败
                if self.on_step_status:
                    try:
                        self.on_step_status(i + 1, step.name, 'failed', str(e))
                    except Exception as ex:
                        print(f"步骤状态回调失败: {ex}")
                
                break
        
        # 执行完成
        log.completed_at = datetime.now()
        if log.status == ExecutionStatus.RUNNING:
            log.status = ExecutionStatus.COMPLETED
        
        # 生成结果摘要
        log.result_summary = {
            'total': log.total_steps,
            'completed': log.completed_steps,
            'failed': log.failed_steps,
            'duration': log.duration,
        }
        
        # 发送完成进度
        if not self.is_stopped():
            self._send_progress(1.0, f"执行完成: 成功{log.completed_steps}, 失败{log.failed_steps}")
        
        return log
    
    def execute_plan_parallel(self, plan: ExecutionPlan, max_workers: int = 5) -> ExecutionLog:
        """
        并行执行计划
        
        Args:
            plan: 执行计划
            max_workers: 最大并发数，默认5
            
        Returns:
            ExecutionLog: 执行日志
        """
        # 创建执行日志
        log_id = str(uuid.uuid4())[:8]
        log = ExecutionLog(
            id=log_id,
            plan_id=plan.id,
            plan_name=plan.name,
            started_at=datetime.now(),
            status=ExecutionStatus.RUNNING,
            total_steps=len(plan.steps),
        )
        
        # 初始化上下文
        self.context.clear()
        self.initialize_context()
        self.context.start_execution()
        
        # 按顺序获取步骤
        steps = sorted(plan.steps, key=lambda s: s.order_index)
        
        # 用于存储每个步骤的结果
        step_results = {}
        completed_count = 0
        failed_count = 0
        total = len(steps)
        
        # 发送开始进度
        self._send_progress(0.0, f"开始并行执行（最大并发数: {max_workers}）")
        
        try:
            # 使用线程池并行执行
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                future_to_step = {
                    executor.submit(self._execute_step_with_context, step, idx): (step, idx)
                    for idx, step in enumerate(steps)
                }
                
                # 处理完成的任务
                for future in as_completed(future_to_step):
                    step, idx = future_to_step[future]
                    try:
                        result = future.result()
                        step_results[step.id] = result
                        
                        # 更新计数
                        if result.get('success', False):
                            completed_count += 1
                        else:
                            failed_count += 1
                        
                        # 更新进度
                        progress = (completed_count + failed_count) / total
                        self._send_progress(
                            progress,
                            f"进度: {completed_count + failed_count}/{total} (成功: {completed_count}, 失败: {failed_count})"
                        )
                        
                        # 保存结果到上下文（注意：并行时需要注意线程安全）
                        self.context.save_step_result(step.id, result)
                        
                    except Exception as e:
                        failed_count += 1
                        step_results[step.id] = {
                            'success': False,
                            'error': str(e),
                        }
                        self._send_progress(
                            (completed_count + failed_count) / total,
                            f"进度: {completed_count + failed_count}/{total} (成功: {completed_count}, 失败: {failed_count})"
                        )
            
            # 更新日志
            log.completed_steps = completed_count
            log.failed_steps = failed_count
            
            # 如果有失败的步骤，标记为部分失败
            if failed_count > 0:
                if completed_count == 0:
                    log.status = ExecutionStatus.FAILED
                else:
                    log.status = ExecutionStatus.COMPLETED  # 部分成功也视为完成
                    log.error_message = f"{failed_count}个步骤失败"
            else:
                log.status = ExecutionStatus.COMPLETED
            
        except Exception as e:
            log.status = ExecutionStatus.FAILED
            log.error_message = f"并行执行异常: {str(e)}"
        
        # 执行完成
        log.completed_at = datetime.now()
        
        # 生成结果摘要
        log.result_summary = {
            'total': log.total_steps,
            'completed': log.completed_steps,
            'failed': log.failed_steps,
            'duration': log.duration,
            'parallel': True,
            'max_workers': max_workers,
        }
        
        # 发送完成进度
        self._send_progress(1.0, f"执行完成: 成功{completed_count}, 失败{failed_count}")
        
        return log
    
    def _execute_step_with_context(self, step: ExecutionStep, index: int) -> dict:
        """
        执行单个步骤（带独立上下文，用于并行执行）
        
        Args:
            step: 执行步骤
            index: 步骤索引
            
        Returns:
            dict: 执行结果
        """
        # 为每个步骤创建独立的变量解析器（避免线程安全问题）
        local_resolver = VariableResolver()
        local_context = ExecutionContext()
        
        # 复制全局和环境变量
        local_context.set_global_vars(self.context.global_vars.copy())
        local_context.set_env_vars(self.context.env_vars.copy())
        
        # 设置当前步骤
        local_context.set_current_step(step.id, step.name)
        
        # 将上一步的结果复制到当前上下文（如果有的话）
        # 注意：并行执行时，步骤之间不应该有依赖关系
        # 如果有depends_on字段，需要特殊处理
        
        try:
            # 从请求列表管理器获取请求详情
            request = self.request_list_manager.get_request(step.request_id)
            
            if not request:
                return {
                    'success': False,
                    'error': f'未找到请求: {step.request_id}',
                    'status_code': None,
                    'data': None,
                    'headers': {},
                    'execution_time': 0,
                }
            
            # 解析URL中的变量（使用局部上下文）
            local_context_dict = local_context.get_context_dict()
            local_resolver.set_context(local_context_dict)
            
            url = local_resolver.resolve(request.url)
            
            # 解析Headers中的变量
            headers = {}
            for key, value in request.headers.items():
                headers[key] = local_resolver.resolve(str(value))
            
            # 解析Params中的变量
            params = {}
            for key, value in request.params.items():
                params[key] = local_resolver.resolve(str(value))
            
            # 解析Body中的变量
            body = request.body
            if body and isinstance(body, str):
                body = local_resolver.resolve(body)
            
            # 构建 HttpRequest 对象
            from models.models import HttpRequest, HttpMethod
            
            try:
                method_enum = HttpMethod(request.method.upper())
            except ValueError:
                method_enum = HttpMethod.GET
            
            http_request = HttpRequest(
                method=method_enum,
                url=url,
                headers=headers,
                params=params,
                body=body if body else "",
                body_type=request.body_type if hasattr(request, 'body_type') else 'none',
            )
            
            # 发送HTTP请求
            start_time = time.time()
            response = self.http_service.send_request(http_request, verify_ssl=True)
            execution_time = (time.time() - start_time) * 1000
            
            # 构建结果
            result = {
                'success': response.status_code < 400 if response.status_code else False,
                'status_code': response.status_code,
                'data': response.body,
                'headers': dict(response.headers) if response.headers else {},
                'execution_time': execution_time,
                'request': {
                    'method': request.method,
                    'url': url,
                    'headers': headers,
                    'params': params,
                },
            }
            
            # 如果有自定义方法，执行方法
            if step.custom_method:
                script_context = local_context.get_context_dict()
                script_context['response'] = result
                
                script_result = self.script_sandbox.execute(step.custom_method, script_context)
                
                if not script_result['success']:
                    result['success'] = False
                    result['error'] = script_result['error']
                    result['script_error'] = True
                    return result
                
                # 将脚本中设置的变量保存到局部上下文
                for key, value in script_result.get('variables', {}).items():
                    local_context.set_variable(key, value)
                
                result['script_output'] = script_result.get('result')
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': None,
                'data': None,
                'headers': {},
                'execution_time': 0,
            }
    
    def _execute_step(self, step: ExecutionStep) -> dict:
        """
        执行单个步骤
        
        Args:
            step: 执行步骤
            
        Returns:
            dict: 执行结果
        """
        try:
            # 从请求列表管理器获取请求详情
            request = self.request_list_manager.get_request(step.request_id)
            
            if not request:
                return {
                    'success': False,
                    'error': f'未找到请求: {step.request_id}',
                    'status_code': None,
                    'data': None,
                    'headers': {},
                    'execution_time': 0,
                }
            
            # 解析URL中的变量
            url = self.variable_resolver.resolve(request.url)
            
            # 解析Headers中的变量
            headers = {}
            for key, value in request.headers.items():
                headers[key] = self.variable_resolver.resolve(str(value))
            
            # 解析Params中的变量
            params = {}
            for key, value in request.params.items():
                params[key] = self.variable_resolver.resolve(str(value))
            
            # 解析Body中的变量
            body = request.body
            if body and isinstance(body, str):
                body = self.variable_resolver.resolve(body)
            
            # 构建 HttpRequest 对象
            from models.models import HttpRequest, HttpMethod
            
            # 将字符串方法转换为 HttpMethod 枚举
            try:
                method_enum = HttpMethod(request.method.upper())
            except ValueError:
                method_enum = HttpMethod.GET
            
            http_request = HttpRequest(
                method=method_enum,
                url=url,
                headers=headers,
                params=params,
                body=body if body else "",
                body_type=request.body_type if hasattr(request, 'body_type') else 'none',
            )
            
            # 发送HTTP请求
            start_time = time.time()
            response = self.http_service.send_request(http_request, verify_ssl=True)
            execution_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            # 构建结果
            result = {
                'success': response.status_code < 400 if response.status_code else False,
                'status_code': response.status_code,
                'data': response.body,
                'headers': dict(response.headers) if response.headers else {},
                'execution_time': execution_time,
                'request': {
                    'method': request.method,
                    'url': url,
                    'headers': headers,
                    'params': params,
                },
            }
            
            # 如果有自定义方法，执行方法
            if step.custom_method:
                script_result = self._execute_script(step.custom_method, result)
                
                if not script_result['success']:
                    result['success'] = False
                    result['error'] = script_result['error']
                    result['script_error'] = True
                    return result
                
                # 将脚本中设置的变量保存到上下文
                for key, value in script_result.get('variables', {}).items():
                    self.context.set_variable(key, value)
                
                result['script_output'] = script_result.get('result')
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': None,
                'data': None,
                'headers': {},
                'execution_time': 0,
            }
    
    def _execute_script(self, script: str, response: dict) -> dict:
        """
        执行自定义脚本
        
        Args:
            script: Python脚本
            response: HTTP响应数据
            
        Returns:
            dict: 脚本执行结果
        """
        # 准备上下文
        context = self.context.get_context_dict()
        context['response'] = response
        
        # 执行脚本
        result = self.script_sandbox.execute(script, context)
        
        return result
    
    def _send_progress(self, progress: float, message: str):
        """发送进度更新"""
        if self.on_progress:
            try:
                self.on_progress(progress, message)
            except Exception as e:
                print(f"进度回调错误: {e}")
