"""系统设置管理器 - 管理应用设置"""

import uuid
from models.database import DatabaseManager, SettingsModel


class SettingsManager:
    """系统设置管理器"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self._init_default_settings()
    
    def _init_default_settings(self):
        """初始化默认设置"""
        session = self.db_manager.get_session()
        try:
            # SSL 验证设置（默认开启）
            if not session.query(SettingsModel).filter_by(key='ssl_verify_enabled').first():
                ssl_setting = SettingsModel(
                    id=str(uuid.uuid4()),
                    key='ssl_verify_enabled',
                    value='true',
                    description='是否启用 SSL 证书验证'
                )
                session.add(ssl_setting)
                session.commit()
        except Exception as e:
            print(f"初始化设置失败: {e}")
        finally:
            session.close()
    
    def get_setting(self, key: str, default_value: str = '') -> str:
        """
        获取设置值
        
        Args:
            key: 设置键
            default_value: 默认值
            
        Returns:
            设置值
        """
        session = self.db_manager.get_session()
        try:
            setting = session.query(SettingsModel).filter_by(key=key).first()
            if setting:
                return setting.value
            return default_value
        finally:
            session.close()
    
    def set_setting(self, key: str, value: str, description: str = ''):
        """
        设置值
        
        Args:
            key: 设置键
            value: 设置值
            description: 描述
        """
        session = self.db_manager.get_session()
        try:
            setting = session.query(SettingsModel).filter_by(key=key).first()
            
            if setting:
                # 更新现有设置
                setting.value = value
                if description:
                    setting.description = description
            else:
                # 创建新设置
                setting = SettingsModel(
                    id=str(uuid.uuid4()),
                    key=key,
                    value=value,
                    description=description
                )
                session.add(setting)
            
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"保存设置失败: {e}")
            raise
        finally:
            session.close()
    
    def get_ssl_verify_enabled(self) -> bool:
        """获取 SSL 验证是否启用"""
        value = self.get_setting('ssl_verify_enabled', 'true')
        return value.lower() in ('true', '1', 'yes')
    
    def set_ssl_verify_enabled(self, enabled: bool):
        """设置 SSL 验证是否启用"""
        self.set_setting('ssl_verify_enabled', str(enabled).lower(), '是否启用 SSL 证书验证')
    
    def get_all_settings(self) -> dict:
        """获取所有设置"""
        session = self.db_manager.get_session()
        try:
            settings = session.query(SettingsModel).all()
            return {s.key: s.value for s in settings}
        finally:
            session.close()
