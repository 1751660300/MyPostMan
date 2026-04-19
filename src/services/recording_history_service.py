"""录制历史服务模块 - 管理录制历史记录"""

import json
from models.database import DatabaseManager, RecordingHistoryModel
from models.models import RecordingHistory
from typing import List, Optional
from datetime import datetime
import uuid


class RecordingHistoryService:
    """录制历史服务"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_manager = db_manager or DatabaseManager()
    
    def add_record(self, record: dict) -> str:
        """添加录制记录
        
        Args:
            record: 包含录制信息的字典
            
        Returns:
            记录 ID
        """
        session = self.db_manager.get_session()
        try:
            record_id = str(uuid.uuid4())
            
            db_record = RecordingHistoryModel(
                id=record_id,
                url=record.get('url', ''),
                auth_type=record.get('auth_type', 'custom'),
                variable_name=record.get('variable_name', ''),
                value=record.get('value', ''),
                save_location=record.get('save_location', 'global'),
                fields_count=record.get('fields_count', 0),
                has_auto_capture=record.get('has_auto_capture', False),
                script_file=record.get('script_file', ''),
                actions_count=record.get('actions_count', 0),
                script_content=record.get('script_content', ''),
                field_configs=json.dumps(record.get('field_configs', [])),
            )
            
            session.add(db_record)
            session.commit()
            
            print(f"✅ 录制记录已保存到数据库: {record_id}")
            return record_id
            
        except Exception as e:
            session.rollback()
            print(f"❌ 保存录制记录失败: {e}")
            import traceback
            traceback.print_exc()
            return ""
        finally:
            session.close()
    
    def get_all_records(self, limit: int = 100, offset: int = 0) -> List[RecordingHistory]:
        """获取所有录制记录
        
        Args:
            limit: 每页数量
            offset: 偏移量
            
        Returns:
            录制记录列表
        """
        session = self.db_manager.get_session()
        try:
            records = session.query(RecordingHistoryModel)\
                .order_by(RecordingHistoryModel.created_at.desc())\
                .limit(limit)\
                .offset(offset)\
                .all()
            
            return [
                RecordingHistory(
                    id=r.id,
                    url=r.url,
                    auth_type=r.auth_type,
                    variable_name=r.variable_name,
                    value=r.value,
                    save_location=r.save_location,
                    created_at=r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    fields_count=r.fields_count,
                    has_auto_capture=r.has_auto_capture,
                    script_file=r.script_file,
                    actions_count=r.actions_count,
                    script_content=r.script_content,
                    field_configs=json.loads(r.field_configs) if r.field_configs else [],
                )
                for r in records
            ]
        finally:
            session.close()
    
    def get_record_by_id(self, record_id: str) -> Optional[RecordingHistory]:
        """根据 ID 获取录制记录
        
        Args:
            record_id: 记录 ID
            
        Returns:
            录制记录或 None
        """
        session = self.db_manager.get_session()
        try:
            record = session.query(RecordingHistoryModel)\
                .filter(RecordingHistoryModel.id == record_id)\
                .first()
            
            if record:
                return RecordingHistory(
                    id=record.id,
                    url=record.url,
                    auth_type=record.auth_type,
                    variable_name=record.variable_name,
                    value=record.value,
                    save_location=record.save_location,
                    created_at=record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    fields_count=record.fields_count,
                    has_auto_capture=record.has_auto_capture,
                    script_file=record.script_file,
                    actions_count=record.actions_count,
                    script_content=record.script_content,
                    field_configs=json.loads(record.field_configs) if record.field_configs else [],
                )
            return None
        finally:
            session.close()
    
    def update_script_content(self, record_id: str, script_content: str) -> bool:
        """更新脚本内容
        
        Args:
            record_id: 记录 ID
            script_content: 新的脚本内容
            
        Returns:
            是否成功
        """
        session = self.db_manager.get_session()
        try:
            record = session.query(RecordingHistoryModel)\
                .filter(RecordingHistoryModel.id == record_id)\
                .first()
            
            if record:
                record.script_content = script_content
                session.commit()
                print(f"✅ 脚本内容已更新: {record_id}")
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"❌ 更新脚本内容失败: {e}")
            return False
        finally:
            session.close()
    
    def delete_record(self, record_id: str) -> bool:
        """删除录制记录
        
        Args:
            record_id: 记录 ID
            
        Returns:
            是否成功
        """
        session = self.db_manager.get_session()
        try:
            record = session.query(RecordingHistoryModel)\
                .filter(RecordingHistoryModel.id == record_id)\
                .first()
            
            if record:
                session.delete(record)
                session.commit()
                print(f"✅ 录制记录已删除: {record_id}")
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"❌ 删除录制记录失败: {e}")
            return False
        finally:
            session.close()
    
    def get_total_count(self) -> int:
        """获取记录总数"""
        session = self.db_manager.get_session()
        try:
            return session.query(RecordingHistoryModel).count()
        finally:
            session.close()

