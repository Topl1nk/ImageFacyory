"""
Main Properties Panel - composite widget.

Combines all property widgets into a single panel.
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt

from .base_property_widget import BasePropertyWidget
from .node_info_widget import NodeInfoWidget
from .node_properties_widget import NodePropertiesWidget
from .pin_properties_widget import PinPropertiesWidget
from .variable_properties_widget import VariablePropertiesWidget

if TYPE_CHECKING:
    from ...viewmodels.properties_viewmodel import PropertiesViewModel
    from ...views.node_editor import NodeEditorView


class PropertiesPanel(QWidget):
    """
    Main Properties Panel - composite widget.
    
    Combines:
    - NodeInfoWidget
    - NodePropertiesWidget  
    - PinPropertiesWidget
    - VariablePropertiesWidget
    - Delete button
    """
    
    def __init__(self, viewmodel: PropertiesViewModel, node_editor: Optional[NodeEditorView] = None):
        super().__init__()
        self.viewmodel = viewmodel
        self.node_editor = node_editor
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        layout.addWidget(scroll_area)
        
        # Content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_layout.setSpacing(8)
        
        scroll_area.setWidget(self.content_widget)
        
        # Create property widgets
        self.node_info_widget = NodeInfoWidget(self.viewmodel)
        self.node_properties_widget = NodePropertiesWidget(self.viewmodel)
        self.pin_properties_widget = PinPropertiesWidget(self.viewmodel)
        self.variable_properties_widget = VariablePropertiesWidget(self.viewmodel)
        
        # Add widgets to layout
        self.content_layout.addWidget(self.node_info_widget)
        self.content_layout.addWidget(self.node_properties_widget)
        self.content_layout.addWidget(self.pin_properties_widget)
        self.content_layout.addWidget(self.variable_properties_widget)
        
        # Delete button
        self.delete_btn = QPushButton("Delete Node")
        self.delete_btn.clicked.connect(self.delete_current_node)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c12719;
            }
        """)
        self.content_layout.addWidget(self.delete_btn)
        
        # Add stretch to fill space
        self.content_layout.addStretch()
        
        # Initially hide all widgets
        self.hide_all_widgets()
    
    def setup_connections(self) -> None:
        """Setup signal connections."""
        # Connect ViewModel signals to show appropriate widgets
        self.viewmodel.node_info_changed.connect(self.on_node_selected)
        self.viewmodel.pin_info_changed.connect(self.on_pin_selected)
        self.viewmodel.selection_cleared.connect(self.on_selection_cleared)
        
        # Connect widget update signals
        self.node_info_widget.widget_updated.connect(self.on_widget_updated)
        self.node_properties_widget.widget_updated.connect(self.on_widget_updated)
        self.pin_properties_widget.widget_updated.connect(self.on_widget_updated)
        self.variable_properties_widget.widget_updated.connect(self.on_widget_updated)
    
    def on_node_selected(self, node_info) -> None:
        """Called when a node is selected."""
        # Show node-related widgets
        self.node_info_widget.show_widget()
        self.node_properties_widget.show_widget()
        
        # Hide other widgets
        self.pin_properties_widget.hide_widget()
        self.variable_properties_widget.hide_widget()
        
        # Show delete button
        self.delete_btn.show()
    
    def on_pin_selected(self, pin_info) -> None:
        """Called when a pin is selected."""
        # Show pin-related widgets
        self.pin_properties_widget.show_widget()
        
        # Hide other widgets
        self.node_info_widget.hide_widget()
        self.node_properties_widget.hide_widget()
        self.variable_properties_widget.hide_widget()
        
        # Hide delete button for pins
        self.delete_btn.hide()
    
    def on_selection_cleared(self) -> None:
        """Called when selection is cleared."""
        self.hide_all_widgets()
        self.show_no_selection_message()
    
    def hide_all_widgets(self) -> None:
        """Hide all property widgets."""
        self.node_info_widget.hide_widget()
        self.node_properties_widget.hide_widget()
        self.pin_properties_widget.hide_widget()
        self.variable_properties_widget.hide_widget()
        self.delete_btn.hide()
    
    def show_no_selection_message(self) -> None:
        """Show message when nothing is selected."""
        # Remove any existing "no selection" labels
        for i in reversed(range(self.content_layout.count())):
            child = self.content_layout.itemAt(i)
            if child.widget() and isinstance(child.widget(), QLabel):
                if child.widget().text() == "No node selected":
                    child.widget().deleteLater()
        
        # Add new "no selection" label
        no_selection_label = QLabel("No node selected")
        no_selection_label.setAlignment(Qt.AlignCenter)
        no_selection_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-style: italic;
                padding: 20px;
            }
        """)
        self.content_layout.addWidget(no_selection_label)
    
    def on_widget_updated(self) -> None:
        """Called when any widget is updated."""
        # Remove "no selection" message if widgets are shown
        for i in reversed(range(self.content_layout.count())):
            child = self.content_layout.itemAt(i)
            if child.widget() and isinstance(child.widget(), QLabel):
                if child.widget().text() == "No node selected":
                    child.widget().deleteLater()
    
    def delete_current_node(self) -> None:
        """Delete the currently selected node."""
        if not self.viewmodel.current_node_id:
            return
            
        reply = QMessageBox.question(
            self, "Delete Node",
            "Are you sure you want to delete this node?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                success = self.viewmodel.delete_node(self.viewmodel.current_node_id)
                if success and self.node_editor:
                    # Also remove from NodeEditor if available
                    self.node_editor.remove_node(self.viewmodel.current_node_id)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to delete node: {e}")
    
    def show_variable_properties(self, variable_data: dict) -> None:
        """Show variable properties for editing."""
        self.variable_properties_widget.show_variable_properties(variable_data)
        
        # Hide other widgets
        self.node_info_widget.hide_widget()
        self.node_properties_widget.hide_widget()
        self.pin_properties_widget.hide_widget()
        
        # Hide delete button for variables
        self.delete_btn.hide() 