"""历史记录管理模块 - 管理请求历史"""

import json
import time
import uuid
from typing import Optional
from models import HttpRequest, HttpResponse, HistoryItem, HttpMethod
from models.database import DatabaseManager, HistoryModel


class HistoryManager:
    """历史记录管理器"""

    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.db = DatabaseManager()

    def add_entry(
        self,
        request: HttpRequest,
        response: HttpResponse,
    ) -> HistoryItem:
        """
        添加一条历史记录

        Args:
            request: 请求数据
            response: 响应数据

        Returns:
            HistoryItem: 创建的历史记录项
        """
        entry = HistoryItem(
            id=str(uuid.uuid4())[:8],
            url=request.url,
            method=request.method,
            status_code=response.status_code if response.status_code else 0,
            elapsed=response.elapsed,
            timestamp=time.time(),
            request=request,
            response=response,
        )

        # 保存到数据库
        session = self.db.get_session()
        try:
            model = HistoryModel(
                id=entry.id,
                url=entry.url,
                method=entry.method.value,
                status_code=entry.status_code,
                elapsed=entry.elapsed,
                timestamp=entry.timestamp,
                request_headers=json.dumps(request.headers) if request.headers else None,
                request_params=json.dumps(request.params) if request.params else None,
                request_body=request.body,
                request_body_type=request.body_type,
                response_headers=json.dumps(response.headers) if response.headers else None,
                response_body=response.body,
                response_error=response.error,
            )
            session.add(model)

            # 限制历史记录数量
            count = session.query(HistoryModel).count()
            if count > self.max_history:
                # 删除最旧的记录
                oldest = session.query(HistoryModel).order_by(HistoryModel.timestamp.asc()).first()
                if oldest:
                    session.delete(oldest)

            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

        return entry

    def get_all(self) -> list[HistoryItem]:
        """获取所有历史记录"""
        session = self.db.get_session()
        try:
            models = session.query(HistoryModel).order_by(HistoryModel.timestamp.desc()).all()
            return [self._model_to_item(m) for m in models]
        finally:
            session.close()

    def get_by_id(self, entry_id: str) -> Optional[HistoryItem]:
        """根据 ID 获取历史记录"""
        session = self.db.get_session()
        try:
            model = session.query(HistoryModel).filter(HistoryModel.id == entry_id).first()
            if not model:
                return None
            return self._model_to_item(model)
        finally:
            session.close()

    def clear(self):
        """清空所有历史记录"""
        session = self.db.get_session()
        try:
            session.query(HistoryModel).delete()
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def remove(self, entry_id: str) -> bool:
        """删除指定历史记录"""
        session = self.db.get_session()
        try:
            model = session.query(HistoryModel).filter(HistoryModel.id == entry_id).first()
            if model:
                session.delete(model)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_recent(self, count: int = 10) -> list[HistoryItem]:
        """获取最近的历史记录"""
        session = self.db.get_session()
        try:
            models = session.query(HistoryModel).order_by(
                HistoryModel.timestamp.desc()
            ).limit(count).all()
            return [self._model_to_item(m) for m in models]
        finally:
            session.close()

    def get_paged(self, page: int = 1, page_size: int = 20) -> tuple[list[HistoryItem], int]:
        """
        分页查询历史记录（按时间倒序）

        Args:
            page: 页码（从1开始）
            page_size: 每页数量

        Returns:
            tuple: (历史记录列表, 总记录数)
        """
        session = self.db.get_session()
        try:
            # 获取总记录数
            total = session.query(HistoryModel).count()

            # 计算偏移量
            offset = (page - 1) * page_size

            # 分页查询，按时间倒序
            models = session.query(HistoryModel).order_by(
                HistoryModel.timestamp.desc()
            ).limit(page_size).offset(offset).all()

            return [self._model_to_item(m) for m in models], total
        finally:
            session.close()

    def get_total_count(self) -> int:
        """获取历史记录总数"""
        session = self.db.get_session()
        try:
            return session.query(HistoryModel).count()
        finally:
            session.close()

    def _model_to_item(self, model: HistoryModel) -> HistoryItem:
        """将数据库模型转换为 HistoryItem"""
        # 解析请求数据
        headers = json.loads(model.request_headers) if model.request_headers else {}
        params = json.loads(model.request_params) if model.request_params else {}
        
        request = HttpRequest(
            url=model.url,
            method=HttpMethod(model.method),
            headers=headers,
            params=params,
            body=model.request_body,
            body_type=model.request_body_type or 'none',
        )

        # 解析响应数据
        response_headers = json.loads(model.response_headers) if model.response_headers else {}
        
        response = HttpResponse(
            status_code=model.status_code,
            elapsed=model.elapsed,
            headers=response_headers,
            body=model.response_body or '',
            error=model.response_error,
        )

        return HistoryItem(
            id=model.id,
            url=model.url,
            method=HttpMethod(model.method),
            status_code=model.status_code,
            elapsed=model.elapsed,
            timestamp=model.timestamp,
            request=request,
            response=response,
        )

    @staticmethod
    def format_timestamp(timestamp: float) -> str:
        """格式化时间戳为可读字符串"""
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
