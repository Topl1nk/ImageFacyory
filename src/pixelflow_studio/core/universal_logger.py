"""
Система тотального логирования действий пользователя.
Записывает КАЖДОЕ действие с максимальными деталями.
"""

import time
import threading
from typing import Any, Dict, Optional
from pathlib import Path
from datetime import datetime
import json
from dataclasses import dataclass, asdict
from enum import Enum

from loguru import logger


class ActionCategory(Enum):
    """Категории действий для детального логирования."""
    MOUSE_CLICK = "mouse_click"
    MOUSE_MOVE = "mouse_move"
    MOUSE_DRAG = "mouse_drag"
    KEYBOARD = "keyboard"
    NODE_CREATE = "node_create"
    NODE_DELETE = "node_delete"
    NODE_MOVE = "node_move"
    NODE_SELECT = "node_select"
    CONNECTION_CREATE = "connection_create"
    CONNECTION_DELETE = "connection_delete"
    PIN_CLICK = "pin_click"
    PIN_HOVER = "pin_hover"
    CANVAS_ZOOM = "canvas_zoom"
    CANVAS_PAN = "canvas_pan"
    MENU_OPEN = "menu_open"
    MENU_CLOSE = "menu_close"
    MENU_CLICK = "menu_click"
    WINDOW_RESIZE = "window_resize"
    WINDOW_MOVE = "window_move"
    WINDOW_FOCUS = "window_focus"
    SCENE_UPDATE = "scene_update"
    PROPERTY_CHANGE = "property_change"
    FILE_OPERATION = "file_operation"
    ERROR_OCCURRED = "error_occurred"
    SYSTEM_STATE = "system_state"


@dataclass
class ActionDetails:
    """Детальная информация о действии."""
    timestamp: float
    category: ActionCategory
    action: str
    coordinates: Optional[Dict[str, float]] = None
    object_id: Optional[str] = None
    object_type: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    scene_state: Optional[Dict[str, Any]] = None
    window_state: Optional[Dict[str, Any]] = None
    mouse_state: Optional[Dict[str, Any]] = None
    keyboard_state: Optional[Dict[str, Any]] = None
    thread_id: Optional[str] = None
    stack_trace: Optional[str] = None


