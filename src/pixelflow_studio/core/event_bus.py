"""
Централизованная система событий для PixelFlow Studio.

Обеспечивает слабую связанность между компонентами через сигналы.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from PySide6.QtCore import QObject, Signal


class EventBus(QObject):
    """
    Централизованная система событий.
    
    Позволяет компонентам общаться без прямых зависимостей.
    """
    
    # Сигналы для основных событий приложения
    node_selected = Signal(str)  # node_id
    node_deselected = Signal()
    node_added = Signal(str)  # node_id
    node_removed = Signal(str)  # node_id
    node_moved = Signal(str, float, float)  # node_id, x, y
    
    pin_selected = Signal(str, str)  # node_id, pin_id
    pin_deselected = Signal()
    pin_value_changed = Signal(str, str, object)  # node_id, pin_id, value
    
    connection_created = Signal(str, str, str, str)  # from_node, from_pin, to_node, to_pin
    connection_removed = Signal(str, str, str, str)  # from_node, from_pin, to_node, to_pin
    
    variable_created = Signal(str)  # var_id
    variable_updated = Signal(str, str, object)  # var_id, property, value
    variable_deleted = Signal(str)  # var_id
    
    graph_changed = Signal()
    project_saved = Signal(str)  # file_path
    project_loaded = Signal(str)  # file_path
    
    # Системные события
    error_occurred = Signal(str, str)  # error_type, message
    warning_occurred = Signal(str, str)  # warning_type, message
    info_message = Signal(str)  # message
    
    def __init__(self):
        super().__init__()
        self._instance: Optional[EventBus] = None
        self._listeners: Dict[str, List[Callable]] = {}
    
    @classmethod
    def instance(cls) -> EventBus:
        """Возвращает единственный экземпляр EventBus (Singleton)."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def subscribe(self, event_name: str, callback: Callable) -> None:
        """
        Подписывает callback на событие.
        
        Args:
            event_name: Имя события
            callback: Функция для вызова при событии
        """
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(callback)
    
    def unsubscribe(self, event_name: str, callback: Callable) -> None:
        """
        Отписывает callback от события.
        
        Args:
            event_name: Имя события
            callback: Функция для отписки
        """
        if event_name in self._listeners:
            try:
                self._listeners[event_name].remove(callback)
            except ValueError:
                pass  # Callback не найден
    
    def emit(self, event_name: str, *args, **kwargs) -> None:
        """
        Генерирует событие.
        
        Args:
            event_name: Имя события
            *args: Позиционные аргументы для callback
            **kwargs: Именованные аргументы для callback
        """
        if event_name in self._listeners:
            for callback in self._listeners[event_name]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    # Логируем ошибку в callback
                    self.error_occurred.emit(
                        "callback_error", 
                        f"Error in {event_name} callback: {e}"
                    )
    
    def clear_listeners(self, event_name: Optional[str] = None) -> None:
        """
        Очищает слушателей событий.
        
        Args:
            event_name: Имя события для очистки, или None для всех
        """
        if event_name:
            self._listeners.pop(event_name, None)
        else:
            self._listeners.clear()


# Глобальный экземпляр для удобства
event_bus = EventBus.instance()


# Декораторы для удобства
def on_event(event_name: str):
    """
    Декоратор для подписки на события.
    
    Usage:
        @on_event("node_selected")
        def handle_node_selected(node_id: str):
            print(f"Node {node_id} selected")
    """
    def decorator(func: Callable) -> Callable:
        event_bus.subscribe(event_name, func)
        return func
    return decorator


def emit_event(event_name: str):
    """
    Декоратор для генерации событий после выполнения функции.
    
    Usage:
        @emit_event("node_added")
        def add_node(node_id: str):
            # Логика добавления ноды
            return node_id
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            event_bus.emit(event_name, result)
            return result
        return wrapper
    return decorator 