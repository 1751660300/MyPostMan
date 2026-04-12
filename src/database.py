"""数据库模型模块 - 定义 SQLAlchemy 数据模型"""

from sqlalchemy import create_engine, Column, String, Integer, Float, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

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


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: str = 'mypostman.db'):
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.Session = sessionmaker(bind=self.engine)
        self._create_tables()

    def _create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(self.engine)

    def get_session(self):
        """获取数据库会话"""
        return self.Session()
