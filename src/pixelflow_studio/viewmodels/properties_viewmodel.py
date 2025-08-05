"""
ViewModel for Properties Panel - отделяет бизнес-логику от UI.
"""

from __future__ import annotations

from typing import Optional, Any, TYPE_CHECKING
from dataclasses import dataclass
from PySide6.QtCore import Signal, Property

from .base_viewmodel import BaseViewModel

if TYPE_CHECKING:
    from ..core.application import Application


@dataclass
class NodeInfo:
    """Информация о ноде для отображения."""
    id: str
    name: str
    category: str
    description: str
    position: tuple[float, float]
    node_type: str


@dataclass
class PinInfo:
    """Информация о пине для отображения."""
    id: str
    name: str
    pin_type: str
    direction: str
    value: Any
    connections_count: int


class PropertiesViewModel(BaseViewModel):
    """
    ViewModel для Properties Panel.
    
    Отвечает за:
    - Управление состоянием выделения
    - Бизнес-логику обновления свойств
    - Координацию между различными панелями
    """
    
    # Сигналы для уведомления UI об изменениях
    node_info_changed = Signal(NodeInfo)
    pin_info_changed = Signal(PinInfo)
    variable_updated = Signal(str, str, object)  # var_id, property, value
    selection_cleared = Signal()
    
    def __init__(self, app: Application):
        super().__init__(app, "properties")
        self._current_node_id: Optional[str] = None
        self._current_pin_id: Optional[str] = None
        
        # Подключаемся к событиям графа
        self.app.graph.node_added.connect(self._on_node_added)
        self.app.graph.node_removed.connect(self._on_node_removed)
        self.app.graph.connection_added.connect(self._on_connection_changed)
        self.app.graph.connection_removed.connect(self._on_connection_changed)
    
    # Properties для QML/Qt binding
    @Property(str, notify=node_info_changed)
    def current_node_id(self) -> str:
        return self._current_node_id or ""
    
    @Property(str, notify=pin_info_changed)
    def current_pin_id(self) -> str:
        return self._current_pin_id or ""
    
    def select_node(self, node_id: str) -> None:
        """Выбирает ноду для отображения свойств."""
        if node_id == self._current_node_id:
            return
            
        self._current_node_id = node_id
        self._current_pin_id = None
        
        if node_id:
            node = self.app.graph.get_node(node_id)
            if node:
                node_info = self._create_node_info(node)
                self.node_info_changed.emit(node_info)
        else:
            self.selection_cleared.emit()
    
    def select_pin(self, node_id: str, pin_id: str) -> None:
        """Выбирает пин для отображения свойств."""
        self._current_node_id = node_id
        self._current_pin_id = pin_id
        
        if node_id and pin_id:
            node = self.app.graph.get_node(node_id)
            if node:
                pin = self._find_pin(node, pin_id)
                if pin:
                    pin_info = self._create_pin_info(pin)
                    self.pin_info_changed.emit(pin_info)
    
    def select_pin_by_id(self, pin_id: str) -> None:
        """Выбирает пин по его ID (находит ноду автоматически)."""
        # Ищем пин во всех нодах
        for node in self.app.graph.nodes:
            pin = self._find_pin(node, pin_id)
            if pin:
                self.select_pin(node.id, pin_id)
                return
        
        # Если пин не найден, очищаем выбор
        self.clear_selection()
    
    def clear_selection(self) -> None:
        """Очистить текущий выбор."""
        self._current_node_id = None
        self._current_pin_id = None
        self.selection_cleared.emit()
    
    def update_node_property(
        self, node_id: str, property_name: str, value: Any
    ) -> None:
        """Обновляет свойство ноды."""
        try:
            node = self.app.graph.get_node(node_id)
            if node and hasattr(node, property_name):
                setattr(node, property_name, value)
                # Уведомляем об изменении графа
                self.app.graph.graph_changed.emit()
        except Exception as e:
            # Логируем ошибку
            self.handle_error(e, f"updating node property {property_name}")
    
    def update_pin_value(self, node_id: str, pin_id: str, value: Any) -> None:
        """Обновляет значение пина."""
        try:
            node = self.app.graph.get_node(node_id)
            if node:
                pin = self._find_pin(node, pin_id)
                if pin:
                    if pin.is_input:
                        pin.info.default_value = value
                    else:
                        pin._cached_value = value
                    # Уведомляем об изменении графа
                    self.app.graph.graph_changed.emit()
        except Exception as e:
            self.handle_error(e, f"updating pin value {pin_id}")
    
    def update_variable(self, var_id: str, property_name: str, value: Any) -> None:
        """Обновляет переменную."""
        try:
            # Делегируем обновление переменной в VariablesManager
            if hasattr(self.app, 'variables_manager'):
                self.app.variables_manager.update_variable(var_id, property_name, value)
                self.variable_updated.emit(var_id, property_name, value)
        except Exception as e:
            self.handle_error(e, f"updating variable {var_id}")
    
    def delete_node(self, node_id: str) -> bool:
        """Удаляет ноду."""
        try:
            success = self.app.graph.remove_node(node_id)
            if success:
                self._current_node_id = None
                self._current_pin_id = None
                self.selection_cleared.emit()
            return success
        except Exception as e:
            self.handle_error(e, f"deleting node {node_id}")
            return False
    
    def _create_node_info(self, node) -> NodeInfo:
        """Создает NodeInfo из ноды."""
        return NodeInfo(
            id=node.id,
            name=node.name,
            category=getattr(node, 'category', 'Unknown'),
            description=getattr(node, 'description', ''),
            position=(node.position.x, node.position.y) if hasattr(node, 'position') else (0, 0),
            node_type=node.__class__.__name__
        )
    
    def _create_pin_info(self, pin) -> PinInfo:
        """Создает PinInfo из пина."""
        return PinInfo(
            id=pin.info.id,
            name=pin.info.name,
            pin_type=pin.info.pin_type.value,
            direction="Output" if pin.is_output else "Input",
            value=pin.info.default_value if pin.is_input else pin._cached_value,
            connections_count=len(pin.connections) if hasattr(pin, 'connections') else 0
        )
    
    def _find_pin(self, node, pin_id: str):
        """Находит пин по ID."""
        for pin in node.input_pins.values():
            if pin.info.id == pin_id:
                return pin
        for pin in node.output_pins.values():
            if pin.info.id == pin_id:
                return pin
        return None
    
    def _on_node_added(self, node_id: str) -> None:
        """Обработчик добавления ноды."""
        pass  # Можно добавить логику если нужно
    
    def _on_node_removed(self, node_id: str) -> None:
        """Обработчик удаления ноды."""
        if node_id == self._current_node_id:
            self.selection_cleared.emit()
    
    def _on_connection_changed(self, node_id: str, pin_id: str) -> None:
        """Обработчик изменения соединений."""
        if node_id == self._current_node_id and pin_id == self._current_pin_id:
            # Обновляем информацию о пине
            node = self.app.graph.get_node(node_id)
            if node:
                pin = self._find_pin(node, pin_id)
                if pin:
                    pin_info = self._create_pin_info(pin)
                    self.pin_info_changed.emit(pin_info)
    
    def _initialize(self) -> None:
        """Initialize the ViewModel-specific functionality."""
        # PropertiesViewModel doesn't need additional initialization
        # beyond what's done in __init__
        pass 