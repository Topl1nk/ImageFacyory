"""
Node information display widget.

Shows read-only information about the selected node.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from PySide6.QtWidgets import QLabel, QHBoxLayout, QWidget, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QClipboard

from .base_property_widget import BasePropertyWidget

if TYPE_CHECKING:
    from ...viewmodels.properties_viewmodel import NodeInfo


class NodeInfoWidget(BasePropertyWidget):
    """
    Widget for displaying node information.
    
    Shows:
    - Node name
    - Category
    - Description
    - Position
    - Node type
    - ID (with copy functionality)
    """
    
    def __init__(self, viewmodel):
        super().__init__(viewmodel, "Node Information")
        self.current_node_info: NodeInfo | None = None
    
    def on_node_info_changed(self, node_info: NodeInfo) -> None:
        """Called when node info changes."""
        self.current_node_info = node_info
        self.clear_content()
        self.populate_node_info(node_info)
        self.show_widget()
    
    def populate_node_info(self, node_info: NodeInfo) -> None:
        """Populate the widget with node information."""
        # Node name
        name_label = QLabel(node_info.name)
        name_label.setStyleSheet("font-weight: bold; color: #ffffff;")
        name_label.setWordWrap(True)
        self.form_layout.addRow("Name:", name_label)
        
        # Category
        if node_info.category and node_info.category != "Unknown":
            category_label = QLabel(node_info.category)
            category_label.setWordWrap(True)
            self.form_layout.addRow("Category:", category_label)
        
        # Description
        if node_info.description:
            desc_label = QLabel(node_info.description)
            desc_label.setWordWrap(True)
            desc_label.setMaximumHeight(60)
            self.form_layout.addRow("Description:", desc_label)
        
        # Position
        pos_label = QLabel(f"({node_info.position[0]:.1f}, {node_info.position[1]:.1f})")
        self.form_layout.addRow("Position:", pos_label)
        
        # Node type
        type_label = QLabel(node_info.node_type)
        self.form_layout.addRow("Type:", type_label)
        
        # Node ID with copy functionality
        id_container = self.create_id_widget(node_info.id)
        self.form_layout.addRow("ID:", id_container)
    
    def create_id_widget(self, node_id: str) -> QWidget:
        """Create widget for displaying and copying node ID."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Short ID display
        short_id = f"{node_id[:8]}..." if len(node_id) > 8 else node_id
        id_label = QLabel(short_id)
        id_label.setStyleSheet("font-family: monospace; color: #666666; font-size: 10px;")
        id_label.setToolTip(f"Полный ID: {node_id}")
        
        # Copy button
        copy_btn = QPushButton("📋")
        copy_btn.setFixedSize(20, 20)
        copy_btn.setToolTip("Копировать ID")
        copy_btn.setStyleSheet("""
            QPushButton {
                font-size: 10px;
                border: none;
                background: transparent;
                color: #888888;
            }
            QPushButton:hover {
                background-color: #404040;
                border-radius: 3px;
            }
        """)
        copy_btn.clicked.connect(lambda: self.copy_to_clipboard(node_id))
        
        layout.addWidget(id_label)
        layout.addWidget(copy_btn)
        layout.addStretch()
        
        return container
    
    def copy_to_clipboard(self, text: str) -> None:
        """Copy text to clipboard."""
        clipboard = QClipboard()
        clipboard.setText(text)
        
        # Show notification
        from PySide6.QtWidgets import QToolTip
        from PySide6.QtGui import QCursor
        QToolTip.showText(QCursor.pos(), "ID скопирован в буфер!")
    
    def on_selection_cleared(self) -> None:
        """Called when selection is cleared."""
        self.current_node_info = None
        super().on_selection_cleared() 