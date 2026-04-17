"""执行计划管理器 - 管理执行计划的CRUD操作"""

import json
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, String, Integer, Boolean, Text, DateTime, ForeignKey, inspect, text
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

from models.database import DatabaseManager
from models.execution_plan import (
    ExecutionPlan,
    ExecutionStep,
    ExecutionLog,
    ExecutionMode,
    ScheduleConfig,
    ExecutionStatus
)

Base = declarative_base()


class ExecutionPlanModel(Base):
    """执行计划数据库模型"""
    __tablename__ = 'execution_plans'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, default='')
    execution_mode = Column(String, nullable=False, default='sequential')
    schedule_config = Column(Text, nullable=True)  # JSON格式
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    steps = relationship("ExecutionStepModel", back_populates="plan", cascade="all, delete-orphan")


class ExecutionStepModel(Base):
    """执行步骤数据库模型"""
    __tablename__ = 'execution_steps'
    
    id = Column(String, primary_key=True)
    plan_id = Column(String, ForeignKey('execution_plans.id', ondelete='CASCADE'), nullable=False)
    request_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    order_index = Column(Integer, nullable=False)
    custom_method = Column(Text, nullable=True)  # 自定义处理方法代码
    params_mapping = Column(Text, nullable=True)  # 参数映射 JSON字符串
    variables = Column(Text, nullable=True)  # JSON格式
    timeout = Column(Integer, default=30)
    retry_count = Column(Integer, default=3)
    depends_on = Column(Text, nullable=True)  # JSON数组
    
    # 关系
    plan = relationship("ExecutionPlanModel", back_populates="steps")


class ExecutionLogModel(Base):
    """执行日志数据库模型"""
    __tablename__ = 'execution_logs'
    
    id = Column(String, primary_key=True)
    plan_id = Column(String, ForeignKey('execution_plans.id'), nullable=False)
    plan_name = Column(String, nullable=False)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default='pending')
    total_steps = Column(Integer, default=0)
    completed_steps = Column(Integer, default=0)
    failed_steps = Column(Integer, default=0)
    result_summary = Column(Text, nullable=True)  # JSON格式
    error_message = Column(Text, nullable=True)


