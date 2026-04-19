"""数据库模型模块 - 定义 SQLAlchemy 数据模型"""

from sqlalchemy import create_engine, Column, String, Integer, Float, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import os

Base = declarative_base()


class EnvironmentModel(Base):
    """环境配置数据库模型"""
    __tablename__ = 'environments'

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系：环境变量
    variables = relationship('EnvironmentVariableModel', back_populates='environment', cascade='all, delete-orphan')


class EnvironmentVariableModel(Base):
    """环境变量数据库模型"""
    __tablename__ = 'environment_variables'

    id = Column(String, primary_key=True)
    environment_id = Column(String, ForeignKey('environments.id'), nullable=False)
    key = Column(String, nullable=False)
    value = Column(Text, default='')

    # 关系
    environment = relationship('EnvironmentModel', back_populates='variables')


class GlobalVariableModel(Base):
    """全局变量数据库模型"""
    __tablename__ = 'global_variables'

    id = Column(String, primary_key=True)
    key = Column(String, nullable=False, unique=True)
    value = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class HistoryModel(Base):
    """历史记录数据库模型"""
    __tablename__ = 'history'

    id = Column(String, primary_key=True)
    url = Column(String, nullable=False)
    method = Column(String, nullable=False)
    status_code = Column(Integer, default=0)
    elapsed = Column(Float, default=0.0)
    timestamp = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    # 请求数据
    request_headers = Column(Text)  # JSON 字符串
    request_params = Column(Text)  # JSON 字符串
    request_body = Column(Text)
    request_body_type = Column(String, default='none')

    # 响应数据
    response_headers = Column(Text)  # JSON 字符串
    response_body = Column(Text)
    response_error = Column(Text)


class RequestListModel(Base):
    """请求列表数据库模型"""
    __tablename__ = 'request_list'

    id = Column(String, primary_key=True)
    url = Column(String, nullable=False)
    method = Column(String, nullable=False, default='GET')
    name = Column(String, default='')
    params = Column(Text)  # JSON 字符串
    headers = Column(Text)  # JSON 字符串
    body = Column(Text, default='')  # 请求体
    body_type = Column(String, default='none')  # 请求体类型
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class RecordingHistoryModel(Base):
    """录制历史记录数据库模型"""
    __tablename__ = 'recording_history'

    id = Column(String, primary_key=True)
    url = Column(String, nullable=False)
    auth_type = Column(String, default='custom')
    variable_name = Column(String, default='')
    value = Column(Text, default='')
    save_location = Column(String, default='global')
    created_at = Column(DateTime, default=datetime.now)
    fields_count = Column(Integer, default=0)
    has_auto_capture = Column(Boolean, default=False)
    script_file = Column(String, default='')  # 脚本文件路径
    actions_count = Column(Integer, default=0)
    script_content = Column(Text, default='')  # 脚本内容（用于编辑）
    field_configs = Column(Text, default='[]')  # 字段配置（JSON格式）


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


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: str = 'mypostman.db'):
        # 如果db_path不是绝对路径，则相对于src目录
        if not os.path.isabs(db_path):
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), db_path)
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.Session = sessionmaker(bind=self.engine)
        self._create_tables()
        self._migrate_tables()

    def _create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(self.engine)

    def _migrate_tables(self):
        """迁移已存在的表，添加新字段"""
        try:
            import sqlite3
            db_path = self.engine.url.database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 检查 recording_history 表是否需要添加 field_configs 字段
            try:
                cursor.execute("SELECT field_configs FROM recording_history LIMIT 1")
            except sqlite3.OperationalError:
                # field_configs 字段不存在，需要添加
                cursor.execute("ALTER TABLE recording_history ADD COLUMN field_configs TEXT DEFAULT '[]'")
                conn.commit()
                print("✅ 数据库迁移：已添加 field_configs 字段")
            
            # 检查request_list表是否需要迁移
            try:
                cursor.execute("SELECT body FROM request_list LIMIT 1")
            except sqlite3.OperationalError:
                # body字段不存在，需要添加
                cursor.execute("ALTER TABLE request_list ADD COLUMN body TEXT DEFAULT ''")
                cursor.execute("ALTER TABLE request_list ADD COLUMN body_type TEXT DEFAULT 'none'")
                conn.commit()
                print("✅ 数据库迁移：已添加 body 和 body_type 字段")
            
            conn.close()
        except Exception as e:
            # 迁移失败不影响正常使用
            print(f"数据库迁移失败（可忽略）: {e}")

    def get_session(self):
        """获取数据库会话"""
        return self.Session()
