"""执行计划数据模型"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum


class ExecutionMode(Enum):
    """执行模式"""
    SEQUENTIAL = "sequential"  # 串行执行
    PARALLEL = "parallel"      # 并行执行


class ScheduleType(Enum):
    """调度类型"""
    ONCE = "once"              # 一次性
    INTERVAL = "interval"      # 间隔执行
    CRON = "cron"              # Cron表达式


class ExecutionStatus(Enum):
    """执行状态"""
    RUNNING = "running"        # 执行中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失败
    STOPPED = "stopped"        # 已停止
    PENDING = "pending"        # 等待中


@dataclass
class ScheduleConfig:
    """定时配置"""
    enabled: bool = False
    schedule_type: ScheduleType = ScheduleType.ONCE
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'enabled': self.enabled,
            'schedule_type': self.schedule_type.value,
            'cron_expression': self.cron_expression,
            'interval_seconds': self.interval_seconds,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ScheduleConfig':
        """从字典创建"""
        return cls(
            enabled=data.get('enabled', False),
            schedule_type=ScheduleType(data.get('schedule_type', 'once')),
            cron_expression=data.get('cron_expression'),
            interval_seconds=data.get('interval_seconds'),
            start_time=datetime.fromisoformat(data['start_time']) if data.get('start_time') else None,
            end_time=datetime.fromisoformat(data['end_time']) if data.get('end_time') else None,
        )


@dataclass
class ExecutionStep:
    """执行步骤"""
    id: str
    plan_id: str
    request_id: str
    name: str
    order_index: int
    custom_method: Optional[str] = None  # 自定义处理方法代码
    params_mapping: Optional[str] = None  # 参数映射 JSON字符串
    variables: dict = field(default_factory=dict)
    timeout: int = 30
    retry_count: int = 3
    depends_on: list = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'request_id': self.request_id,
            'name': self.name,
            'order_index': self.order_index,
            'custom_method': self.custom_method,
            'params_mapping': self.params_mapping,
            'variables': self.variables,
            'timeout': self.timeout,
            'retry_count': self.retry_count,
            'depends_on': self.depends_on,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ExecutionStep':
        """从字典创建"""
        return cls(
            id=data['id'],
            plan_id=data['plan_id'],
            request_id=data['request_id'],
            name=data['name'],
            order_index=data['order_index'],
            custom_method=data.get('custom_method'),
            params_mapping=data.get('params_mapping'),
            variables=data.get('variables', {}),
            timeout=data.get('timeout', 30),
            retry_count=data.get('retry_count', 3),
            depends_on=data.get('depends_on', []),
        )


@dataclass
class ExecutionPlan:
    """执行计划"""
    id: str
    name: str
    description: str = ""
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    steps: list[ExecutionStep] = field(default_factory=list)
    schedule: Optional[ScheduleConfig] = None
    is_active: bool = True
    last_execution_status: Optional[str] = None  # 最近一次执行状态: running, completed, failed
    last_execution_time: Optional[datetime] = None  # 最近一次执行时间
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_step(self, step: ExecutionStep):
        """添加步骤"""
        self.steps.append(step)
        self.steps.sort(key=lambda s: s.order_index)
        self.updated_at = datetime.now()
    
    def remove_step(self, step_id: str):
        """移除步骤"""
        self.steps = [s for s in self.steps if s.id != step_id]
        # 重新排序
        for i, step in enumerate(self.steps):
            step.order_index = i
        self.updated_at = datetime.now()
    
    def get_step_by_id(self, step_id: str) -> Optional[ExecutionStep]:
        """根据ID获取步骤"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'execution_mode': self.execution_mode.value,
            'steps': [step.to_dict() for step in self.steps],
            'schedule': self.schedule.to_dict() if self.schedule else None,
            'is_active': self.is_active,
            'last_execution_status': self.last_execution_status,
            'last_execution_time': self.last_execution_time.isoformat() if self.last_execution_time else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ExecutionPlan':
        """从字典创建"""
        steps = [ExecutionStep.from_dict(s) for s in data.get('steps', [])]
        schedule_data = data.get('schedule')
        schedule = ScheduleConfig.from_dict(schedule_data) if schedule_data else None
        
        return cls(
            id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            execution_mode=ExecutionMode(data.get('execution_mode', 'sequential')),
            steps=steps,
            schedule=schedule,
            is_active=data.get('is_active', True),
            last_execution_status=data.get('last_execution_status'),
            last_execution_time=datetime.fromisoformat(data['last_execution_time']) if data.get('last_execution_time') else None,
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now(),
        )


@dataclass
class ExecutionLog:
    """执行日志"""
    id: str
    plan_id: str
    plan_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    total_steps: int = 0
    completed_steps: int = 0
    failed_steps: int = 0
    result_summary: dict = field(default_factory=dict)
    error_message: Optional[str] = None
    
    @property
    def progress(self) -> float:
        """执行进度（0-100）"""
        if self.total_steps == 0:
            return 0.0
        return (self.completed_steps / self.total_steps) * 100
    
    @property
    def duration(self) -> Optional[float]:
        """执行时长（秒）"""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'plan_name': self.plan_name,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'status': self.status.value,
            'total_steps': self.total_steps,
            'completed_steps': self.completed_steps,
            'failed_steps': self.failed_steps,
            'result_summary': self.result_summary,
            'error_message': self.error_message,
            'progress': self.progress,
            'duration': self.duration,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ExecutionLog':
        """从字典创建"""
        return cls(
            id=data['id'],
            plan_id=data['plan_id'],
            plan_name=data['plan_name'],
            started_at=datetime.fromisoformat(data['started_at']),
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            status=ExecutionStatus(data.get('status', 'pending')),
            total_steps=data.get('total_steps', 0),
            completed_steps=data.get('completed_steps', 0),
            failed_steps=data.get('failed_steps', 0),
            result_summary=data.get('result_summary', {}),
            error_message=data.get('error_message'),
        )