class UniversalLogger:
    """
    Логгер который записывает АБСОЛЮТНО ВСЕ действия пользователя.
    Каждый клик, движение, изменение - все с координатами и деталями.
    """
    
    def __init__(self):
        self.session_id = f"session_{int(time.time())}"
        self.log_file = Path("logs") / f"{self.session_id}.jsonl"
        self.log_file.parent.mkdir(exist_ok=True)
        
        self.action_counter = 0
        self.lock = threading.Lock()
        
        # Состояние для отслеживания изменений
        self.last_mouse_pos = None
        self.last_window_size = None
        self.last_scene_bounds = None
        self.selected_nodes = set()
        self.hovered_objects = set()
        
        logger.info(f"🔍 UNIVERSAL LOGGER STARTED: {self.session_id}")
        self.log_action(ActionCategory.SYSTEM_STATE, "logger_initialized", {
            "session_id": self.session_id,
            "log_file": str(self.log_file),
            "timestamp": datetime.now().isoformat()
        })
    
    def log_action(self, category: ActionCategory, action: str, details: Dict[str, Any] = None):
        """Логирует действие с максимальными деталями."""
        with self.lock:
            self.action_counter += 1
            
            action_details = ActionDetails(
                timestamp=time.time(),
                category=category,
                action=action,
                thread_id=threading.current_thread().name,
                properties=details or {}
            )
            
            # Записываем в файл
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    # Конвертируем enum в строку для JSON
                    data = asdict(action_details)
                    data['category'] = category.value
                    json.dump(data, f, ensure_ascii=False)
                    f.write('\n')
            except Exception as e:
                logger.error(f"Failed to write action log: {e}")
            
            # Выводим в консоль с деталями
            coords_str = ""
            if action_details.coordinates:
                coords_str = f" at ({action_details.coordinates.get('x', '?')}, {action_details.coordinates.get('y', '?')})"
            
            details_str = ""
            if details:
                key_details = []
                for key, value in details.items():
                    if key in ['x', 'y', 'width', 'height', 'id', 'type', 'name']:
                        key_details.append(f"{key}={value}")
                if key_details:
                    details_str = f" [{', '.join(key_details)}]"
            
            logger.info(f"🔍 [{self.action_counter:06d}] {category.value}.{action}{coords_str}{details_str}")
    
    def log_mouse_click(self, x: float, y: float, button: str, modifiers: list = None):
        """Логирует клик мыши."""
        details = {
            "button": button,
            "modifiers": modifiers or [],
            "scene_coordinates": self._get_scene_coords(x, y)
        }
        
        action_details = ActionDetails(
            timestamp=time.time(),
            category=ActionCategory.MOUSE_CLICK,
            action=f"click_{button}",
            coordinates={"x": x, "y": y},  # Координаты в правильном месте!
            thread_id=threading.current_thread().name,
            properties=details
        )
        
        self._write_and_log_action(action_details)
    
    def _write_and_log_action(self, action_details: ActionDetails):
        """Записывает действие в файл и выводит в консоль."""
        with self.lock:
            self.action_counter += 1
            
            # Записываем в файл
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    # Конвертируем enum в строку для JSON
                    data = asdict(action_details)
                    data['category'] = action_details.category.value
                    json.dump(data, f, ensure_ascii=False)
                    f.write('\n')
            except Exception as e:
                logger.error(f"Failed to write action log: {e}")
            
            # Выводим в консоль с деталями
            coords_str = ""
            if action_details.coordinates:
                coords_str = f" at ({action_details.coordinates.get('x', '?')}, {action_details.coordinates.get('y', '?')})"
            
            details_str = ""
            if action_details.properties:
                key_details = []
                for key, value in action_details.properties.items():
                    if key in ['x', 'y', 'width', 'height', 'id', 'type', 'name', 'button']:
                        key_details.append(f"{key}={value}")
                if key_details:
                    details_str = f" [{', '.join(key_details)}]"
            
            logger.info(f"🔍 [{self.action_counter:06d}] {action_details.category.value}.{action_details.action}{coords_str}{details_str}")
    
    def log_mouse_move(self, x: float, y: float, buttons_pressed: list = None):
        """Логирует движение мыши (только если изменились координаты)."""
        if self.last_mouse_pos != (x, y):
            self.last_mouse_pos = (x, y)
            self.log_action(ActionCategory.MOUSE_MOVE, "move", {
                "coordinates": {"x": x, "y": y},
                "buttons_pressed": buttons_pressed or [],
                "scene_coordinates": self._get_scene_coords(x, y)
            })
    
    def log_mouse_drag(self, start_x: float, start_y: float, end_x: float, end_y: float, object_id: str = None):
        """Логирует перетаскивание."""
        self.log_action(ActionCategory.MOUSE_DRAG, "drag", {
            "start_coordinates": {"x": start_x, "y": start_y},
            "end_coordinates": {"x": end_x, "y": end_y},
            "distance": ((end_x - start_x) ** 2 + (end_y - start_y) ** 2) ** 0.5,
            "object_id": object_id
        })
    
    def log_node_created(self, node_id: str, node_type: str, x: float, y: float, properties: Dict = None):
        """Логирует создание ноды."""
        details = {
            "node_properties": properties or {},
            "total_nodes_count": self._count_nodes()
        }
        
        action_details = ActionDetails(
            timestamp=time.time(),
            category=ActionCategory.NODE_CREATE,
            action="created",
            coordinates={"x": x, "y": y},
            object_id=node_id,
            object_type=node_type,
            thread_id=threading.current_thread().name,
            properties=details
        )
        
        self._write_and_log_action(action_details)
    
    def log_node_deleted(self, node_id: str, node_type: str, x: float, y: float):
        """Логирует удаление ноды."""
        self.log_action(ActionCategory.NODE_DELETE, "deleted", {
            "object_id": node_id,
            "object_type": node_type,
            "coordinates": {"x": x, "y": y},
            "total_nodes_count": self._count_nodes()
        })
    
    def log_node_moved(self, node_id: str, old_x: float, old_y: float, new_x: float, new_y: float):
        """Логирует перемещение ноды."""
        self.log_action(ActionCategory.NODE_MOVE, "moved", {
            "object_id": node_id,
            "old_coordinates": {"x": old_x, "y": old_y},
            "new_coordinates": {"x": new_x, "y": new_y},
            "distance": ((new_x - old_x) ** 2 + (new_y - old_y) ** 2) ** 0.5
        })
    
    def log_connection_created(self, output_node: str, output_pin: str, input_node: str, input_pin: str):
        """Логирует создание соединения."""
        self.log_action(ActionCategory.CONNECTION_CREATE, "created", {
            "output_node": output_node,
            "output_pin": output_pin,
            "input_node": input_node,
            "input_pin": input_pin,
            "connection_id": f"{output_node}.{output_pin}->{input_node}.{input_pin}",
            "total_connections_count": self._count_connections()
        })
    
    def log_pin_interaction(self, pin_id: str, pin_type: str, node_id: str, action: str, x: float, y: float):
        """Логирует взаимодействие с пином."""
        self.log_action(ActionCategory.PIN_CLICK if "click" in action else ActionCategory.PIN_HOVER, action, {
            "object_id": pin_id,
            "object_type": pin_type,
            "node_id": node_id,
            "coordinates": {"x": x, "y": y}
        })
    
    def log_canvas_zoom(self, old_zoom: float, new_zoom: float, center_x: float, center_y: float):
        """Логирует зум канваса."""
        self.log_action(ActionCategory.CANVAS_ZOOM, "zoom_changed", {
            "old_zoom": old_zoom,
            "new_zoom": new_zoom,
            "zoom_delta": new_zoom - old_zoom,
            "zoom_center": {"x": center_x, "y": center_y}
        })
    
    def log_window_event(self, event_type: str, x: int = None, y: int = None, width: int = None, height: int = None):
        """Логирует события окна."""
        details = {"event_type": event_type}
        if x is not None and y is not None:
            details["coordinates"] = {"x": x, "y": y}
        if width is not None and height is not None:
            details["size"] = {"width": width, "height": height}
            
        self.log_action(ActionCategory.WINDOW_RESIZE if "resize" in event_type else ActionCategory.WINDOW_FOCUS, event_type, details)
    
    def log_menu_interaction(self, menu_type: str, action: str, item_name: str = None, x: float = None, y: float = None):
        """Логирует взаимодействие с меню."""
        category = ActionCategory.MENU_OPEN if "open" in action else ActionCategory.MENU_CLOSE if "close" in action else ActionCategory.MENU_CLICK
        
        details = {
            "menu_type": menu_type,
            "item_name": item_name
        }
        if x is not None and y is not None:
            details["coordinates"] = {"x": x, "y": y}
            
        self.log_action(category, action, details)
    
    def log_error(self, error_message: str, error_type: str = None, context: Dict = None):
        """Логирует ошибки."""
        details = {
            "error_message": error_message,
            "error_type": error_type,
            "context": context or {}
        }
        
        action_details = ActionDetails(
            timestamp=time.time(),
            category=ActionCategory.ERROR_OCCURRED,
            action="error",
            object_type=error_type,
            thread_id=threading.current_thread().name,
            properties=details,
            stack_trace=self._get_stack_trace()
        )
        
        self._write_and_log_action(action_details)
    
    def log_system_state(self, state_name: str, details: Dict):
        """Логирует состояние системы."""
        self.log_action(ActionCategory.SYSTEM_STATE, state_name, details)
    
    def _get_scene_coords(self, x: float, y: float) -> Dict[str, float]:
        """Получает координаты в сцене (заглушка, будет переопределено)."""
        return {"scene_x": x, "scene_y": y}
    
    def _count_nodes(self) -> int:
        """Считает количество нод (заглушка, будет переопределено)."""
        return 0
    
    def _count_connections(self) -> int:
        """Считает количество соединений (заглушка, будет переопределено)."""
        return 0
    
    def _get_stack_trace(self) -> str:
        """Получает stack trace."""
        import traceback
        return traceback.format_stack()[-5:]  # Последние 5 кадров


# Глобальный экземпляр логгера
_universal_logger = None

def get_universal_logger() -> UniversalLogger:
    """Получить глобальный экземпляр логгера."""
    global _universal_logger
    if _universal_logger is None:
        _universal_logger = UniversalLogger()
    return _universal_logger

def setup_universal_logging(app):
    """Настроить логирование для приложения."""
    logger_instance = get_universal_logger()
    
    # Переопределяем методы подсчета
    def count_nodes():
        return len(app.graph.nodes) if hasattr(app, 'graph') else 0
        
    def count_connections():
        return len(app.graph.connections) if hasattr(app, 'graph') else 0
    
    logger_instance._count_nodes = count_nodes
    logger_instance._count_connections = count_connections
    
    return logger_instance 