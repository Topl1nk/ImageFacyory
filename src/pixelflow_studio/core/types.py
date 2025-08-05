"""
Core type definitions for PixelFlow Studio.

This module defines the fundamental types used throughout the application,
including pin types, connection types, and data structures.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Protocol, TypeVar, Union
from uuid import uuid4

import numpy as np
from PIL import Image
from PySide6.QtCore import QObject, QPointF, Signal
from PySide6.QtGui import QColor


class PinType(Enum):
    """Types of pins that can be connected in the node graph."""
    
    # Execution flow
    EXEC = "exec"
    
    # Basic data types
    BOOL = "bool"
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    PATH = "path"
    
    # Complex data types
    IMAGE = "image"
    COLOR = "color"
    VECTOR2 = "vector2"
    VECTOR3 = "vector3"
    MATRIX = "matrix"
    
    # Advanced types
    ARRAY = "array"
    DICT = "dict"
    ANY = "any"

    @property
    def color(self) -> QColor:
        """Get the visual color for this pin type."""
        color_map = {
            PinType.EXEC: QColor(255, 255, 255),      # White - как на скриншоте
            PinType.BOOL: QColor(220, 48, 48),        # Red
            PinType.INT: QColor(48, 220, 48),         # Green  
            PinType.FLOAT: QColor(48, 48, 220),       # Blue
            PinType.STRING: QColor(220, 48, 220),     # Magenta
            PinType.PATH: QColor(139, 69, 19),        # Brown - для путей к файлам
            PinType.IMAGE: QColor(255, 165, 0),       # Orange
            PinType.COLOR: QColor(255, 255, 0),       # Yellow
            PinType.VECTOR2: QColor(255, 128, 0),     # Orange-yellow
            PinType.VECTOR3: QColor(128, 255, 128),   # Light green
            PinType.MATRIX: QColor(128, 128, 255),    # Light blue
            PinType.ARRAY: QColor(192, 192, 192),     # Light gray
            PinType.DICT: QColor(64, 224, 208),       # Turquoise
            PinType.ANY: QColor(128, 128, 128),       # Gray
        }
        return color_map.get(self, QColor(128, 128, 128))

    def is_compatible_with(self, other: PinType) -> bool:
        """Check if this pin type can connect to another pin type."""
        if self == other:
            return True
        if self == PinType.ANY or other == PinType.ANY:
            return True
        
        # Special compatibility rules
        numeric_types = {PinType.INT, PinType.FLOAT}
        if self in numeric_types and other in numeric_types:
            return True
        
        # PATH и STRING совместимы (путь - это строка)
        string_types = {PinType.STRING, PinType.PATH}
        if self in string_types and other in string_types:
            return True
            
        return False


class ConnectionType(Enum):
    """Types of connections between pins."""
    DATA = auto()
    EXECUTION = auto()


class PinDirection(Enum):
    """Direction of data flow for pins."""
    INPUT = "input"
    OUTPUT = "output"


# Type aliases for better readability
NodeID = str
PinID = str
ConnectionID = str

# Value types that can be passed through pins
PinValue = Union[
    None,
    bool,
    int, 
    float,
    str,
    Image.Image,
    np.ndarray,
    QColor,
    tuple,
    list,
    dict,
]


@dataclass(frozen=True)
class Position:
    """2D position with integer coordinates to avoid Qt float->int errors."""
    x: int
    y: int
    
    def to_qpointf(self) -> QPointF:
        """Convert to Qt point."""
        return QPointF(float(self.x), float(self.y))
    
    @classmethod
    def from_qpointf(cls, point: QPointF) -> Position:
        """Create from Qt point."""
        return cls(int(point.x()), int(point.y()))


@dataclass
class PinInfo:
    """Information about a pin."""
    id: PinID = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    pin_type: PinType = PinType.ANY
    direction: PinDirection = PinDirection.INPUT
    description: str = ""
    default_value: PinValue = None
    is_multiple: bool = False  # Can have multiple connections
    position: Position = field(default_factory=lambda: Position(0, 0))


@dataclass 
class ConnectionInfo:
    """Information about a connection between pins."""
    id: ConnectionID = field(default_factory=lambda: str(uuid4()))
    output_pin_id: PinID = field(default_factory=lambda: str(uuid4()))
    input_pin_id: PinID = field(default_factory=lambda: str(uuid4()))
    connection_type: ConnectionType = ConnectionType.DATA


@dataclass
class NodeInfo:
    """Information about a node."""
    id: NodeID = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    category: str = "General"
    position: Position = field(default_factory=lambda: Position(0, 0))
    input_pins: List[PinInfo] = field(default_factory=list)
    output_pins: List[PinInfo] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class NodeProtocol(Protocol):
    """Protocol defining the interface for all nodes."""
    
    @property
    def id(self) -> NodeID:
        """Unique identifier for the node."""
        ...
    
    @property
    def name(self) -> str:
        """Display name of the node."""
        ...
    
    @property
    def category(self) -> str:
        """Category for organization."""
        ...
    
    async def execute(self) -> None:
        """Execute the node's logic."""
        ...


class ExecutionContext:
    """Context for node execution."""
    
    def __init__(self) -> None:
        self.is_cancelled: bool = False
        self.progress: float = 0.0
        self.metadata: Dict[str, Any] = {}
        
    def cancel(self) -> None:
        """Cancel the execution."""
        self.is_cancelled = True
        
    def set_progress(self, progress: float) -> None:
        """Set execution progress (0.0 to 1.0)."""
        self.progress = max(0.0, min(1.0, progress))


class GraphEvent(QObject):
    """Event system for graph changes."""
    
    node_added = Signal(NodeID)
    node_removed = Signal(NodeID)
    node_moved = Signal(NodeID, Position)
    
    connection_added = Signal(ConnectionID)
    connection_removed = Signal(ConnectionID)
    
    pin_value_changed = Signal(PinID, object)
    
    execution_started = Signal()
    execution_finished = Signal()
    execution_progress = Signal(float)


# Generic type variable for nodes
T = TypeVar('T', bound=NodeProtocol)


@dataclass
class ValidationError:
    """Represents a validation error in the graph."""
    message: str
    node_id: Optional[NodeID] = None
    pin_id: Optional[PinID] = None
    severity: str = "error"  # "error", "warning", "info"


class ValidationResult:
    """Result of graph validation."""
    
    def __init__(self) -> None:
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        
    @property
    def is_valid(self) -> bool:
        """True if no errors (warnings are OK)."""
        return len(self.errors) == 0
        
    def add_error(self, message: str, node_id: Optional[NodeID] = None, 
                  pin_id: Optional[PinID] = None) -> None:
        """Add an error to the result."""
        self.errors.append(ValidationError(message, node_id, pin_id, "error"))
        
    def add_warning(self, message: str, node_id: Optional[NodeID] = None,
                   pin_id: Optional[PinID] = None) -> None:
        """Add a warning to the result."""
        self.warnings.append(ValidationError(message, node_id, pin_id, "warning"))


# Constants
DEFAULT_NODE_SIZE = Position(120, 80)
DEFAULT_PIN_RADIUS = 8
DEFAULT_CONNECTION_WIDTH = 3 