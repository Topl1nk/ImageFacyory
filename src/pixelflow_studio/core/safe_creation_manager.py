"""
Безопасный менеджер создания нод - предотвращает ВСЕ виды дублирования
"""

import time
import threading
from typing import Set, Optional, Dict, Any
from dataclasses import dataclass
from .types import Position, NodeID
from loguru import logger


@dataclass
class CreationRequest:
    """Запрос на создание ноды"""
    class_name: str
    position: Position
    timestamp: float
    thread_id: int
    
    def __hash__(self):
        # Уникальный ключ для предотвращения дублирования
        return hash((
            self.class_name,
            self.position.x,  # Position уже содержит int координаты
            self.position.y,
            round(self.timestamp, 1)  # Группируем клики в пределах 100ms
        ))


class SafeNodeCreationManager:
    """
    Централизованный менеджер безопасного создания нод
    Предотвращает ВСЕ виды дублирования
    """
    
    def __init__(self):
        self._active_requests: Set[CreationRequest] = set()
        self._processing_requests: Set[CreationRequest] = set()
        self._completed_requests: Dict[int, CreationRequest] = {}
        self._lock = threading.RLock()
        self._creation_timeout = 5.0  # секунд
        self._ui_sync_in_progress = False
        
        # Статистика для отладки
        self._stats = {
            'total_requests': 0,
            'duplicate_blocked': 0,
            'timeout_cleaned': 0,
            'successful_created': 0
        }
    
    def request_node_creation(self, class_name: str, position: Position) -> Optional['CreationRequest']:
        """
        Безопасный запрос на создание ноды
        Возвращает None если это дублирующий запрос
        """
        with self._lock:
            request = CreationRequest(
                class_name=class_name,
                position=position,
                timestamp=time.time(),
                thread_id=threading.get_ident()
            )
            
            self._stats['total_requests'] += 1
            
            # Очищаем старые запросы
            self._cleanup_old_requests()
            
            # Проверяем дублирование
            if self._is_duplicate_request(request):
                self._stats['duplicate_blocked'] += 1
                logger.warning(f"🚫 Заблокирован дублирующий запрос: {class_name} at ({position.x}, {position.y})")
                return None
            
            # Если UI синхронизация в процессе - откладываем
            if self._ui_sync_in_progress:
                logger.warning(f"⏳ UI синхронизация в процессе, откладываем создание: {class_name}")
                return None
            
            # Регистрируем запрос
            self._active_requests.add(request)
            logger.info(f"✅ Зарегистрирован запрос: {class_name} at ({position.x}, {position.y})")
            
            return request
    
    def begin_processing(self, request: CreationRequest) -> bool:
        """
        Начинаем обработку запроса
        Возвращает False если запрос уже не актуален
        """
        with self._lock:
            if request not in self._active_requests:
                logger.warning(f"🚫 Запрос больше не актуален: {request.class_name}")
                return False
            
            self._active_requests.remove(request)
            self._processing_requests.add(request)
            logger.info(f"🔄 Начинаем обработку: {request.class_name}")
            
            return True
    
    def complete_processing(self, request: CreationRequest, node_id: NodeID) -> None:
        """Завершаем обработку запроса"""
        with self._lock:
            if request in self._processing_requests:
                self._processing_requests.remove(request)
                self._completed_requests[hash(request)] = request
                self._stats['successful_created'] += 1
                logger.info(f"✅ Завершено создание: {request.class_name} -> {node_id}")
    
    def fail_processing(self, request: CreationRequest, error: str) -> None:
        """Помечаем запрос как неудачный"""
        with self._lock:
            if request in self._processing_requests:
                self._processing_requests.remove(request)
                logger.error(f"❌ Ошибка создания: {request.class_name} - {error}")
    
    def set_ui_sync_state(self, in_progress: bool) -> None:
        """Устанавливаем состояние UI синхронизации"""
        with self._lock:
            old_state = self._ui_sync_in_progress
            self._ui_sync_in_progress = in_progress
            
            if old_state != in_progress:
                state_name = "начата" if in_progress else "завершена"
                logger.info(f"🔄 UI синхронизация {state_name}")
    
    def _is_duplicate_request(self, request: CreationRequest) -> bool:
        """Проверяет, является ли запрос дублирующим"""
        request_hash = hash(request)
        
        # Проверяем активные запросы
        for active_req in self._active_requests:
            if hash(active_req) == request_hash:
                return True
        
        # Проверяем обрабатываемые запросы
        for processing_req in self._processing_requests:
            if hash(processing_req) == request_hash:
                return True
        
        # Проверяем недавно завершенные запросы
        if request_hash in self._completed_requests:
            completed_req = self._completed_requests[request_hash]
            if time.time() - completed_req.timestamp < 1.0:  # В течение 1 секунды
                return True
        
        return False
    
    def _cleanup_old_requests(self) -> None:
        """Очищает старые запросы"""
        current_time = time.time()
        
        # Очищаем активные запросы старше timeout
        expired_active = {
            req for req in self._active_requests 
            if current_time - req.timestamp > self._creation_timeout
        }
        
        for req in expired_active:
            self._active_requests.remove(req)
            self._stats['timeout_cleaned'] += 1
            logger.warning(f"🗑️ Очищен просроченный запрос: {req.class_name}")
        
        # Очищаем обрабатываемые запросы старше timeout
        expired_processing = {
            req for req in self._processing_requests 
            if current_time - req.timestamp > self._creation_timeout
        }
        
        for req in expired_processing:
            self._processing_requests.remove(req)
            logger.error(f"🗑️ Принудительно прерван запрос: {req.class_name}")
        
        # Очищаем завершенные запросы старше 10 секунд
        expired_completed = [
            req_hash for req_hash, req in self._completed_requests.items()
            if current_time - req.timestamp > 10.0
        ]
        
        for req_hash in expired_completed:
            del self._completed_requests[req_hash]
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику работы"""
        with self._lock:
            return {
                **self._stats,
                'active_requests': len(self._active_requests),
                'processing_requests': len(self._processing_requests),
                'completed_requests': len(self._completed_requests),
                'ui_sync_in_progress': self._ui_sync_in_progress
            }
    
    def reset_stats(self) -> None:
        """Сбрасывает статистику"""
        with self._lock:
            self._stats = {
                'total_requests': 0,
                'duplicate_blocked': 0,
                'timeout_cleaned': 0,
                'successful_created': 0
            }
            logger.info("📊 Статистика сброшена")


# Глобальный экземпляр менеджера
_safe_creation_manager = None


def get_safe_creation_manager() -> SafeNodeCreationManager:
    """Получить глобальный экземпляр менеджера безопасного создания"""
    global _safe_creation_manager
    if _safe_creation_manager is None:
        _safe_creation_manager = SafeNodeCreationManager()
    return _safe_creation_manager