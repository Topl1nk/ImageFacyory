"""
Pin properties widget.

Displays and allows editing of pin properties.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from PySide6.QtWidgets import QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox

from .base_property_widget import BasePropertyWidget

if TYPE_CHECKING:
    from ...viewmodels.properties_viewmodel import PinInfo


class PinPropertiesWidget(BasePropertyWidget):
    """
    Widget for displaying and editing pin properties.
    
    Shows:
    - Pin name
    - Pin type
    - Direction
    - Value (for input pins)
    - Connections count
    """
    
    def __init__(self, viewmodel):
        super().__init__(viewmodel, "Pin Properties")
        self.current_pin_info: PinInfo | None = None
    
    def on_pin_info_changed(self, pin_info: PinInfo) -> None:
        """Called when pin info changes."""
        self.current_pin_info = pin_info
        self.clear_content()
        self.populate_pin_info(pin_info)
        self.show_widget()
    
    def populate_pin_info(self, pin_info: PinInfo) -> None:
        """Populate the widget with pin information."""
        # Pin name
        name_label = QLabel(pin_info.name)
        name_label.setStyleSheet("font-weight: bold; color: #ffffff;")
        self.form_layout.addRow("Name:", name_label)
        
        # Pin type
        type_label = QLabel(pin_info.pin_type)
        self.form_layout.addRow("Type:", type_label)
        
        # Pin direction
        direction_label = QLabel(pin_info.direction)
        self.form_layout.addRow("Direction:", direction_label)
        
        # Pin ID
        id_label = QLabel(pin_info.id)
        id_label.setStyleSheet("font-family: monospace; color: #888888;")
        self.form_layout.addRow("ID:", id_label)
        
        # Pin value (for input pins)
        if pin_info.direction == "Input":
            value_widget = self.create_value_editor(pin_info)
            if value_widget:
                self.form_layout.addRow("Value:", value_widget)
        
        # Connections
        if pin_info.connections_count > 0:
            connections_label = QLabel(f"{pin_info.connections_count} connection(s)")
            self.form_layout.addRow("Connections:", connections_label)
        else:
            connections_label = QLabel("No connections")
            connections_label.setStyleSheet("color: #888888; font-style: italic;")
            self.form_layout.addRow("Connections:", connections_label)
    
    def create_value_editor(self, pin_info: PinInfo) -> QWidget | None:
        """Create an editor widget for pin value."""
        pin_type = pin_info.pin_type
        current_value = pin_info.value
        
        if pin_type == "BOOL":
            editor = QCheckBox()
            editor.setChecked(current_value if current_value is not None else False)
            editor.toggled.connect(
                lambda checked: self.on_pin_value_changed(pin_info.id, checked)
            )
            return editor
            
        elif pin_type == "INT":
            editor = QSpinBox()
            editor.setRange(-999999, 999999)
            editor.setValue(current_value if current_value is not None else 0)
            editor.valueChanged.connect(
                lambda value: self.on_pin_value_changed(pin_info.id, value)
            )
            return editor
            
        elif pin_type == "FLOAT":
            editor = QDoubleSpinBox()
            editor.setRange(-999999.0, 999999.0)
            editor.setDecimals(3)
            editor.setValue(current_value if current_value is not None else 0.0)
            editor.valueChanged.connect(
                lambda value: self.on_pin_value_changed(pin_info.id, value)
            )
            return editor
            
        elif pin_type == "STRING":
            editor = QLineEdit()
            editor.setText(str(current_value) if current_value is not None else "")
            editor.textChanged.connect(
                lambda text: self.on_pin_value_changed(pin_info.id, text)
            )
            return editor
        
        return None
    
    def on_pin_value_changed(self, pin_id: str, value) -> None:
        """Handle pin value changes."""
        try:
            if self.current_pin_info:
                # Update the pin value through ViewModel
                self.viewmodel.update_pin_value(
                    self.current_pin_info.id.split('_')[0],  # Extract node_id
                    pin_id,
                    value
                )
        except Exception as e:
            self.viewmodel.handle_error(e, "updating pin value")
    
    def on_selection_cleared(self) -> None:
        """Called when selection is cleared."""
        self.current_pin_info = None
        super().on_selection_cleared() 