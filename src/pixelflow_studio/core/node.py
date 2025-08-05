"""
Base node implementation for PixelFlow Studio.

This module provides the fundamental Node class that all other nodes inherit from.
It implements the core functionality for pins, connections, and execution.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set

from loguru import logger
from PySide6.QtCore import QObject, Signal, QAbstractItemModel

from uuid import uuid4

from .types import (
    ConnectionID,
    ConnectionInfo,
    ExecutionContext,
    NodeID,
    PinDirection,
    PinID,
    PinInfo,
    PinType,
    PinValue,
    Position,
)


class Pin:
    """Represents a pin on a node that can connect to other pins."""

    def __init__(
        self,
        node: Node,
        name: str,
        pin_type: PinType,
        direction: PinDirection,
        description: str = "",
        default_value: PinValue = None,
        is_multiple: bool = False,
    ) -> None:
        self.info = PinInfo(
            name=name,
            pin_type=pin_type,
            direction=direction,
            description=description,
            default_value=default_value,
            is_multiple=is_multiple,
        )
        self.node = node
        self.connections: Set[ConnectionID] = set()
        self._cached_value: PinValue = default_value

    @property
    def id(self) -> PinID:
        """Get the unique identifier for this pin."""
        return self.info.id

    @property
    def name(self) -> str:
        """Get the display name of this pin."""
        return self.info.name

    @property
    def pin_type(self) -> PinType:
        """Get the type of this pin."""
        return self.info.pin_type

    @property
    def direction(self) -> PinDirection:
        """Get the direction of this pin."""
        return self.info.direction

    @property
    def is_input(self) -> bool:
        """True if this is an input pin."""
        return self.direction == PinDirection.INPUT

    @property
    def is_output(self) -> bool:
        """True if this is an output pin."""
        return self.direction == PinDirection.OUTPUT

    def can_connect_to(self, other: Pin) -> bool:
        """Check if this pin can connect to another pin.
        
        This function only checks basic compatibility (direction, types).
        Existing connections are handled by Graph.connect_pins() which auto-removes them.
        This enables professional workflow without blocking users.
        """
        from loguru import logger
        
        # Can't connect to itself
        if self == other:
            logger.debug(f"❌ Cannot connect pin to itself: {self.name}")
            return False

        # Must be different directions
        if self.direction == other.direction:
            logger.debug(f"❌ Cannot connect pins of same direction: {self.name}({self.direction.name}) -> {other.name}({other.direction.name})")
            return False

        # Check type compatibility
        if not self.pin_type.is_compatible_with(other.pin_type):
            logger.debug(f"❌ Incompatible pin types: {self.name}({self.pin_type.name}) -> {other.name}({other.pin_type.name})")
            return False

        # ✅ PROFESSIONAL WORKFLOW: No longer block existing connections!
        # Graph.connect_pins() will auto-remove old connections and create new ones
        # This enables smooth UX like in Unreal Engine, Houdini, Blender
        
        # Note existing connections but allow replacement
        if not self.info.is_multiple and len(self.connections) > 0:
            logger.debug(f"🔄 Output pin has existing connection, will be auto-replaced: {self.name}")
        
        if not other.info.is_multiple and len(other.connections) > 0:
            logger.debug(f"🔄 Input pin has existing connection, will be auto-replaced: {other.name}")

        logger.debug(f"✅ Can connect: {self.name}({self.pin_type.name}, {self.direction.name}) -> {other.name}({other.pin_type.name}, {other.direction.name})")
        return True

    async def get_value(self) -> PinValue:
        """Get the current value of this pin."""
        if self.is_output:
            return self._cached_value

        # For input pins, get value from connected output
        if self.connections:
            # Get the first connection (input pins typically have only one)
            connection_id = next(iter(self.connections))
            connection = self.node.graph.get_connection(connection_id)
            if connection:
                output_pin = self.node.graph.get_pin(connection.info.output_pin_id)
                if output_pin:
                    return await output_pin.get_value()

        return self.info.default_value

    async def set_value(self, value: PinValue) -> None:
        """Set the value of this pin."""
        if self.is_input:
            logger.warning(f"Attempted to set value on input pin {self.name}")
            return

        self._cached_value = value
        
        # Notify connected nodes
        if self.node.graph:
            await self.node.graph.propagate_value_change(self.id, value)

    def add_connection(self, connection_id: ConnectionID) -> None:
        """Add a connection to this pin."""
        self.connections.add(connection_id)

    def remove_connection(self, connection_id: ConnectionID) -> None:
        """Remove a connection from this pin."""
        self.connections.discard(connection_id)


class NodeMeta(type(QObject), type(ABC)):
    """Metaclass to resolve QObject and ABC metaclass conflict."""
    pass


class Node(QObject, ABC, metaclass=NodeMeta):
    """
    Base class for all nodes in the graph.
    
    This class provides the fundamental functionality that all nodes need:
    - Pin management (inputs and outputs)
    - Execution logic
    - Connection handling
    - Event signaling
    """

    # Signals
    execution_started = Signal()
    execution_finished = Signal()
    execution_error = Signal(str)
    pin_value_changed = Signal(str, object)  # pin_name, value

    def __init__(
        self,
        name: str = "Node",
        description: str = "",
        category: str = "General",
    ) -> None:
        super().__init__()
        self._id = str(uuid4())
        self._name = name
        self._description = description
        self._category = category
        self._position = Position(0, 0)

        # Pin storage
        self._input_pins: Dict[str, Pin] = {}
        self._output_pins: Dict[str, Pin] = {}

        # Execution state
        self._is_executing = False
        self._execution_context: Optional[ExecutionContext] = None

        # Graph reference (set by graph when added)
        self.graph: Optional[Graph] = None

        # Setup pins (implemented by subclasses)
        self.setup_pins()

    @property
    def id(self) -> NodeID:
        """Get the unique identifier for this node."""
        return self._id

    @property
    def name(self) -> str:
        """Get the display name of this node."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Set the display name of this node."""
        self._name = value

    @property
    def description(self) -> str:
        """Get the description of this node."""
        return self._description

    @property
    def category(self) -> str:
        """Get the category of this node."""
        return self._category

    @property
    def position(self) -> Position:
        """Get the position of this node."""
        return self._position

    @position.setter
    def position(self, value: Position) -> None:
        """Set the position of this node."""
        self._position = value

    @property
    def is_executing(self) -> bool:
        """True if this node is currently executing."""
        return self._is_executing

    @property
    def input_pins(self) -> Dict[str, Pin]:
        """Get all input pins."""
        return self._input_pins.copy()

    @property
    def output_pins(self) -> Dict[str, Pin]:
        """Get all output pins."""
        return self._output_pins.copy()

    def get_pin(self, name: str) -> Optional[Pin]:
        """Get a pin by name (searches both inputs and outputs)."""
        return self._input_pins.get(name) or self._output_pins.get(name)

    def get_input_pin(self, name: str) -> Optional[Pin]:
        """Get an input pin by name."""
        return self._input_pins.get(name)

    def get_output_pin(self, name: str) -> Optional[Pin]:
        """Get an output pin by name."""
        return self._output_pins.get(name)

    @abstractmethod
    def setup_pins(self) -> None:
        """
        Setup the pins for this node.
        
        This method must be implemented by subclasses to define
        their input and output pins.
        """
        pass

    @abstractmethod
    async def execute(self, context: ExecutionContext) -> None:
        """
        Execute the logic of this node.
        
        Args:
            context: Execution context containing cancellation and progress info
            
        This method must be implemented by subclasses to define
        their processing logic.
        """
        pass

    def add_input_pin(
        self,
        name: str,
        pin_type: PinType,
        description: str = "",
        default_value: PinValue = None,
        is_multiple: bool = False,
    ) -> Pin:
        """Add an input pin to this node."""
        if name in self._input_pins:
            raise ValueError(f"Input pin '{name}' already exists")

        pin = Pin(
            self, name, pin_type, PinDirection.INPUT, description, default_value, is_multiple
        )
        self._input_pins[name] = pin
        return pin

    def add_output_pin(
        self,
        name: str,
        pin_type: PinType,
        description: str = "",
        default_value: PinValue = None,
        is_multiple: bool = True,
    ) -> Pin:
        """Add an output pin to this node."""
        if name in self._output_pins:
            raise ValueError(f"Output pin '{name}' already exists")

        pin = Pin(
            self, name, pin_type, PinDirection.OUTPUT, description, default_value, is_multiple
        )
        self._output_pins[name] = pin
        return pin

    async def get_input_value(self, pin_name: str) -> PinValue:
        """Get the value of an input pin."""
        pin = self.get_input_pin(pin_name)
        if pin is None:
            raise ValueError(f"Input pin '{pin_name}' not found")
        return await pin.get_value()

    async def set_output_value(self, pin_name: str, value: PinValue) -> None:
        """Set the value of an output pin."""
        pin = self.get_output_pin(pin_name)
        if pin is None:
            raise ValueError(f"Output pin '{pin_name}' not found")
        await pin.set_value(value)
        self.pin_value_changed.emit(pin_name, value)

    async def execute_safe(self, context: Optional[ExecutionContext] = None) -> None:
        """
        Execute this node safely with error handling.
        
        Args:
            context: Optional execution context
        """
        if self._is_executing:
            logger.warning(f"Node {self.name} is already executing")
            return

        if context is None:
            context = ExecutionContext()

        self._execution_context = context
        self._is_executing = True
        self.execution_started.emit()

        try:
            logger.debug(f"Executing node: {self.name}")
            await self.execute(context)
            logger.debug(f"Finished executing node: {self.name}")
        except Exception as e:
            error_msg = f"Error executing node {self.name}: {e}"
            logger.error(error_msg)
            self.execution_error.emit(error_msg)
            raise
        finally:
            self._is_executing = False
            self._execution_context = None
            self.execution_finished.emit()

    def cancel_execution(self) -> None:
        """Cancel the current execution."""
        if self._execution_context:
            self._execution_context.cancel()

    def get_all_pins(self) -> List[Pin]:
        """Get all pins (both input and output)."""
        return list(self._input_pins.values()) + list(self._output_pins.values())

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', id={self.id})"

    def __repr__(self) -> str:
        return self.__str__()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize this node to a dictionary."""
        return {
            "id": self._id,
            "name": self._name,
            "description": self._description,
            "category": self._category,
            "class_name": self.__class__.__name__,
            "position": {
                "x": self._position.x,
                "y": self._position.y
            },
            "input_pins": {
                name: {
                    "name": pin.info.name,
                    "type": pin.info.pin_type.name,
                    "direction": pin.info.direction.name,
                    "description": pin.info.description,
                    "value": pin.info.default_value,
                    "is_multiple": pin.info.is_multiple
                }
                for name, pin in self._input_pins.items()
            },
            "output_pins": {
                name: {
                    "name": pin.info.name,
                    "type": pin.info.pin_type.name,
                    "direction": pin.info.direction.name,
                    "description": pin.info.description,
                    "value": pin._cached_value,
                    "is_multiple": pin.info.is_multiple
                }
                for name, pin in self._output_pins.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], node_classes: Dict[str, type]) -> 'Node':
        """Deserialize a node from a dictionary."""
        class_name = data["class_name"]
        if class_name not in node_classes:
            raise ValueError(f"Unknown node class: {class_name}")
        
        # Create instance of the correct node class
        node_class = node_classes[class_name]
        node = node_class()
        
        # Restore node properties
        node._id = data["id"]
        node._position = Position(data["position"]["x"], data["position"]["y"])
        
        # Restore pin values  
        for name, pin_data in data["input_pins"].items():
            if name in node._input_pins:
                # For input pins, update the default value
                pin = node._input_pins[name]
                pin.info.default_value = pin_data["value"]
        
        for name, pin_data in data["output_pins"].items():
            if name in node._output_pins:
                # For output pins, update the cached value
                pin = node._output_pins[name]
                pin._cached_value = pin_data["value"]
        
        return node


# Import here to avoid circular imports
from .graph import Graph 