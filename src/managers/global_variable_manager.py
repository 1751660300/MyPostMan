"""全局变量管理模块 - 管理跨环境的全局变量"""

import uuid
from datetime import datetime
from models.database import DatabaseManager, GlobalVariableModel


class GlobalVariableManager:
    """全局变量管理器类"""

    def __init__(self):
        self.db = DatabaseManager()
        self._init_default_variables()

    def _init_default_variables(self):
        """初始化默认全局变量"""
        session = self.db.get_session()
        try:
            # 检查是否已有全局变量
            var_count = session.query(GlobalVariableModel).count()
            if var_count == 0:
                # 创建默认全局变量
                default_vars = {
                    "version": "1.0.0",
                    "app_name": "MyPostMan"
                }
                for key, value in default_vars.items():
                    var = GlobalVariableModel(
                        id=str(uuid.uuid4()),
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

    def set_variable(self, key: str, value: str):
        """
        设置全局变量

        Args:
            key: 变量名
            value: 变量值
        """
        session = self.db.get_session()
        try:
            # 查找是否已存在
            var = session.query(GlobalVariableModel).filter(GlobalVariableModel.key == key).first()
            if var:
                var.value = value
                var.updated_at = datetime.now()
            else:
                var = GlobalVariableModel(
                    id=str(uuid.uuid4()),
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

    def get_variable(self, key: str, default: str = None) -> str:
        """
        获取全局变量

        Args:
            key: 变量名
            default: 默认值（如果变量不存在）

        Returns:
            str: 变量值
        """
        session = self.db.get_session()
        try:
            var = session.query(GlobalVariableModel).filter(GlobalVariableModel.key == key).first()
            return var.value if var else default
        finally:
            session.close()

    def delete_variable(self, key: str) -> bool:
        """
        删除全局变量

        Args:
            key: 变量名

        Returns:
            bool: 是否删除成功
        """
        session = self.db.get_session()
        try:
            var = session.query(GlobalVariableModel).filter(GlobalVariableModel.key == key).first()
            if var:
                session.delete(var)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_all_variables(self) -> dict[str, str]:
        """
        获取所有全局变量

        Returns:
            dict[str, str]: 变量键值对
        """
        session = self.db.get_session()
        try:
            vars = session.query(GlobalVariableModel).all()
            return {var.key: var.value for var in vars}
        finally:
            session.close()

    def set_variables(self, variables: dict[str, str]):
        """
        批量设置全局变量

        Args:
            variables: 变量键值对
        """
        session = self.db.get_session()
        try:
            # 删除所有现有的
            session.query(GlobalVariableModel).delete()

            # 添加新的
            for key, value in variables.items():
                var = GlobalVariableModel(
                    id=str(uuid.uuid4()),
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

    def clear_all(self):
        """清空所有全局变量"""
        session = self.db.get_session()
        try:
            session.query(GlobalVariableModel).delete()
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
