"""
Node editor view for PixelFlow Studio.
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any
from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QTimer
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPainterPath,
    QMouseEvent, QWheelEvent, QKeyEvent, QDragEnterEvent,
    QDropEvent, QDragMoveEvent, QDragLeaveEvent
)
from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsRectItem,
    QGraphicsTextItem, QGraphicsEllipseItem, QGraphicsPathItem,
    QVBoxLayout, QWidget, QFrame, QLabel, QPushButton, QHBoxLayout,
    QMenu, QInputDialog, QMessageBox, QLineEdit, QCheckBox, QListWidget,
    QListWidgetItem, QWidgetAction
)
from PySide6.QtGui import QAction

from ..core.application import Application
from ..core.types import NodeID, PinID, Position, PinType
from ..core.safe_creation_manager import get_safe_creation_manager
from ..core.demo_system import get_demo_system, ActionType, ExpectedOutcome
from ..core.universal_logger import get_universal_logger
from .node_graphics import NodeGraphicsItem, PinGraphicsItem, ConnectionGraphicsItem


class NodeEditorView(QGraphicsView):
    """
    Node editor view for creating and editing node graphs.
    
    Features:
    - Visual node editing
    - Connection creation and management
    - Zoom and pan support
    - Selection management
    - Context menus
    """
    
    # Signals
    selection_changed = Signal()
    graph_changed = Signal()
    node_added = Signal(str, NodeID)  # class_name, node_id
    node_removed = Signal(NodeID)
    connection_created = Signal(NodeID, PinID, NodeID, PinID)
    connection_removed = Signal(NodeID, PinID, NodeID, PinID)
    
    # MVVM signals for PropertiesViewModel
    node_selected = Signal(str)  # node_id
    node_deselected = Signal()
    pin_selected = Signal(str)  # pin_id
    
    def __init__(self, app: Application):
        super().__init__()
        self.app = app
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # Инициализация демо системы
        self.demo_system = get_demo_system(app)
        
        # Инициализация тотального логгера
        self.universal_logger = get_universal_logger()
        self.universal_logger.log_system_state("node_editor_initialized", {
            "scene_rect": {"x": 0, "y": 0, "width": 0, "height": 0},
            "viewport_size": {"width": self.width(), "height": self.height()}
        })
        
        # View settings
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        # 🎨 Синяя зона выделения (профессиональный стиль)
        self.setStyleSheet("""
            QGraphicsView {
                selection-background-color: rgba(64, 128, 255, 80);
                outline: none;
            }
            QGraphicsView::item:selected {
                background-color: rgba(64, 128, 255, 80);
                border: 2px solid #4080FF;
            }
        """)
        
        # Zoom settings
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 3.0
        
        # Connection creation
        self.connection_start_pin: Optional[PinGraphicsItem] = None
        self.temp_connection: Optional[ConnectionGraphicsItem] = None
        
        # 🎮 Панорамирование на колесико мыши (как в профессиональных инструментах)
        self.is_panning = False
        self.last_pan_point = QPointF()
        
        # 📁 Поддержка Drag & Drop для создания Path нод
        self.setAcceptDrops(True)
        
        # Selection
        self.selected_nodes: List[NodeGraphicsItem] = []
        self.selected_connections: List[ConnectionGraphicsItem] = []
        
        # Undo/Redo
        self.undo_stack: List[Dict[str, Any]] = []
        self.redo_stack: List[Dict[str, Any]] = []
        self.max_undo_steps = 50
        
        # Grid
        self.grid_size = 20
        self.grid_color = QColor(50, 50, 50)
        self.grid_visible = True
        
        # Connection display settings
        self.use_curved_connections = True  # По умолчанию плавные кривые
        
        # Background
        self.background_color = QColor(30, 30, 30)
        
        self.setup_scene()
        self.setup_connections()
        
        # НЕ вызываем sync_with_graph здесь - он будет вызван автоматически при изменениях графа
        
    def toggle_connection_style(self) -> None:
        """Toggle between curved and straight connections."""
        self.use_curved_connections = not self.use_curved_connections
        
        # Обновляем все существующие соединения
        for item in self.scene.items():
            if isinstance(item, ConnectionGraphicsItem):
                item.update_path()
                
        print(f"Connection style: {'Curved' if self.use_curved_connections else 'Straight'}")
    
    def set_connection_style(self, use_curved: bool) -> None:
        """Set the connection style explicitly."""
        if self.use_curved_connections != use_curved:
            self.use_curved_connections = use_curved
            
            # Обновляем все существующие соединения
            for item in self.scene.items():
                if isinstance(item, ConnectionGraphicsItem):
                    item.update_path()
        
    def setup_scene(self) -> None:
        """Setup the graphics scene."""
        self.scene.setSceneRect(-2000, -2000, 4000, 4000)
        self.setBackgroundBrush(QBrush(self.background_color))
        
    def setup_connections(self) -> None:
        """Setup signal connections."""
        self.scene.selectionChanged.connect(self.on_selection_changed)
        
        # НЕ подключаем автоматическую синхронизацию - она вызывает дублирование
        # sync_with_graph будет вызываться ТОЛЬКО вручную когда это действительно нужно
        # if hasattr(self.app.graph, 'graph_changed'):
        #     self.app.graph.graph_changed.connect(self.sync_with_graph)
        
    def setBackgroundBrush(self, brush: QBrush) -> None:
        """Set the background brush."""
        super().setBackgroundBrush(brush)
        
    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        """Draw the background with grid."""
        super().drawBackground(painter, rect)
        
        if not self.grid_visible:
            return
            
        # Draw grid
        painter.setPen(QPen(self.grid_color, 1, Qt.SolidLine))
        
        left = int(rect.left()) - (int(rect.left()) % self.grid_size)
        top = int(rect.top()) - (int(rect.top()) % self.grid_size)
        
        # Draw vertical lines
        x = left
        while x < rect.right():
            painter.drawLine(x, rect.top(), x, rect.bottom())
            x += self.grid_size
            
        # Draw horizontal lines
        y = top
        while y < rect.bottom():
            painter.drawLine(rect.left(), y, rect.right(), y)
            y += self.grid_size
            
    def add_node(self, node_class_name: str, position: Optional[Position] = None) -> Optional[NodeID]:
        """Add a new node to the editor using safe creation manager."""
        # ПАРАНОИК ЛОГИРОВАНИЕ - записываем сразу в начале
        self.universal_logger.log_system_state("add_node_started", {
            "class_name": node_class_name,
            "position_provided": position is not None,
            "position": {"x": position.x, "y": position.y} if position else None
        })
        
        try:
            # Set position
            self.universal_logger.log_system_state("step_1_check_position", {"position_is_none": position is None})
            
            if position is None:
                # Place at center of view
                center = self.mapToScene(self.viewport().rect().center())
                position = Position(x=int(center.x()), y=int(center.y()))
                self.universal_logger.log_system_state("step_1b_created_center_position", {
                    "center": {"x": center.x(), "y": center.y()},
                    "position": {"x": position.x, "y": position.y}
                })
            
            # Request safe creation
            self.universal_logger.log_system_state("step_2_getting_creation_manager", {})
            creation_manager = get_safe_creation_manager()
            
            self.universal_logger.log_system_state("step_3_requesting_creation", {
                "class_name": node_class_name,
                "position": {"x": position.x, "y": position.y}
            })
            request = creation_manager.request_node_creation(node_class_name, position)
            
            if request is None:
                # Duplicate request blocked
                return None
            
            # Begin processing
            if not creation_manager.begin_processing(request):
                # Request is no longer valid
                return None
            
            try:
                # Create node in the graph
                self.universal_logger.log_system_state("node_creation_step_1", {
                    "step": "creating_node_instance",
                    "class": node_class_name,
                    "position": {"x": position.x, "y": position.y}
                })
                
                node = self.app.create_node(node_class_name)
                
                self.universal_logger.log_system_state("node_creation_step_2", {
                    "step": "setting_position",
                    "node_id": node.id,
                    "position": {"x": position.x, "y": position.y}
                })
                
                node.position = position
                
                self.universal_logger.log_system_state("node_creation_step_3", {
                    "step": "adding_to_graph",
                    "node_id": node.id
                })
                
                self.app.graph.add_node(node)
                
                # Get node ID from the node itself
                node_id = node.id
                
                # Mark creation as completed
                creation_manager.complete_processing(request, node_id)
                
                # Записать действие в демо систему
                if self.demo_system:
                    self.demo_system.record_action(
                        ActionType.NODE_CREATE,
                        {
                            "class_name": node_class_name,
                            "position": {"x": position.x, "y": position.y},
                            "node_id": node_id
                        },
                        ExpectedOutcome.SUCCESS,
                        {"expected_nodes_created": 1}
                    )
                
                # ДОБАВЛЯЕМ ТОЛЬКО новую ноду без пересоздания всех
                self.add_single_node_graphics(node)
                
                # Emit signal
                self.node_added.emit(node_class_name, node_id)
                self.graph_changed.emit()
                
                # Add to undo stack
                self.add_undo_action({
                    'type': 'add_node',
                    'node_id': node_id,
                    'node_class': node_class_name,
                    'position': position
                })
                
                # Логируем создание ноды
                self.universal_logger.log_node_created(
                    node_id, node_class_name, position.x, position.y,
                    {
                        "input_pins": len(node.input_pins),
                        "output_pins": len(node.output_pins),
                        "node_name": node.name,
                        "category": node.category
                    }
                )
                
                return node_id
                
            except Exception as e:
                # Mark creation as failed
                creation_manager.fail_processing(request, str(e))
                raise e
            
        except Exception as e:
            # Логируем ошибку создания ноды БЕЗ диалога
            self.universal_logger.log_error(
                f"Failed to add node: {e}",
                "node_creation_error",
                {
                    "node_class": node_class_name,
                    "position": {"x": position.x if position else None, "y": position.y if position else None},
                    "error_type": type(e).__name__,
                    "full_traceback": str(e.__traceback__)
                }
            )
            # НЕ показываем диалог - просто логируем и возвращаем None
            import traceback
            print(f"ОШИБКА СОЗДАНИЯ НОДЫ: {e}")
            traceback.print_exc()
            return None
            
    def remove_node(self, node_id: NodeID) -> None:
        """Remove a node from the editor."""
        try:
            # Находим объект ноды по node_id
            node = self.app.graph.get_node(node_id)
            if not node:
                raise ValueError(f"Node with ID {node_id} not found")
            
            # СНАЧАЛА удаляем все графические соединения связанные с этой нодой
            connections_to_remove = []
            for item in self.scene.items():
                if isinstance(item, ConnectionGraphicsItem):
                    # Проверяем, связано ли соединение с удаляемой нодой
                    start_node_id = item.start_pin.node_id if item.start_pin else None
                    end_node_id = item.end_pin.node_id if item.end_pin else None
                    
                    if start_node_id == node_id or end_node_id == node_id:
                        connections_to_remove.append(item)
            
            # Удаляем графические соединения из сцены
            for connection_item in connections_to_remove:
                self.scene.removeItem(connection_item)
            
            # Remove from graph (передаем объект ноды, а не ID) - это также удалит соединения на уровне графа
            self.app.graph.remove_node(node)
            
            # Remove graphics item
            for item in self.scene.items():
                if isinstance(item, NodeGraphicsItem) and item.node_id == node_id:
                    self.scene.removeItem(item)
                    break
                    
            # Emit signal
            self.node_removed.emit(node_id)
            self.graph_changed.emit()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to remove node: {e}")
            
    def create_connection(self, start_pin: PinGraphicsItem, end_pin: PinGraphicsItem) -> bool:
        """Create a connection between two pins."""
        try:
            # Validate connection
            if not start_pin.pin_type.is_compatible_with(end_pin.pin_type):
                QMessageBox.warning(self, "Error", "Incompatible pin types")
                return False
                
            if start_pin.is_output == end_pin.is_output:
                QMessageBox.warning(self, "Error", "Cannot connect pins of same direction")
                return False
                
            # Determine input and output pins
            if start_pin.is_output:
                output_pin = start_pin
                input_pin = end_pin
            else:
                output_pin = end_pin
                input_pin = start_pin
                
            # Get pin objects
            output_pin_obj = self.app.graph.get_pin(output_pin.pin_id)
            input_pin_obj = self.app.graph.get_pin(input_pin.pin_id)
            
            if not output_pin_obj or not input_pin_obj:
                QMessageBox.warning(self, "Error", "Pin objects not found")
                return False
            
            from loguru import logger
            logger.info(f"🎨 GUI: Professional workflow - connecting {output_pin_obj.name} -> {input_pin_obj.name}")
            
            # PROFESSIONAL WORKFLOW: Auto-remove existing connections (GUI + Logic)
            connections_to_remove = []
            
            # Find existing output connections
            if not output_pin_obj.info.is_multiple and len(output_pin_obj.connections) > 0:
                logger.info(f"🔄 GUI: Output pin '{output_pin_obj.name}' has existing connections - will auto-remove")
                for conn_id in list(output_pin_obj.connections):
                    connections_to_remove.append(conn_id)
            
            # Find existing input connections  
            if not input_pin_obj.info.is_multiple and len(input_pin_obj.connections) > 0:
                logger.info(f"🔄 GUI: Input pin '{input_pin_obj.name}' has existing connections - will auto-remove")
                for conn_id in list(input_pin_obj.connections):
                    connections_to_remove.append(conn_id)
            
            # Remove old connections (both graphics and logic)
            for conn_id in connections_to_remove:
                logger.info(f"🗑️ GUI: Auto-removing old connection: {conn_id}")
                self.remove_connection(conn_id)  # This removes both graphics and logic
                logger.info(f"✅ GUI: Auto-removed old connection successfully")
                
            # Create connection in graph (should not have conflicts now)
            logger.info(f"🆕 GUI: Creating new connection in graph")
            connection = self.app.graph.connect_pins(output_pin_obj, input_pin_obj)
            
            # Записать действие в демо систему
            if self.demo_system:
                self.demo_system.record_action(
                    ActionType.CONNECTION_CREATE,
                    {
                        "output_node_id": output_pin.node_id,
                        "output_pin_name": output_pin_obj.info.name,
                        "input_node_id": input_pin.node_id,
                        "input_pin_name": input_pin_obj.info.name,
                        "connection_id": connection.id
                    },
                    ExpectedOutcome.SUCCESS,
                    {"expected_connections_created": 1}
                )
            
            # Create graphics connection
            logger.info(f"🎨 GUI: Creating graphics connection")
            connection_graphics = ConnectionGraphicsItem(
                output_pin, input_pin, connection.id, self
            )
            self.scene.addItem(connection_graphics)
            
            # Update pin states to connected
            self._update_pin_connection_state(output_pin_obj)
            self._update_pin_connection_state(input_pin_obj)
            
            # Emit signal
            self.connection_created.emit(
                output_pin.node_id, output_pin.pin_id,
                input_pin.node_id, input_pin.pin_id
            )
            self.graph_changed.emit()
            
            logger.info(f"🎉 GUI: Professional workflow completed successfully!")
            return True
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to create connection: {e}")
            return False
            
    def remove_connection(self, connection_id: str) -> None:
        """Remove a connection from the editor."""
        try:
            # Find the connection object by ID
            connection = self.app.graph.get_connection(connection_id)
            if connection is None:
                raise ValueError(f"Connection with ID {connection_id} not found")
            
            # Store pin info before removing connection
            output_pin = connection.output_pin
            input_pin = connection.input_pin
            
            # Remove from graph (pass the connection object, not just ID)
            self.app.graph.remove_connection(connection)
            
            # Update pin states - check if they still have other connections
            self._update_pin_connection_state(output_pin)
            self._update_pin_connection_state(input_pin)
            
            # Remove graphics item
            for item in self.scene.items():
                if isinstance(item, ConnectionGraphicsItem) and item.connection_id == connection_id:
                    self.scene.removeItem(item)
                    break
                    
            # Emit signal
            self.graph_changed.emit()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to remove connection: {e}")
            
    def _update_pin_connection_state(self, pin) -> None:
        """Update the visual state of a pin based on its connection status."""
        try:
            # Check if the pin still has any connections
            has_connections = len(pin.connections) > 0
            
            # Find the corresponding graphics pin and update its state
            for item in self.scene.items():
                if isinstance(item, NodeGraphicsItem):
                    # Check input pins
                    for pin_graphics in item.input_pins:
                        if hasattr(pin_graphics, 'pin') and pin_graphics.pin == pin:
                            pin_graphics.set_connected(has_connections)
                            break
                    # Check output pins  
                    for pin_graphics in item.output_pins:
                        if hasattr(pin_graphics, 'pin') and pin_graphics.pin == pin:
                            pin_graphics.set_connected(has_connections)
                            break
        except Exception as e:
            print(f"Error updating pin connection state: {e}")
            
    # Mouse events
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press events."""
        # Логируем КАЖДЫЙ клик мыши
        button_name = "left" if event.button() == Qt.LeftButton else "right" if event.button() == Qt.RightButton else "middle"
        self.universal_logger.log_mouse_click(
            event.pos().x(), event.pos().y(), button_name,
            [mod.name for mod in Qt.KeyboardModifier if event.modifiers() & mod]
        )
        
        # Проверяем на что кликнули
        item = self.itemAt(event.pos())
        scene_pos = self.mapToScene(event.pos())
        
        if item:
            item_type = type(item).__name__
            item_id = getattr(item, 'node_id', None) or getattr(item, 'pin_id', None) or str(id(item))
            self.universal_logger.log_system_state("item_clicked", {
                "item_type": item_type,
                "item_id": item_id,
                "click_coordinates": {"x": event.pos().x(), "y": event.pos().y()},
                "scene_coordinates": {"x": scene_pos.x(), "y": scene_pos.y()}
            })
        
        if event.button() == Qt.LeftButton:
            # Check if clicking on a pin
            if isinstance(item, PinGraphicsItem):
                self.universal_logger.log_pin_interaction(
                    item.pin_id, item.pin_type.name, item.node_id, "click_start_connection",
                    event.pos().x(), event.pos().y()
                )
                self.start_connection_creation(item)
            else:
                # ОЧИСТКА ВЫДЕЛЕНИЯ при клике на пустое место (как в рабочем коде)
                if not item:  # Клик на пустое место
                    self.scene.clearSelection()
                    self.universal_logger.log_system_state("selection_cleared", {
                        "reason": "click_on_empty_space",
                        "click_coordinates": {"x": event.pos().x(), "y": event.pos().y()}
                    })
                     
                # Start selection
                super().mousePressEvent(event)
        elif event.button() == Qt.MiddleButton:
            # 🎮 Панорамирование на колесико мыши (как в Unreal Engine, Blender)
            self.is_panning = True
            self.last_pan_point = QPointF(event.pos())
            self.setCursor(Qt.ClosedHandCursor)  # Курсор руки при панорамировании
            self.universal_logger.log_system_state("panning_started", {
                "start_coordinates": {"x": event.pos().x(), "y": event.pos().y()}
            })
        elif event.button() == Qt.RightButton:
            self.universal_logger.log_menu_interaction("context_menu", "open", None, event.pos().x(), event.pos().y())
            self.show_context_menu(event.pos())
        else:
            super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move events."""
        if self.is_panning:
            # 🎮 Панорамирование: сдвигаем сцену плавно
            current_point = QPointF(event.pos())
            delta = current_point - self.last_pan_point
            
            # Панорамирование через scroll bars для плавности
            h_scroll = self.horizontalScrollBar()
            v_scroll = self.verticalScrollBar()
            
            h_scroll.setValue(h_scroll.value() - int(delta.x()))
            v_scroll.setValue(v_scroll.value() - int(delta.y()))
            
            self.last_pan_point = current_point
            
        elif self.connection_start_pin and self.temp_connection:
            # Update temporary connection
            scene_pos = self.mapToScene(event.pos())
            self.temp_connection.update_end_point(scene_pos)
        else:
            super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release events."""
        if event.button() == Qt.LeftButton and self.connection_start_pin:
            # Finish connection creation - ПРОСТАЯ И НАДЕЖНАЯ логика
            target_pin = None
            
            # Метод 1: Прямой поиск через itemAt
            item = self.itemAt(event.pos())
            print(f"🔍 itemAt найден: {type(item).__name__ if item else 'None'}")
            if (isinstance(item, PinGraphicsItem) or hasattr(item, 'pin_id')) and item != self.connection_start_pin:
                target_pin = item
                print(f"✅ Найден целевой пин через itemAt: {target_pin.pin.name}")
            
            # Метод 2: Если не найден, ищем в небольшой области (для точности)
            if not target_pin:
                scene_pos = self.mapToScene(event.pos())
                # Ищем в области 10x10 пикселей вокруг позиции мыши
                rect = QRectF(scene_pos.x() - 5, scene_pos.y() - 5, 10, 10)
                items = self.scene.items(rect)
                print(f"🔍 В области найдено {len(items)} элементов:")
                
                for i, item in enumerate(items):
                    print(f"  [{i}] {type(item).__name__}")
                    if (isinstance(item, PinGraphicsItem) or hasattr(item, 'pin_id')) and item != self.connection_start_pin:
                        target_pin = item
                        print(f"✅ Найден целевой пин через область: {target_pin.pin.name}")
                        break
            
            if target_pin:
                print(f"🔗 Создаем соединение к пину: {target_pin.pin.name}")
                # Найден целевой пин - создаем соединение
                self.finish_connection_creation(target_pin)
            else:
                print("❌ Пин не найден - показываем меню")
                # Отпустили в пустом месте - показываем умное меню создания нод
                self.show_context_menu(event.pos(), start_pin=self.connection_start_pin)
        elif event.button() == Qt.MiddleButton and self.is_panning:
            # 🎮 Завершение панорамирования
            self.is_panning = False
            self.setCursor(Qt.ArrowCursor)  # Возвращаем обычный курсор
            self.universal_logger.log_system_state("panning_ended", {
                "end_coordinates": {"x": event.pos().x(), "y": event.pos().y()}
            })
        else:
            super().mouseReleaseEvent(event)
            
    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle wheel events for zooming and panning."""
        delta = event.angleDelta().y()
        mouse_pos = event.position().toPoint()
        
        # Логируем КАЖДОЕ движение колеса
        if event.modifiers() == Qt.ShiftModifier:
            # Horizontal scrolling with Shift
            old_value = self.horizontalScrollBar().value()
            new_value = old_value - delta
            self.horizontalScrollBar().setValue(new_value)
            self.universal_logger.log_system_state("canvas_pan_horizontal", {
                "delta": delta,
                "old_scroll": old_value,
                "new_scroll": new_value,
                "mouse_coordinates": {"x": mouse_pos.x(), "y": mouse_pos.y()}
            })
        elif event.modifiers() == Qt.ControlModifier:
            # Vertical scrolling with Ctrl
            old_value = self.verticalScrollBar().value()
            new_value = old_value - delta
            self.verticalScrollBar().setValue(new_value)
            self.universal_logger.log_system_state("canvas_pan_vertical", {
                "delta": delta,
                "old_scroll": old_value,
                "new_scroll": new_value,
                "mouse_coordinates": {"x": mouse_pos.x(), "y": mouse_pos.y()}
            })
        else:
            # DEFAULT: Zoom with plain mouse wheel (как в Unreal Engine)
            old_zoom = self.zoom_factor
            zoom_factor = 1.15 if delta > 0 else 1.0 / 1.15
            
            # Apply zoom
            if (delta > 0 and self.zoom_factor < self.max_zoom) or \
               (delta < 0 and self.zoom_factor > self.min_zoom):
                self.zoom_factor *= zoom_factor
                self.zoom_factor = max(self.min_zoom, min(self.max_zoom, self.zoom_factor))
                
                # Set transform to zoom at cursor position
                self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
                self.setTransform(self.transform().scale(zoom_factor, zoom_factor))
                self.setTransformationAnchor(QGraphicsView.AnchorViewCenter)
                
                # Логируем зум
                self.universal_logger.log_canvas_zoom(
                    old_zoom, self.zoom_factor, mouse_pos.x(), mouse_pos.y()
                )
            
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events."""
        if event.key() == Qt.Key_Delete:
            self.delete_selected()
        elif event.key() == Qt.Key_A and event.modifiers() == Qt.ControlModifier:
            self.select_all()
        elif event.key() == Qt.Key_Z and event.modifiers() == Qt.ControlModifier:
            if event.modifiers() == Qt.ShiftModifier:
                self.redo()
            else:
                self.undo()
        elif event.key() == Qt.Key_F and event.modifiers() == Qt.ControlModifier:
            self.zoom_to_fit()
        elif event.key() == Qt.Key_0 and event.modifiers() == Qt.ControlModifier:
            self.reset_zoom()
        elif event.key() == Qt.Key_Plus and event.modifiers() == Qt.ControlModifier:
            self.zoom_in()
        elif event.key() == Qt.Key_Minus and event.modifiers() == Qt.ControlModifier:
            self.zoom_out()
        elif event.key() == Qt.Key_Space and event.modifiers() == Qt.ControlModifier:
            # Toggle pan mode
            self.setDragMode(QGraphicsView.ScrollHandDrag if self.dragMode() == QGraphicsView.RubberBandDrag else QGraphicsView.RubberBandDrag)
        elif event.key() == Qt.Key_L:
            # Toggle connection style (L for Lines)
            self.toggle_connection_style()
        else:
            super().keyPressEvent(event)
            
    # Connection creation
    def start_connection_creation(self, pin: PinGraphicsItem) -> None:
        """Start creating a connection from a pin."""
        self.connection_start_pin = pin
        
        # Создаем временное соединение
        self.temp_connection = ConnectionGraphicsItem(
            pin, None, None, self, is_temporary=True
        )
        
        # Добавляем в сцену
        self.scene.addItem(self.temp_connection)
        
        # Устанавливаем высокий Z-value чтобы соединение было поверх всего
        self.temp_connection.setZValue(100)
        
    def finish_connection_creation(self, end_pin: PinGraphicsItem) -> None:
        """Finish creating a connection."""
        if self.connection_start_pin and self.temp_connection:
            success = self.create_connection(self.connection_start_pin, end_pin)
            if success:
                # Remove temporary connection SAFELY
                if self.temp_connection and self.temp_connection.scene():
                    self.scene.removeItem(self.temp_connection)
                self.temp_connection = None
                
        self.cancel_connection_creation()
        
    def cancel_connection_creation(self) -> None:
        """Cancel connection creation."""
        if self.temp_connection and self.temp_connection.scene():
            self.scene.removeItem(self.temp_connection)
        self.temp_connection = None
        self.connection_start_pin = None
        
    # Context menu
    def show_context_menu(self, pos: QPoint, start_pin=None) -> None:
        """Show context menu at position. Universal for right-click and connection creation."""
        scene_pos = self.mapToScene(pos)
        item = self.scene.itemAt(scene_pos, self.transform()) if not start_pin else None
        
        menu = QMenu(self)
        
        if isinstance(item, NodeGraphicsItem):
            # Node context menu
            delete_action = QAction("🗑️ Delete Node", menu)
            delete_action.triggered.connect(lambda: self.remove_node(item.node_id))
            menu.addAction(delete_action)
            
            menu.addSeparator()
            
            execute_action = QAction("▶️ Execute Node", menu)
            execute_action.triggered.connect(lambda: self.execute_node(item.node_id))
            menu.addAction(execute_action)
            
        elif isinstance(item, ConnectionGraphicsItem):
            # Connection context menu
            delete_action = QAction("🗑️ Delete Connection", menu)
            delete_action.triggered.connect(lambda: self.remove_connection(item.connection_id))
            menu.addAction(delete_action)
            
        else:
            # Empty space context menu ИЛИ создание соединения
            # ЕДИНОЕ МЕНЮ для всех случаев
            search_widget = self.create_node_menu(scene_pos, start_pin=start_pin)
            search_action = QWidgetAction(menu)
            search_action.setDefaultWidget(search_widget)
            menu.addAction(search_action)
                    
        if menu.actions():
            menu.exec(self.mapToGlobal(pos))
            
        # Если это было создание соединения и меню закрылось - отменяем соединение
        if start_pin:
            self.cancel_connection_creation()
            
    def show_connection_context_menu(self, connection: 'ConnectionGraphicsItem', screen_pos: QPoint) -> None:
        """Show context menu for connections."""
        menu = QMenu(self)
        
        delete_action = QAction("🗑️ Delete Connection", menu)
        delete_action.triggered.connect(lambda: self.remove_connection(connection.connection_id))
        menu.addAction(delete_action)
        
        menu.exec(screen_pos)
            
    # Selection
    def on_selection_changed(self) -> None:
        """Handle selection changes."""
        self.selected_nodes = []
        self.selected_connections = []
        
        for item in self.scene.selectedItems():
            if isinstance(item, NodeGraphicsItem):
                self.selected_nodes.append(item)
            elif isinstance(item, ConnectionGraphicsItem):
                self.selected_connections.append(item)
        
        # Emit MVVM signals for PropertiesViewModel
        if self.selected_nodes:
            # Выбираем первую ноду для отображения в Properties
            first_node = self.selected_nodes[0]
            self.node_selected.emit(first_node.node.id)
        else:
            # Нет выбранных нод - очищаем выбор
            self.node_deselected.emit()
                
        self.selection_changed.emit()
        
    def select_all(self) -> None:
        """Select all items."""
        for item in self.scene.items():
            if isinstance(item, (NodeGraphicsItem, ConnectionGraphicsItem)):
                item.setSelected(True)
                
    def delete_selected(self) -> None:
        """Delete selected items."""
        # Delete connections first
        for connection in self.selected_connections:
            self.remove_connection(connection.connection_id)
            
        # Delete nodes
        for node in self.selected_nodes:
            self.remove_node(node.node.id)  # Передаем node_id, а не объект graphics item
            
    # Zoom
    def zoom_in(self) -> None:
        """Zoom in."""
        if self.zoom_factor < self.max_zoom:
            self.zoom_factor *= 1.2
            self.zoom_factor = min(self.zoom_factor, self.max_zoom)
            self.setTransform(self.transform().scale(1.2, 1.2))
            
    def zoom_out(self) -> None:
        """Zoom out."""
        if self.zoom_factor > self.min_zoom:
            self.zoom_factor /= 1.2
            self.zoom_factor = max(self.zoom_factor, self.min_zoom)
            self.setTransform(self.transform().scale(1/1.2, 1/1.2))
            
    def zoom_to_fit(self) -> None:
        """Fit all items to view."""
        if self.scene.items():
            self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
            self.zoom_factor = 1.0
            
    def zoom_to_selection(self) -> None:
        """Zoom to selected items."""
        selected_items = self.scene.selectedItems()
        if selected_items:
            # Calculate bounding rect of selected items
            selection_rect = QRectF()
            for item in selected_items:
                selection_rect = selection_rect.united(item.sceneBoundingRect())
            
            # Add some padding
            selection_rect.adjust(-50, -50, 50, 50)
            self.fitInView(selection_rect, Qt.KeepAspectRatio)
            
    def reset_zoom(self) -> None:
        """Reset zoom to 100%."""
        self.zoom_factor = 1.0
        self.resetTransform()
            
    # Undo/Redo
    def add_undo_action(self, action: Dict[str, Any]) -> None:
        """Add action to undo stack."""
        self.undo_stack.append(action)
        if len(self.undo_stack) > self.max_undo_steps:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
        
    def undo(self) -> None:
        """Undo last action."""
        if not self.undo_stack:
            return
            
        action = self.undo_stack.pop()
        self.redo_stack.append(action)
        
        if action['type'] == 'add_node':
            self.remove_node(action['node_id'])
        # Add more undo types as needed
        
    def redo(self) -> None:
        """Redo last undone action."""
        if not self.redo_stack:
            return
            
        action = self.redo_stack.pop()
        self.undo_stack.append(action)
        
        if action['type'] == 'add_node':
            self.add_node(action['node_class'], action['position'])
        # Add more redo types as needed
        
    # Execution
    def execute_node(self, node_id: NodeID) -> None:
        """Execute a specific node."""
        try:
            node = self.app.graph.get_node(node_id)
            if node:
                import asyncio
                asyncio.create_task(node.execute())
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to execute node: {e}")
            
    def execute_selected(self) -> None:
        """Execute selected nodes."""
        for node in self.selected_nodes:
                            self.execute_node(node.id)
            
    def add_single_node_graphics(self, node) -> None:
        """Добавляет ТОЛЬКО одну новую ноду без пересоздания всех."""
        # Проверяем что эта нода еще не добавлена
        existing_items = [item for item in self.scene.items() if isinstance(item, NodeGraphicsItem)]
        for item in existing_items:
            if item.node_id == node.id:
                self.universal_logger.log_system_state("node_graphics_already_exists", {
                    "node_id": node.id,
                    "skipping_creation": True
                })
                return  # Нода уже существует
        
        # Создаем графический элемент ТОЛЬКО для новой ноды
        node_graphics = NodeGraphicsItem(node, self)
        node_graphics.setPos(int(node.position.x), int(node.position.y))
        self.scene.addItem(node_graphics)
        
        self.universal_logger.log_system_state("single_node_graphics_created", {
            "node_id": node.id,
            "position": {"x": node.position.x, "y": node.position.y},
            "class_name": type(node).__name__
        })
    
    def refresh_graphics(self) -> None:
        """Refresh all graphics after loading a project."""
        # Clear all existing graphics
        for item in list(self.scene.items()):
            if isinstance(item, (NodeGraphicsItem, ConnectionGraphicsItem)):
                self.scene.removeItem(item)
        
        # Create graphics for all nodes in graph
        for node in self.app.graph.nodes:
            self.add_single_node_graphics(node)
        
        # Create graphics for all connections
        for connection in self.app.graph._connections.values():
            # Find the graphics pins
            output_pin_graphics = self._find_pin_graphics(connection.output_pin)
            input_pin_graphics = self._find_pin_graphics(connection.input_pin)
            
            if output_pin_graphics and input_pin_graphics:
                connection_graphics = ConnectionGraphicsItem(
                    output_pin_graphics, input_pin_graphics, connection.id, self
                )
                self.scene.addItem(connection_graphics)
        
        self.universal_logger.log_system_state("graphics_refreshed", {
            "nodes": len(self.app.graph.nodes),
            "connections": len(self.app.graph._connections)
        })
    
    def _find_pin_graphics(self, pin):
        """Find graphics pin for a given logical pin."""
        for item in self.scene.items():
            if isinstance(item, NodeGraphicsItem) and item.node_id == pin.node.id:
                # Check input pins
                for pin_graphics in item.input_pins:
                    if hasattr(pin_graphics, 'pin') and pin_graphics.pin == pin:
                        return pin_graphics
                # Check output pins
                for pin_graphics in item.output_pins:
                    if hasattr(pin_graphics, 'pin') and pin_graphics.pin == pin:
                        return pin_graphics
        return None
        
    def sync_with_graph(self) -> None:
        """Synchronize the scene with the application graph."""
        # Notify creation manager that UI sync is starting
        creation_manager = get_safe_creation_manager()
        creation_manager.set_ui_sync_state(True)
        
        try:
            # Get existing node graphics items by node_id
            existing_node_graphics = {}
            existing_items = [item for item in self.scene.items() if isinstance(item, NodeGraphicsItem)]
            for item in existing_items:
                existing_node_graphics[item.node_id] = item
            
            # Track which nodes should exist
            graph_node_ids = {node.id for node in self.app.graph.nodes}
            existing_node_ids = set(existing_node_graphics.keys())
            
            # Remove graphics for nodes that no longer exist in graph
            nodes_to_remove = existing_node_ids - graph_node_ids
            for node_id in nodes_to_remove:
                graphics_item = existing_node_graphics[node_id]
                self.scene.removeItem(graphics_item)
                self.universal_logger.log_system_state("node_graphics_removed", {
                    "node_id": node_id,
                    "reason": "node_deleted_from_graph"
                })
            
            # Add or update nodes from the graph
            for node in self.app.graph.nodes:
                if node.id in existing_node_graphics:
                    # Update existing node position
                    graphics_item = existing_node_graphics[node.id]
                    graphics_item.setPos(int(node.position.x), int(node.position.y))
                    self.universal_logger.log_system_state("node_graphics_updated", {
                        "node_id": node.id,
                        "new_position": {"x": node.position.x, "y": node.position.y}
                    })
                else:
                    # Create new graphics item for new node
                    node_graphics = NodeGraphicsItem(node, self)
                    node_graphics.setPos(int(node.position.x), int(node.position.y))
                    self.scene.addItem(node_graphics)
                    self.universal_logger.log_system_state("node_graphics_created", {
                        "node_id": node.id,
                        "position": {"x": node.position.x, "y": node.position.y},
                        "class_name": type(node).__name__
                    })
                    
            # Clear existing connection graphics
            existing_connections = [item for item in self.scene.items() if isinstance(item, ConnectionGraphicsItem)]
            for item in existing_connections:
                self.scene.removeItem(item)
            
            # Add connections from the graph
            for connection in self.app.graph.connections:
                # Find the corresponding pin graphics items
                start_pin_graphics = self.find_pin_graphics_item(connection.info.output_pin_id)
                end_pin_graphics = self.find_pin_graphics_item(connection.info.input_pin_id)
                
                if start_pin_graphics and end_pin_graphics:
                    connection_graphics = ConnectionGraphicsItem(
                        start_pin_graphics, end_pin_graphics, connection.id, self
                    )
                    self.scene.addItem(connection_graphics)
        finally:
            # Notify creation manager that UI sync is finished
            creation_manager.set_ui_sync_state(False)
                
    def find_pin_graphics_item(self, pin_id: str) -> Optional[PinGraphicsItem]:
        """Find a pin graphics item by pin ID."""
        for item in self.scene.items():
            if isinstance(item, NodeGraphicsItem):
                for pin in item.input_pins + item.output_pins:
                    if pin.pin.id == pin_id:
                        return pin
        return None
    
    def find_pin_graphics_for_node_pin(self, node, pin) -> Optional[PinGraphicsItem]:
        """Find pin graphics item for a specific node pin."""
        for item in self.scene.items():
            if isinstance(item, NodeGraphicsItem) and item.node_id == node.id:
                for pin_graphics in item.input_pins + item.output_pins:
                    if pin_graphics.pin.id == pin.id:
                        return pin_graphics
        return None 

    def create_node_menu(self, scene_pos: QPointF, start_pin=None) -> QWidget:
        """Создает ЕДИНОЕ меню выбора нод - АБСОЛЮТНО одинаковое для всех случаев."""
        # Create search widget
        search_widget = QWidget()
        search_layout = QVBoxLayout(search_widget)
        search_layout.setContentsMargins(5, 5, 5, 5)
        
        # УБИРАЮ info_label - теперь меню выглядят ОДИНАКОВО
        
        # Search input
        search_input = QLineEdit()
        search_input.setPlaceholderText("Search nodes...")
        search_input.setMinimumWidth(200)
        search_layout.addWidget(search_input)
        
        # Filter checkbox - ОДИНАКОВЫЙ текст для всех случаев
        filter_checkbox = QCheckBox("Show contextual nodes only")
        if start_pin:
            # При создании соединения фильтр включен по умолчанию
            filter_checkbox.setChecked(True)
        search_layout.addWidget(filter_checkbox)
        
        # Node list
        node_list = QListWidget()
        node_list.setMaximumHeight(300)
        search_layout.addWidget(node_list)
        
        # Функция для получения нод с учетом фильтрации
        def get_nodes_to_show(apply_filter=False):
            categories = self.app.get_node_categories()
            nodes_to_show = []
            
            if apply_filter and start_pin:
                # Умная фильтрация для совместимых нод (только при создании соединения И включенном фильтре)
                for category, nodes in categories.items():
                    for node_info in nodes:
                        try:
                            temp_node = node_info['class']()
                            has_compatible_pin = False
                            
                            pins_to_check = temp_node.input_pins.values() if start_pin.is_output else temp_node.output_pins.values()
                            
                            for pin in pins_to_check:
                                if start_pin.pin_type.is_compatible_with(pin.info.pin_type):
                                    has_compatible_pin = True
                                    break
                            
                            if has_compatible_pin:
                                nodes_to_show.append({
                                    'name': node_info['name'],
                                    'class': node_info['class'],
                                    'category': category,
                                    'description': getattr(node_info['class'], '__doc__', ''),
                                    'temp_node': temp_node
                                })
                        except Exception:
                            continue
            else:
                # Все ноды (если нет start_pin или фильтр отключен)
                for category, nodes in categories.items():
                    for node_info in nodes:
                        nodes_to_show.append({
                            'name': node_info['name'],
                            'class': node_info['class'],
                            'category': category,
                            'description': getattr(node_info['class'], '__doc__', '')
                        })
            
            return nodes_to_show
        
        # Sort by category, then by name
        def sort_nodes(nodes_list):
            return sorted(nodes_list, key=lambda x: (x['category'], x['name']))
        
        # Populate list with category headers
        def populate_list():
            # Get nodes based on filter state
            nodes_to_show = get_nodes_to_show(filter_checkbox.isChecked())
            
            # Clear existing items
            node_list.clear()
            
            # Add category headers
            current_category = None
            for node_info in sort_nodes(nodes_to_show):
                if node_info['category'] != current_category:
                    current_category = node_info['category']
                    # Category header - ОДИНАКОВАЯ иконка для всех случаев
                    header_item = QListWidgetItem(f"📁 {current_category}")
                    header_item.setBackground(QColor(60, 60, 65))
                    header_item.setForeground(QColor(200, 200, 200))
                    header_item.setFlags(header_item.flags() & ~Qt.ItemIsSelectable)
                    node_list.addItem(header_item)
                
                # Node item - ОДИНАКОВАЯ иконка для всех случаев  
                item = QListWidgetItem(f"  {node_info['name']}")
                item.setData(Qt.UserRole, node_info)
                item.setToolTip(node_info['description'])
                node_list.addItem(item)
            
            # Если нет нод - ОДИНАКОВЫЙ текст
            if not nodes_to_show:
                no_nodes_item = QListWidgetItem("❌ No nodes found")
                no_nodes_item.setFlags(no_nodes_item.flags() & ~Qt.ItemIsSelectable)
                node_list.addItem(no_nodes_item)
        
        # Initial population
        populate_list()
        
        # Search functionality
        def filter_nodes():
            search_text = search_input.text().lower()
            
            if not search_text:
                # Если поиск пустой, показываем всё что есть в списке 
                for i in range(node_list.count()):
                    node_list.item(i).setHidden(False)
                return
            
            # Hide all items first
            for i in range(node_list.count()):
                node_list.item(i).setHidden(True)
            
            # Show matching items and their categories
            visible_categories = set()
            for i in range(node_list.count()):
                item = node_list.item(i)
                node_info = item.data(Qt.UserRole)
                
                if node_info:  # This is a node item (not category header)
                    matches_search = (search_text in node_info['name'].lower() or 
                                    search_text in node_info['category'].lower() or
                                    search_text in node_info.get('description', '').lower())
                    
                    if matches_search:
                        item.setHidden(False)
                        visible_categories.add(node_info['category'])
            
            # Show category headers for visible categories
            for i in range(node_list.count()):
                item = node_list.item(i)
                if not item.data(Qt.UserRole):  # This is a category header
                    category_name = item.text().replace("📁 ", "").replace("🔌 ", "")
                    if category_name in visible_categories:
                        item.setHidden(False)
        
        search_input.textChanged.connect(filter_nodes)
        filter_checkbox.toggled.connect(populate_list) # Re-populate when filter changes
        
        # Функция создания ноды
        def create_node_action():
            current_item = node_list.currentItem()
            if current_item and current_item.data(Qt.UserRole):
                node_info = current_item.data(Qt.UserRole)
                
                # Create new node
                node_id = self.add_node(node_info['class'].__name__, Position(int(scene_pos.x()), int(scene_pos.y())))
                
                # If this is smart creation, connect to the pin
                if start_pin and node_id:
                    new_node = self.app.graph.get_node(node_id)
                    if new_node:
                        pins_to_check = new_node.input_pins.values() if start_pin.is_output else new_node.output_pins.values()
                        
                        for pin in pins_to_check:
                            if start_pin.pin_type.is_compatible_with(pin.info.pin_type):
                                try:
                                    if start_pin.is_output:
                                        start_pin_obj = self.app.graph.get_pin(start_pin.pin_id)
                                        end_pin_obj = pin
                                    else:
                                        start_pin_obj = pin
                                        end_pin_obj = self.app.graph.get_pin(start_pin.pin_id)
                                    
                                    connection = self.app.graph.connect_pins(start_pin_obj, end_pin_obj)
                                    
                                    # Создаем графическое соединение
                                    start_pin_graphics = self.connection_start_pin
                                    end_pin_graphics = self.find_pin_graphics_for_node_pin(new_node, pin)
                                    
                                    if end_pin_graphics:
                                        connection_graphics = ConnectionGraphicsItem(
                                            start_pin_graphics, end_pin_graphics, connection.id, self
                                        )
                                        self.scene.addItem(connection_graphics)
                                except Exception as e:
                                    print(f"Failed to create connection: {e}")
                                break
                
                return True
            return False
        
        # ОБЫЧНЫЙ КЛИК вместо двойного (как просил пользователь)
        def on_item_clicked(item):
            if item and item.data(Qt.UserRole):  # Only for node items, not headers
                if create_node_action():
                    # Закрываем меню через parent
                    search_widget.parent().close() if search_widget.parent() else None
        
        node_list.itemClicked.connect(on_item_clicked)
        
        return search_widget
    
    # 📁 Drag & Drop Support для создания Path нод
    
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter events for file/folder drops."""
        if event.mimeData().hasUrls():
            # Проверяем что есть хотя бы один файл или папка
            urls = event.mimeData().urls()
            if any(url.isLocalFile() for url in urls):
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        """Handle drag move events."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        """Handle drag leave events."""
        event.accept()
    
    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop events to create Path variable nodes."""
        if not event.mimeData().hasUrls():
            event.ignore()
            return
            
        # Получаем позицию в сцене
        scene_pos = self.mapToScene(event.pos())
        
        try:
            # Обрабатываем каждый файл/папку
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    
                    # Создаем PathVariableNode
                    path_node_id = self.add_node("PathVariableNode", Position(scene_pos.x(), scene_pos.y()))
                    
                    if path_node_id:
                        # Устанавливаем путь в ноду
                        node = self.app.graph.get_node(path_node_id)
                        if node and hasattr(node, 'set_path'):
                            node.set_path(file_path)
                            
                        # Сдвигаем позицию для следующей ноды
                        scene_pos.setY(scene_pos.y() + 100)
                        
                        # Логируем действие
                        self.universal_logger.log_action_with_coordinates(
                            "file_drop", "dropped", 
                            event.pos().x(), event.pos().y(),
                            {"file_path": file_path, "node_id": str(path_node_id)}
                        )
            
            event.acceptProposedAction()
            
        except Exception as e:
            print(f"Error handling drop event: {e}")
            event.ignore() 