class ExecutionPlanManager:
    """执行计划管理器"""
    
    def __init__(self, db_path: str = None):
        """
        初始化执行计划管理器
        
        Args:
            db_path: 数据库路径，如果为None则使用默认路径
        """
        if db_path is None:
            import os
            db_path = os.path.join(os.path.dirname(__file__), '..', 'mypostman.db')
        
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        # 执行数据库迁移（必须在 Session 创建之后）
        self._migrate_database()
    
    def _migrate_database(self):
        """数据库迁移：添加新字段，删除旧字段"""
        session = self.Session()
        try:
            # 检查是否需要迁移
            columns = [col['name'] for col in inspect(self.engine).get_columns('execution_steps')]
            
            needs_migration = False
            if 'custom_method' not in columns or 'params_mapping' not in columns or 'script' in columns:
                needs_migration = True
            
            if needs_migration:
                print("检测到数据库需要迁移...")
                
                # 1. 创建临时表
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS execution_steps_new (
                        id VARCHAR PRIMARY KEY,
                        plan_id VARCHAR NOT NULL,
                        request_id VARCHAR NOT NULL,
                        name VARCHAR NOT NULL,
                        order_index INTEGER NOT NULL,
                        custom_method TEXT,
                        params_mapping TEXT,
                        variables TEXT,
                        timeout INTEGER DEFAULT 30,
                        retry_count INTEGER DEFAULT 3,
                        depends_on TEXT,
                        FOREIGN KEY (plan_id) REFERENCES execution_plans(id) ON DELETE CASCADE
                    )
                """))
                
                # 2. 复制数据（将 script 转换为 custom_method）
                session.execute(text("""
                    INSERT INTO execution_steps_new 
                    SELECT id, plan_id, request_id, name, order_index, 
                           script as custom_method, 
                           NULL as params_mapping,
                           variables, timeout, retry_count, depends_on
                    FROM execution_steps
                """))
                
                # 3. 删除旧表
                session.execute(text("DROP TABLE execution_steps"))
                
                # 4. 重命名新表
                session.execute(text("ALTER TABLE execution_steps_new RENAME TO execution_steps"))
                
                session.commit()
                print("数据库迁移完成！")
        except Exception as e:
            session.rollback()
            print(f"数据库迁移失败: {e}")
            raise e
        finally:
            session.close()
    
    def _model_to_plan(self, model: ExecutionPlanModel) -> ExecutionPlan:
        """将数据库模型转换为ExecutionPlan对象"""
        steps = [self._step_model_to_step(s) for s in model.steps]
        steps.sort(key=lambda s: s.order_index)
        
        schedule_data = json.loads(model.schedule_config) if model.schedule_config else None
        schedule = ScheduleConfig.from_dict(schedule_data) if schedule_data else None
        
        return ExecutionPlan(
            id=model.id,
            name=model.name,
            description=model.description or '',
            execution_mode=ExecutionMode(model.execution_mode),
            steps=steps,
            schedule=schedule,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
    
    def _step_model_to_step(self, model: ExecutionStepModel) -> ExecutionStep:
        """将步骤数据库模型转换为ExecutionStep对象"""
        variables = json.loads(model.variables) if model.variables else {}
        depends_on = json.loads(model.depends_on) if model.depends_on else []
        
        return ExecutionStep(
            id=model.id,
            plan_id=model.plan_id,
            request_id=model.request_id,
            name=model.name,
            order_index=model.order_index,
            custom_method=model.custom_method,
            params_mapping=model.params_mapping,
            variables=variables,
            timeout=model.timeout,
            retry_count=model.retry_count,
            depends_on=depends_on,
        )
    
    def create_plan(self, name: str, description: str = "", 
                   execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL,
                   schedule: Optional[ScheduleConfig] = None) -> ExecutionPlan:
        """
        创建执行计划
        
        Args:
            name: 计划名称
            description: 计划描述
            execution_mode: 执行模式
            schedule: 定时配置
            
        Returns:
            ExecutionPlan: 创建的执行计划
        """
        plan_id = str(uuid.uuid4())[:8]
        now = datetime.now()
        
        plan_model = ExecutionPlanModel(
            id=plan_id,
            name=name,
            description=description,
            execution_mode=execution_mode.value,
            schedule_config=json.dumps(schedule.to_dict()) if schedule else None,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        
        session = self.Session()
        try:
            session.add(plan_model)
            session.commit()
            
            # 返回转换后的对象
            return self._model_to_plan(plan_model)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def update_plan(self, plan_id: str, name: str = None, description: str = None,
                   execution_mode: ExecutionMode = None, schedule: Optional[ScheduleConfig] = None,
                   is_active: bool = None) -> Optional[ExecutionPlan]:
        """
        更新执行计划
        
        Args:
            plan_id: 计划ID
            name: 新名称
            description: 新描述
            execution_mode: 新执行模式
            schedule: 新定时配置
            is_active: 是否激活
            
        Returns:
            Optional[ExecutionPlan]: 更新后的计划，如果不存在则返回None
        """
        session = self.Session()
        try:
            plan_model = session.query(ExecutionPlanModel).filter_by(id=plan_id).first()
            if not plan_model:
                return None
            
            if name is not None:
                plan_model.name = name
            if description is not None:
                plan_model.description = description
            if execution_mode is not None:
                plan_model.execution_mode = execution_mode.value
            if schedule is not None:
                plan_model.schedule_config = json.dumps(schedule.to_dict())
            if is_active is not None:
                plan_model.is_active = is_active
            
            plan_model.updated_at = datetime.now()
            session.commit()
            
            return self._model_to_plan(plan_model)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def delete_plan(self, plan_id: str) -> bool:
        """
        删除执行计划
        
        Args:
            plan_id: 计划ID
            
        Returns:
            bool: 是否删除成功
        """
        session = self.Session()
        try:
            plan_model = session.query(ExecutionPlanModel).filter_by(id=plan_id).first()
            if not plan_model:
                return False
            
            session.delete(plan_model)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_plan(self, plan_id: str) -> Optional[ExecutionPlan]:
        """
        获取执行计划详情
        
        Args:
            plan_id: 计划ID
            
        Returns:
            Optional[ExecutionPlan]: 执行计划，如果不存在则返回None
        """
        session = self.Session()
        try:
            plan_model = session.query(ExecutionPlanModel).filter_by(id=plan_id).first()
            if not plan_model:
                return None
            
            return self._model_to_plan(plan_model)
        finally:
            session.close()
    
    def get_all_plans(self, active_only: bool = False) -> list[ExecutionPlan]:
        """
        获取所有执行计划
        
        Args:
            active_only: 是否只获取激活的计划
            
        Returns:
            list[ExecutionPlan]: 执行计划列表
        """
        session = self.Session()
        try:
            query = session.query(ExecutionPlanModel)
            if active_only:
                query = query.filter_by(is_active=True)
            
            query = query.order_by(ExecutionPlanModel.updated_at.desc())
            plan_models = query.all()
            
            return [self._model_to_plan(m) for m in plan_models]
        finally:
            session.close()
    
    def add_step(self, plan_id: str, request_id: str, name: str,
                order_index: int = None, custom_method: str = None, params_mapping: str = None,
                variables: dict = None, timeout: int = 30,
                retry_count: int = 3, depends_on: list = None) -> Optional[ExecutionStep]:
        """
        添加执行步骤
        
        Args:
            plan_id: 计划ID
            request_id: 请求ID
            name: 步骤名称
            order_index: 排序索引（如果为None则自动追加到最后）
            custom_method: 自定义处理方法代码
            params_mapping: 参数映射 JSON字符串
            variables: 变量映射
            timeout: 超时时间（秒）
            retry_count: 重试次数
            depends_on: 依赖的步骤ID列表
            
        Returns:
            Optional[ExecutionStep]: 添加的步骤，如果计划不存在则返回None
        """
        session = self.Session()
        try:
            plan_model = session.query(ExecutionPlanModel).filter_by(id=plan_id).first()
            if not plan_model:
                return None
            
            # 如果未指定order_index，则追加到最后
            if order_index is None:
                max_order = session.query(ExecutionStepModel).filter_by(plan_id=plan_id).count()
                order_index = max_order
            
            step_id = str(uuid.uuid4())[:8]
            step_model = ExecutionStepModel(
                id=step_id,
                plan_id=plan_id,
                request_id=request_id,
                name=name,
                order_index=order_index,
                custom_method=custom_method,
                params_mapping=params_mapping,
                variables=json.dumps(variables) if variables else None,
                timeout=timeout,
                retry_count=retry_count,
                depends_on=json.dumps(depends_on) if depends_on else None,
            )
            
            session.add(step_model)
            
            # 更新计划的更新时间
            plan_model.updated_at = datetime.now()
            
            session.commit()
            
            return self._step_model_to_step(step_model)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def remove_step(self, step_id: str) -> bool:
        """
        移除执行步骤
        
        Args:
            step_id: 步骤ID
            
        Returns:
            bool: 是否移除成功
        """
        session = self.Session()
        try:
            step_model = session.query(ExecutionStepModel).filter_by(id=step_id).first()
            if not step_model:
                return False
            
            plan_id = step_model.plan_id
            session.delete(step_model)
            
            # 重新排序剩余步骤
            remaining_steps = session.query(ExecutionStepModel).filter_by(plan_id=plan_id).order_by(ExecutionStepModel.order_index).all()
            for i, step in enumerate(remaining_steps):
                step.order_index = i
            
            # 更新计划的更新时间
            plan_model = session.query(ExecutionPlanModel).filter_by(id=plan_id).first()
            if plan_model:
                plan_model.updated_at = datetime.now()
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def update_step(self, step_id: str, request_id: str = None, name: str = None,
                   custom_method: str = None, params_mapping: str = None,
                   variables: dict = None, timeout: int = None,
                   retry_count: int = None, depends_on: list = None) -> Optional[ExecutionStep]:
        """
        更新执行步骤
        
        Args:
            step_id: 步骤ID
            request_id: 请求ID
            name: 步骤名称
            custom_method: 自定义处理方法代码
            params_mapping: 参数映射 JSON字符串
            variables: 变量映射
            timeout: 超时时间（秒）
            retry_count: 重试次数
            depends_on: 依赖的步骤ID列表
            
        Returns:
            Optional[ExecutionStep]: 更新后的步骤，如果不存在则返回None
        """
        session = self.Session()
        try:
            step_model = session.query(ExecutionStepModel).filter_by(id=step_id).first()
            if not step_model:
                return None
            
            if request_id is not None:
                step_model.request_id = request_id
            if name is not None:
                step_model.name = name
            if custom_method is not None:
                step_model.custom_method = custom_method
            if params_mapping is not None:
                step_model.params_mapping = params_mapping
            if variables is not None:
                step_model.variables = json.dumps(variables)
            if timeout is not None:
                step_model.timeout = timeout
            if retry_count is not None:
                step_model.retry_count = retry_count
            if depends_on is not None:
                step_model.depends_on = json.dumps(depends_on)
            
            # 更新计划的更新时间
            plan_model = session.query(ExecutionPlanModel).filter_by(id=step_model.plan_id).first()
            if plan_model:
                plan_model.updated_at = datetime.now()
            
            session.commit()
            return self._step_model_to_step(step_model)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def delete_step(self, step_id: str) -> bool:
        """
        删除执行步骤（remove_step的别名）
        
        Args:
            step_id: 步骤ID
            
        Returns:
            bool: 是否删除成功
        """
        return self.remove_step(step_id)
    
    def reorder_steps(self, plan_id: str, step_ids: list[str]) -> bool:
        """
        重新排序步骤
        
        Args:
            plan_id: 计划ID
            step_ids: 按新顺序排列的步骤ID列表
            
        Returns:
            bool: 是否重排序成功
        """
        session = self.Session()
        try:
            for i, step_id in enumerate(step_ids):
                step_model = session.query(ExecutionStepModel).filter_by(id=step_id, plan_id=plan_id).first()
                if step_model:
                    step_model.order_index = i
            
            # 更新计划的更新时间
            plan_model = session.query(ExecutionPlanModel).filter_by(id=plan_id).first()
            if plan_model:
                plan_model.updated_at = datetime.now()
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def move_step(self, step_id: str, direction: str) -> bool:
        """
        移动步骤（上移或下移）
        
        Args:
            step_id: 步骤ID
            direction: 方向 ('up' 或 'down')
            
        Returns:
            bool: 是否移动成功
        """
        session = self.Session()
        try:
            # 获取当前步骤
            step_model = session.query(ExecutionStepModel).filter_by(id=step_id).first()
            if not step_model:
                return False
            
            plan_id = step_model.plan_id
            current_order = step_model.order_index
            
            # 查找相邻步骤
            if direction == 'up':
                # 查找上一个步骤
                prev_step = session.query(ExecutionStepModel).filter(
                    ExecutionStepModel.plan_id == plan_id,
                    ExecutionStepModel.order_index == current_order - 1
                ).first()
                
                if prev_step:
                    # 交换 order_index
                    prev_step.order_index = current_order
                    step_model.order_index = current_order - 1
                else:
                    return False  # 已经是第一个，不能上移
                    
            elif direction == 'down':
                # 查找下一个步骤
                next_step = session.query(ExecutionStepModel).filter(
                    ExecutionStepModel.plan_id == plan_id,
                    ExecutionStepModel.order_index == current_order + 1
                ).first()
                
                if next_step:
                    # 交换 order_index
                    next_step.order_index = current_order
                    step_model.order_index = current_order + 1
                else:
                    return False  # 已经是最后一个，不能下移
            else:
                return False  # 无效的方向
            
            # 更新计划的更新时间
            plan_model = session.query(ExecutionPlanModel).filter_by(id=plan_id).first()
            if plan_model:
                plan_model.updated_at = datetime.now()
            
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def move_step(self, step_id: str, direction: str) -> bool:
        """
        移动步骤（上移或下移）
        
        Args:
            step_id: 步骤ID
            direction: 方向 ('up' 或 'down')
            
        Returns:
            bool: 是否移动成功
        """
        session = self.Session()
        try:
            # 获取当前步骤
            step_model = session.query(ExecutionStepModel).filter_by(id=step_id).first()
            if not step_model:
                return False
            
            plan_id = step_model.plan_id
            current_order = step_model.order_index
            
            # 查找相邻步骤
            if direction == 'up':
                # 查找上一个步骤
                prev_step = session.query(ExecutionStepModel).filter(
                    ExecutionStepModel.plan_id == plan_id,
                    ExecutionStepModel.order_index == current_order - 1
                ).first()
                
                if prev_step:
                    # 交换 order_index
                    prev_step.order_index = current_order
                    step_model.order_index = current_order - 1
                else:
                    return False  # 已经是第一个，不能上移
                    
            elif direction == 'down':
                # 查找下一个步骤
                next_step = session.query(ExecutionStepModel).filter(
                    ExecutionStepModel.plan_id == plan_id,
                    ExecutionStepModel.order_index == current_order + 1
                ).first()
                
                if next_step:
                    # 交换 order_index
                    next_step.order_index = current_order
                    step_model.order_index = current_order + 1
                else:
                    return False  # 已经是最后一个，不能下移
            else:
                return False  # 无效的方向
            
            # 更新计划的更新时间
            plan_model = session.query(ExecutionPlanModel).filter_by(id=plan_id).first()
            if plan_model:
                plan_model.updated_at = datetime.now()
            
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def save_execution_log(self, log: ExecutionLog) -> str:
        """
        保存执行日志
        
        Args:
            log: 执行日志对象
            
        Returns:
            str: 日志ID
        """
        session = self.Session()
        try:
            log_model = ExecutionLogModel(
                id=log.id,
                plan_id=log.plan_id,
                plan_name=log.plan_name,
                started_at=log.started_at,
                completed_at=log.completed_at,
                status=log.status.value,
                total_steps=log.total_steps,
                completed_steps=log.completed_steps,
                failed_steps=log.failed_steps,
                result_summary=json.dumps(log.result_summary) if log.result_summary else None,
                error_message=log.error_message,
            )
            
            session.add(log_model)
            session.commit()
            
            return log.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def update_execution_log(self, log_id: str, **kwargs) -> Optional[ExecutionLog]:
        """
        更新执行日志
        
        Args:
            log_id: 日志ID
            **kwargs: 要更新的字段
            
        Returns:
            Optional[ExecutionLog]: 更新后的日志
        """
        session = self.Session()
        try:
            log_model = session.query(ExecutionLogModel).filter_by(id=log_id).first()
            if not log_model:
                return None
            
            if 'status' in kwargs:
                log_model.status = kwargs['status'].value
            if 'completed_at' in kwargs:
                log_model.completed_at = kwargs['completed_at']
            if 'completed_steps' in kwargs:
                log_model.completed_steps = kwargs['completed_steps']
            if 'failed_steps' in kwargs:
                log_model.failed_steps = kwargs['failed_steps']
            if 'result_summary' in kwargs:
                log_model.result_summary = json.dumps(kwargs['result_summary'])
            if 'error_message' in kwargs:
                log_model.error_message = kwargs['error_message']
            
            session.commit()
            
            # 重新查询以获取最新数据
            log_model = session.query(ExecutionLogModel).filter_by(id=log_id).first()
            return self._log_model_to_log(log_model)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_execution_logs(self, plan_id: str = None, limit: int = 50) -> list[ExecutionLog]:
        """
        获取执行日志
        
        Args:
            plan_id: 计划ID（可选，如果不提供则获取所有日志）
            limit: 返回数量限制
            
        Returns:
            list[ExecutionLog]: 执行日志列表
        """
        session = self.Session()
        try:
            query = session.query(ExecutionLogModel)
            if plan_id:
                query = query.filter_by(plan_id=plan_id)
            
            query = query.order_by(ExecutionLogModel.started_at.desc()).limit(limit)
            log_models = query.all()
            
            return [self._log_model_to_log(m) for m in log_models]
        finally:
            session.close()
    
    def _log_model_to_log(self, model: ExecutionLogModel) -> ExecutionLog:
        """将日志数据库模型转换为ExecutionLog对象"""
        result_summary = json.loads(model.result_summary) if model.result_summary else {}
        
        return ExecutionLog(
            id=model.id,
            plan_id=model.plan_id,
            plan_name=model.plan_name,
            started_at=model.started_at,
            completed_at=model.completed_at,
            status=ExecutionStatus(model.status),
            total_steps=model.total_steps,
            completed_steps=model.completed_steps,
            failed_steps=model.failed_steps,
            result_summary=result_summary,
            error_message=model.error_message,
        )
