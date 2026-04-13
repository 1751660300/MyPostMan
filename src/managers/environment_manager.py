"""环境管理模块 - 管理多套环境配置"""

import uuid
import sys
import os
from typing import Optional

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from models import Environment
from models.database import DatabaseManager, EnvironmentModel, EnvironmentVariableModel


class EnvironmentManager:
    """环境管理器类"""

    def __init__(self):
        self.db = DatabaseManager()
        self._init_default_environment()

    def _init_default_environment(self):
        """初始化默认环境"""
        session = self.db.get_session()
        try:
            # 检查是否已有环境
            env_count = session.query(EnvironmentModel).count()
            if env_count == 0:
                # 创建默认环境
                env_id = str(uuid.uuid4())
                default_env = EnvironmentModel(
                    id=env_id,
                    name="默认环境",
                    is_active=True
                )
                session.add(default_env)

                # 添加默认变量
                default_vars = {
                    "base_url": "https://api.example.com",
                    "timeout": "30"
                }
                for key, value in default_vars.items():
                    var = EnvironmentVariableModel(
                        id=str(uuid.uuid4()),
                        environment_id=env_id,
                        key=key,
                        value=value
                    )
                    session.add(var)

                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def add_environment(self, name: str, variables: dict[str, str] = None) -> Environment:
        """
        添加新环境

        Args:
            name: 环境名称
            variables: 环境变量键值对（必须包含 base_url）

        Returns:
            Environment: 新创建的环境对象
            
        Raises:
            ValueError: 如果变量中不包含 base_url
        """
        # 验证 base_url 是否存在
        if not variables or 'base_url' not in variables:
            raise ValueError("环境变量中必须包含 base_url 字段")
        
        session = self.db.get_session()
        try:
            # 取消其他环境的激活状态
            session.query(EnvironmentModel).update({EnvironmentModel.is_active: False})

            env_id = str(uuid.uuid4())
            env = EnvironmentModel(
                id=env_id,
                name=name,
                is_active=True
            )
            session.add(env)

            # 添加变量
            if variables:
                for key, value in variables.items():
                    var = EnvironmentVariableModel(
                        id=str(uuid.uuid4()),
                        environment_id=env_id,
                        key=key,
                        value=value
                    )
                    session.add(var)

            session.commit()

            return Environment(
                id=env_id,
                name=name,
                variables=variables or {},
                is_active=True
            )
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_environment(self, env_id: str, name: str = None, variables: dict[str, str] = None) -> bool:
        """
        更新环境配置

        Args:
            env_id: 环境ID
            name: 新环境名称
            variables: 新变量键值对（必须包含 base_url）

        Returns:
            bool: 是否更新成功
            
        Raises:
            ValueError: 如果变量中不包含 base_url
        """
        # 验证 base_url 是否存在
        if variables is not None and 'base_url' not in variables:
            raise ValueError("环境变量中必须包含 base_url 字段")
        
        session = self.db.get_session()
        try:
            env = session.query(EnvironmentModel).filter(EnvironmentModel.id == env_id).first()
            if not env:
                return False

            if name is not None:
                env.name = name

            # 更新变量：删除旧的，添加新的
            if variables is not None:
                session.query(EnvironmentVariableModel).filter(
                    EnvironmentVariableModel.environment_id == env_id
                ).delete()

                for key, value in variables.items():
                    var = EnvironmentVariableModel(
                        id=str(uuid.uuid4()),
                        environment_id=env_id,
                        key=key,
                        value=value
                    )
                    session.add(var)

            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete_environment(self, env_id: str) -> bool:
        """
        删除环境

        Args:
            env_id: 环境ID

        Returns:
            bool: 是否删除成功
        """
        session = self.db.get_session()
        try:
            env = session.query(EnvironmentModel).filter(EnvironmentModel.id == env_id).first()
            if not env:
                return False

            # 不允许删除最后一个环境
            env_count = session.query(EnvironmentModel).count()
            if env_count <= 1:
                return False

            # 如果删除的是活动环境，激活第一个其他环境
            if env.is_active:
                other_env = session.query(EnvironmentModel).filter(
                    EnvironmentModel.id != env_id
                ).first()
                if other_env:
                    other_env.is_active = True

            session.delete(env)
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def set_active(self, env_id: str) -> bool:
        """
        设置活动环境

        Args:
            env_id: 要激活的环境ID

        Returns:
            bool: 是否设置成功
        """
        session = self.db.get_session()
        try:
            # 取消所有环境的激活状态
            session.query(EnvironmentModel).update({EnvironmentModel.is_active: False})

            # 激活指定环境
            env = session.query(EnvironmentModel).filter(EnvironmentModel.id == env_id).first()
            if env:
                env.is_active = True
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_active_environment(self) -> Optional[Environment]:
        """
        获取当前活动环境

        Returns:
            Optional[Environment]: 活动环境对象，如果没有则返回None
        """
        session = self.db.get_session()
        try:
            env = session.query(EnvironmentModel).filter(EnvironmentModel.is_active == True).first()
            if not env:
                return None

            # 确保获取最新的变量数据
            session.refresh(env)
            variables = {
                var.key: var.value
                for var in env.variables
            }

            return Environment(
                id=env.id,
                name=env.name,
                variables=variables,
                is_active=env.is_active
            )
        finally:
            session.close()

    def get_environment(self, env_id: str) -> Optional[Environment]:
        """
        根据ID获取环境

        Args:
            env_id: 环境ID

        Returns:
            Optional[Environment]: 环境对象
        """
        session = self.db.get_session()
        try:
            env = session.query(EnvironmentModel).filter(EnvironmentModel.id == env_id).first()
            if not env:
                return None

            # 确保获取最新的变量数据
            session.refresh(env)
            variables = {
                var.key: var.value
                for var in env.variables
            }

            return Environment(
                id=env.id,
                name=env.name,
                variables=variables,
                is_active=env.is_active
            )
        finally:
            session.close()

    def get_all_environments(self) -> list[Environment]:
        """
        获取所有环境

        Returns:
            list[Environment]: 环境列表
        """
        session = self.db.get_session()
        try:
            envs = session.query(EnvironmentModel).all()
            result = []
            for env in envs:
                # 确保获取最新的变量数据
                session.refresh(env)
                variables = {
                    var.key: var.value
                    for var in env.variables
                }
                result.append(Environment(
                    id=env.id,
                    name=env.name,
                    variables=variables,
                    is_active=env.is_active
                ))
            return result
        finally:
            session.close()

    def get_active_variables(self) -> dict[str, str]:
        """
        获取活动环境的变量

        Returns:
            dict[str, str]: 变量键值对
        """
        active_env = self.get_active_environment()
        return active_env.variables if active_env else {}
