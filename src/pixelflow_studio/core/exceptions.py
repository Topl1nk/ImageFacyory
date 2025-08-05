"""
Custom exceptions for PixelFlow Studio.

This module defines specific exception classes for different error types,
replacing generic Exception handling with more specific error types.
"""

from __future__ import annotations

from typing import Optional, Any


class PixelFlowError(Exception):
    """Base exception class for all PixelFlow Studio errors."""
    
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.details = details
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class NodeError(PixelFlowError):
    """Base class for node-related errors."""
    pass


class NodeExecutionError(NodeError):
    """Error that occurs during node execution."""
    
    def __init__(self, node_name: str, operation: str, error: Exception):
        message = f"Node execution failed: {node_name}"
        details = f"Operation: {operation}, Error: {error}"
        super().__init__(message, details)
        self.node_name = node_name
        self.operation = operation
        self.original_error = error


class NodeCreationError(NodeError):
    """Error that occurs during node creation."""
    
    def __init__(self, node_class: str, reason: str):
        message = f"Failed to create node: {node_class}"
        super().__init__(message, reason)
        self.node_class = node_class


class PinError(PixelFlowError):
    """Base class for pin-related errors."""
    pass


class PinConnectionError(PinError):
    """Error that occurs during pin connection."""
    
    def __init__(self, output_pin: str, input_pin: str, reason: str):
        message = f"Pin connection failed: {output_pin} -> {input_pin}"
        super().__init__(message, reason)
        self.output_pin = output_pin
        self.input_pin = input_pin


class PinValueError(PinError):
    """Error that occurs when setting invalid pin values."""
    
    def __init__(self, pin_name: str, value: Any, expected_type: str):
        message = f"Invalid pin value: {pin_name}"
        details = f"Value: {value}, Expected type: {expected_type}"
        super().__init__(message, details)
        self.pin_name = pin_name
        self.value = value
        self.expected_type = expected_type


class GraphError(PixelFlowError):
    """Base class for graph-related errors."""
    pass


class GraphValidationError(GraphError):
    """Error that occurs during graph validation."""
    
    def __init__(self, validation_errors: list[str]):
        message = "Graph validation failed"
        details = "; ".join(validation_errors)
        super().__init__(message, details)
        self.validation_errors = validation_errors


class GraphExecutionError(GraphError):
    """Error that occurs during graph execution."""
    
    def __init__(self, execution_step: str, error: Exception):
        message = f"Graph execution failed at step: {execution_step}"
        super().__init__(message, str(error))
        self.execution_step = execution_step
        self.original_error = error


class FileError(PixelFlowError):
    """Base class for file-related errors."""
    pass


class ProjectLoadError(FileError):
    """Error that occurs when loading a project file."""
    
    def __init__(self, file_path: str, reason: str):
        message = f"Failed to load project: {file_path}"
        super().__init__(message, reason)
        self.file_path = file_path


class ProjectSaveError(FileError):
    """Error that occurs when saving a project file."""
    
    def __init__(self, file_path: str, reason: str):
        message = f"Failed to save project: {file_path}"
        super().__init__(message, reason)
        self.file_path = file_path


class ImageLoadError(FileError):
    """Error that occurs when loading an image file."""
    
    def __init__(self, file_path: str, reason: str):
        message = f"Failed to load image: {file_path}"
        super().__init__(message, reason)
        self.file_path = file_path


class ImageSaveError(FileError):
    """Error that occurs when saving an image file."""
    
    def __init__(self, file_path: str, reason: str):
        message = f"Failed to save image: {file_path}"
        super().__init__(message, reason)
        self.file_path = file_path


class UIError(PixelFlowError):
    """Base class for UI-related errors."""
    pass


class WidgetCreationError(UIError):
    """Error that occurs when creating UI widgets."""
    
    def __init__(self, widget_type: str, reason: str):
        message = f"Failed to create widget: {widget_type}"
        super().__init__(message, reason)
        self.widget_type = widget_type


class LayoutError(UIError):
    """Error that occurs when setting up UI layouts."""
    
    def __init__(self, layout_type: str, reason: str):
        message = f"Failed to setup layout: {layout_type}"
        super().__init__(message, reason)
        self.layout_type = layout_type


class ConfigurationError(PixelFlowError):
    """Error that occurs when loading or saving configuration."""
    
    def __init__(self, config_key: str, reason: str):
        message = f"Configuration error: {config_key}"
        super().__init__(message, reason)
        self.config_key = config_key


class ValidationError(PixelFlowError):
    """Error that occurs during data validation."""
    
    def __init__(self, field_name: str, value: Any, constraint: str):
        message = f"Validation failed: {field_name}"
        details = f"Value: {value}, Constraint: {constraint}"
        super().__init__(message, details)
        self.field_name = field_name
        self.value = value
        self.constraint = constraint


class ResourceError(PixelFlowError):
    """Error that occurs when managing resources."""
    
    def __init__(self, resource_type: str, resource_id: str, reason: str):
        message = f"Resource error: {resource_type} ({resource_id})"
        super().__init__(message, reason)
        self.resource_type = resource_type
        self.resource_id = resource_id


class MemoryError(PixelFlowError):
    """Error that occurs when memory is insufficient."""
    
    def __init__(self, operation: str, required_memory: str):
        message = f"Insufficient memory for operation: {operation}"
        super().__init__(message, f"Required: {required_memory}")
        self.operation = operation
        self.required_memory = required_memory


class TimeoutError(PixelFlowError):
    """Error that occurs when an operation times out."""
    
    def __init__(self, operation: str, timeout_seconds: float):
        message = f"Operation timed out: {operation}"
        super().__init__(message, f"Timeout: {timeout_seconds}s")
        self.operation = operation
        self.timeout_seconds = timeout_seconds 