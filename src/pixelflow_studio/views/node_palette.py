"""
Node palette widget for PixelFlow Studio.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QLineEdit, QFrame, QPushButton
)

from ..core.application import Application


class NodePaletteWidget(QWidget):
    """
    Widget for displaying and selecting nodes to add to the graph.
    
    Features:
    - Clean minimal tree view of node categories
    - Advanced search functionality with category filtering
    - Node preview and description display
    - Modern dark theme styling
    - Double-click to add nodes
    """
    
    # Signals
    node_selected = Signal(str)  # node_class_name
    
    def __init__(self, app: Application):
        super().__init__()
        self.app = app
        
        self.setup_ui()
        self.populate_tree()
        self.setup_connections()
        
    def setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Search bar и кнопка управления категориями
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search nodes...")
        self.search_edit.setMaximumHeight(28)
        self.search_edit.setStyleSheet("""
            QLineEdit {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                padding: 6px 10px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #0078d4;
                background-color: #404040;
            }
        """)
        search_layout.addWidget(self.search_edit)
        
        # Кнопка для сворачивания/разворачивания всех категорий
        self.collapse_all_btn = QPushButton()
        self.collapse_all_btn.setMaximumSize(28, 28)
        self.collapse_all_btn.setMinimumSize(28, 28)
        self.collapse_all_btn.setToolTip("Collapse/Expand all categories")
        self.all_expanded = True  # Изначально все развернуто
        self.update_collapse_button()
        self.collapse_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                border-color: #0078d4;
                background-color: #404040;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
        """)
        search_layout.addWidget(self.collapse_all_btn)
        
        layout.addLayout(search_layout)
        
        # Node tree - современный минималистичный дизайн
        self.node_tree = QTreeWidget()
        self.node_tree.setHeaderHidden(True)
        self.node_tree.setAlternatingRowColors(False)  # Убираем полосы для чистоты
        self.node_tree.setRootIsDecorated(True)
        self.node_tree.setExpandsOnDoubleClick(True)
        self.node_tree.setIndentation(15)  # Меньший отступ для современности
        
        # Стильный дизайн для Tree View с четким разделением категорий и нод
        self.node_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #2b2b2b;
                border: 1px solid #555555;
                border-radius: 6px;
                color: #ffffff;
                outline: none;
                font-size: 14px;
                selection-background-color: #0078d4;
                padding: 4px;
            }
            QTreeWidget::item {
                height: 22px;
                border: none;
                padding-left: 6px;
                border-radius: 3px;
                margin: 1px;
            }
            QTreeWidget::item:hover {
                background-color: rgba(64, 64, 64, 0.7);
            }
            QTreeWidget::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QTreeWidget::branch {
                width: 20px;
                background-color: transparent;
            }
            QTreeWidget::branch:has-children:closed {
                border-image: none;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTYgNEwxMCA4TDYgMTJWNFoiIGZpbGw9IiNkZGRkZGQiLz4KPC9zdmc+);
            }
            QTreeWidget::branch:has-children:open {
                border-image: none;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQgNkw4IDEwTDEyIDZINFoiIGZpbGw9IiNkZGRkZGQiLz4KPC9zdmc+);
            }
        """)
        
        layout.addWidget(self.node_tree)
        
        # Node info
        self.node_info_label = QLabel("Select a node to see its description")
        self.node_info_label.setWordWrap(True)
        self.node_info_label.setMaximumHeight(80)
        self.node_info_label.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                border: 1px solid #404040;
                border-radius: 5px;
                padding: 5px;
                color: #cccccc;
            }
        """)
        layout.addWidget(self.node_info_label)
        
        # Кнопку "Add Selected Node" удалена - теперь достаточно двойного клика
        
    def update_collapse_button(self) -> None:
        """Update collapse button text based on current state."""
        if self.all_expanded:
            self.collapse_all_btn.setText("⌄")  # Down arrow when expanded
        else:
            self.collapse_all_btn.setText("›")  # Right arrow when collapsed
            
    def toggle_all_categories(self) -> None:
        """Toggle expand/collapse state for all categories."""
        self.all_expanded = not self.all_expanded
        self.update_collapse_button()
        
        # Применяем состояние ко всем категориям
        for i in range(self.node_tree.topLevelItemCount()):
            category_item = self.node_tree.topLevelItem(i)
            category_item.setExpanded(self.all_expanded)
        
    def setup_connections(self) -> None:
        """Setup signal connections."""
        self.search_edit.textChanged.connect(self.filter_nodes)
        self.collapse_all_btn.clicked.connect(self.toggle_all_categories)
        self.node_tree.itemClicked.connect(self.on_node_selected)
        self.node_tree.itemDoubleClicked.connect(self.on_node_double_clicked)
        
    def populate_tree(self) -> None:
        """Populate the node tree with available nodes."""
        self.node_tree.clear()
        
        # Get node categories
        categories = self.app.get_node_categories()
            
        # Create tree items with clean minimal styling
        for category, nodes in sorted(categories.items()):
            category_item = QTreeWidgetItem(self.node_tree)
            
            # Современный минималистичный текст для категории
            category_item.setText(0, category.title())  # Не КРИЧИМ заглавными
            category_item.setExpanded(True)
            
            # Современная иерархия - категории тише чем ноды
            category_font = QFont("Arial", 9, QFont.Normal)  # Меньше чем ноды
            category_item.setFont(0, category_font)
            
            # Приглушенный цвет для категорий
            from PySide6.QtGui import QColor, QBrush
            category_item.setForeground(0, QBrush(QColor("#808080")))  # Серый для категорий
            
            # Помечаем что это категория (не нода)
            category_item.setData(0, Qt.UserRole, None)
            
            for node_info in nodes:
                node_item = QTreeWidgetItem(category_item)
                node_item.setText(0, f"   {node_info['name']}")  # Минимальный отступ для принадлежности
                node_item.setData(0, Qt.UserRole, node_info['class'].__name__)
                node_item.setToolTip(0, node_info.get('description', ''))
                
                # Ноды - главный контент, делаем их заметными
                node_font = QFont("Arial", 10)  # Больше чем категории
                node_item.setFont(0, node_font)
                node_item.setForeground(0, QBrush(QColor("#ffffff")))  # Белый для нод - они важнее
                

    def filter_nodes(self) -> None:
        """Filter nodes based on search text."""
        search_text = self.search_edit.text().lower()
        
        # Filter tree view
        for i in range(self.node_tree.topLevelItemCount()):
            category_item = self.node_tree.topLevelItem(i)
            
            # Check if any nodes in category match search
            has_visible_nodes = False
            for j in range(category_item.childCount()):
                node_item = category_item.child(j)
                node_name = node_item.text(0).lower()
                node_visible = (search_text == "" or search_text in node_name)
                node_item.setHidden(not node_visible)
                if node_visible:
                    has_visible_nodes = True
                    
            category_item.setHidden(not has_visible_nodes)
            
    def on_node_selected(self, item) -> None:
        """Handle node selection."""
        node_class_name = item.data(0, Qt.UserRole)
        
        # Проверяем что это нода, а не категория
        if node_class_name is not None:
            # Update info label
            node_classes = self.app.node_classes
            if node_class_name in node_classes:
                node_info = node_classes[node_class_name]
                description = node_info.get('description', 'No description available')
                category = node_info.get('category', 'Unknown')
                
                info_text = f"<b>{node_info['name']}</b><br>"
                info_text += f"<i>Category: {category}</i><br>"
                info_text += f"{description}"
                
                self.node_info_label.setText(info_text)
                
            # Сохраняем выбранный класс ноды
            self.selected_node_class = node_class_name
        else:
            # Если выбрана категория, показываем информацию о категории
            category_name = item.text(0)
            self.node_info_label.setText(f"<b>{category_name} Category</b><br><i>Expand to see available nodes</i>")
            
    def on_node_double_clicked(self, item) -> None:
        """Handle node double click - directly add node."""
        node_class_name = item.data(0, Qt.UserRole)
        
        # Только для нод, не для категорий
        if node_class_name is not None:
            # Напрямую добавляем ноду без промежуточных шагов
            self.node_selected.emit(node_class_name)
            
    def get_selected_node_class(self) -> Optional[str]:
        """Get the currently selected node class name."""
        return getattr(self, 'selected_node_class', None) 