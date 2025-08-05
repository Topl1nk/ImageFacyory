"""
Base class for all property widgets.

Provides common functionality and interface for property editing widgets.
"""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QFormLayout, QSizePolicy
from PySide6.QtCore import Signal, Qt

if TYPE_CHECKING:
    from ...viewmodels.properties_viewmodel import PropertiesViewModel


class BasePropertyWidget(QWidget):
    """
    Base class for all property editing widgets.
    
    Provides:
    - Common layout structure
    - Signal handling
    - ViewModel integration
    - Styling consistency
    """
    
    # Сигналы для уведомления об изменениях
    property_changed = Signal(str, object)  # property_name, new_value
    widget_updated = Signal()
    
    def __init__(self, viewmodel: PropertiesViewModel, title: str = ""):
        super().__init__()
        self.viewmodel = viewmodel
        self.title = title
        
        self.setup_ui()
        self.setup_connections()
        self.apply_styling()
    
    def setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Main group box
        self.group_box = QGroupBox(self.title)
        self.group_box.setSizePolicy(
            QSizePolicy.Expanding, 
            QSizePolicy.Preferred
        )
        layout.addWidget(self.group_box)
        
        # Form layout for properties
        self.form_layout = QFormLayout(self.group_box)
        self.form_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
        )
        self.form_layout.setHorizontalSpacing(5)
        self.form_layout.setVerticalSpacing(5)
        self.form_layout.setContentsMargins(10, 15, 10, 10)
    
    def setup_connections(self) -> None:
        """Setup signal connections."""
        # Подключаемся к сигналам ViewModel
        self.viewmodel.node_info_changed.connect(self.on_node_info_changed)
        self.viewmodel.pin_info_changed.connect(self.on_pin_info_changed)
        self.viewmodel.selection_cleared.connect(self.on_selection_cleared)
    
    def apply_styling(self) -> None:
        """Apply consistent styling."""
        self.group_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
    
    def show_widget(self) -> None:
        """Show this widget."""
        self.show()
        self.widget_updated.emit()
    
    def hide_widget(self) -> None:
        """Hide this widget."""
        self.hide()
    
    def clear_content(self) -> None:
        """Clear all content from the widget."""
        # Очищаем все виджеты из form_layout
        while self.form_layout.count():
            child = self.form_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def update_title(self, title: str) -> None:
        """Update the widget title."""
        self.title = title
        self.group_box.setTitle(title)
    
    # Виртуальные методы для переопределения в наследниках
    def on_node_info_changed(self, node_info) -> None:
        """Called when node info changes."""
        pass
    
    def on_pin_info_changed(self, pin_info) -> None:
        """Called when pin info changes."""
        pass
    
    def on_selection_cleared(self) -> None:
        """Called when selection is cleared."""
        self.clear_content()
        self.hide_widget()
    
    def refresh_content(self) -> None:
        """Refresh the widget content."""
        pass 