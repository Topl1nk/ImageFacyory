"""
Variables Panel - список переменных как в Unreal Engine.
Показывает все Variable ноды в проекте и позволяет создавать новые.
"""

from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .node_editor import NodeEditorView
    from ..core.application import Application
    from ..core.node import Node

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QListWidget, QListWidgetItem, QMessageBox,
    QSizePolicy, QHeaderView
)
from PySide6.QtGui import QFont, QColor

from ..core.types import Position, PinType


class VariablesPanel(QWidget):
    """
    Panel для отображения и управления переменными как в Unreal Engine.
    
    Features:
    - Список всех Variable нод в проекте
    - Кнопка + для создания новых переменных  
    - Выбор переменной для настройки в Properties Panel
    - Автообновление при изменениях в графе
    """
    
    # Signal для уведомления о выборе переменной
    variable_selected = Signal(str)  # node_id
    
    def __init__(self, app: 'Application', node_editor: Optional['NodeEditorView'] = None, parent=None):
        super().__init__(parent)
        self.app = app
        self.node_editor = node_editor
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self) -> None:
        """Setup the user interface."""
        
        # Применяем темную тему в стиле Unreal Engine
        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                color: white;
            }
            QLabel {
                color: white;
                font-weight: bold;
            }
            QListWidget {
                border: 1px solid #555;
                border-radius: 4px;
                background-color: #383838;
                color: white;
                alternate-background-color: #404040;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #555;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #4a4a4a;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QComboBox {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                background-color: #404040;
                color: white;
                min-height: 20px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid white;
                margin-right: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Убираем дублирующий заголовок - он уже есть в QDockWidget
        
        # Простая кнопка + (без dropdown - тип настраивается в Properties!)
        self.add_button = QPushButton("+ Add Variable")
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.add_button.setToolTip("Add new variable (type configured in Properties)")
        layout.addWidget(self.add_button)
        
        # Список переменных
        self.variables_list = QListWidget()
        self.variables_list.setAlternatingRowColors(True)
        self.variables_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.variables_list)
        
        # Инициализируем список переменных
        self.variables_list_data = []
        self.refresh_variables_list()
        
    def setup_connections(self) -> None:
        """Setup signal connections."""
        self.add_button.clicked.connect(self.add_variable)
        self.variables_list.itemClicked.connect(self.on_variable_selected)
        self.variables_list.itemDoubleClicked.connect(self.on_variable_double_clicked)
        
        # Подключаемся к изменениям в графе
        if self.app and self.app.graph:
            # Можно добавить signals из graph для автообновления
            pass
    
    def auto_refresh_variables(self) -> None:
        """Автоматически обновляет список переменных."""
        self.refresh_variables_list()
    
    def add_variable(self) -> None:
        """Создает новую переменную только в списке (НЕ на сцене!)."""
        try:
            # Генерируем простое имя
            if not hasattr(self, 'variables_list_data'):
                self.variables_list_data = []
            existing_count = len(self.variables_list_data) + 1
            variable_name = f"Variable_{existing_count}"
            
            # Создаем данные переменной (НЕ ноду!)
            variable_data = {
                'id': f"var_{existing_count}_{hash(variable_name)}",
                'name': variable_name,
                'type': 'Float',  # По умолчанию Float
                'value': 0.0,
                'description': f"Variable {existing_count}"
            }
            
            # Добавляем в список данных
            self.variables_list_data.append(variable_data)
            
            # Обновляем UI список
            self.refresh_variables_list()
            
            # Автоматически выбираем созданную переменную
            self.select_variable_by_id(variable_data['id'])
            
            # Показываем уведомление
            from PySide6.QtWidgets import QToolTip
            from PySide6.QtGui import QCursor
            QToolTip.showText(QCursor.pos(), f"✅ {variable_name} created! Configure in Properties.")
                
        except Exception as e:
            # Показываем ошибку
            QMessageBox.warning(self, "Error", f"Failed to create variable:\n{str(e)}")
    
    # Удален метод get_variable_nodes - больше не используется
    
    def refresh_variables_list(self) -> None:
        """Обновляет список переменных из внутренних данных."""
        self.variables_list.clear()
        
        if not hasattr(self, 'variables_list_data'):
            self.variables_list_data = []
            return
        
        # Определяем цвета для типов (убираем тупые иконки!)
        type_colors = {
            'Float': '#4CAF50',      # Зеленый
            'Integer': '#2196F3',    # Синий
            'Boolean': '#FF9800',    # Оранжевый
            'String': '#9C27B0',     # Фиолетовый
            'Path': '#795548'        # Коричневый
        }
        
        for var_data in self.variables_list_data:
            # Получаем цвет для типа
            color = type_colors.get(var_data['type'], '#4CAF50')
            
            # Создаем элемент списка БЕЗ тупых иконок
            item_text = f"{var_data['name']} • {var_data['type']}"
            item = QListWidgetItem(item_text)
            
            # Устанавливаем цвет вместо иконки
            item.setBackground(QColor(color))
            item.setForeground(QColor('white'))
            
            # Сохраняем ID переменной
            item.setData(Qt.UserRole, var_data['id'])
            
            # Устанавливаем шрифт
            font = QFont()
            font.setPointSize(10)
            font.setBold(True)
            item.setFont(font)
            
            self.variables_list.addItem(item)
    
    def on_variable_selected(self, item: QListWidgetItem) -> None:
        """Обрабатывает выбор переменной."""
        if item:
            var_id = item.data(Qt.UserRole)
            self.select_variable_by_id(var_id)
    
    def on_variable_double_clicked(self, item: QListWidgetItem) -> None:
        """Обрабатывает двойной клик по переменной - добавляет на сцену."""
        if item:
            var_id = item.data(Qt.UserRole)
            self.add_variable_to_scene(var_id)
    
    def add_variable_to_scene(self, var_id: str) -> None:
        """Добавляет переменную на сцену как ноду."""
        # Находим данные переменной
        var_data = self.get_variable_by_id(var_id)
        if not var_data:
            return
        
        # Определяем класс ноды по типу переменной
        type_to_node_class = {
            'Float': 'FloatVariableNode',
            'Integer': 'IntegerVariableNode', 
            'Boolean': 'BooleanVariableNode',
            'String': 'StringVariableNode',
            'Path': 'PathVariableNode'
        }
        
        node_class_name = type_to_node_class.get(var_data['type'], 'FloatVariableNode')
        
        # Создаем ноду на сцене
        if self.node_editor:
            # Получаем позицию в центре видимой области
            center_pos = self.node_editor.mapToScene(
                self.node_editor.viewport().rect().center()
            )
            
            # Создаем ноду через node_editor
            position = Position(int(center_pos.x()), int(center_pos.y()))
            node_id = self.node_editor.add_node(node_class_name, position)
            
            # Настраиваем имя и значение ноды
            if node_id:
                node = self.app.graph.get_node(node_id)
                if node:
                    node.name = var_data['name']
                    # Устанавливаем значение по умолчанию
                    if hasattr(node, 'value'):
                        node.value = var_data['value']
                    
                    # Показываем уведомление
                    from PySide6.QtWidgets import QToolTip
                    from PySide6.QtGui import QCursor
                    QToolTip.showText(QCursor.pos(), f"✅ {var_data['name']} added to scene!")
    
    def select_variable_by_id(self, var_id: str) -> None:
        """Выбирает переменную по ID и показывает в Properties."""
        if var_id:
            # Находим данные переменной
            selected_var = None
            for var_data in self.variables_list_data:
                if var_data['id'] == var_id:
                    selected_var = var_data
                    break
            
            if selected_var:
                # Уведомляем о выборе переменной
                self.variable_selected.emit(var_id)
                
                # Уведомляем Properties Panel о выборе переменной
                main_window = self.parent()
                while main_window and not hasattr(main_window, 'properties_panel'):
                    main_window = main_window.parent()
                if main_window and hasattr(main_window, 'properties_panel'):
                    main_window.properties_panel.show_variable_properties(selected_var)
    
    def get_variable_by_id(self, var_id: str) -> dict:
        """Получает данные переменной по ID."""
        for var_data in self.variables_list_data:
            if var_data['id'] == var_id:
                return var_data
        return None