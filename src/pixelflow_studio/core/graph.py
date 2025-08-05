"""
Graph implementation for PixelFlow Studio.

This module provides the Graph class which manages nodes, connections,
and execution order in the node graph.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Set

from loguru import logger
from PySide6.QtCore import QObject, Signal

from .node import Node, Pin
from .types import (
    ConnectionID,
    ConnectionInfo,
    ExecutionContext,
    GraphEvent,
    NodeID,
    PinID,
    Position,
    ValidationResult,
)


class Connection:
    """Represents a connection between two pins."""

    def __init__(self, output_pin: Pin, input_pin: Pin) -> None:
        # Professional workflow: Only check basic compatibility
        # Graph.connect_pins() handles existing connections removal before calling this
        if not output_pin.can_connect_to(input_pin):
            # Only report fundamental incompatibilities (not existing connections)
            error_details = []
            
            if output_pin == input_pin:
                error_details.append("trying to connect pin to itself")
            elif output_pin.direction == input_pin.direction:
                error_details.append(f"both pins have same direction ({output_pin.direction.name})")
            elif not output_pin.pin_type.is_compatible_with(input_pin.pin_type):
                error_details.append(f"incompatible types ({output_pin.pin_type.name} -> {input_pin.pin_type.name})")
            else:
                error_details.append("fundamental incompatibility")
            
            error_msg = f"Cannot connect {output_pin.name}({output_pin.pin_type.name}) to {input_pin.name}({input_pin.pin_type.name}): {', '.join(error_details)}"
            raise ValueError(error_msg)

        self.info = ConnectionInfo(
            output_pin_id=output_pin.id,
            input_pin_id=input_pin.id,
        )
        self.output_pin = output_pin
        self.input_pin = input_pin

        # Add connection to pins
        output_pin.add_connection(self.info.id)
        input_pin.add_connection(self.info.id)

    @property
    def id(self) -> ConnectionID:
        """Get the unique identifier for this connection."""
        return self.info.id

    def disconnect(self) -> None:
        """Remove this connection from both pins."""
        self.output_pin.remove_connection(self.info.id)
        self.input_pin.remove_connection(self.info.id)


class Graph(QObject):
    """
    Manages a collection of nodes and their connections.
    
    The Graph is responsible for:
    - Managing nodes and connections
    - Validating the graph structure
    - Executing the graph in the correct order
    - Propagating value changes
    """

    # Signals
    node_added = Signal(object)  # Node
    node_removed = Signal(object)  # Node
    node_moved = Signal(object, Position)  # Node, Position
    
    connection_added = Signal(object)  # Connection
    connection_removed = Signal(object)  # Connection
    
    graph_changed = Signal()  # General graph change
    
    execution_started = Signal()
    execution_finished = Signal()
    execution_progress = Signal(float)
    execution_error = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._nodes: Dict[NodeID, Node] = {}
        self._connections: Dict[ConnectionID, Connection] = {}
        self._pins: Dict[PinID, Pin] = {}
        
        self._execution_order: List[Node] = []
        self._is_executing = False
        self._execution_context: Optional[ExecutionContext] = None

    @property
    def nodes(self) -> List[Node]:
        """Get all nodes in the graph."""
        return list(self._nodes.values())

    @property
    def connections(self) -> List[Connection]:
        """Get all connections in the graph."""
        return list(self._connections.values())

    @property
    def is_executing(self) -> bool:
        """True if the graph is currently executing."""
        return self._is_executing

    def add_node(self, node: Node) -> None:
        """Add a node to the graph."""
        if node.id in self._nodes:
            raise ValueError(f"Node with ID {node.id} already exists")

        self._nodes[node.id] = node
        node.graph = self

        # Register all pins
        for pin in node.get_all_pins():
            self._pins[pin.id] = pin

        # Clear execution order cache
        self._execution_order.clear()

        self.node_added.emit(node)
        self.graph_changed.emit()
        logger.debug(f"Added node: {node.name}")

    def remove_node(self, node: Node) -> None:
        """Remove a node from the graph."""
        if node.id not in self._nodes:
            raise ValueError(f"Node with ID {node.id} not found")

        # Remove all connections to/from this node
        connections_to_remove = []
        for connection in self._connections.values():
            if (connection.output_pin.node == node or 
                connection.input_pin.node == node):
                connections_to_remove.append(connection)

        for connection in connections_to_remove:
            self.remove_connection(connection)

        # Remove pins
        for pin in node.get_all_pins():
            self._pins.pop(pin.id, None)

        # Remove node
        del self._nodes[node.id]
        node.graph = None

        # Clear execution order cache
        self._execution_order.clear()

        self.node_removed.emit(node)
        self.graph_changed.emit()
        logger.debug(f"Removed node: {node.name}")

    def get_node(self, node_id: NodeID) -> Optional[Node]:
        """Get a node by its ID."""
        return self._nodes.get(node_id)

    def get_pin(self, pin_id: PinID) -> Optional[Pin]:
        """Get a pin by its ID."""
        return self._pins.get(pin_id)

    def get_connection(self, connection_id: ConnectionID) -> Optional[Connection]:
        """Get a connection by its ID."""
        return self._connections.get(connection_id)

    def connect_pins(self, output_pin: Pin, input_pin: Pin) -> Connection:
        """Create a connection between two pins.
        
        Note: Auto-removal of existing connections is handled by GUI layer
        to ensure both graphics and logic are properly cleaned up.
        """
        
        logger.debug(f"🔗 GRAPH: Creating connection {output_pin.name}({output_pin.pin_type.name}) -> {input_pin.name}({input_pin.pin_type.name})")
        
        # Create the new connection (basic compatibility check in Connection.__init__)
        connection = Connection(output_pin, input_pin)
        self._connections[connection.id] = connection

        # Clear execution order cache
        self._execution_order.clear()

        self.connection_added.emit(connection)
        self.graph_changed.emit()
        logger.debug(f"✅ GRAPH: Connection created successfully: {output_pin.name} -> {input_pin.name}")
        
        return connection

    def remove_connection(self, connection: Connection) -> None:
        """Remove a connection from the graph."""
        if connection.id not in self._connections:
            raise ValueError(f"Connection with ID {connection.id} not found")

        connection.disconnect()
        del self._connections[connection.id]

        # Clear execution order cache
        self._execution_order.clear()

        self.connection_removed.emit(connection)
        self.graph_changed.emit()
        logger.debug(f"Removed connection {connection.output_pin.name} -> {connection.input_pin.name}")

    def move_node(self, node: Node, position: Position) -> None:
        """Move a node to a new position."""
        if node.id not in self._nodes:
            raise ValueError(f"Node with ID {node.id} not found")

        node.position = position
        self.node_moved.emit(node, position)

    def validate(self) -> ValidationResult:
        """Validate the graph structure."""
        result = ValidationResult()

        # Check for cycles
        if self._has_cycles():
            result.add_error("Graph contains cycles")

        # Check for disconnected nodes
        for node in self._nodes.values():
            has_input_connections = any(
                len(pin.connections) > 0 for pin in node.input_pins.values()
            )
            has_output_connections = any(
                len(pin.connections) > 0 for pin in node.output_pins.values()
            )
            
            if not has_input_connections and not has_output_connections:
                result.add_warning(f"Node '{node.name}' has no connections", node.id)

        # Check for incompatible connections
        for connection in self._connections.values():
            if not connection.output_pin.pin_type.is_compatible_with(
                connection.input_pin.pin_type
            ):
                result.add_error(
                    f"Incompatible connection: {connection.output_pin.pin_type.value} -> {connection.input_pin.pin_type.value}",
                    connection.output_pin.node.id
                )

        return result

    def _has_cycles(self) -> bool:
        """Check if the graph has cycles using DFS."""
        visited = set()
        rec_stack = set()

        def dfs(node: Node) -> bool:
            if node.id in rec_stack:
                return True
            if node.id in visited:
                return False

            visited.add(node.id)
            rec_stack.add(node.id)

            # Visit connected nodes
            for pin in node.output_pins.values():
                for connection_id in pin.connections:
                    connection = self._connections.get(connection_id)
                    if connection:
                        next_node = connection.input_pin.node
                        if dfs(next_node):
                            return True

            rec_stack.remove(node.id)
            return False

        for node in self._nodes.values():
            if node.id not in visited:
                if dfs(node):
                    return True

        return False

    def calculate_execution_order(self) -> List[Node]:
        """Calculate the execution order using topological sort."""
        if self._execution_order:
            return self._execution_order.copy()

        # Kahn's algorithm for topological sorting
        in_degree = {node.id: 0 for node in self._nodes.values()}
        
        # Calculate in-degrees
        for connection in self._connections.values():
            target_node_id = connection.input_pin.node.id
            in_degree[target_node_id] += 1

        # Start with nodes that have no incoming edges
        queue = [node for node in self._nodes.values() if in_degree[node.id] == 0]
        execution_order = []

        while queue:
            current_node = queue.pop(0)
            execution_order.append(current_node)

            # Update in-degrees of connected nodes
            for pin in current_node.output_pins.values():
                for connection_id in pin.connections:
                    connection = self._connections.get(connection_id)
                    if connection:
                        next_node = connection.input_pin.node
                        in_degree[next_node.id] -= 1
                        if in_degree[next_node.id] == 0:
                            queue.append(next_node)

        # Check for cycles
        if len(execution_order) != len(self._nodes):
            raise RuntimeError("Graph contains cycles - cannot determine execution order")

        self._execution_order = execution_order
        return execution_order.copy()

    async def execute_all(self, context: Optional[ExecutionContext] = None) -> None:
        """Execute all nodes in the correct order."""
        if self._is_executing:
            logger.warning("Graph is already executing")
            return

        if context is None:
            context = ExecutionContext()

        self._execution_context = context
        self._is_executing = True
        self.execution_started.emit()

        try:
            # Validate graph first
            validation_result = self.validate()
            if not validation_result.is_valid:
                error_msg = "Graph validation failed: " + "; ".join(
                    error.message for error in validation_result.errors
                )
                raise RuntimeError(error_msg)

            # Calculate execution order
            execution_order = self.calculate_execution_order()
            total_nodes = len(execution_order)

            logger.info(f"Executing graph with {total_nodes} nodes")

            # Execute nodes in order
            for i, node in enumerate(execution_order):
                if context.is_cancelled:
                    logger.info("Graph execution cancelled")
                    break

                # Update progress
                progress = (i / total_nodes) if total_nodes > 0 else 1.0
                context.set_progress(progress)
                self.execution_progress.emit(progress)

                # Execute node
                await node.execute_safe(context)

            # Final progress
            if not context.is_cancelled:
                context.set_progress(1.0)
                self.execution_progress.emit(1.0)
                logger.info("Graph execution completed")

        except Exception as e:
            error_msg = f"Graph execution failed: {e}"
            logger.error(error_msg)
            self.execution_error.emit(error_msg)
            raise
        finally:
            self._is_executing = False
            self._execution_context = None
            self.execution_finished.emit()

    async def execute_node(self, node: Node, context: Optional[ExecutionContext] = None) -> None:
        """Execute a single node and its dependencies."""
        if context is None:
            context = ExecutionContext()

        # Find all dependencies
        dependencies = self._get_node_dependencies(node)
        
        # Execute dependencies first
        for dep_node in dependencies:
            if context.is_cancelled:
                break
            await dep_node.execute_safe(context)

        # Execute the target node
        if not context.is_cancelled:
            await node.execute_safe(context)

    def _get_node_dependencies(self, node: Node) -> List[Node]:
        """Get all nodes that this node depends on."""
        dependencies = []
        visited = set()

        def collect_dependencies(current_node: Node) -> None:
            if current_node.id in visited:
                return
            visited.add(current_node.id)

            # Find all nodes connected to inputs
            for pin in current_node.input_pins.values():
                for connection_id in pin.connections:
                    connection = self._connections.get(connection_id)
                    if connection:
                        source_node = connection.output_pin.node
                        collect_dependencies(source_node)
                        if source_node not in dependencies:
                            dependencies.append(source_node)

        collect_dependencies(node)
        return dependencies

    async def propagate_value_change(self, pin_id: PinID, value) -> None:
        """Propagate a value change through connected pins."""
        pin = self.get_pin(pin_id)
        if not pin or not pin.is_output:
            return

        # Find all connected input pins
        for connection_id in pin.connections:
            connection = self.get_connection(connection_id)
            if connection:
                # The value will be fetched when the connected node executes
                # This is a lazy evaluation approach
                pass

    def clear(self) -> None:
        """Clear all nodes and connections from the graph."""
        # Remove all connections first
        for connection in list(self._connections.values()):
            self.remove_connection(connection)

        # Remove all nodes
        for node in list(self._nodes.values()):
            self.remove_node(node)

        logger.info("Graph cleared")

    def cancel_execution(self) -> None:
        """Cancel the current graph execution."""
        if self._execution_context:
            self._execution_context.cancel()

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about the graph."""
        return {
            "nodes": len(self._nodes),
            "connections": len(self._connections),
            "pins": len(self._pins),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize this graph to a dictionary."""
        return {
            "version": "1.0",
            "nodes": [node.to_dict() for node in self._nodes.values()],
            "connections": [
                {
                    "id": str(conn.id),
                    "output_pin_id": str(conn.output_pin.id),
                    "input_pin_id": str(conn.input_pin.id),
                    "output_node_id": str(conn.output_pin.node.id),
                    "input_node_id": str(conn.input_pin.node.id),
                    "output_pin_name": conn.output_pin.info.name,
                    "input_pin_name": conn.input_pin.info.name
                }
                for conn in self._connections.values()
            ]
        }

    def from_dict(self, data: Dict[str, Any], node_classes: Dict[str, type]) -> None:
        """Deserialize a graph from a dictionary."""
        # Clear current graph
        self.clear()
        
        # Check version compatibility
        version = data.get("version", "1.0")
        if version != "1.0":
            logger.warning(f"Loading project with version {version}, expected 1.0")
        
        # Load nodes
        node_id_map = {}  # old_id -> new_node
        for node_data in data["nodes"]:
            try:
                node = Node.from_dict(node_data, node_classes)
                old_id = node_data["id"]
                self.add_node(node)
                node_id_map[old_id] = node
                logger.debug(f"Loaded node: {node.name} ({node.__class__.__name__})")
            except Exception as e:
                logger.error(f"Failed to load node: {e}")
                continue
        
        # Load connections
        for conn_data in data["connections"]:
            try:
                output_node_id = conn_data["output_node_id"]
                input_node_id = conn_data["input_node_id"]
                output_pin_name = conn_data["output_pin_name"]
                input_pin_name = conn_data["input_pin_name"]
                
                # Find nodes by old IDs
                if output_node_id not in node_id_map or input_node_id not in node_id_map:
                    logger.warning(f"Skipping connection: nodes not found")
                    continue
                
                output_node = node_id_map[output_node_id]
                input_node = node_id_map[input_node_id]
                
                # Find pins
                output_pin = output_node.get_output_pin(output_pin_name)
                input_pin = input_node.get_input_pin(input_pin_name)
                
                if output_pin and input_pin:
                    self.connect_pins(output_pin, input_pin)
                    logger.debug(f"Connected: {output_node.name}.{output_pin_name} -> {input_node.name}.{input_pin_name}")
                else:
                    logger.warning(f"Skipping connection: pins not found")
                    
            except Exception as e:
                logger.error(f"Failed to load connection: {e}")
                continue
        
        logger.info(f"Graph loaded: {len(self._nodes)} nodes, {len(self._connections)} connections") 