"""
Variable properties widget.

Allows editing of variable properties and values.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Any
from PySide6.QtWidgets import (
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, 
    QComboBox, QPushButton, QHBoxLayout, QWidget
)

from .base_property_widget import BasePropertyWidget

if TYPE_CHECKING:
    from ...viewmodels.properties_viewmodel import PropertiesViewModel


class VariablePropertiesWidget(BasePropertyWidget):
    """
    Widget for editing variable properties.
    
    Handles:
    - Variable name editing
    - Variable type selection
    - Variable value editing
    - Variable description
    """
    
    def __init__(self, viewmodel: PropertiesViewModel):
        super().__init__(viewmodel, "Variable Properties")
        self.current_variable_data: Dict[str, Any] | None = None
    
    def show_variable_properties(self, variable_data: Dict[str, Any]) -> None:
        """Show variable properties for editing."""
        self.current_variable_data = variable_data
        self.clear_content()
        self.populate_variable_properties(variable_data)
        self.show_widget()
    
    def populate_variable_properties(self, variable_data: Dict[str, Any]) -> None:
        """Populate the widget with variable properties."""
        # Variable name with editing capability
        name_edit = QLineEdit(variable_data['name'])
        name_edit.setStyleSheet(
            "font-weight: bold; color: #ffffff; "
            "background-color: #404040; border: 1px solid #555; padding: 5px;"
        )
        name_edit.textChanged.connect(
            lambda text: self.update_variable_name(variable_data['id'], text)
        )
        self.form_layout.addRow("Variable Name:", name_edit)
        
        # Variable type with dropdown
        type_container = self.create_type_selector(variable_data)
        self.form_layout.addRow("Variable Type:", type_container)
        
        # Variable description
        desc_edit = QLineEdit(variable_data.get('description', ''))
        desc_edit.setStyleSheet(
            "background-color: #404040; border: 1px solid #555; "
            "padding: 5px; color: white;"
        )
        desc_edit.textChanged.connect(
            lambda text: self.update_variable_description(variable_data['id'], text)
        )
        self.form_layout.addRow("Description:", desc_edit)
        
        # Variable value editor
        value_editor = self.create_variable_value_editor(variable_data)
        if value_editor:
            self.form_layout.addRow("Default Value:", value_editor)
    
    def create_type_selector(self, variable_data: Dict[str, Any]) -> QWidget:
        """Create type selection widget."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        type_combo = QComboBox()
        type_combo.addItems(['Float', 'Integer', 'Boolean', 'String', 'Path'])
        type_combo.setCurrentText(variable_data['type'])
        type_combo.setStyleSheet("""
            QComboBox {
                background-color: #404040;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                color: white;
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
        
        apply_btn = QPushButton("Apply")
        apply_btn.setMaximumWidth(60)
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005f99;
            }
        """)
        apply_btn.clicked.connect(
            lambda: self.update_variable_type(variable_data['id'], type_combo.currentText())
        )
        
        layout.addWidget(type_combo, 1)
        layout.addWidget(apply_btn)
        
        return container
    
    def create_variable_value_editor(self, variable_data: Dict[str, Any]) -> QWidget | None:
        """Create value editor for variable."""
        var_type = variable_data['type']
        current_value = variable_data.get('value', None)
        
        if var_type == 'Float':
            editor = QDoubleSpinBox()
            editor.setRange(-999999.0, 999999.0)
            editor.setDecimals(3)
            editor.setValue(current_value if current_value is not None else 0.0)
            editor.valueChanged.connect(
                lambda val: self.update_variable_value(variable_data['id'], val)
            )
            return editor
            
        elif var_type == 'Integer':
            editor = QSpinBox()
            editor.setRange(-999999, 999999)
            editor.setValue(current_value if current_value is not None else 0)
            editor.valueChanged.connect(
                lambda val: self.update_variable_value(variable_data['id'], val)
            )
            return editor
            
        elif var_type == 'Boolean':
            editor = QCheckBox("True")
            editor.setChecked(current_value if current_value is not None else False)
            editor.toggled.connect(
                lambda checked: self.update_variable_value(variable_data['id'], checked)
            )
            return editor
            
        elif var_type in ['String', 'Path']:
            editor = QLineEdit()
            editor.setText(str(current_value) if current_value is not None else "")
            editor.textChanged.connect(
                lambda text: self.update_variable_value(variable_data['id'], text)
            )
            return editor
        
        return None
    
    def update_variable_name(self, var_id: str, new_name: str) -> None:
        """Update variable name."""
        self.viewmodel.update_variable(var_id, 'name', new_name)
    
    def update_variable_type(self, var_id: str, new_type: str) -> None:
        """Update variable type."""
        self.viewmodel.update_variable(var_id, 'type', new_type)
    
    def update_variable_description(self, var_id: str, new_description: str) -> None:
        """Update variable description."""
        self.viewmodel.update_variable(var_id, 'description', new_description)
    
    def update_variable_value(self, var_id: str, new_value) -> None:
        """Update variable value."""
        self.viewmodel.update_variable(var_id, 'value', new_value)
    
    def on_selection_cleared(self) -> None:
        """Called when selection is cleared."""
        self.current_variable_data = None
        super().on_selection_cleared() 