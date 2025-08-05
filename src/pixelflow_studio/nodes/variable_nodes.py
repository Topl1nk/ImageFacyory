"""
Variable nodes for PixelFlow Studio.

These nodes provide basic variable types that can be used as sources of values
for other nodes in the graph.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

from PySide6.QtWidgets import QFileDialog

from ..core.node import Node
from ..core.types import PinInfo, PinType, NodeID


class FloatVariableNode(Node):
    """A node that outputs a float value."""
    
    def __init__(self, node_id: Optional[NodeID] = None):
        super().__init__(
            name="Float Variable",
            description="Outputs a floating-point number value",
            category="Variables"
        )
        
    def setup_pins(self) -> None:
        """Setup input and output pins."""
        # Выходной пин для значения
        self.add_output_pin(
            name="value",
            pin_type=PinType.FLOAT,
            description="Float value output",
            default_value=0.0,
            is_multiple=True
        )
        
    async def execute(self) -> None:
        """Execute the node."""
        # Получаем значение из выходного пина
        value_pin = self.get_output_pin("value")
        if value_pin:
            # Значение уже установлено через Properties Panel
            pass


class IntegerVariableNode(Node):
    """A node that outputs an integer value."""
    
    def __init__(self, node_id: Optional[NodeID] = None):
        super().__init__(
            name="Integer Variable",
            description="Outputs an integer number value",
            category="Variables"
        )
        
    def setup_pins(self) -> None:
        """Setup input and output pins."""
        # Выходной пин для значения
        self.add_output_pin(
            name="value",
            pin_type=PinType.INT,
            description="Integer value output",
            default_value=0,
            is_multiple=True
        )
        
    async def execute(self) -> None:
        """Execute the node."""
        # Получаем значение из выходного пина
        value_pin = self.get_output_pin("value")
        if value_pin:
            # Значение уже установлено через Properties Panel
            pass


class BooleanVariableNode(Node):
    """A node that outputs a boolean value."""
    
    def __init__(self, node_id: Optional[NodeID] = None):
        super().__init__(
            name="Boolean Variable",
            description="Outputs a true/false value",
            category="Variables"
        )
        
    def setup_pins(self) -> None:
        """Setup input and output pins."""
        # Выходной пин для значения
        self.add_output_pin(
            name="value",
            pin_type=PinType.BOOL,
            description="Boolean value output",
            default_value=False,
            is_multiple=True
        )
        
    async def execute(self) -> None:
        """Execute the node."""
        # Получаем значение из выходного пина
        value_pin = self.get_output_pin("value")
        if value_pin:
            # Значение уже установлено через Properties Panel
            pass


class StringVariableNode(Node):
    """A node that outputs a string value."""
    
    def __init__(self, node_id: Optional[NodeID] = None):
        super().__init__(
            name="String Variable",
            description="Outputs a text string value",
            category="Variables"
        )
        
    def setup_pins(self) -> None:
        """Setup input and output pins."""
        # Выходной пин для значения
        self.add_output_pin(
            name="value",
            pin_type=PinType.STRING,
            description="String value output",
            default_value="",
            is_multiple=True
        )
        
    async def execute(self) -> None:
        """Execute the node."""
        # Получаем значение из выходного пина
        value_pin = self.get_output_pin("value")
        if value_pin:
            # Значение уже установлено через Properties Panel
            pass


class PathVariableNode(Node):
    """A node that outputs a file/folder path."""
    
    def __init__(self, node_id: Optional[NodeID] = None):
        super().__init__(
            name="Path Variable",
            description="Outputs a file or folder path",
            category="Variables"
        )
        self._path_value = ""
        
    def setup_pins(self) -> None:
        """Setup input and output pins."""
        # Выходной пин для пути
        self.add_output_pin(
            name="path",
            pin_type=PinType.PATH,
            description="File or folder path output",
            default_value="",
            is_multiple=True
        )
        
    def set_path(self, path: str) -> None:
        """Set the path value (used for drag&drop)."""
        self._path_value = path
        path_pin = self.get_output_pin("path")
        if path_pin:
            path_pin.set_value(path)
            
    def get_path(self) -> str:
        """Get the current path value."""
        return self._path_value
        
    async def execute(self) -> None:
        """Execute the node."""
        # Получаем значение из выходного пина
        path_pin = self.get_output_pin("path")
        if path_pin:
            # Значение уже установлено через Properties Panel или drag&drop
            pass
            
    def to_dict(self) -> Dict[str, Any]:
        """Serialize node to dictionary."""
        data = super().to_dict()
        data["path_value"] = self._path_value
        return data
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PathVariableNode':
        """Deserialize node from dictionary."""
        node = super().from_dict(data)
        if isinstance(node, cls):
            node._path_value = data.get("path_value", "")
        return node