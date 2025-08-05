"""
Node properties editing widget.

Allows editing of node properties and input pin values.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from PySide6.QtWidgets import (
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, 
    QSlider, QHBoxLayout, QWidget, QComboBox, QPushButton
)
from PySide6.QtCore import Qt

from .base_property_widget import BasePropertyWidget
from ...core.types import PinType

if TYPE_CHECKING:
    from ...viewmodels.properties_viewmodel import NodeInfo


class NodePropertiesWidget(BasePropertyWidget):
    """
    Widget for editing node properties.
    
    Handles:
    - Input pin value editing
    - Node property editing
    - Variable type conversion (for Variable nodes)
    """
    
    def __init__(self, viewmodel):
        super().__init__(viewmodel, "Node Properties")
        self.current_node_info: NodeInfo | None = None
        self.property_widgets: dict = {}
    
    def on_node_info_changed(self, node_info: NodeInfo) -> None:
        """Called when node info changes."""
        self.current_node_info = node_info
        self.clear_content()
        self.populate_node_properties(node_info)
        self.show_widget()
    
    def populate_node_properties(self, node_info: NodeInfo) -> None:
        """Populate the widget with node properties."""
        if not self.current_node_info:
            return
            
        # Get the actual node from the graph
        node = self.viewmodel.app.graph.get_node(node_info.id)
        if not node:
            return
        
        # Create property editors for input pins
        property_count = 0
        for pin_name, pin in node.input_pins.items():
            try:
                if pin.info.pin_type != PinType.EXEC:  # Skip execution pins
                    if pin.info.pin_type in [PinType.FLOAT, PinType.INT, PinType.BOOL, PinType.STRING]:
                        editor = self.create_pin_editor(pin)
                        if editor:
                            self.form_layout.addRow(f"{pin_name}:", editor)
                            self.property_widgets[pin_name] = editor
                            property_count += 1
            except NameError:
                # Fallback if PinType is not available
                if hasattr(pin.info, 'pin_type') and pin.info.pin_type != 'exec':
                    editor = self.create_pin_editor(pin)
                    if editor:
                        self.form_layout.addRow(f"{pin_name}:", editor)
                        self.property_widgets[pin_name] = editor
                        property_count += 1
        
        # Show message if no editable properties
        if property_count == 0:
            no_props_label = QLabel("No editable properties")
            no_props_label.setStyleSheet("color: #888888; font-style: italic;")
            self.form_layout.addRow("", no_props_label)
    
    def create_pin_editor(self, pin) -> QWidget | None:
        """Create an editor widget for a pin."""
        pin_type = pin.info.pin_type
        
        try:
            if pin_type == PinType.BOOL:
                editor = QCheckBox()
                current_value = self.get_pin_current_value(pin)
                editor.setChecked(current_value if current_value is not None else False)
                editor.toggled.connect(
                    lambda checked: self.on_pin_value_changed(pin, checked)
                )
                return editor
                
            elif pin_type == PinType.INT:
                editor = QSpinBox()
                editor.setRange(-999999, 999999)
                current_value = self.get_pin_current_value(pin)
                editor.setValue(current_value if current_value is not None else 0)
                editor.valueChanged.connect(
                    lambda value: self.on_pin_value_changed(pin, value)
                )
                return editor
                
            elif pin_type == PinType.FLOAT:
                # Create container with spinbox and slider
                container = QWidget()
                layout = QHBoxLayout(container)
                layout.setContentsMargins(0, 0, 0, 0)
                
                # Determine range based on pin name
                pin_name = pin.info.name.lower()
                if 'brightness' in pin_name or 'contrast' in pin_name:
                    min_val, max_val, step = 0.0, 3.0, 0.1
                    default_val = 1.0
                else:
                    min_val, max_val, step = -100.0, 100.0, 1.0
                    default_val = 0.0
                
                # SpinBox
                spinbox = QDoubleSpinBox()
                spinbox.setRange(min_val, max_val)
                spinbox.setSingleStep(step)
                spinbox.setDecimals(2)
                current_value = self.get_pin_current_value(pin)
                spinbox.setValue(current_value if current_value is not None else default_val)
                spinbox.setMinimumWidth(80)
                
                # Slider for convenience
                slider = QSlider(Qt.Horizontal)
                slider.setRange(int(min_val * 100), int(max_val * 100))
                slider.setValue(
                    int((current_value if current_value is not None else default_val) * 100)
                )
                
                # Synchronize widgets
                def on_spinbox_changed(value):
                    slider.blockSignals(True)
                    slider.setValue(int(value * 100))
                    slider.blockSignals(False)
                    self.on_pin_value_changed(pin, value)
                
                def on_slider_changed(value):
                    float_value = value / 100.0
                    spinbox.blockSignals(True)
                    spinbox.setValue(float_value)
                    spinbox.blockSignals(False)
                    self.on_pin_value_changed(pin, float_value)
                
                spinbox.valueChanged.connect(on_spinbox_changed)
                slider.valueChanged.connect(on_slider_changed)
                
                layout.addWidget(spinbox)
                layout.addWidget(slider, 1)  # Stretch slider
                
                return container
                
            elif pin_type == PinType.STRING:
                editor = QLineEdit()
                current_value = self.get_pin_current_value(pin)
                editor.setText(str(current_value) if current_value is not None else "")
                editor.textChanged.connect(
                    lambda text: self.on_pin_value_changed(pin, text)
                )
                return editor
        except NameError:
            # Fallback if PinType is not available - use string comparison
            pin_type_str = str(pin_type).lower()
            if pin_type_str == 'bool':
                editor = QCheckBox()
                current_value = self.get_pin_current_value(pin)
                editor.setChecked(current_value if current_value is not None else False)
                editor.toggled.connect(
                    lambda checked: self.on_pin_value_changed(pin, checked)
                )
                return editor
            elif pin_type_str == 'int':
                editor = QSpinBox()
                editor.setRange(-999999, 999999)
                current_value = self.get_pin_current_value(pin)
                editor.setValue(current_value if current_value is not None else 0)
                editor.valueChanged.connect(
                    lambda value: self.on_pin_value_changed(pin, value)
                )
                return editor
            elif pin_type_str == 'float':
                # Simple float editor without slider for fallback
                editor = QDoubleSpinBox()
                editor.setRange(-100.0, 100.0)
                editor.setSingleStep(0.1)
                editor.setDecimals(2)
                current_value = self.get_pin_current_value(pin)
                editor.setValue(current_value if current_value is not None else 0.0)
                editor.valueChanged.connect(
                    lambda value: self.on_pin_value_changed(pin, value)
                )
                return editor
            elif pin_type_str == 'string':
                editor = QLineEdit()
                current_value = self.get_pin_current_value(pin)
                editor.setText(str(current_value) if current_value is not None else "")
                editor.textChanged.connect(
                    lambda text: self.on_pin_value_changed(pin, text)
                )
                return editor
        
        return None
    
    def get_pin_current_value(self, pin):
        """Get the current value of a pin."""
        if pin.is_input:
            return pin.info.default_value
        else:
            return pin._cached_value
    
    def on_pin_value_changed(self, pin, value) -> None:
        """Handle pin value changes."""
        try:
            # Update the pin value through ViewModel
            self.viewmodel.update_pin_value(
                self.current_node_info.id, 
                pin.info.id, 
                value
            )
        except Exception as e:
            self.viewmodel.handle_error(e, "updating pin value")
    
    def on_selection_cleared(self) -> None:
        """Called when selection is cleared."""
        self.current_node_info = None
        self.property_widgets.clear()
        super().on_selection_cleared() 