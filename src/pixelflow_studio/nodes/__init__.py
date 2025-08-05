"""
Image processing nodes for PixelFlow Studio.

This package contains all the built-in nodes for image processing operations.
"""

from .base import ImageProcessingNode
from .io_nodes import LoadImageNode, SaveImageNode, ImagePreviewNode
from .filter_nodes import BlurNode, SharpenNode
from .transform_nodes import ResizeNode, RotateNode, FlipNode
from .color_nodes import BrightnessContrastNode, HSVAdjustNode
from .generator_nodes import SolidColorNode, NoiseNode
from .variable_nodes import (
    FloatVariableNode, IntegerVariableNode, BooleanVariableNode, 
    StringVariableNode, PathVariableNode
)

__all__ = [
    "ImageProcessingNode",
    "LoadImageNode",
    "SaveImageNode", 
    "ImagePreviewNode",
    "BlurNode",
    "SharpenNode",
    "ResizeNode",
    "RotateNode",
    "FlipNode",
    "BrightnessContrastNode",
    "HSVAdjustNode",
    "SolidColorNode",
    "NoiseNode",
    "FloatVariableNode",
    "IntegerVariableNode", 
    "BooleanVariableNode",
    "StringVariableNode",
    "PathVariableNode",
]

# Registry of all available node classes
NODE_REGISTRY = {
    # I/O Nodes
    "LoadImageNode": LoadImageNode,
    "SaveImageNode": SaveImageNode,
    "ImagePreviewNode": ImagePreviewNode,
    
    # Filter Nodes
    "BlurNode": BlurNode,
    "SharpenNode": SharpenNode,
    
    # Transform Nodes
    "ResizeNode": ResizeNode,
    "RotateNode": RotateNode,
    "FlipNode": FlipNode,
    
    # Color Nodes
    "BrightnessContrastNode": BrightnessContrastNode,
    "HSVAdjustNode": HSVAdjustNode,
    
    # Generator Nodes
    "SolidColorNode": SolidColorNode,
    "NoiseNode": NoiseNode,
    
    # Variable Nodes
    "FloatVariableNode": FloatVariableNode,
    "IntegerVariableNode": IntegerVariableNode,
    "BooleanVariableNode": BooleanVariableNode,
    "StringVariableNode": StringVariableNode,
    "PathVariableNode": PathVariableNode,
}

def get_node_class(class_name: str):
    """Get a node class by name."""
    return NODE_REGISTRY.get(class_name)

def get_all_node_classes():
    """Get all registered node classes."""
    return list(NODE_REGISTRY.values())

def get_node_categories():
    """Get all node categories."""
    categories = {}
    for node_class in NODE_REGISTRY.values():
        # Create temporary instance to get category
        temp_instance = node_class()
        category = temp_instance.category
        if category not in categories:
            categories[category] = []
        categories[category].append(node_class)
    return categories 