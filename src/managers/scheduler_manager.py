"""定时调度管理器 - 管理执行计划的定时任务"""

import json
from datetime import datetime
from typing import Optional, Callable
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

from models.execution_plan import ExecutionPlan, ScheduleConfig, ScheduleType
from managers.execution_plan_manager import ExecutionPlanManager


class SchedulerManager:
    """
    定时调度管理器
    
    使用 APScheduler 管理执行计划的定时任务
    """
    
    _instance = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化调度管理器"""
        if self._initialized:
            return
        
        self._initialized = True
        self.scheduler = BackgroundScheduler()
        self.execution_plan_manager = ExecutionPlanManager()
        self._on_execution_complete: Optional[Callable] = None
        
        # 启动调度器
        self.scheduler.start()
        
        # 恢复之前的定时任务
        self._restore_schedules()
    
    def _restore_schedules(self):
        """恢复数据库中已启用的定时任务"""
        try:
            # 获取所有计划
            plans = self.execution_plan_manager.get_all_plans()
            
            for plan in plans:
                if plan.schedule and plan.schedule.enabled:
                    # 重新添加到调度器
                    self.add_schedule(plan.id, plan.schedule)
                    print(f"恢复定时任务: {plan.name}")
        except Exception as e:
            print(f"恢复定时任务失败: {e}")
    
    def set_execution_complete_callback(self, callback: Callable):
        """
        设置执行完成回调
        
        Args:
            callback: 回调函数，接收 (plan_id, log) 参数
        """
        self._on_execution_complete = callback
    
    def add_schedule(self, plan_id: str, schedule_config: ScheduleConfig) -> bool:
        """
        添加定时任务
        
        Args:
            plan_id: 计划ID
            schedule_config: 调度配置
            
        Returns:
            bool: 是否添加成功
        """
        try:
            # 先移除已存在的任务
            self.remove_schedule(plan_id)
            
            # 根据调度类型创建触发器
            trigger = self._create_trigger(schedule_config)
            if not trigger:
                return False
            
            # 添加任务
            self.scheduler.add_job(
                func=self._execute_scheduled_plan,
                trigger=trigger,
                args=[plan_id],
                id=f"plan_{plan_id}",
                name=f"执行计划: {plan_id}",
                replace_existing=True,
            )
            
            # 更新数据库中的调度配置
            plan = self.execution_plan_manager.get_plan(plan_id)
            if plan:
                self.execution_plan_manager.update_plan(
                    plan_id=plan_id,
                    schedule=schedule_config
                )
            
            return True
            
        except Exception as e:
            print(f"添加定时任务失败: {e}")
            return False
    
    def remove_schedule(self, plan_id: str) -> bool:
        """
        移除定时任务
        
        Args:
            plan_id: 计划ID
            
        Returns:
            bool: 是否移除成功
        """
        try:
            job_id = f"plan_{plan_id}"
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                return True
            return False
        except Exception as e:
            print(f"移除定时任务失败: {e}")
            return False
    
    def update_schedule(self, plan_id: str, schedule_config: ScheduleConfig) -> bool:
        """
        更新定时任务
        
        Args:
            plan_id: 计划ID
            schedule_config: 新的调度配置
            
        Returns:
            bool: 是否更新成功
        """
        # 先移除旧任务
        self.remove_schedule(plan_id)
        
        # 如果新配置未启用，则不添加
        if not schedule_config.enabled:
            return True
        
        # 添加新任务
        return self.add_schedule(plan_id, schedule_config)
    
    def get_scheduled_plans(self) -> list:
        """
        获取所有已调度的计划
        
        Returns:
            list: 已调度的计划列表
        """
        jobs = self.scheduler.get_jobs()
        scheduled_plans = []
        
        for job in jobs:
            if job.id.startswith("plan_"):
                plan_id = job.id.replace("plan_", "")
                plan = self.execution_plan_manager.get_plan(plan_id)
                if plan:
                    scheduled_plans.append({
                        'plan': plan,
                        'next_run_time': job.next_run_time,
                    })
        
        return scheduled_plans
    
    def pause_schedule(self, plan_id: str) -> bool:
        """
        暂停定时任务
        
        Args:
            plan_id: 计划ID
            
        Returns:
            bool: 是否暂停成功
        """
        try:
            job_id = f"plan_{plan_id}"
            job = self.scheduler.get_job(job_id)
            if job:
                job.pause()
                return True
            return False
        except Exception as e:
            print(f"暂停定时任务失败: {e}")
            return False
    
    def resume_schedule(self, plan_id: str) -> bool:
        """
        恢复定时任务
        
        Args:
            plan_id: 计划ID
            
        Returns:
            bool: 是否恢复成功
        """
        try:
            job_id = f"plan_{plan_id}"
            job = self.scheduler.get_job(job_id)
            if job:
                job.resume()
                return True
            return False
        except Exception as e:
            print(f"恢复定时任务失败: {e}")
            return False
    
    def _create_trigger(self, schedule_config: ScheduleConfig):
        """
        根据调度配置创建触发器
        
        Args:
            schedule_config: 调度配置
            
        Returns:
            Trigger: APScheduler 触发器
        """
        if not schedule_config.enabled:
            return None
        
        if schedule_config.schedule_type == ScheduleType.ONCE:
            # 一次性执行
            if schedule_config.start_time:
                return DateTrigger(run_date=schedule_config.start_time)
            return None
            
        elif schedule_config.schedule_type == ScheduleType.INTERVAL:
            # 间隔执行
            if schedule_config.interval_seconds:
                return IntervalTrigger(seconds=schedule_config.interval_seconds)
            return None
            
        elif schedule_config.schedule_type == ScheduleType.CRON:
            # Cron 表达式
            if schedule_config.cron_expression:
                try:
                    return CronTrigger.from_crontab(schedule_config.cron_expression)
                except Exception as e:
                    print(f"Cron 表达式解析失败: {e}")
                    return None
            return None
        
        return None
    
    def _execute_scheduled_plan(self, plan_id: str):
        """
        执行定时计划
        
        Args:
            plan_id: 计划ID
        """
        try:
            print(f"开始执行定时计划: {plan_id}")
            
            # 获取计划
            plan = self.execution_plan_manager.get_plan(plan_id)
            if not plan:
                print(f"计划不存在: {plan_id}")
                return
            
            # 导入执行引擎
            from services.execution_engine import ExecutionEngine
            
            # 创建执行引擎并执行
            engine = ExecutionEngine()
            log = engine.execute_plan_sequential(plan)
            
            # 保存执行日志
            self.execution_plan_manager.save_execution_log(log)
            
            # 调用完成回调
            if self._on_execution_complete:
                self._on_execution_complete(plan_id, log)
            
            print(f"定时计划执行完成: {plan_id}, 状态: {log.status.value}")
            
        except Exception as e:
            print(f"定时计划执行失败: {plan_id}, 错误: {e}")
            import traceback
            traceback.print_exc()
    
    def shutdown(self):
        """关闭调度器"""
        self.scheduler.shutdown()
    
    def __del__(self):
        """析构时关闭调度器"""
        try:
            self.shutdown()
        except:
            pass
